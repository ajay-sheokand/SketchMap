
from django.http.response import HttpResponse
import geopandas as gpd
from shapely.constructive import concave_hull
import numpy as np
import json
import os
import math
from shapely import geometry, ops, Geometry, snap, unary_union, get_coordinates
from shapely.geometry import Polygon, LineString, MultiLineString, mapping, shape
import shapely.wkt
from geojson import Feature, Point, FeatureCollection, Polygon, dump
from django.views.decorators.csrf import ensure_csrf_cookie
from shapely.ops import unary_union,polygonize, substring
from copy import deepcopy
import pandas as pd





def make_gen_id(base_align):
    """
    Deterministic group ID derived from base-map IDs.
    Same set of base IDs -> same gen_id, regardless of order or participant.
    """
    if base_align is None:
        return None
    if isinstance(base_align, (list, tuple, set)):
        ids = sorted({int(i) for i in base_align})
    else:
        ids = [int(base_align)]
    return "g." + ".".join(str(i) for i in ids)

@ensure_csrf_cookie
def requestFME(request):

    basedata = request.POST.get('basedata')
    sketchdata = request.POST.get('sketchdata')
    aligndata = request.POST.get('aligndata')
    sketchname = request.POST.get('sketchmapName')
    print ('sketchmap', sketchname)

    USER_PROJ_DIR = "generalizedMap"

    baseMapdata = json.loads(basedata)
    sketchMapdata = json.loads(sketchdata)
    alignMapdata = json.loads(aligndata)

    try:
        Inputbasepath = os.path.join(USER_PROJ_DIR,"inputbaseMap"+".json")
        Inputsketchpath = os.path.join(USER_PROJ_DIR,"inputsketchMap"+".json")
        Inputaligndata =  os.path.join(USER_PROJ_DIR,"alignment"+".json")

        if os.path.exists(Inputbasepath):
            os.remove(Inputbasepath)
        f = open(Inputbasepath, "a+")
        f.write(json.dumps(baseMapdata,indent=4))
        f.close()

        if os.path.exists(Inputsketchpath):
            os.remove(Inputsketchpath)
        f = open(Inputsketchpath, "a+")
        f.write(json.dumps(sketchMapdata,indent=4))
        f.close()

        if os.path.exists(Inputaligndata):
            os.remove(Inputaligndata)
        f = open(Inputaligndata, "a+")
        f.write(json.dumps(alignMapdata,indent=4))
        f.close()
    except IOError:
        print("Files written")

    result= spatial_transformation()

    return HttpResponse(result)

missingstreet = None
def spatial_transformation():
    USER_PROJ_DIR = "generalizedMap"
    Inputbasepath = os.path.join(USER_PROJ_DIR,"inputbaseMap"+".json")
    Inputsketchpath = os.path.join(USER_PROJ_DIR,"inputsketchMap"+".json")
    Inputaligndata =  os.path.join(USER_PROJ_DIR,"alignment"+".json")

    base = open(Inputbasepath)
    sketch = open(Inputsketchpath)
    align = open(Inputaligndata)

    data_ip = json.load(base)
    data_ips = json.load(sketch)






    # returns JSON object as a dictionary
    data = json.load(align)
    amal_ids = []
    ng_id_1 = []
    c_ids =[]
    om_ids=[]
    a2e_ids =[]
    s_amal_ids =[]
    # s_ng_ids = []
    s_c_ids =[]
    s_om_ids=[]
    s_a2e_ids =[]
    corresponding_sketch_ids = []
    corresponding_base_ids = []
    a2e_ss_ids = []
    s_a2e_ss_ids = []

    for k in data:
        if (k != "checkAlignnum"):
            key = 'genType'
            if key in data[k]:
                if data[k][key] == 'Amalgamation':
                    id = data[k]['BaseAlign']['0']
                    amal_ids.append(id)
                    id1 = data[k]['SketchAlign']['0']
                    s_amal_ids.append(id1)
                if data[k][key] == "No generalization":
                    ng_id = data[k]['BaseAlign']['0']
                    ng_id_1.append(ng_id)
                    # ng_id1 = val1['SketchAlign']['0']
                    # s_ng_ids.append(ng_id1)

                if data[k][key]== "OmissionMerge":
                    om_id = data[k]['BaseAlign']['0']
                    om_ids.append(om_id)
                    om_id1 = data[k]['SketchAlign']['0']
                    s_om_ids.append(om_id1)

                if data[k][key]== "Collapse":
                    c_id = data[k]['BaseAlign']['0']
                    c_ids.append(c_id)
                    c_id1 = data[k]['SketchAlign']['0']
                    s_c_ids.append(c_id1)

                if data[k][key]== "Abstraction to show existence":
                    a2e_id = data[k]['BaseAlign']['0']
                    a2e_ids.append(a2e_id)
                    a2e_id1 = data[k]['SketchAlign']['0']
                    s_a2e_ids.append(a2e_id1)

                if data[k][key]== "Abstraction to show existence - street stub":
                    a2e_ss_id = data[k]['BaseAlign']['0']
                    a2e_ss_ids.append(a2e_ss_id)
                    a2e_ss_id1 = data[k]['SketchAlign']['0']
                    s_a2e_ss_ids.append(a2e_ss_id1)



    m_ids =[]
    m_linepolygon_ids = []
    m_coor= []
    for i in data_ip['features']:
        geo = i['geometry']
        properties = i['properties']
        id = properties['id']

        if properties.get('missing'):
            m_linepolygon_ids.append(id)

        if properties.get('missing') and geo['type'] == 'LineString':
            m_ids.append(id)
            m_coor.append(geo['coordinates'])






    def calculate_angle(p1, p2, p3):
        """
        Calculate the angle between three points.
        """
        def vector(a, b):
            return [b[0] - a[0], b[1] - a[1]]

        v1 = vector(p1, p2)
        v2 = vector(p2, p3)

        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        magnitude1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        magnitude2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

        if magnitude1 * magnitude2 == 0:
            return 0

        cos_angle = dot_product / (magnitude1 * magnitude2)
        angle = math.acos(min(1, max(cos_angle, -1)))  # Ensure value is within [-1, 1] for acos

        return math.degrees(angle)

    def is_curved(coordinates, curvature_threshold=30):
        """
        Check if a sequence of coordinates represents a curved path.
        """
        for j in range(1, len(coordinates) - 1):
            angle = calculate_angle(coordinates[j-1], coordinates[j], coordinates[j+1])
            if angle < 180 - curvature_threshold:
                return True
        return False

    def check_closed_loop(curved_ids):
        """
              Check for a closed loop.
        """
        filtered = [geo for geo in data_ip['features'] if geo['properties']['id'] in curved_ids]
        if filtered:
            filteredGDF = gpd.GeoDataFrame.from_features(filtered)
            #print (filteredGDF.geometry)

            # Perform Polygonization
            polygons = list(polygonize(filteredGDF.geometry))
            #print ("CHECCCCCKKK", polygons)

            # Find Source Line IDs for Each Polygon
            loop_data = []
            if polygons:
                for poly in polygons:
                    contributing_ids = filteredGDF[filteredGDF.geometry.covered_by(poly)]["id"].tolist()
                    loop_data.append(contributing_ids)

            return loop_data




    def check_curvature_and_loop(m_ids, m_coor, curvature_threshold=30):
        """
        Check which streets are curved and if they form closed loops.
        """
        curved_ids = []
        loop_ids = []
        straight_ids = []

        for id, coordinates in zip(m_ids, m_coor):
            if is_curved(coordinates,curvature_threshold):
                curved_ids.append(id)

        loop_ids = check_closed_loop(curved_ids)





        curved_ids = list(set(curved_ids))
        # loop_ids = list(set(loop_ids))
        # straight_ids = list(set(straight_ids))

        return {
            "curved_ids": curved_ids,
            "loop_ids": loop_ids,
            "straight_ids": straight_ids
        }

    result = check_curvature_and_loop(m_ids, m_coor)


    loop_ids = result["loop_ids"]
    st_ids = result["straight_ids"]

    # breakpoint()

    def extract_endpoints(coordinates):
        """
        Extract the endpoints from a set of coordinates.
        """
        start = coordinates[0]
        end = coordinates[-1]
        return start, end

    # Function to find connected streets and their coordinates
    def find_connected_streets(loop_ids, all_segments):
        """
        Find streets that are connected to the streets forming a closed loop.
        """
        connected_streets = []
        connected_street_points = []

        #if isinstance(loop_ids[0], int):
            #loop_ids = [loop_ids]

        # Step 1: Process each loop group separately
        for loop_group in loop_ids:
            loop_endpoints = []
            loop_segments = []

            # Identify endpoints of segments in loop_ids and store them in loop_endpoints
            for segment in all_segments['features']:
                properties = segment['properties']
                segment_id = properties['id']
                if segment_id in loop_group:
                    geometry = segment['geometry']
                    segment_coor = geometry['coordinates']
                    start, end = extract_endpoints(segment_coor)

                    loop_endpoints.append(start)
                    loop_endpoints.append(end)
                    loop_segments.append((segment_id, start, end))

            connected_streets_ids = []
            connected_street_coords = []

            # Find segments connected to loop segments
            for loop_endpoint in loop_endpoints:
                for segment in all_segments['features']:
                    properties = segment['properties']
                    segment_id = properties['id']
                    if segment_id in loop_group:
                        continue  # Skip segments that are already part of the loop
                    geometry = segment['geometry']
                    segment_coor = geometry['coordinates']
                    start, end = extract_endpoints(segment_coor)

                    # Check if the start or end point of the segment matches any loop endpoint
                    if start == loop_endpoint or end == loop_endpoint:
                        if segment_id not in connected_streets_ids:
                            connected_streets_ids.append(segment_id)
                        if start == loop_endpoint:
                            connected_street_coords.append(start)
                        elif end == loop_endpoint:
                            connected_street_coords.append(end)

            unique_coords = list(set(tuple(coord) for coord in connected_street_coords))
            unique_coords = [list(coord) for coord in unique_coords]
            # breakpoint()
            connected_streets.append(connected_streets_ids)
            connected_street_points.append(unique_coords)
        return connected_streets, connected_street_points

    ng_ids = []
    connected_streets = []
    connected_streets_st = []
    connected_street_points = []
    st_points = []
    if loop_ids :
        # Call the function and get the results
        connected_streets, connected_street_points = find_connected_streets(loop_ids, data_ip)
        connected_streets_st, st_points = find_connected_streets(st_ids, data_ip)

        # Iterate through the lists in reverse order to safely remove elements
        for index in range(len(connected_streets_st) - 1, -1, -1):
            if len(connected_streets_st[index]) < 4:
                # Remove the sublist from both lists if it has fewer than 4 elements
                del connected_streets_st[index]
                del st_ids[index]



        # Flatten connected_streets and connected_streets_st for easier comparison
        flattened_connected_streets = [item for sublist in connected_streets for item in sublist]
        flattened_connected_streets_st = [item for sublist in connected_streets_st for item in sublist]

        # Create the final list by excluding elements in connected_streets and connected_streets_st
        ng_ids = [
            [item for item in sublist if
             item not in flattened_connected_streets and item not in flattened_connected_streets_st]
            for sublist in ng_id_1
        ]

        # Remove empty sublists
        ng_ids = [sublist for sublist in ng_ids if sublist]

        #print(ng_ids)
    else:
        ng_ids = ng_id_1

    # breakpoint()

    poly = []
    line = []
    point = []
    a2e_l = []
    a2e_p= []
    a2e_ids_l=[]
    a2e_ids_p=[]
    ng_ids_l = []
    ng_ids_p = []
    mis_ids_p = []
    mis_ids_p_prop = []
    mis_ids_l = []
    mis_ids_l_prop = []
    no_gen_l = []
    no_gen_p = []


    poly_res = []
    line_res = []
    point_res = []
    ng_res_l = []
    ng_res_p = []
    mis_res_l = []
    mis_res_p = []
    a2e_l_res = []
    a2e_p_res = []

    for x in m_linepolygon_ids:
        line_group = []
        poly_group = []
        filtered_geom = [geo['geometry']['coordinates'] for geo in data_ip['features'] if geo['properties']['id'] == x]
        filtered_geomtype = [geo['geometry']['type'] for geo in data_ip['features'] if geo['properties']['id'] == x]
        filtered_prop = [geo['properties'] for geo in data_ip['features'] if geo['properties']['id'] == x]
        if 'LineString' in filtered_geomtype:
            for i in filtered_geom:
                each_line = geometry.LineString(i)
                mis_res_l.append(each_line)
                mis_ids_l_prop.append(filtered_prop[0])
        if 'Polygon' in filtered_geomtype:
            for i in filtered_geom:
                each_poly = geometry.Polygon(i[0])
                mis_res_p.append(each_poly)
                mis_ids_p_prop.append(filtered_prop[0])




    for x in amal_ids:
        poly_group = []
        filtered = [geo['geometry']['coordinates'] for geo in data_ip['features'] if geo['properties']['id'] in x]
        for i in filtered:
            each_poly = geometry.Polygon(i[0])
            poly_group.append(each_poly)
        poly_res.append(poly_group)

    for x in om_ids:
        line_group = []
        filtered= [geo['geometry']['coordinates'] for geo in data_ip['features'] if geo['properties']['id'] in x]
        filtered_id = [geo['properties']['id'] for geo in data_ip['features'] if geo['properties']['id'] in x]
        for i in filtered:
            each_line = geometry.LineString(i)
            line_group.append(each_line)
        line_res.append(line_group)



    for x in ng_id_1:
        line_group = []
        poly_group = []
        filtered_geom = [geo['geometry']['coordinates']for geo in data_ip['features'] if geo['properties']['id'] in x]
        filtered_geomtype = [geo['geometry']['type'] for geo in data_ip['features'] if geo['properties']['id'] in x]
        filtered_id = [geo['properties']['id'] for geo in data_ip['features'] if geo['properties']['id'] in x]
        if 'LineString' in filtered_geomtype:
            for i in filtered_geom:
                each_line = geometry.LineString(i)
                line_group.append(each_line)
            ng_res_l.append(line_group)
            ng_ids_l.append(filtered_id[0])
        if 'Polygon' in filtered_geomtype:
            for i in filtered_geom:
                each_poly = geometry.Polygon(i[0])
                poly_group.append(each_poly)
            ng_res_p.append(poly_group)
            ng_ids_p.append(filtered_id[0])


    for x in c_ids:
        point_group = []
        filtered = [geo['geometry']['coordinates'] for geo in data_ip['features'] if geo['properties']['id'] in x]
        for i in filtered:
            each_point = geometry.Polygon(i[0])
            point_group.append(each_point)
        point_res.append(point_group)

    for x in a2e_ids:
       #print ("xhgjkl",x )
       poly_group = []
       line_group = []
       filtered_geom = [geo['geometry']['coordinates'] for geo in data_ip['features'] if geo['properties']['id'] in x]
       filtered_geomtype = [geo['geometry']['type'] for geo in data_ip['features'] if geo['properties']['id'] in x]
       filtered_id = [geo['properties']['id'] for geo in data_ip['features'] if geo['properties']['id'] in x]
       if 'LineString' in filtered_geomtype:
           for i in filtered_geom:
               each_line = geometry.LineString(i)
               line_group.append(each_line)
           a2e_l_res.append(line_group)
           a2e_ids_l.append(filtered_id)
           #print("line",a2e_ids_l)
       if 'Polygon' in filtered_geomtype:
           for i in filtered_geom:
               each_poly = geometry.Polygon(i[0])
               poly_group.append(each_poly)
           a2e_p_res.append(poly_group)
           a2e_ids_p.append(filtered_id)

    a2e_ssl_res =[]
    a2e_ss_ids_l=[]

#street stub base map
    for x in a2e_ss_ids:
       line_group = []
       filtered_geom = [geo['geometry']['coordinates'] for geo in data_ip['features'] if geo['properties']['id'] in x]
       filtered_geomtype = [geo['geometry']['type'] for geo in data_ip['features'] if geo['properties']['id'] in x]
       filtered_id = [geo['properties']['id'] for geo in data_ip['features'] if geo['properties']['id'] in x]
       if 'LineString' in filtered_geomtype:
           for i in filtered_geom:
               each_line = geometry.LineString(i)
               line_group.append(each_line)
           a2e_ssl_res.append(line_group)
           a2e_ss_ids_l.append(filtered_id)
           #print("line",a2e_ids_l)


    def get_corresponding_base_ids(sketch_ids):
        corresponding_base_ids=[]
        for k in data:
            if (k != "checkAlignnum"):
                key = 'genType'
                if key in data[k]:
                    check = list(filter(lambda x: x in data[k]['SketchAlign']['0'], sketch_ids))
                    if bool(check):
                        corresponding_base_ids.append(data[k]['BaseAlign']['0'])

        return corresponding_base_ids


#street stub sketch map
    flat_ss_sids = {
        sid
        for group in s_a2e_ss_ids
        for sid in group
    }

    sketch_ids_intersect_mapping = {
        sid: []
        for group in s_a2e_ss_ids
        for sid in group
    }

    # build sketch geometry lookup
    sketch_ss_geom_by_sid = {
        feat["properties"]["sid"]: shape(feat["geometry"])
        for feat in data_ips["features"]
        if feat["properties"]["sid"] in flat_ss_sids
    }


    for feat in data_ips["features"]:
        sketch_sid = feat["properties"]["sid"]
        sketch_geom = shape(feat["geometry"])

        # skip sketch features themselves if needed
        if sketch_sid in flat_ss_sids:
            continue

        for sketch_ss_sid, sketch_ss_geom in sketch_ss_geom_by_sid.items():
            if sketch_geom.intersects(sketch_ss_geom):
                sketch_ids_intersect_mapping[sketch_ss_sid].append(sketch_sid)

    sketch_to_base_mapping = {}

    for sketch_sid, intersecting_sids in sketch_ids_intersect_mapping.items():
        base_ids = get_corresponding_base_ids(intersecting_sids)
        sketch_to_base_mapping[sketch_sid] = base_ids













    #for group in a2e_ids:
    #    group_l = []
    #    group_p = []
    #    coor_l = []
    #    coor_p = []
    #    for id in group:
    #        for feature in data_ip['features']:
    #            geo = feature['geometry']
    #            properties = feature['properties']
    #            if properties['id'] == id:
    #                type = geo['type']
    #                coor = geo['coordinates']
    #                if len(coor) > 1:
    #                    # Handle LineString
    #                    f_coor = geometry.LineString(coor)
    #                    coor_l.append(f_coor)
    #                    # a2e_ids_l.append(id)
    #                    group_l.append(id)
    #                else:
    #                    # Handle Polygon
    #                    f_coor = geometry.Polygon(coor[0])
    #                    coor_p.append(f_coor)
    #                    group_p.append(id)




    #point_res = []
    #for sublist in c_ids:
        #start = sum([len(sub) for sub in point_res])
        #end = start + len(sublist)
        #point_res.append(point[start:end])

    #line_res = []
    #for sublist in om_ids:
        #start = sum([len(sub) for sub in line_res])
        #end = start + len(sublist)
        #line_res.append(line[start:end])

    #ng_res_l = []
    #for sublist in ng_ids:
        #start = sum([len(sub) for sub in ng_res_l])
        #end = start + len(sublist)
        #ng_res_l.append(no_gen_l[start:end])

    #ng_res_p = []
    #for sublist in ng_ids:
        #start = sum([len(sub) for sub in ng_res_p])
        #end = start + len(sublist)
        #ng_res_p.append(no_gen_p[start:end])

    #a2e_l_res = []
    #for sublist in a2e_ids:
    #    start = sum([len(sub) for sub in a2e_l_res])
    #    end = start + len(sublist)
    #    a2e_l_res.append(a2e_l[start:end])
    #    #print(a2e_l_res)

    #a2e_p_res=[]
    #for sublist in a2e_ids:
    #    start = sum([len(sub) for sub in a2e_p_res])
    #    end = start + len(sublist)
    #    a2e_p_res.append(a2e_p[start:end])
    #    #print(a2e_p_res, "check check")

    # breakpoint()
    s_ng_ids_l = []
    s_ng_ids_p = []
    s_a2e_ids_l = []
    s_a2e_ids_p = []
    s_rac_ids = []
    s_jm_ids = []
    s_ng_ids_p_map = {}
    s_ng_ids_l_map = {}

    def is_in_nested_list(nested_list, value):
        return any(value in sublist for sublist in nested_list)

    # Iterate through the data and update SketchAlign


    for key, value in data.items():
        if (key != "checkAlignnum"):
            #print ("sub", key, value)
            if isinstance(value, dict) and "BaseAlign" in value:
                if value.get("BaseAlign", {}).get("0", []):
                    base_align_value = value["BaseAlign"]["0"][0]
                    sketch_align_value = value["SketchAlign"]["0"]
                    #print ("base", base_align_value,sketch_align_value)

                    s_ng_ids_p_map[base_align_value] = sketch_align_value
                    s_ng_ids_l_map[base_align_value] = sketch_align_value
                    #if base_align_value in ng_ids_p:
                    #    s_ng_ids_p.append(sketch_align_value)
                    #elif base_align_value in ng_ids_l:
                    #   s_ng_ids_l.append(sketch_align_value)
                    if is_in_nested_list(a2e_ids_p,base_align_value):
                        s_a2e_ids_p.append(sketch_align_value)
                    if is_in_nested_list(a2e_ids_l, base_align_value):
                        s_a2e_ids_l.append(sketch_align_value)
                    if is_in_nested_list(connected_streets, base_align_value):
                        s_rac_ids.append(sketch_align_value)
                        #print ("TIME FOR RAC", s_rac_ids)
                    if is_in_nested_list(connected_streets_st, base_align_value):
                        s_jm_ids.append(sketch_align_value)
                    #print ("checksketch", s_a2e_ids_l, s_a2e_ids_p)

    s_ng_ids_p = [s_ng_ids_p_map[ng_id] for ng_id in ng_ids_p if ng_id in s_ng_ids_p_map]
    s_ng_ids_l = [s_ng_ids_l_map[ng_id] for ng_id in ng_ids_l if ng_id in s_ng_ids_l_map]
    #print (s_ng_ids_l, "sketch map ids")

    features = []


    # amalgamation .................................................................
    for x, ids, sids in zip(poly_res, amal_ids, s_amal_ids):
        mpt = geometry.MultiPolygon(x)
        res =  concave_hull(mpt,0.9).wkt
        g1_a = shapely.wkt.loads(res)
        #fig, ax = plt.subplots()
        #x,y = g1_a.exterior.xy
        #ax.plot(x, y)
        features.append(Feature(geometry=g1_a, properties={"genType": "Amalgamation", "BaseAlign": ids, "SketchAlign":sids[0]}))

    # omission_merge................................................................
    for x, ids, sids in zip(line_res, om_ids, s_om_ids):
        # breakpoint()
        #print (x, "x", ids, "ids")
        multi_line = geometry.MultiLineString(x)
        merged_line = ops.linemerge(multi_line)
        g1_o = shapely.wkt.loads(str(merged_line))
        features.append(Feature(geometry=g1_o, properties={"genType": "OmissionMerge", "BaseAlign": ids,"SketchAlign":sids[0]}))

    # collapse......................................................................
    for x, ids, sids in zip(point_res, c_ids, s_c_ids):
        collapse = x[0].centroid
        g1_c = shapely.wkt.loads(str(collapse))
        features.append(Feature(geometry=g1_c, properties={"genType": "Collapse", "BaseAlign": ids,"SketchAlign":sids[0]}))

    def is_connected(multi_line):
        merged = ops.linemerge(multi_line)
        if isinstance(merged, geometry.LineString):
            return True
        elif isinstance(merged, geometry.MultiLineString) and len(merged.geoms) == 1:
            return True
        return False



    # Abstraction to show existence Streets and buildings ..........................
    if a2e_l_res and a2e_l_res[0]:
        for x, ids, sids in zip(a2e_l_res, a2e_ids_l, s_a2e_ids_l):
            if len(x) == 0:
                continue
            multi_line = geometry.MultiLineString(x)
            if is_connected(multi_line):
                merged_line = ops.linemerge(multi_line)
                g1_a2e = geometry.shape(merged_line)
                gen_type = "Multi-MultiOmissionMerge"
                features.append(Feature(geometry=g1_a2e, properties={"genType3": gen_type, "BaseAlign": ids, "SketchAlign":sids}))
            else:
                g1_a2e = multi_line
                gen_type = "Abstraction to show existence streets"
                features.append(Feature(geometry=g1_a2e, properties={"genType": gen_type, "BaseAlign":  ids, "SketchAlign":sids}))

    normalized_mapping = {
        k: {b for sub in v for b in sub}
        for k, v in sketch_to_base_mapping.items()
    }

    base_geom_by_id = {
        feat["properties"]["id"]: shape(feat["geometry"])
        for feat in data_ip["features"]
    }

    if a2e_ssl_res :
        for x, ids, sids in zip(a2e_ssl_res,a2e_ss_ids,s_a2e_ss_ids):
            gen_type = "Abstraction to show existence - street stub"
            if x[0].geom_type == "LineString":
                line = x[0]
                half = line.length / 2

                part1 = substring(line, 0, half)
                part2 = substring(line, half, line.length)

                split_lines = [part1, part2]
                for part in split_lines:
                    # find which base IDs intersect this part
                    intersecting_base_ids = {
                        base_id
                        for base_id, base_geom in base_geom_by_id.items()
                        if base_geom.intersects(part)
                    }

                    # decide which sketch street this part belongs to
                    assigned_sketch = None
                    for sketch_sid, base_ids in normalized_mapping.items():
                        if intersecting_base_ids & base_ids:
                            assigned_sketch = sketch_sid
                            break

                    if assigned_sketch is None:
                        continue  # or log warning

                    features.append(
                        Feature(
                            geometry=mapping(part),
                            properties={
                                "genType3": gen_type,
                                "BaseAlign": list(intersecting_base_ids),
                                "SketchAlign": assigned_sketch,
                                "feat_type": "street"
                            }
                        )
                    )

    if a2e_p_res and a2e_p_res[0]:
        for x, ids, sids in zip(a2e_p_res, a2e_ids_p, s_a2e_ids_p):
            if len(x) == 0:
                continue
            mpt = geometry.MultiPolygon(x)
            res = mpt.wkt
            g1_a2e = shapely.wkt.loads(res)
            features.append(Feature(geometry=g1_a2e, properties={"genType": "Abstraction to show existence buildings", "BaseAlign": ids, "SketchAlign":sids}))


    # No Generalization .............................................................


    for x, ids, sids in zip(ng_res_l, ng_ids_l, s_ng_ids_l):
        if len(x) == 0: # Skip empty inputs
            continue
        line = shapely.geometry.LineString(x[0])
        wkt_string = line.wkt
        features.append(Feature(geometry=shapely.wkt.loads(wkt_string), properties={"genType": "No generalization", "BaseAlign": ids,"SketchAlign":sids}))

    for ids, sids in zip(ng_ids_p, s_ng_ids_p):
        # fetch the original feature EXACTLY as received
        original_feature = next(
            f for f in data_ip["features"]
            if f["properties"]["id"] == ids
        )


        # copy geometry without modification
        features.append({
            "type": "Feature",
            "geometry": deepcopy(original_feature["geometry"]),
            "properties": {
                **original_feature["properties"],
                "genType": "No generalization",
                "BaseAlign": ids,
                "SketchAlign": sids
            }
        })


    # Roundabout Collapse ...........................................................
    sketch = open(Inputsketchpath)
    sketchdata= json.load(sketch)
    s_rac_l = []
    for sublist in s_rac_ids:
        for sid in sublist:
            for feature in sketchdata['features']:
                if feature['properties']['sid'] == sid:
                    s_rac_l.append(geometry.LineString(feature['geometry']['coordinates']))

    s_rac_l_res = []
    for sublist in s_rac_ids:
        start = sum([len(sub) for sub in s_rac_l_res])
        end = start + len(sublist)
        s_rac_l_res.append(s_rac_l[start:end])

    def connection_check (s_rac_l_res, connected_streets, s_rac_ids):
        for x, ids, sids in zip(s_rac_l_res, connected_streets, s_rac_ids):
            multi_line = geometry.MultiLineString(x)
            if is_connected(multi_line):
                return 'connected'
            else:
                return 'not connected'

    def find_features(data_ip, loop_ids, features):
        rac_l_res = []

        # Ensure loop_ids is a list of lists
        if isinstance(loop_ids[0], int):
            loop_ids = [loop_ids]

        for loop_group in loop_ids:
            group_list = []  # Create a sublist for each loop group

            for id in loop_group:  # Iterate over each id in the current loop group
                found_in_basealign = False  # Flag to check if id is found in BaseAlign

                # Check in features first
                for feature in features:
                    properties = feature['properties']
                    base_align = properties.get('BaseAlign')

                    if isinstance(base_align, list):
                        if id in base_align:  # Check if the id is in the list
                            geo = feature['geometry']
                            type = geo['type']
                            coor = geo['coordinates']

                            if type == 'LineString':
                                f_coor = geometry.LineString(coor)
                                group_list.append(f_coor)  # Append to the current group sublist
                                found_in_basealign = True
                                break  # No need to check further since we found the id
                    elif isinstance(base_align, int):
                        if id == base_align:  # Check if the id matches the single integer
                            geo = feature['geometry']
                            type = geo['type']
                            coor = geo['coordinates']

                            if type == 'LineString':
                                f_coor = geometry.LineString(coor)
                                group_list.append(f_coor)  # Append to the current group sublist
                                found_in_basealign = True
                                break  # No need to check further since we found the id

                # If the id was not found in BaseAlign, check in data_ip
                if not found_in_basealign:
                    for feature in data_ip['features']:
                        properties = feature['properties']

                        if properties['id'] == id:  # Check if the id matches
                            geo = feature['geometry']
                            type = geo['type']
                            coor = geo['coordinates']

                            if type == 'LineString':
                                f_coor = geometry.LineString(coor)
                                group_list.append(f_coor)  # Append to the current group sublist
                            break  # No need to check further since we found the id

            rac_l_res.append(group_list)

        return rac_l_res

    connection_status = connection_check(s_rac_l_res, connected_streets, s_rac_ids)
    centroids = []
    # Only proceed if connected
    if connection_status == 'connected':
        rac_l_res = find_features(data_ip, loop_ids, features)

        for group in rac_l_res:
            # Create a MultiLineString from the current group
            multi_line = geometry.MultiLineString(group)

            # Calculate the centroid of the MultiLineString
            centroid1 = multi_line.centroid
            centroids.append(centroid1)


        new_line = []

        for group_index, point_group in enumerate(connected_street_points):
            centroid = centroids[group_index]

            unique_points = set(tuple(point) for point in point_group)

            # Create new line segments joining each point to the centroid
            for point in unique_points:
                new_segment = LineString([point, (centroid.x, centroid.y)])
                new_line.append(new_segment)

        for group_index, street_group in enumerate(connected_streets):
            for segment_id in street_group:
                found_in_basealign = False  # Flag to track if the segment is found in features
                # First, check in the features list
                for feature in features:
                    properties = feature['properties']
                    base_align = properties.get('BaseAlign')
                    if isinstance(base_align, list):
                        if segment_id in base_align:
                            geo = feature['geometry']
                            if geo['type'] == 'LineString':
                                original_line = LineString(geo['coordinates'])
                                combined_segment = None  # Initialize combined_segment as None
                                found_in_basealign = True  # Mark as found
                                break  # Stop checking features once the segment is found
                    elif isinstance(base_align, int):
                        if segment_id == base_align:
                            geo = feature['geometry']
                            if geo['type'] == 'LineString':
                                original_line = LineString(geo['coordinates'])
                                combined_segment = None  # Initialize combined_segment as None
                                found_in_basealign = True
                                break
                # If not found in features, check in data_ip['features']
                if not found_in_basealign:
                    for feature in data_ip['features']:
                        properties = feature['properties']
                        geo = feature['geometry']
                        if properties['id'] == segment_id and geo['type'] == 'LineString':
                            original_line = LineString(geo['coordinates'])
                            combined_segment = None  # Initialize combined_segment as None
                            break

                # Find the corresponding new line segment
                for new_segment in new_line:
                    if original_line.coords[-1] == new_segment.coords[0]:
                        combined_segment = LineString(list(original_line.coords) + list(new_segment.coords[1:]))
                        break  # Exit the loop once combined_segment is found
                    elif original_line.coords[0] == new_segment.coords[0]:
                        combined_segment = LineString(list(new_segment.coords[1:]) + list(original_line.coords))
                        break  # Exit the loop once combined_segment is found

                # Ensure combined_segment is assigned
                if combined_segment:
                    # print(combined_segment)
                    sketch_align_value = None
                    for key, value in data.items():
                        if (key != "checkAlignnum"):
                            base_align_list = value['BaseAlign']['0']
                            if segment_id in base_align_list:
                                sketch_align_value = value['SketchAlign']['0'][0]
                                break
                    # print(segment_id, sketch_align_value)

                    # Create new feature for the extended line segment
                    feature_found = False

                    # Iterate through the existing features
                    for feature in features:
                        # Check if the current feature's BaseAlign matches the segment_id
                        if 'BaseAlign' in feature['properties']:
                            base_align = feature['properties']['BaseAlign']

                            # Normalize base_align to always be a list
                            if not isinstance(base_align, list):
                                base_align = [base_align]

                            # Check if segment_id is in the list
                            if segment_id in base_align:
                                # Update the geometry and properties
                                #print ("rac", segment_id)
                                feature['geometry'] = geometry.mapping(combined_segment)
                                feature['properties']['genType1'] = "Roundaboutcollapse"
                                feature['properties']['RoundAboutCount'] = len(connected_streets)
                                feature_found = True
                                break
                    if not feature_found:
                        new_feature = Feature(
                            geometry= combined_segment,
                            properties={
                                "genType1":"Roundaboutcollapse",
                                "BaseAlign": segment_id,  # Use the respective id
                                "SketchAlign": sketch_align_value,  # Index of the group, adjust if needed
                                "RoundAboutCount": len(connected_streets)
                            }
                        )
                        features.append(new_feature)

    # Junction merge.................................................................
    #s_jm_l = []
    #for sublist in s_jm_ids:
    #    for sid in sublist:
    #        for feature in sketchdata['features']:
    #            if feature['properties']['sid'] == sid:
    #                s_jm_l.append(geometry.LineString(feature['geometry']['coordinates']))

    #s_jm_l_res = []
    #for sublist in s_jm_ids:
    #    start = sum([len(sub) for sub in s_jm_l_res])
    #    end = start + len(sublist)
    #    s_jm_l_res.append(s_jm_l[start:end])

    #connection_status = connection_check(s_jm_l_res, connected_streets_st, s_jm_ids)


    #def find_center_point_of_segment(line_segments):
        """
        Find the center points of all line segments.
        :param line_segments: A list of Shapely LineString objects representing the line segments.
        :return: A list of Shapely Point objects representing the center points of the line segments.
        """
    #    center_points = []
    #    for line_segment in line_segments:
    #        for line in line_segment:
    #            if isinstance(line, LineString):
    #                coords = list(line.coords)
    #                midpoint_x = (coords[0][0] + coords[1][0]) / 2
    #                midpoint_y = (coords[0][1] + coords[1][1]) / 2
    #                center_point = geometry.Point(midpoint_x, midpoint_y)
    #                center_points.append(center_point)

    #    return center_points

    #g_jm_line = []

    #for street_group in connected_streets_st:
    #    group_list = []  # Create a sublist for each street group

    #    for id in street_group:  # Iterate over each id in the current street group
            # Flag to check if id is found in BaseAlign
    #        found_in_basealign = False

            # Check in additional_features first
    #        for feature in features:
    #            properties = feature['properties']
    #            base_align = properties.get('BaseAlign')

    #            if isinstance(base_align, list):
    #                if id in base_align:  # Check if the id is in the list
    #                    geo = feature['geometry']
    #                    type = geo['type']
    #                    coor = geo['coordinates']

     #                   if type == 'LineString':
     #                       f_coor = geometry.LineString(coor)
     #                       group_list.append((id, f_coor))  # Append to the current group sublist
     #                       found_in_basealign = True
     #                       break  # No need to check further since we found the id
     #           elif isinstance(base_align, int):
     #               if id == base_align:  # Check if the id matches the single integer
     #                   geo = feature['geometry']
     #                   type = geo['type']
     #                   coor = geo['coordinates']

     #                   if type == 'LineString':
     #                       f_coor = geometry.LineString(coor)
     #                       group_list.append((id, f_coor))  # Append to the current group sublist
     #                       found_in_basealign = True
     #                       break  # No need to check further since we found the id

            # If the id was not found in BaseAlign, check in data_ip
     #       if not found_in_basealign:
     #           for feature in data_ip['features']:
     #               properties = feature['properties']

     #               if properties['id'] == id:  # Check if the id matches
     #                   geo = feature['geometry']
     #                   type = geo['type']
     #                   coor = geo['coordinates']

     #                   if type == 'LineString':
     #                       f_coor = geometry.LineString(coor)
     #                       group_list.append((id, f_coor))  # Append to the current group sublist
     #                   break  # No need to check further since we found the id

     #   g_jm_line.append(group_list)

    #print(g_jm_line)


    def extract_relevant_point(line, st_points):
        coords = list(line.coords)

        def point_in_st_points(point):
            """ Check if a given point is in st_points. """
            for group in st_points:
                for st_point in group:
                    if tuple(st_point) == point:
                        return True
            return False

        # Check if the line is curved (more than two points)
        if len(coords) > 2:
            # breakpoint()
            if point_in_st_points(coords[0]) and point_in_st_points(coords[-1]):
                return coords[:-1]
            # Check if the start or end of the line is in st_points
            elif point_in_st_points(coords[0]):
                return coords[1:]  # Take the point next to the start point
            elif point_in_st_points(coords[-1]):
                return coords[:-1]  # Take the point before the end point
            else:
                # If neither start nor end is in st_points, return the second-to-last point
                return None
        else:
            # For straight lines, return the endpoint that is in st_points
            if point_in_st_points(coords[0]):
                return coords[-1]
            elif point_in_st_points(coords[-1]):
                return coords[0]
            else:
            #     # If neither endpoint is in st_points, return the first coordinate by default
                return None

    #def create_junction_segments(line_segments, center_point, st_points):
        """
        Create junction segments by extending each line segment to the center point.
        :param line_segments: A list of Shapely LineString objects representing the line segments.
        :param center_point: A Shapely Point object representing the center point.
        :return: A list of new Shapely LineString objects.
        """
    #    new_segments = []
    #    for segment_id, line in line_segments:
    #        relevant_point = extract_relevant_point(line, st_points)
    #        if relevant_point is not None:
    #            if relevant_point == list(line.coords[1:]):
                # relevant_point is the result of coords[1:], so append center_point
    #                new_segment = LineString([(center_point.x, center_point.y)] + list(relevant_point))
    #            elif relevant_point == list(line.coords[:-1]):
    #                # relevant_point is the result of coords[:-1], so prepend center_point
    #                new_segment = LineString(list(relevant_point) + [(center_point.x, center_point.y)])
    #            else:
                    # This handles cases where relevant_point is a single coordinate or an unexpected format
    #                new_segment = LineString([relevant_point, (center_point.x, center_point.y)])

                # new_segments.append(new_segment)
     #           new_segments.append((segment_id, new_segment))

            # print(new_segment)
     #   return new_segments

    #def process_line_segments(g_jm_line, center_points):
        """
        Process line segments by splitting into groups of 4, finding center points, and creating junction segments.
        :param jm_l_res: A list of Shapely LineString objects representing the line segments.
        :return: A list of new Shapely LineString objects representing the junctions.
        """
     #   new_segments = []
     #   for idx, segment_group in enumerate(g_jm_line):
     #       if idx >= len(center_points):
     #           #print(f"Warning: More segment groups ({len(g_jm_line)}) than center points ({len(center_points)}). Skipping remaining groups.")
     #           break

     #       center_point = center_points[idx]
     #       junction_segments = create_junction_segments(segment_group, center_point, st_points)
     #       new_segments.extend(junction_segments)
     #   #print(new_segments)

     #   return new_segments

    # Only proceed if connected
    #if connection_status == 'connected':
    #    jm_l_res = find_features(data_ip, st_ids, features)

        # Assuming jm_l_res contains Shapely LineString objects
    #    center_points = find_center_point_of_segment(jm_l_res)

      #  print(center_points)

     #   new_segments = process_line_segments(g_jm_line, center_points)


     #   for segment_id, new_segment in new_segments:
     #       sketch_align_value = None
     #       for key, value in data.items():
     #           if (key != "checkAlignnum"):
                    #print("subkey", key, value)
     #               base_align_list = value['BaseAlign']['0']
     #               if segment_id in base_align_list:
     #                   sketch_align_value = value['SketchAlign']['0'][0]
     #                   break

            # print(segment_id, sketch_align_value)
     #       feature_found = False

            # Iterate through the existing features
     #       for feature in features:
                # Check if the current feature's BaseAlign matches the segment_id
     #           if 'BaseAlign' in feature['properties']:
     #               base_align = feature['properties']['BaseAlign']

                    # Normalize base_align to always be a list
     #               if not isinstance(base_align, list):
     #                   base_align = [base_align]

                    # Check if segment_id is in the list
     #               if segment_id in base_align:
                        # Update the geometry and properties
     #                   feature['geometry'] = geometry.mapping(new_segment)
     #                   feature['properties']['genType2'] = "JunctionMerge"
     #                   feature['properties']['JunctionMergeCount'] = len(center_points)
     #                   feature_found = True
     #                   break
     #       if not feature_found:
     #           new_feature = Feature(
     #               geometry= new_segment,
     #               properties={
     #                   "genType2": "JunctionMerge",
     #                   "BaseAlign": segment_id,  # Use the respective id
     #                   "SketchAlign": sketch_align_value,  # Index of the group, adjust if needed
     #                   "JunctionMergeCount": len(center_points)
     #               }
     #           )
     #           features.append(new_feature)

    # print(features)

    feature_collection = FeatureCollection(features)

    base = open(Inputbasepath)
    base_data = json.load(base)
    # Create a dictionary to map "id" to base data properties
    id_to_properties = {feature["properties"]["id"]: feature["properties"] for feature in base_data["features"]}

    # Iterate through feature collection features
    for feature in feature_collection["features"]:
        base_align = feature["properties"]["BaseAlign"]
        if isinstance(base_align, list):
            # Initialize an empty dictionary to store the merged properties
            merged_properties = {}

            # Loop through the list of IDs
            for bid in base_align:
                if bid in id_to_properties:
                    # Merge the properties of this ID into the merged_properties dictionary
                    merged_properties.update(id_to_properties[bid])

            # Update the feature's properties with the merged properties
            feature["properties"].update(merged_properties)
        elif base_align in id_to_properties:
            base_properties = id_to_properties[base_align]
            # Merge the sketch data properties into the feature collection properties
            feature["properties"].update(base_properties)

    # breakpoint()
    # f_out = routedirection(routedata,feature_collection)

    # # Iterate through the features in inputbasemap and update coordinates if id matches
    # for feature in feature_collection['features']:
    #     properties = feature['properties']
    #     id = properties.get("BaseAlign")
    #     # id = str(id_str).strip('[]')
    #     # breakpoint()
    #     if id is not None:
    #     # Ensure id is a tuple if needed
    #         id = tuple(id) if isinstance(id, list) else id
    #         if id in f_out :
    #             geo = feature['geometry']
    #             geo['coordinates'] = f_out[id]

    for feature in feature_collection['features']:
        # Check if the geometry type is 'Point'
        type = feature['geometry']['type']
        # coordinates = feature['geometry']['coordinates']
        if type == 'Point':
            # Create a GeoDataFrame with the input feature
            gdf = gpd.GeoDataFrame.from_features([feature])

            # Create a buffered polygon around the point (e.g., with a radius of 1 unit)
            buffered_radius = 1.0
            buffered_polygon = gdf.buffer(buffered_radius)

            # Simplify the buffered polygon to reduce the number of coordinates
            simplified_buffer = buffered_polygon.simplify(0.001)

            # Convert the simplified buffered polygon to GeoJSON format
            simplified_geojson = simplified_buffer.to_json()

            # Parse the simplified GeoJSON string to a Python dictionary
            simplified_data = json.loads(simplified_geojson)

            # Update the 'geometry' key in the original feature
            feature['geometry'] = simplified_data['features'][0]['geometry']

    #JUNCTION MERGE
    def snap_point_to_nearest_end(line, snap_point):
        coords = list(line.coords)  # Get the line's coordinates
        start, end = geometry.Point(coords[0]), geometry.Point (coords[-1])  # Get first and last point

        # Compute distances
        dist_start = snap_point.distance(start)
        dist_end = snap_point.distance(end)

        # Append snap point to the closest endpoint
        if dist_start < dist_end:
            new_coords = [snap_point] + coords  # Add to start
        else:
            new_coords = coords + [snap_point]  # Add to end

        return LineString(new_coords)  # Create new LineString

    def get_connected_segments(m_ids):
        otherthanmissing = [geo for geo in data_ip['features'] if
                            geo['properties']['id'] not in m_ids and geo['geometry']['type'] == 'LineString']
        missing = [geo for geo in data_ip['features'] if geo['properties']['id'] in m_ids]
        if missing:
            otherthanmissingGDF = gpd.GeoDataFrame.from_features(otherthanmissing)
            missingGDF = gpd.GeoDataFrame.from_features(missing)
            result = gpd.overlay(otherthanmissingGDF, missingGDF, how='intersection', keep_geom_type=False)
            pd.set_option("display.max_columns", None)
            return result["id_1"]

    def get_corresponding_sketch_ids(connectedsegments):
        for k in data:
            if (k != "checkAlignnum"):
                key = 'genType'
                if key in data[k]:
                    check = list(filter(lambda x: x in data[k]['BaseAlign']['0'], connectedsegments))
                    if bool(check):
                        corresponding_sketch_ids.append(data[k]['SketchAlign']['0'])
        return corresponding_sketch_ids


    def detectJunctionMerge(sketch_ids):
        sketch_ids = [item for sublist in sketch_ids for item in sublist]
        sketchsegments = [geo for geo in data_ips['features'] if geo['properties']['sid'] in sketch_ids]
        sketchGDF = gpd.GeoDataFrame.from_features(sketchsegments)
        sketchGDF['geom'] = sketchGDF.geometry
        # Self join
        sj = gpd.sjoin(sketchGDF, sketchGDF,
                       how="inner",
                       predicate="intersects",
                       lsuffix="left",
                       rsuffix="right")

        # Remove geometries that intersect themselves
        sj = sj[sj.index != sj.index_right]

        # Extract the intersecting geometry
        sj['intersection_geom'] = sj['geom_left'].intersection(sj['geom_right'])

        # Reset the geometry (remember to set the CRS correctly!)
        sj.set_geometry('intersection_geom', drop=True, inplace=True)

        # Drop duplicate geometries
        final_gdf = sj.drop_duplicates(subset=['geometry', 'id_left']).reset_index()

        # Drop intermediate fields
        drops = ['geom_left', 'geom_right', 'index_right', 'index']
        final_gdf = final_gdf.drop(drops, axis=1)
        # Count occurrences of each geometry
        geometry_counts = final_gdf['geometry'].value_counts()

        # Filter geometries that appear more than 4 times
        frequent_geometries = geometry_counts[geometry_counts >= 4].index

        # Get rows where 'geometry' appears more than 4 times
        filtered_df = final_gdf[final_gdf['geometry'].isin(frequent_geometries)]
        groupeddf = filtered_df.groupby(filtered_df["geometry"].apply(lambda g: g.wkt))["sid_left"].apply(list).reset_index()
        return groupeddf.sid_left


    def joinSegmentsJunctionMerge(sketch_ids):
        basefeaturesForJM = []
        missing = [geo for geo in data_ip['features'] if geo['properties']['id'] in m_ids]
        missinggdf = gpd.GeoDataFrame.from_features(missing)
        for feature in feature_collection['features']:
            if isinstance(feature["properties"]["SketchAlign"],(list,tuple,np.ndarray)):
                check = bool(set(feature["properties"]["SketchAlign"]) & set(sketch_ids))
            else:
                check = feature["properties"]["SketchAlign"] in sketch_ids
            if bool(check):
                basefeaturesForJM.append(feature)
        if basefeaturesForJM:
            ToBeMergedSegmentsGDF = gpd.GeoDataFrame.from_features(basefeaturesForJM)
            overlay = gpd.overlay(missinggdf, ToBeMergedSegmentsGDF, how='intersection', keep_geom_type=False)
            id_counts = overlay['id_1'].value_counts()
            global missingstreet
            missingstreet = id_counts[id_counts >= 4].index
            if  len(missingstreet) != 0:
                missingstreetsGeom = [geo for geo in data_ip['features'] if geo['properties']['id'] in missingstreet]
                centroidMissingstreetsGeom = geometry.LineString(missingstreetsGeom[0]['geometry']['coordinates']).centroid
                bufferCentroid = centroidMissingstreetsGeom.buffer(25)
                bufferCentroidgdf = gpd.GeoDataFrame(index=[0], geometry=[bufferCentroid])
                clip = gpd.overlay(ToBeMergedSegmentsGDF, bufferCentroidgdf, how='difference', keep_geom_type=False)
                # Plot all LineStrings on the same graph
                #fig, ax = plt.subplots(figsize=(6, 6))
                #clip.plot(ax=ax, color='blue', linewidth=2)
                # bufferCentroidgdf.plot(ax=ax , linewidth = 2)
                # Show the plot
                #plt.show()
                for i, geom in enumerate( clip['geometry']):
                    geom =  snap_point_to_nearest_end(geom,centroidMissingstreetsGeom)
                    clip['geometry'][i] = geom



                #clip["geometry"] = clip.apply(lambda x: snap(x.geometry, centroidMissingstreetsGeom, tolerance=26), axis=1)
                # Create a single plot (without subplots)



                #print (clip, "DONEEEEE")
                return clip





    junctionmergeCount = 0
    connectedsegments = get_connected_segments(m_ids)
    if connectedsegments is not None and not connectedsegments.empty:
        correspondingsketchsegments = get_corresponding_sketch_ids(connectedsegments)
        junctionmerge_sketch_ids = detectJunctionMerge(correspondingsketchsegments)
        if junctionmerge_sketch_ids is not None and not (junctionmerge_sketch_ids.empty):
            for i in junctionmerge_sketch_ids:
                joinedJunctionSegments = joinSegmentsJunctionMerge(i)
                if joinedJunctionSegments is not None:
                    junctionmergeCount = junctionmergeCount + 1
                    for feature in feature_collection["features"]:
                        if feature["properties"]["id"] in joinedJunctionSegments["id"].to_numpy():
                            id = feature["properties"]["id"]
                            coordinates = joinedJunctionSegments.loc[joinedJunctionSegments["id"] == id]
                            # Convert the simplified buffered polygon to GeoJSON format
                            coordinates_json = coordinates.to_json()

                            # Parse the simplified GeoJSON string to a Python dictionary
                            coordinates_jsondata = json.loads(coordinates_json)
                            # Update the 'geometry' key in the original feature
                            feature['geometry'] = coordinates_jsondata['features'][0]['geometry']
                            feature['properties']['JunctionMergeCount']=junctionmergeCount
                            feature['properties']['genType2'] = 'JunctionMerge'


    for feature in sketchdata['features']:
        # Check if the geometry type is 'Point'
        type = feature['geometry']['type']
        feature['properties']['mapType'] = 'Sketch'
        # coordinates = feature['geometry']['coordinates']
        if type == 'Point':
            # Create a GeoDataFrame with the input feature
            gdf = gpd.GeoDataFrame.from_features([feature])

            # Create a buffered polygon around the point (e.g., with a radius of 1 unit)
            buffered_radius = 1.0
            buffered_polygon = gdf.buffer(buffered_radius)

            # Simplify the buffered polygon to reduce the number of coordinates
            simplified_buffer = buffered_polygon.simplify(0.001)

            # Convert the simplified buffered polygon to GeoJSON format
            simplified_geojson = simplified_buffer.to_json()

            # Parse the simplified GeoJSON string to a Python dictionary
            simplified_data = json.loads(simplified_geojson)

            # Update the 'geometry' key in the original feature
            feature['geometry'] = simplified_data['features'][0]['geometry']

    # Initialize list to store coordinates for s_a2e_ids
    s_a2e_l = []
    s_a2e_p = []

    for sublist in s_a2e_ids_l:
        for sid in sublist:
            for feature in sketchdata['features']:
                if feature['properties']['sid'] == sid:
                    if feature['geometry']['type'] == 'LineString':
                        s_a2e_l.append(geometry.LineString(feature['geometry']['coordinates']))


    for feature in sketchdata['features']:
        geo = feature['geometry']
        properties = feature['properties']
        sid = properties['sid']
        for sublist in s_a2e_ids_p:
            for y in sublist:
                if y == sid:
                    if geo['type'] == 'Polygon':
                        f_coor = geometry.Polygon(geo['coordinates'][0])
                        s_a2e_p.append(f_coor)


    s_a2e_l_res = []
    for sublist in s_a2e_ids:
        start = sum([len(sub) for sub in s_a2e_l_res])
        end = start + len(sublist)
        s_a2e_l_res.append(s_a2e_l[start:end])

    s_a2e_p_res = []
    for sublist in s_a2e_ids:
        start = sum([len(sub) for sub in s_a2e_p_res])
        end = start + len(sublist)
        s_a2e_p_res.append(s_a2e_p[start:end])

    for x, ids, sids in zip(s_a2e_l_res, a2e_ids, s_a2e_ids_l):
        multi_line = geometry.MultiLineString(x)
        if is_connected(multi_line):
            merged_line = ops.linemerge(multi_line)
            g1_a2e = geometry.shape(merged_line)
            gen_type = "Multi-MultiOmissionMerge"

        else:
            g1_a2e = multi_line
            gen_type = "Others"

        # Gather properties from the sketchdata
        merged_properties = {"mapType": "Sketch", "genType3":gen_type}
        for feature in sketchdata['features']:
            if feature['properties']['sid'] in sids:
                merged_properties.update(feature['properties'])
                # processed_sids.add(feature['properties']['sid'])

        features.append(Feature(geometry=geometry.mapping(g1_a2e), properties=merged_properties))

    # sketchdata['features'] = [feature for feature in sketchdata['features'] if feature['properties']['sid'] not in processed_sids]

    for x, ids, sids in zip(s_a2e_p_res, a2e_ids_p, s_a2e_ids_p):
        if len(x) == 0: # Skip empty inputs
            continue
        #print (x, ids, sids, "check a2ep")
        mpt = geometry.MultiPolygon(x)
        res = mpt.wkt
        g1_a2e = shapely.wkt.loads(res)

        # Gather properties from the sketchdata
        merged_properties = {"mapType": "Sketch"}
        for feature in sketchdata['features']:
            if feature['properties']['sid'] in sids:
                merged_properties.update(feature['properties'])
                # processed_sids.add(feature['properties']['sid'])

        features.append(Feature(geometry=geometry.mapping(g1_a2e), properties=merged_properties))





    # Assuming you have two feature collections, feature_collection1 and feature_collection2
    combined_feature_collection = {
        "type": "FeatureCollection",
        "features": []
    }

    # Finally append the missing features
    def to_iterable(x):
        if x is None:
            return []
        if hasattr(x, "values"):  # works for pandas Series/Index/DataFrame
            return x.values.tolist()
        return list(x)  # works for lists, tuples, sets, etc.

    for x, prop in zip(mis_res_l, mis_ids_l_prop):
        global missingstreet
        temp_loop_id=[]
        if loop_ids is not None and len(loop_ids)!=0:
            temp_loop_id = loop_ids[0]
        temp_loop_ids = set(to_iterable(temp_loop_id))
        missingstreet_ids = set(to_iterable(missingstreet))
        if prop.get('id') not in temp_loop_ids and prop.get('id') not in missingstreet_ids:
            line = shapely.geometry.LineString(x)
            wkt_string = line.wkt
            features.append(Feature(geometry=shapely.wkt.loads(wkt_string),
                                    properties = prop ))


    for x, prop in zip(mis_res_p, mis_ids_p_prop):
        original_feature = next(
            f for f in data_ip["features"]
            if f["properties"]["id"] == prop['id']
        )


        # copy geometry without modification
        features.append({
            "type": "Feature",
            "geometry": deepcopy(original_feature["geometry"]),
            "properties": prop
        })


    # Append the features from feature_collection1 to the combined feature collection
    for feature in feature_collection["features"]:
        combined_feature_collection["features"].append(feature)

    # Flatten s_a2e_ids to easily check if an sid is in this list
    flattened_s_a2e_ids = [sid for sublist in s_a2e_ids for sid in sublist]
    # Append the features from feature_collection2 to the combined feature collection
    for feature in sketchdata["features"]:
        if feature['properties']['sid'] not in flattened_s_a2e_ids:
            combined_feature_collection["features"].append(feature)

    # Pass 1: stamp gen_id on every feature that has BaseAlign
    sid_to_gen_id = {}  # sketch sid -> gen_id, built from base-side features

    for feat in combined_feature_collection["features"]:
        props = feat["properties"]
        base_align = props.get("BaseAlign")
        if base_align is None:
            continue

        gen_id = make_gen_id(base_align)
        props["gen_id"] = gen_id

        # Record the sketch sids this gen_id corresponds to,
        # so we can stamp the same gen_id on the sketch-side features in pass 2.
        sketch_align = props.get("SketchAlign")
        if sketch_align is None:
            continue
        if isinstance(sketch_align, (list, tuple, set)):
            for sid in sketch_align:
                sid_to_gen_id[sid] = gen_id
        else:
            sid_to_gen_id[sketch_align] = gen_id

    # Pass 2: stamp gen_id on sketch-only features via their sid
    for feat in combined_feature_collection["features"]:
        props = feat["properties"]
        if "gen_id" in props:
            continue
        sid = props.get("sid")
        if sid is not None and sid in sid_to_gen_id:
            props["gen_id"] = sid_to_gen_id[sid]

    # print(combined_feature_collection)
    align.close()
    base.close()
    sketch.close()

    outputpath =  os.path.join(USER_PROJ_DIR,"generalizedoutputMap"+".json")
    if os.path.exists(outputpath):
        os.remove(outputpath)
    f = open(outputpath, "a+")
    f.write(json.dumps(combined_feature_collection,indent=4))
    f.close()

    return(json.dumps(combined_feature_collection,indent=4))




