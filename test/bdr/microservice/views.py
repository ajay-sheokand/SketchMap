import json
import numpy as np
import geopandas as gpd
import skimage as sk
import sklearn.metrics as met
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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


"""
def find_juncs_from_geojson(geojson_dict, prefix, valid_ids, id_property='id'):
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


def compute_LandmarksBDR(basemap_geojson, sketchmap_geojson):
    """
    Returns a JSON file with the 6 calculated BDR measures
    """
    # Data preparation
    bsm_data = gpd.read_file(basemap_geojson)
    skm_data = gpd.read_file(sketchmap_geojson)
    dict_align = {} # stores the (base map id, sketch map id) pairs
    X = [] # coordinates of points on the base map
    Y = [] # coordinates of points on the sketch map

    # Landmarks extraction & alignment
    bsm_polys = bsm_data.loc[(bsm_data['otype'] == 'Polygon') & (~(bsm_data['SketchAlign'].map(len, na_action='ignore') > 1))] # subdataset with 1:1 aligned polygons only
    for i in range(bsm_polys.shape[0]): # for each line
        if bsm_polys[['aligned']].iloc[i, 0]: # if the landmark is drawn on the sketch map
            id_poly = int(bsm_polys[['id']].iloc[i, 0])
            geom_poly = bsm_polys[['geometry']].iloc[i, 0]
            coords_mbr = compute_mbr_points(geom_poly)
            dict_align[id_poly] = int(bsm_polys[['SketchAlign']].iloc[i, 0][0][1:]) # landmark id on sketch map saved without 'S'

    # MBRs calculation for the base map & sketch map
    for bsm_id in dict_align.keys():
        skm_id = dict_align[bsm_id]
        bsm_geom = bsm_polys[['geometry']].loc[['id'] == bsm_id]
        skm_geom = skm_data[['geometry']].loc[['id'] == skm_id]
        bsm_coords_mbr = compute_mbr_points(bsm_geom)
        skm_coords_mbr = compute_mbr_points(skm_geom)
        X.extend(bsm_coords_mbr)
        Y.extend(skm_coords_mbr)

    # Estimation of the transformation parameters
    X, Y = np.array(X), np.array(Y)
    tform = sk.transform.SimilarityTransform()
    tform.estimate(X, Y)
    predicted_Y = tform(X)

    # Computation of the 6 BDR measures
    R2 = met.r2_score(Y, predicted_Y)
    r = np.sqrt(R2)
    DI = 100 * np.sqrt(1 - R2)
    phi = tform.scale
    theta = np.degrees(tform.rotation)
    alpha1, alpha2 = tform.translation

    return {
        'r': round(r, 4),
        'DI': round(DI, 4),
        'phi': round(phi, 4),
        'theta': round(theta, 4),
        'alpha1': round(alpha1, 4),
        'alpha2': round(alpha2, 4)
    }


@csrf_exempt
def calculateLandmarksBDR(request):
    """ 
    This is the function that Django will call when the frontend 
    sends a POST request to /bdr/calculateLandmarksBDR/ 
    It reads the two geoJSON payloads and then passes them to 
    compute_bdr, and then sends then back as JSON.

    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status = 405)
    try:
        basemap_geojson = json.loads(request.POST.get('basemapdata', '{}'))
        sketchmap_geojson = json.loads(request.POST.get('sketchmapdata', '{}'))
        result = compute_LandmarksBDR(basemap_geojson, sketchmap_geojson)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status = 500)
    

@csrf_exempt
def calculateJunctionsBDR(request):
    """ 
    This is the function that Django will call when the frontend 
    sends a POST request to /bdr/calculateLandmarksBDR/ 
    It reads the two geoJSON payloads and then passes them to 
    compute_bdr, and then sends then back as JSON.

    """
    pass