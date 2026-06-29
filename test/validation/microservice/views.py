import os
from django.shortcuts import render
from django.http import HttpResponse
import json
from shapely import ops, union_all,reverse
from shapely.geometry import Point, box, LineString
from shapely.ops import snap, unary_union, linemerge
import numbers
import numpy as np
import geopandas as gpd
import pandas as pd
import networkx as nx
from collections import defaultdict
import copy




def get_max_route_order(gdf, idxs, prop="sketchrouteorder"):

    max_val = None

    for idx in idxs:
        val = gdf.at[idx, prop] if prop in gdf.columns else None

        if val is None:
            continue

        try:
            val = int(val)
        except:
            continue

        if max_val is None or val > max_val:
            max_val = val

    return max_val


def merge_lines_ordered(geoms):

    if not geoms:
        return None

    geoms = [LineString(g.coords) for g in geoms]

    merged_coords = list(geoms[0].coords)

    for g in geoms[1:]:

        start = merged_coords[-1]

        g_coords = list(g.coords)

        if g_coords[0] == start:
            merged_coords.extend(g_coords[1:])

        elif g_coords[-1] == start:
            merged_coords.extend(g_coords[-2::-1])

        else:
            # find closest endpoint
            d1 = (g_coords[0][0]-start[0])**2 + (g_coords[0][1]-start[1])**2
            d2 = (g_coords[-1][0]-start[0])**2 + (g_coords[-1][1]-start[1])**2

            if d1 < d2:
                merged_coords.extend(g_coords[1:])
            else:
                merged_coords.extend(g_coords[-2::-1])

    return LineString(merged_coords)

def merge_simple_intersections(linegdf):

    nodes = []
    for line in linegdf.geometry:
        nodes.append(Point(line.coords[0]))
        nodes.append(Point(line.coords[-1]))

    nodes_gs = gpd.GeoSeries(nodes)
    unique_nodes = nodes_gs.drop_duplicates()


    streetsegments_geoseries = linegdf.geometry


    # Build spatial index for lines
    sindex = streetsegments_geoseries.sindex

    records = []
    for i, n in enumerate(unique_nodes):
        # Candidate line indices that might intersect
        possible_idxs = list(sindex.intersection(n.bounds))
        if not possible_idxs:
            records.append({
                "geometry": n,
                "n_intersections": 0,
                "line_ids": []
            })
            continue

        # Filter actual intersections
        intersects_mask = streetsegments_geoseries.iloc[possible_idxs].intersects(n)
        intersecting_ids = list(linegdf.iloc[possible_idxs][intersects_mask]["id"])

        records.append({
            "geometry": n,
            "n_intersections": len(intersecting_ids),
            "line_ids": intersecting_ids
        })

    # Return GeoDataFrame
    pointsandlines =  gpd.GeoDataFrame(records)


    filteredsegments = pointsandlines[pointsandlines["n_intersections"] == 2]


    # --- STEP 2: Build connectivity graph
    G = nx.Graph()
    for line_ids in filteredsegments["line_ids"]:
        if len(line_ids) == 2:
            G.add_edge(line_ids[0], line_ids[1])

    # --- STEP 3: Find connected components (chains)
    merged_records = []
    merged_ids = set()
    id_mapping = {}
    merged_audit = []

    for component in nx.connected_components(G):
        component_ids = list(component)
        linestobemerged = linegdf[linegdf["id"].isin(component_ids)].copy()

        merged_line = merge_lines_ordered(list(linestobemerged.geometry))
        representative_row = linestobemerged.iloc[0].copy()
        new_id = representative_row["id"]

        representative_row["geometry"] = merged_line
        representative_row["merged_from"] = component_ids

        merged_records.append(representative_row)
        merged_ids.update(component_ids)

        # map old ids → new id
        for old_id in component_ids:
            id_mapping[old_id] = new_id

        merged_audit.append({
            "new_id": new_id,
            "merged_from": component_ids
        })

    # --- STEP 4: Combine back
    merged_gdf = gpd.GeoDataFrame(merged_records)
    cleaned_gdf = linegdf[~linegdf["id"].isin(merged_ids)].copy()
    cleaned_gdf = pd.concat([cleaned_gdf, merged_gdf], ignore_index=True)

    gj = json.loads(cleaned_gdf.to_json())

    # Remove feature-level "id"
    for feature in gj["features"]:
        feature.pop("id", None)  # remove the "id" key if it exists
    geojson_str = json.dumps(gj)



    return geojson_str, id_mapping, merged_audit




def snap_line_endpoints(lines_gdf, bounds=[[0,0],[600,850]]):

    # store before geometries as WKT (simple, fast)
    before_wkt = {row["id"]: row.geometry.wkt for _, row in lines_gdf.iterrows()}

    # Extract endpoints
    endpoints = [Point(line.coords[0]) for line in lines_gdf.geometry] + \
                [Point(line.coords[-1]) for line in lines_gdf.geometry]
    endpoints_gs = gpd.GeoSeries(endpoints)

    bounds = [[0, 0], [600, 850]]  # xmin, ymin, xmax, ymax in coordinate units
    # Compute tolerance from bounds in same units as coordinates
    xmin, ymin = bounds[0]
    xmax, ymax = bounds[1]
    width = xmax - xmin
    height = ymax - ymin
    tolerance = 0.01 * min(width, height)  # 1% of smaller dimension


    # Snap endpoints
    endpoints_union = unary_union(endpoints_gs)
    snapped_lines = lines_gdf.copy()
    snapped_lines["geometry"] = snapped_lines.geometry.apply(
        lambda g: snap(g, endpoints_union, tolerance)
    )

    # detect real changes
    changed_ids = []
    for _, row in snapped_lines.iterrows():
        _id = row["id"]
        if row.geometry.wkt != before_wkt[_id]:
            changed_ids.append(_id)


    return snapped_lines,changed_ids

def find_snapped_groups(original_lines_gdf, snapped_lines_gdf, id_col="id"):
    # Step 1: before intersections
    before_pairs = endpoint_intersection_pairs(original_lines_gdf, id_col=id_col)

    # Step 2: after intersections
    after_pairs = endpoint_intersection_pairs(snapped_lines_gdf, id_col=id_col)

    # Step 3: pairs that are new (were not intersecting before)
    new_pairs = after_pairs - before_pairs



    return new_pairs


# small helpers
def _to_native_id(x):
    # convert numpy/pandas ints to native int when possible, else str
    try:
        return int(x)
    except Exception:
        return str(x)

def _id_sort_key(x):
    # sort numeric ids numerically, strings lexicographically
    if isinstance(x, int):
        return (0, x)
    try:
        xi = int(x)
        return (0, xi)
    except Exception:
        return (1, str(x))


def endpoint_intersection_pairs(lines_gdf, id_col="id"):
    rows = []

    for _, row in lines_gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.geom_type != "LineString":
            continue

        sid = row[id_col]
        coords = list(geom.coords)
        for (x, y) in coords:
            rows.append({"id": sid, "x": x, "y": y})

    if not rows:
        return set()

    df_ep = pd.DataFrame(rows)

    # group by coordinate, collect ids that meet at that coordinate
    grouped = df_ep.groupby(["x", "y"])["id"].apply(list)

    pairs = set()
    for seg_ids in grouped:
        if len(seg_ids) < 2:
            continue
        seg_ids = [_to_native_id(s) for s in seg_ids]
        for i in range(len(seg_ids)):
            for j in range(i + 1, len(seg_ids)):
                a, b = seg_ids[i], seg_ids[j]
                if a == b:
                    continue
                pairs.add(frozenset((a, b)))

    return pairs

def combine_by_alignment(alignment):
    groups = []

    for key, value in alignment.items():
        if key == "checkAlignnum":
            continue

        base = set(value["BaseAlign"]["0"])
        sketch = set(sum(value["SketchAlign"].values(), []))

        merged = False

        for g in groups:
            if base & g["base"] or sketch & g["sketch"]:
                g["base"].update(base)
                g["sketch"].update(sketch)
                merged = True
                break

        if not merged:
            groups.append({
                "base": set(base),
                "sketch": set(sketch),
                "genType": value.get("genType"),
                "degreeOfGeneralization": value.get("degreeOfGeneralization")
            })

    merged = {}

    for i, g in enumerate(groups, start=1):
        merged[str(i)] = {
            "BaseAlign": {"0": list(g["base"])},
            "SketchAlign": {"0": list(g["sketch"])},
            "genType": g["genType"],
            "degreeOfGeneralization": g["degreeOfGeneralization"]
        }

    merged["checkAlignnum"] = len(groups)
    return merged

def remap_alignment_ids(alignment, id_mapping):
    """
    Update alignment dictionary to reflect new IDs from merging.
    """
    new_alignment = {}

    for key, value in alignment.items():
        if key == "checkAlignnum":
            continue

        new_val = copy.deepcopy(value)

        # ---- BaseAlign remap ----
        new_basealign = {}
        for k, v in value["BaseAlign"].items():
            new_ids = [id_mapping.get(old_id, old_id) for old_id in v]
            new_basealign[k] = list(set(new_ids))

        new_val["BaseAlign"] = new_basealign

        # ---- SketchAlign remap ----
        new_sketchalign = {}
        for k, v in value["SketchAlign"].items():
            new_ids = [id_mapping.get(old_id, old_id) for old_id in v]
            new_sketchalign[k] = list(set(new_ids))

        new_val["SketchAlign"] = new_sketchalign

        new_alignment[key] = new_val

    new_alignment["checkAlignnum"] = len(new_alignment)

    return new_alignment



def validateRoute(line_gdf, route_ids, id_col="id", inplace=False):
    if not route_ids or len(route_ids) < 2:
        return line_gdf if inplace else line_gdf.copy()

    gdf = line_gdf if inplace else line_gdf.copy()
    id_to_idx = {val: idx for idx, val in gdf[id_col].items()}

    # normalize
    if not isinstance(route_ids[0], list):
        route_steps = [[rid] for rid in route_ids]
    else:
        route_steps = [list(step) for step in route_ids]

    def sort_group_spatially(group_ids, entry_point):
        remaining = list(group_ids)
        ordered = []
        current_point = entry_point

        while remaining:
            best_id   = None
            best_idx  = None
            best_dist = float("inf")
            best_flip = False

            for rid in remaining:
                idx = id_to_idx.get(rid)
                if idx is None:
                    continue
                geom  = gdf.at[idx, "geometry"]
                start = tuple(geom.coords[0])
                end   = tuple(geom.coords[-1])

                d_start = (start[0]-current_point[0])**2 + (start[1]-current_point[1])**2
                d_end   = (end[0]-current_point[0])**2   + (end[1]-current_point[1])**2

                if d_start < best_dist:
                    best_dist = d_start
                    best_id   = rid
                    best_idx  = idx
                    best_flip = False

                if d_end < best_dist:
                    best_dist = d_end
                    best_id   = rid
                    best_idx  = idx
                    best_flip = True

            if best_flip:
                gdf.at[best_idx, "geometry"] = reverse(gdf.at[best_idx, "geometry"])

            ordered.append(best_id)
            remaining.remove(best_id)
            current_point = tuple(gdf.at[best_idx, "geometry"].coords[-1])

        return ordered, current_point

    # Step 1: Orient first group using second group as reference
    # Find entry point for first group — work backwards from second group
    first_group  = route_steps[0]
    second_group = route_steps[1]

    s_idx = id_to_idx.get(second_group[0])
    if s_idx is not None:
        s_geom = gdf.at[s_idx, "geometry"]
        # entry to first group is whichever end of second group's first segment
        # is NOT the connection point — use start of second group as the
        # "far end" to orient first group towards it
        entry_for_first = tuple(s_geom.coords[0])
    else:
        f_idx = id_to_idx.get(first_group[0])
        entry_for_first = tuple(gdf.at[f_idx, "geometry"].coords[0])

    # sort first group spatially, ending closest to second group
    # we want the EXIT of first group to be close to second group entry
    # so we find entry_point as the opposite end — use the far end of second group
    s_geom      = gdf.at[s_idx, "geometry"]
    s_start     = tuple(s_geom.coords[0])
    s_end       = tuple(s_geom.coords[-1])

    f_idx0      = id_to_idx.get(first_group[0])
    f_geom0     = gdf.at[f_idx0, "geometry"]
    f_start     = tuple(f_geom0.coords[0])
    f_end       = tuple(f_geom0.coords[-1])

    # pick whichever end of first segment is farther from second group
    d_fs = min((f_start[0]-s_start[0])**2+(f_start[1]-s_start[1])**2,
               (f_start[0]-s_end[0])**2  +(f_start[1]-s_end[1])**2)
    d_fe = min((f_end[0]-s_start[0])**2  +(f_end[1]-s_start[1])**2,
               (f_end[0]-s_end[0])**2    +(f_end[1]-s_end[1])**2)

    # entry_point for sorting = the far end (we want to walk TOWARDS second group)
    far_entry = f_start if d_fs > d_fe else f_end

    ordered_first, exit_point = sort_group_spatially(first_group, far_entry)
    route_steps[0] = ordered_first

    # Step 2: Chain remaining groups
    current_exit = exit_point

    for step_i in range(1, len(route_steps)):
        ordered, current_exit = sort_group_spatially(route_steps[step_i], current_exit)
        route_steps[step_i] = ordered

    return gdf

def to_builtin_types(obj):
    """
    Recursively convert numpy / pandas types to native Python types
    Useful just before json.dumps
    """
    # primitives
    if isinstance(obj, (str, bool, type(None))):
        return obj
    if isinstance(obj, numbers.Integral) and not isinstance(obj, bool):
        return int(obj)
    if isinstance(obj, numbers.Real):
        return float(obj)
    # numpy scalar types
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    # mapping
    if isinstance(obj, dict):
        return { to_builtin_types(k): to_builtin_types(v) for k, v in obj.items() }
    # list/tuple
    if isinstance(obj, (list, tuple, set)):
        return [to_builtin_types(i) for i in obj]
    # fallback to string
    return str(obj)



def apply_approved_snaps(line_gdf, snap_groups, id_col="id", inplace=False):


    gdf = line_gdf if inplace else line_gdf.copy()

    # id -> row index
    id_to_idx = {row_id: idx for idx, row_id in gdf[id_col].items()}
    snap_groups = snap_groups or []
    for group in snap_groups:
        if not group or len(group) < 2:
            continue

        # anchor is the first id in the group
        anchor_id = group[0]
        anchor_idx = id_to_idx.get(anchor_id)
        if anchor_idx is None:
            continue

        anchor_geom = gdf.at[anchor_idx, "geometry"]
        anchor_coords = list(anchor_geom.coords)
        anchor_endpoints = [anchor_coords[0], anchor_coords[-1]]  # (x,y) tuples

        # snap all other lines in the group to the anchor endpoints
        for sid in group[1:]:
            idx = id_to_idx.get(sid)
            if idx is None:
                continue

            geom = gdf.at[idx, "geometry"]
            coords = list(geom.coords)
            if len(coords) < 2:
                continue

            # endpoints of this line
            ep = [coords[0], coords[-1]]

            # find which endpoint (start or end) is closest to which anchor endpoint
            min_dist2 = float("inf")
            best_anchor = None
            best_ep_idx = None

            for a in anchor_endpoints:
                for j, e in enumerate(ep):
                    dx = a[0] - e[0]
                    dy = a[1] - e[1]
                    d2 = dx*dx + dy*dy  # squared distance
                    if d2 < min_dist2:
                        min_dist2 = d2
                        best_anchor = a
                        best_ep_idx = j

            # move that endpoint to the chosen anchor coord
            if best_ep_idx == 0:
                coords[0] = best_anchor
            else:
                coords[-1] = best_anchor

            gdf.at[idx, "geometry"] = LineString(coords)

    return gdf

from shapely.ops import linemerge

def apply_approved_merges(line_gdf, merge_groups, id_col="id", inplace=False):

    gdf = line_gdf if inplace else line_gdf.copy()

    # id -> row index
    id_to_idx = {row_id: idx for idx, row_id in gdf[id_col].items()}

    rows_to_drop = []
    for group in merge_groups:
        if not group or len(group) < 2:
            continue

        # collect valid indices for this group
        idxs = []
        for sid in group:
            idx = id_to_idx.get(sid)
            if idx is not None:
                idxs.append(idx)

        if len(idxs) < 2:
            continue

        # geometries to merge
        geoms = list(gdf.loc[idxs, "geometry"])
        merged_geom = merge_lines_ordered(geoms)

        # representative = first id in group
        rep_id = group[0]
        rep_idx = id_to_idx.get(rep_id)

        # get max sketchrouteorder
        max_order = get_max_route_order(gdf, idxs, "sketchrouteorder")

        if rep_idx is None:
            # fallback: first index in idxs
            rep_idx = idxs[0]
            rep_id = gdf.at[rep_idx, id_col]

        # assign merged geometry to representative row
        gdf.at[rep_idx, "geometry"] = merged_geom
        if max_order is not None:
            gdf.at[rep_idx, "SketchRouteSeqOrder"] = max_order

        # mark other rows for deletion
        for idx in idxs:
            if idx != rep_idx:
                rows_to_drop.append(idx)

    if rows_to_drop:
        gdf = gdf.drop(index=rows_to_drop).reset_index(drop=True)

    return gdf

def convert_mapping_to_sketch_ids(id_mapping):
    sketch_mapping = {}
    for k, v in id_mapping.items():
        sketch_mapping[f"S{k}"] = f"S{v}"
    return sketch_mapping


def validate(request):
    type= request.POST.get('type')
    action = request.POST.get('action', 'preview')  # 'preview' or 'apply'

    if type == "metric":
        metricmapdata = request.POST.get('metricdata')
        routearray_raw = request.POST.get('route')  # string like "[1,2,3]"
        print("routearray_", routearray_raw)
        route_ids = json.loads(routearray_raw) if routearray_raw else []
        print(route_ids)

        metricMap = json.loads(metricmapdata)


        features = metricMap.get("features", [])

        line_features = []
        polygon_features = []

        for f in features:
            gtype = f["geometry"]["type"]
            if gtype == "LineString":
                line_features.append(f)
            elif gtype in ("Polygon", "MultiPolygon"):
                polygon_features.append(f)

        # Convert lines to GeoDataFrame
        line_gdf = gpd.GeoDataFrame.from_features(line_features)



        # --- Snap and merge Lines ---
        snapped_lines, snapped_ids = snap_line_endpoints(line_gdf)
        grouped_snaps = find_snapped_groups(line_gdf, snapped_lines)
        merged_lines_json, id_mapping,merged_audit = merge_simple_intersections(snapped_lines)



        snap_id_pairs = [sorted(list(g)) for g in grouped_snaps]

        audit = {
            "snap": snap_id_pairs,
            "merge": merged_audit
        }


        if action == 'preview':
            # Return proposed edits and audit to UI — do NOT commit changes
            return HttpResponse(json.dumps({
                "audit": to_builtin_types(audit)
            }), content_type="application/json")

        if action == 'apply':
            approved_snap_pairs = request.POST.get('snap')
            approved_merge_pairs = request.POST.get('merge')
            approved_snap_json = json.loads(approved_snap_pairs) if approved_snap_pairs else []
            approved_merge_json = json.loads(approved_merge_pairs) if approved_merge_pairs else []

            snapped_lines = apply_approved_snaps(line_gdf, approved_snap_json, id_col="id", inplace=False)

            approved_merge_json = approved_merge_json or []
            merge_groups = [m["merged_from"] for m in approved_merge_json]
            merged_lines = apply_approved_merges(snapped_lines, merge_groups, id_col="id", inplace=False)
            print ("inside apply", route_ids)
            routecorrected = validateRoute(merged_lines, route_ids, id_col="id", inplace=False)

            edited_lines_geojson = json.loads(routecorrected.to_json())
            edited_line_features = edited_lines_geojson["features"]


            # 3) combine back with polygons
            final_geojson = {
                "type": "FeatureCollection",
                "features": edited_line_features + polygon_features
            }




            return HttpResponse(json.dumps({
                "modifiedStreets": final_geojson
            }), content_type="application/json")


    if type == "sketch":
        sketchmapdata = request.POST.get('sketchdata')
        alignmentdata = request.POST.get('alignment')
        routearray_raw = request.POST.get('route')  # string like "[1,2,3]"
        route_ids = json.loads(routearray_raw) if routearray_raw else []


        sketchMap = json.loads(sketchmapdata)
        alignment = json.loads(alignmentdata)

        # assume metricMap is GeoJSON: {"type": "FeatureCollection", "features": [...]}
        features = sketchMap.get("features", [])

        line_features = []
        polygon_features = []

        for f in features:
            gtype = f["geometry"]["type"]
            if gtype == "LineString":
                line_features.append(f)
            elif gtype in ("Polygon", "MultiPolygon"):
                polygon_features.append(f)

        # Convert lines to GeoDataFrame
        line_gdf = gpd.GeoDataFrame.from_features(line_features)

        # --- Snap and merge Lines ---
        snapped_lines, snapped_ids = snap_line_endpoints(line_gdf)
        grouped_snaps = find_snapped_groups(line_gdf, snapped_lines)
        merged_lines_json, id_mapping, merged_audit = merge_simple_intersections(snapped_lines)
        snap_id_pairs = [sorted(list(g)) for g in grouped_snaps]


        audit = {
            "snap": snap_id_pairs,
            "merge": merged_audit
        }

        if action == 'preview':
            # Return proposed edits and audit to UI — do NOT commit changes
            return HttpResponse(json.dumps({
                "audit": to_builtin_types(audit)
            }), content_type="application/json")

        if action == 'apply':
            approved_snap_pairs = request.POST.get('snap')
            approved_merge_pairs = request.POST.get('merge')
            approved_snap_json = json.loads(approved_snap_pairs) if approved_snap_pairs else []
            approved_merge_json = json.loads(approved_merge_pairs) if approved_merge_pairs else []

            snapped_lines = apply_approved_snaps(line_gdf, approved_snap_json, id_col="id", inplace=False)

            approved_merge_json = approved_merge_json or []
            merge_groups = [m["merged_from"] for m in approved_merge_json]
            merged_lines = apply_approved_merges(snapped_lines, merge_groups, id_col="id", inplace=False)
            print ("inside apply", route_ids)
            routecorrected = validateRoute(merged_lines, route_ids, id_col="id", inplace=False)

            edited_lines_geojson = json.loads(routecorrected.to_json())
            edited_line_features = edited_lines_geojson["features"]

            # 3) combine back with polygons
            final_geojson = {
                "type": "FeatureCollection",
                "features": edited_line_features + polygon_features
            }




            sketch_id_mapping = convert_mapping_to_sketch_ids(id_mapping)
            remapped_alignment = remap_alignment_ids(alignment, sketch_id_mapping)
            corrected_alignment = combine_by_alignment(remapped_alignment)
            print (corrected_alignment, id_mapping)

            response_data = {
                "modifiedStreets": final_geojson,
                "updated_alignment": corrected_alignment
            }



            return HttpResponse(
                json.dumps(to_builtin_types(response_data)),
                content_type="application/json"
            )











