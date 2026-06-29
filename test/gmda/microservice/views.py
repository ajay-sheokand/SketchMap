import json 
import math
import numpy as np
from collections import defaultdict
from shapely.geometry import shape
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



def _normalize_align_value(v):
    """
    This function normalizes the align values to a list of strings. Since SketchAlign values from 
    a feature can be a string, a list, or  nested. This will always return a clean flat list of sketch IDs.
    """
    if v is None: 
        return []
    if isinstance(v, (list, tuple)):
        out = []
        for x in v:
            out.extend(_normalize_align_value(x))
        return out
    s = str(v).strip()
    if s.lower().startswith('s') and s[1:].isdigit():
        s = s[1:]
    return [s] if s else []


def compute_mbr_points(geometry, r_buffer = 1):
    """
    This function will compute the 8 points from the Minimum Bounding 
    Rectangle drawn on a Polygon or MultiPolygon, 
    if it is a PointMarker, it will draw a buffer of 1 pixel radius
    and then extract the 8 points from the MBR.
    """ 
    if geometry.geom_type in ('Polygon', 'MultiPolygon'):
        x_min, y_min, x_max, y_max = map(float, geometry.bounds)
    elif geometry.geom_type =='Point':
        coords = list(geometry.coords)[0]
        x, y = float(coords[0]), float(coords[1])
        x_min, x_max = x - r_buffer, x + r_buffer
        y_min, y_max = y -r_buffer, y + r_buffer
    else:
        return None
    return [
        [x_min, y_max], [(x_min + x_max) / 2, y_max], 
        [x_max, y_max],
        [x_max, (y_min + y_max) / 2], [x_max, y_min],
        [(x_min + x_max) / 2, y_min],
        [x_min, y_min], 
        [x_min, (y_min + y_max) / 2] 
    ]


def landmark_pairs_generator(v_pairs, b_mbr, s_mbr):
    """
    This function will generate all possible point pairs between every pair of aligned
    landmarks by comparing each of the MBR points of one landmark against 
    each of the 8 MBR points of another landmakr.  
    """
    for i in range(len(v_pairs) - 1):
        b1, s1 = v_pairs[i]
        for j in range( i+1 ,len(v_pairs)):
            b2, s2 = v_pairs[j]
            if s1 == s2:
                continue
            b1_pts = b_mbr.get(b1)
            s1_pts = s_mbr.get(s1)
            b2_pts = b_mbr.get(b2)
            s2_pts = s_mbr.get(s2)
            if (
                b1_pts is None
                or s1_pts is None
                or b2_pts is None
                or s2_pts is None
            ):
                continue
            for p1 in range(8):
                for p2 in range(8):
                    yield (
                        b1_pts[p1][0], b1_pts[p1][1],
                        b2_pts[p2][0], b2_pts[p2][1],
                        s1_pts[p1][0], s1_pts[p1][1],
                        s2_pts[p2][0], s2_pts[p2][1]
                    )

class UnionFind:
    """ 
    This is used to group lanmarks that are aligned together.
    For example, if B1 is aligned to S1 and S2 features, 
    UnionFind will group S1 and S2 together, 
    so that we can handle them correctly. 
    (excluding them from 1-to-1 pairs)
    """
    def __init__(self):
        self.parent = {}
    
    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px != py:
            self.parent[px] = py

def compute_gmda(basemap_geojson, sketchmap_geojson):
    """
    
    """
    LANDMARK_TYPES = ('Polygon', 'MultiPolygon', 'CircleMarker', 'Landmark')

    # Loading Basemap Landmarks
    bsm_rows = []
    for feat in basemap_geojson.get('features', []):
        props = (feat.get('properties') or {}).copy()#
        try:
            geom = shape(feat['geometry'])
            props['geometry'] = geom
            otype = props.get('otype') or geom.geom_type
            if otype in LANDMARK_TYPES:
                if geom.geom_type in ('Polygon', 'MultiPolygon') and not geom.is_valid:
                    continue
                bsm_rows.append(props)
        except Exception as e:
                continue
    
    # Loading Sketchmap Landmarks
    skm_rows = []
    for feat in sketchmap_geojson.get('features', []):
        props = (feat.get('properties') or {}).copy()
        try:
            geom = shape(feat['geometry'])
            props['geometry'] = geom
            otype = props.get('otype') or geom.geom_type
            if otype in LANDMARK_TYPES:
                if geom.geom_type in ('Polygon', 'MultiPolygon') and not geom.is_valid:
                    continue
                skm_rows.append(props)
        except Exception as e:
            continue

    # Building MBR points for basemap and sketchmap landmarks
    #This builds two dictionaries, 
    # One for the basemap landmarks 
    # Second, for the sketchmap landmarks
    # mapping each feature ID to its 8 mbr points.
    bsm_dict_mbr = {}
    for row in bsm_rows:
        mbr = compute_mbr_points(row['geometry'])
        if mbr:
            base_id = str(row.get('id', '')).strip()
            if base_id:
                bsm_dict_mbr[base_id] = mbr 
    
    skm_dict_mbr = {}
    for row in skm_rows:
        mbr = compute_mbr_points(row['geometry'])
        sk_id_raw = row.get('sid') or row.get('id')
        if sk_id_raw is not None:
            sk_id = str(sk_id_raw).strip()
            if sk_id.lower().startswith('s') and sk_id[1:].isdigit():
                sk_id = sk_id[1:]
            if mbr:
                skm_dict_mbr[sk_id] = mbr
    
    # Building alignment map from basemap SketchAlign property.
    alignment_map = {}
    for b_row in bsm_rows:
        if b_row.get('missing') is True:
            continue
        otype = b_row.get('otype') or b_row['geometry'].geom_type
        if otype not in LANDMARK_TYPES:
            continue
        base_id = str(b_row.get('id', '')).strip()
        if not base_id:
            continue
        linked = _normalize_align_value(b_row.get('SketchAlign'))
        if linked:
            alignment_map[base_id] = linked

    # Union-Find to group sketchmap features that are aligned together
    #This will read the SketchAlign property from each basemap feature
    # to find which sketch features are aligned to it, 
    # and then it uses UnionFind to group them together.
    uf = UnionFind()
    for base_id, sketch_ids in alignment_map.items():
        for s_id in sketch_ids:
            uf.union(f"B_{base_id}", f"S_{s_id}")
    
    groups = defaultdict(lambda: {'base_ids':set(), 'sketch_ids':set()})
    for base_id, sketch_ids in alignment_map.items():
        root = uf.find(f"B_{base_id}")
        groups[root]['base_ids'].add(base_id)
        for s_id in sketch_ids:
            groups[root]['sketch_ids'].add(s_id)
        
    #Classifying pairs
    #This will separate the 1 to 1 aligned pairs from the 
    #many to one pairs , ntl is total number of landmarks, ndl is the number of drawn landmarks (1 to 1 pairs)

    verified_pairs = []
    excluded_base_ids = set()
    for group in groups.values():
        num_sketch = len(group['sketch_ids'])
        if num_sketch == 1:
            sketch_id = list(group['sketch_ids'])[0]
            for base_id in group['base_ids']:
                if base_id in bsm_dict_mbr and sketch_id in skm_dict_mbr:
                    verified_pairs.append((base_id, sketch_id))
        else:
            excluded_base_ids.update(group['base_ids'])

    nTL = len(bsm_dict_mbr) - len(excluded_base_ids)
    nDL = len(verified_pairs)

    if nDL < 2:
        return {
            'ERROR' : "Insufficient number of aligned Landmark Pairs (Need atleast 2)",
            'Number of Total Landmarks': nTL,
            'Number of Drawn Landmarks': nDL
        }

    # Computing GMDA Metrics

    pairs_gen = list(landmark_pairs_generator(verified_pairs, bsm_dict_mbr, skm_dict_mbr))
    def comb2(n):
        return n * (n - 1) // 2

    n_nTL = comb2(8 * nTL) - nTL * comb2(8) if nTL > 1 else 0
    n_nDL = len(pairs_gen) if pairs_gen else 1

    sum_can, sum_dist_abs, sum_sca_bias = 0, 0, 0
    sum_rot_sin, sum_rot_cos, sum_ang_abs = 0, 0, 0
    max_db, max_ds = 0.001, 0.001

    for b1x, b1y, b2x, b2y, s1x, s1y, s2x, s2y in pairs_gen:
        max_db = max(max_db, np.sqrt((b1x - b2x)**2 + (b1y - b2y)**2))
        max_ds = max(max_ds, np.sqrt((s1x - s2x)**2 + (s1y - s2y)**2))

    for b1x, b1y, b2x, b2y, s1x, s1y, s2x, s2y in pairs_gen:
        if (b1y < b2y and s1y < s2y) or (b1y > b2y and s1y > s2y):
            sum_can += 1
        if (b1x < b2x and s1x < s2x) or (b1x > b2x and s1x > s2x):
            sum_can += 1
        db = np.sqrt((b1x - b2x)**2 + (b1y - b2y)**2) / max_db
        ds = np.sqrt((s1x - s2x)**2 + (s1y - s2y)**2) / max_ds
        sum_sca_bias += (ds - db)
        sum_dist_abs += abs(ds - db)
        ang_b = np.arctan2(b2x - b1x, b2y - b1y)
        ang_s = np.arctan2(s2x - s1x, s2y - s1y)
        d = (ang_s - ang_b + np.pi) % (2 * np.pi) - np.pi
        sum_rot_sin += np.sin(d)
        sum_rot_cos += np.cos(d)
        sum_ang_abs += abs(np.degrees(d))

    return {
        'CanOrg':  round(float(sum_can / (2 * n_nTL)), 4) if n_nTL > 0 else 0,
        'CanAcc':  round(float(sum_can / (2 * n_nDL)), 4) if n_nDL > 0 else 0,
        'ScaBias': round(float(sum_sca_bias / n_nDL), 4) if n_nDL > 0 else 0,
        'DistAcc': round(float(1 - (sum_dist_abs / n_nDL)), 4) if n_nDL > 0 else 0,
        'RotBias': round(float(np.degrees(np.arctan2(sum_rot_sin, sum_rot_cos))), 4),
        'AngAcc':  round(float(1 - sum_ang_abs / (180 * n_nDL)), 4) if n_nDL > 0 else 0,
        'nTL': nTL,
        'nDL': nDL,
    }


def find_juncs_from_geojson(geojson_dict, prefix, valid_ids, id_property='id'):
    """
    
    """
    coord_map = defaultdict(list)

    for feat in geojson_dict.get('features', []):
        geom_dict = feat.get('geometry')
        if not geom_dict or geom_dict.get('type') != 'LineString':
            continue
        props = feat.get('properties', {})
        line_id = str(props.get(id_property, ''))
        if line_id.lower().startswith('s') and line_id[1:].isdigit():
            line_id = line_id[1:]
        if line_id not in valid_ids:
            continue
        coords = geom_dict.get('coordinates', [])
        if len(coords) < 2:
            continue
        for pt in [coords[0], coords[-1]]:
            key = (round(pt[0], 3), round(pt[1], 3))
            if line_id not in coord_map[key]:
                coord_map[key].append(line_id)
        
    junctions = {}
    jb_id = 0
    for (rx, ry), connected_roads in coord_map.items():
        if len(connected_roads) >= 2:
            junc_key = f"{prefix}{jb_id}"
            junctions[junc_key] = [(rx, ry), connected_roads]
            jb_id += 1

    mbr_dict = {}
    for junc_key in junctions:
        r = 1.0
        x, y = junctions[junc_key][0]
        x_min, x_max = x - r, x + r
        y_min, y_max = y - r, y + r
        mbr_dict[junc_key] = [
            [x_min, y_max], [(x_min+x_max)/2, y_max], [x_max, y_max],
            [x_max, (y_min+y_max)/2], [x_max, y_min], [(x_min+x_max)/2, y_min],
            [x_min, y_min], [x_min, (y_min+y_max)/2]
        ]

    return junctions, mbr_dict



def compute_JunctionGMDA(basemap_geojson, sketchmap_geojson):
    # --- Get all basemap line IDs (for nTL - all basemap junctions) ---
    all_bsm_ids = set()
    for feat in basemap_geojson.get('features', []):
        if feat.get('geometry', {}).get('type') == 'LineString':
            line_id = str(feat.get('properties', {}).get('id', ''))
            if line_id:
                all_bsm_ids.add(line_id)

    # --- Get all sketchmap line IDs (using sid property) ---
    all_skm_ids = set()
    for feat in sketchmap_geojson.get('features', []):
        if feat.get('geometry', {}).get('type') == 'LineString':
            sid = str(feat.get('properties', {}).get('sid', ''))
            if sid.lower().startswith('s') and sid[1:].isdigit():
                sid = sid[1:]
            if sid:
                all_skm_ids.add(sid)

    # --- Valid IDs = shared between basemap and sketchmap (same as notebook) ---
    valid_ids = all_bsm_ids.intersection(all_skm_ids)

    print(f"DEBUG: all_bsm_ids={len(all_bsm_ids)}, all_skm_ids={len(all_skm_ids)}, valid_ids={len(valid_ids)}")

    # --- For basemap: use ALL basemap IDs (counts all junctions in nTL) ---
    bsm_juncs, bsm_dict_mbr = find_juncs_from_geojson(
        basemap_geojson, prefix='JB', valid_ids=all_bsm_ids, id_property='id'
    )

    # --- For sketchmap: use only shared IDs ---
    skm_juncs, skm_dict_mbr = find_juncs_from_geojson(
        sketchmap_geojson, prefix='JS', valid_ids=valid_ids, id_property='sid'
    )

    print(f"DEBUG: Basemap Junctions Found: {len(bsm_juncs)}")
    print(f"DEBUG: Sketch Junctions Found: {len(skm_juncs)}")

    if not bsm_juncs or not skm_juncs:
        return {'ERROR': 'No junctions found', 'nTL': len(bsm_dict_mbr), 'nDL': 0}

    # --- Alignment via topology subset check (exactly as notebook cell 83) ---
    alignment_map = {}
    for s_id, s_info in skm_juncs.items():
        s_roads = set(s_info[1])
        for b_id, b_info in bsm_juncs.items():
            b_roads = set(b_info[1])
            if s_roads.issubset(b_roads):
                if b_id not in alignment_map:
                    alignment_map[b_id] = []
                alignment_map[b_id].append(s_id)

    # --- Union-Find grouping (same as notebook) ---
    uf = UnionFind()
    for base_id, sketch_ids in alignment_map.items():
        for s_id in sketch_ids:
            uf.union(f"B_{base_id}", f"S_{s_id}")

    groups = defaultdict(lambda: {'base_ids': set(), 'sketch_ids': set()})
    for base_id, sketch_ids in alignment_map.items():
        root = uf.find(f"B_{base_id}")
        groups[root]['base_ids'].add(base_id)
        for s_id in sketch_ids:
            groups[root]['sketch_ids'].add(s_id)

    # --- Classify pairs (same as notebook) ---
    verified_pairs = []
    excluded_base_ids = set()

    for group in groups.values():
        num_sketch = len(group['sketch_ids'])
        if num_sketch == 1:
            sketch_id = list(group['sketch_ids'])[0]
            for base_id in group['base_ids']:
                if base_id in bsm_dict_mbr and sketch_id in skm_dict_mbr:
                    verified_pairs.append((base_id, sketch_id))
        else:
            excluded_base_ids.update(group['base_ids'])

    nTL = len(bsm_dict_mbr) - len(excluded_base_ids)
    nDL = len(verified_pairs)

    print(f"DEBUG: nTL={nTL}, nDL={nDL}, excluded={len(excluded_base_ids)}, total_bsm={len(bsm_dict_mbr)}")

    if nDL < 2:
        return {'ERROR': 'Insufficient junction pairs', 'nTL': nTL, 'nDL': nDL}

    pairs_gen = list(landmark_pairs_generator(verified_pairs, bsm_dict_mbr, skm_dict_mbr))

    def comb2(n):
        return n * (n - 1) // 2

    n_nTL = comb2(8 * nTL) - nTL * comb2(8) if nTL > 1 else 0
    n_nDL = len(pairs_gen) if pairs_gen else 1

    sum_can, sum_dist_abs, sum_sca_bias = 0, 0, 0
    sum_rot_sin, sum_rot_cos, sum_ang_abs = 0, 0, 0
    max_db, max_ds = 0.001, 0.001

    for b1x, b1y, b2x, b2y, s1x, s1y, s2x, s2y in pairs_gen:
        max_db = max(max_db, np.sqrt((b1x - b2x)**2 + (b1y - b2y)**2))
        max_ds = max(max_ds, np.sqrt((s1x - s2x)**2 + (s1y - s2y)**2))

    for b1x, b1y, b2x, b2y, s1x, s1y, s2x, s2y in pairs_gen:
        if (b1y < b2y and s1y < s2y) or (b1y > b2y and s1y > s2y):
            sum_can += 1
        if (b1x < b2x and s1x < s2x) or (b1x > b2x and s1x > s2x):
            sum_can += 1
        db = np.sqrt((b1x - b2x)**2 + (b1y - b2y)**2) / max_db
        ds = np.sqrt((s1x - s2x)**2 + (s1y - s2y)**2) / max_ds
        sum_sca_bias += (ds - db)
        sum_dist_abs += abs(ds - db)
        ang_b = np.arctan2(b2x - b1x, b2y - b1y)
        ang_s = np.arctan2(s2x - s1x, s2y - s1y)
        d = (ang_s - ang_b + np.pi) % (2 * np.pi) - np.pi
        sum_rot_sin += np.sin(d)
        sum_rot_cos += np.cos(d)
        sum_ang_abs += abs(np.degrees(d))

    return {
        'CanOrg':  round(float(sum_can / (2 * n_nTL)), 4) if n_nTL > 0 else 0,
        'CanAcc':  round(float(sum_can / (2 * n_nDL)), 4) if n_nDL > 0 else 0,
        'ScaBias': round(float(sum_sca_bias / n_nDL), 4) if n_nDL > 0 else 0,
        'DistAcc': round(float(1 - (sum_dist_abs / n_nDL)), 4) if n_nDL > 0 else 0,
        'RotBias': round(float(np.degrees(np.arctan2(sum_rot_sin, sum_rot_cos))), 4),
        'AngAcc':  round(float(1 - sum_ang_abs / (180 * n_nDL)), 4) if n_nDL > 0 else 0,
        'nTL': nTL,
        'nDL': nDL,
    }
"""
def compute_JunctionGMDA(basemap_geojson, sketchmap_geojson):

    import numpy as np
    import math

    # --------------------------------------------------
    # 1. Filter LineStrings by common IDs
    # --------------------------------------------------

    bsm_features = [
        f for f in basemap_geojson.get("features", [])
        if f["geometry"]["type"] == "LineString"
    ]

    skm_features = [
        f for f in sketchmap_geojson.get("features", [])
        if f["geometry"]["type"] == "LineString"
    ]

    bsm_ids = {str(f["properties"].get("id")) for f in bsm_features}
    skm_ids = {str(f["properties"].get("id")) for f in skm_features}

    valid_ids = bsm_ids.intersection(skm_ids)

    filtered_bsm = [
        f for f in bsm_features
        if str(f["properties"].get("id")) in valid_ids
    ]

    filtered_skm = [
        f for f in skm_features
        if str(f["properties"].get("id")) in valid_ids
    ]

    # --------------------------------------------------
    # 2. Junction Detection + MBR Creation
    # --------------------------------------------------

    def find_junctions_and_mbr(features, prefix):

        junctions = {}
        lines_list = []

        for f in features:

            coords = f["geometry"]["coordinates"]

            if len(coords) < 2:
                continue

            lines_list.append({
                "id": str(f["properties"].get("id")),
                "endpoints": [
                    tuple(coords[0]),
                    tuple(coords[-1])
                ]
            })

        def points_match(p1, p2, tol=1e-3):
            return (
                math.isclose(p1[0], p2[0], abs_tol=tol)
                and
                math.isclose(p1[1], p2[1], abs_tol=tol)
            )

        junc_counter = 0

        for i in range(len(lines_list)):

            for j in range(i + 1, len(lines_list)):

                line_a = lines_list[i]
                line_b = lines_list[j]

                for end_a in line_a["endpoints"]:

                    for end_b in line_b["endpoints"]:

                        if not points_match(end_a, end_b):
                            continue

                        new_junction = True

                        for junc_id in junctions.keys():

                            if points_match(
                                end_a,
                                junctions[junc_id][0]
                            ):

                                if (
                                    line_a["id"] in junctions[junc_id][1]
                                    and line_b["id"] not in junctions[junc_id][1]
                                ):
                                    junctions[junc_id][1].append(
                                        line_b["id"]
                                    )

                                elif (
                                    line_b["id"] in junctions[junc_id][1]
                                    and line_a["id"] not in junctions[junc_id][1]
                                ):
                                    junctions[junc_id][1].append(
                                        line_a["id"]
                                    )

                                new_junction = False
                                break

                        if new_junction:

                            junctions[
                                f"{prefix}{junc_counter}"
                            ] = [
                                end_a,
                                [line_a["id"], line_b["id"]]
                            ]

                            junc_counter += 1

        # -------------------------------
        # Build MBRs
        # -------------------------------

        mbr_dict = {}

        for junc_id in junctions.keys():

            x, y = junctions[junc_id][0]

            r = 1.0

            xmin = x - r
            xmax = x + r
            ymin = y - r
            ymax = y + r

            up_left = [xmin, ymax]
            up_center = [(xmin + xmax) / 2, ymax]
            up_right = [xmax, ymax]

            right_center = [xmax, (ymin + ymax) / 2]

            down_right = [xmax, ymin]
            down_center = [(xmin + xmax) / 2, ymin]
            down_left = [xmin, ymin]

            left_center = [xmin, (ymin + ymax) / 2]

            mbr_dict[junc_id] = np.array([
                up_left,
                up_center,
                up_right,
                right_center,
                down_right,
                down_center,
                down_left,
                left_center,
                up_left
            ])

        junc_list = []

        for junc_id in junctions.keys():

            junc_list.append({
                "junc_id": junc_id,
                "line_ids": set(junctions[junc_id][1])
            })

        return junc_list, mbr_dict

    # --------------------------------------------------
    # Detect Junctions
    # --------------------------------------------------

    bsm_juncs, bsm_dict_mbr = find_junctions_and_mbr(
        filtered_bsm,
        "JB"
    )

    skm_juncs, skm_dict_mbr = find_junctions_and_mbr(
        filtered_skm,
        "JS"
    )

    nTL = len(bsm_dict_mbr)

    if not bsm_juncs or not skm_juncs:
        return {
            "ERROR": "No junctions found",
            "nTL": nTL,
            "nDL": 0
        }


    print("Filtered BSM:", len(filtered_bsm))
    print("Filtered SKM:", len(filtered_skm))
    print("BSM Junctions:", len(bsm_juncs))
    print("SKM Junctions:", len(skm_juncs))
    print("Verified Pairs:", len(verified_pairs))
    # --------------------------------------------------
    # 3. Junction Matching
    # --------------------------------------------------

    potential_matches = []

    for s_junc in skm_juncs:

        for b_junc in bsm_juncs:

            shared = (
                s_junc["line_ids"]
                .intersection(b_junc["line_ids"])
            )

            if len(shared) >= 2:

                potential_matches.append(
                    (
                        len(shared),
                        b_junc["junc_id"],
                        s_junc["junc_id"]
                    )
                )

    potential_matches.sort(
        key=lambda x: x[0],
        reverse=True
    )

    verified_pairs = []

    matched_bsm = set()
    matched_skm = set()

    for strength, b_id, s_id in potential_matches:

        if (
            b_id not in matched_bsm
            and
            s_id not in matched_skm
        ):

            verified_pairs.append((b_id, s_id))

            matched_bsm.add(b_id)
            matched_skm.add(s_id)

    nDL = len(verified_pairs)

    if nDL < 2:
        return {
            "ERROR": "Insufficient matches",
            "nTL": nTL,
            "nDL": nDL
        }

    # --------------------------------------------------
    # 4. GMDA Metrics
    # --------------------------------------------------

    pairs_gen = list(
        landmark_pairs_generator(
            verified_pairs,
            bsm_dict_mbr,
            skm_dict_mbr
        )
    )

    def comb2(n):
        return n * (n - 1) // 2

    n_nTL = (
        comb2(8 * nTL) - nTL * comb2(8)
        if nTL > 1 else 0
    )

    n_nDL = len(pairs_gen)

    if n_nDL == 0:
        return {
            "ERROR": "No landmark pairs generated",
            "nTL": nTL,
            "nDL": nDL
        }

    sum_can = 0
    sum_dist_abs = 0
    sum_sca_bias = 0

    sum_rot_sin = 0
    sum_rot_cos = 0
    sum_ang_abs = 0

    max_db = 0.001
    max_ds = 0.001

    for b1x, b1y, b2x, b2y, s1x, s1y, s2x, s2y in pairs_gen:

        max_db = max(
            max_db,
            np.hypot(b1x - b2x, b1y - b2y)
        )

        max_ds = max(
            max_ds,
            np.hypot(s1x - s2x, s1y - s2y)
        )

    for b1x, b1y, b2x, b2y, s1x, s1y, s2x, s2y in pairs_gen:

        if (b1y < b2y and s1y < s2y) or \
           (b1y > b2y and s1y > s2y):
            sum_can += 1

        if (b1x < b2x and s1x < s2x) or \
           (b1x > b2x and s1x > s2x):
            sum_can += 1

        db = np.hypot(
            b1x - b2x,
            b1y - b2y
        ) / max_db

        ds = np.hypot(
            s1x - s2x,
            s1y - s2y
        ) / max_ds

        sum_sca_bias += (ds - db)
        sum_dist_abs += abs(ds - db)

        ang_b = np.arctan2(
            b2x - b1x,
            b2y - b1y
        )

        ang_s = np.arctan2(
            s2x - s1x,
            s2y - s1y
        )

        d = (
            (ang_s - ang_b + np.pi)
            % (2 * np.pi)
        ) - np.pi

        sum_rot_sin += np.sin(d)
        sum_rot_cos += np.cos(d)

        sum_ang_abs += abs(
            np.degrees(d)
        )

    return {
        "CanOrg": round(sum_can / (2 * n_nTL), 4) if n_nTL else 0,
        "CanAcc": round(sum_can / (2 * n_nDL), 4),
        "ScaBias": round(sum_sca_bias / n_nDL, 4),
        "DistAcc": round(1 - (sum_dist_abs / n_nDL), 4),
        "RotBias": round(
            np.degrees(
                np.arctan2(
                    sum_rot_sin,
                    sum_rot_cos
                )
            ),
            4
        ),
        "AngAcc": round(
            1 - (sum_ang_abs / (180 * n_nDL)),
            4
        ),
        "nTL": nTL,
        "nDL": nDL
    }
"""

@csrf_exempt
def calculateGMDA(request):
    """ 
    This is the function that Django will call when the frontend 
    sends a POST request to /gmda/calculateGMDA/ 
    It reads the two geoJSON payloads and then passes them to 
    compute_gmda, and then sends then back as JSON.

    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status = 405)
    try:
        basemap_geojson = json.loads(request.POST.get('basemapdata', '{}'))
        sketchmap_geojson = json.loads(request.POST.get('sketchmapdata', '{}'))
        result = compute_gmda(basemap_geojson, sketchmap_geojson)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status = 500)



@csrf_exempt
def calculateJunctionGMDA(request):
    """
    This function will send the data when it is requested from the frontend.
    It will take the basemapdata, sketchmapdata 
    and send them to compute_JunctionGMDA function, 
    then send the response to the frontend as a JSON response.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        basemap_geojson   = json.loads(request.POST.get('basemapdata', '{}'))
        sketchmap_geojson = json.loads(request.POST.get('sketchmapdata', '{}'))
        #sketchmap_name = request.POST('sketchmapname', 'unknown')

        #DEBUG:
        print(f"DEBUG: Basemap Features: {len(basemap_geojson.get('features', []))}")
        print(f"DEBUG: Sketch Features: {len(sketchmap_geojson.get('features', []))}")
        result = compute_JunctionGMDA(basemap_geojson, sketchmap_geojson)
        return JsonResponse(result)
    except Exception as e:
        import traceback
        return JsonResponse({'ERROR': str(e), 'traceback': traceback.format_exc()}, status=500)
    
