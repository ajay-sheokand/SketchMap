# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 12:38:23 2018

@author: Malumbo
"""

from svgpathtools import svg2paths2
from svgpathtools import Line, QuadraticBezier, CubicBezier
from shapely.geometry import Point, LineString, Polygon
from qualifier.utils_i4l import is_clockwise

def simplify_qcurve_simple(p0, p1, p2, segments = []):  
    # simply replace curve with line
    segments.append({'start':p0, 'end':p2})
    return segments

# simple recursive bezier curve simplification
def simplify_qcurve(p0, p1, p2, c, segments = []):
        
    m0 = ave(p0, p1)
    m1 = ave(p1, p2)
    m2 = ave(p2, p0)
    q0 = ave(m0, m1)
    
    # if curvature is smaller than c then don't split anymore
    if (dist(q0, m2)/dist(p0, p2) <= c):
        segments.append({'start':p0, 'end':p2})
        return segments
    else:
        segments = simplify_qcurve(p0, m0, q0, c)
        segments = simplify_qcurve(q0, m1, p2, c)
    
    return segments

def simplify_ccurve_simple(p0, p1, p2, p3, segments = []):  
    # simply replace curve with line
    segments.append({'start':p0, 'end':p3})
    return segments

# simple recursive bezier curve simplification
def simplify_ccurve(p0, p1, p2, p3, c, segments = []):
        
    m0 = ave(p0, p1)
    m1 = ave(p1, p2)
    m2 = ave(p2, p3)
    m3 = ave(p3, p0)
    q0 = ave(m0, m1)
    q1 = ave(m1, m2)
    u0 = ave(q0, q1)
    
    # if curvature is smaller than c then don't split anymore
    if (dist(u0, m3)/dist(p0, p3) <= c):
        segments.append({'start':p0, 'end':p3})
        return segments
    else:
        segments = simplify_ccurve(p0, m0, q0, u0, c)
        segments = simplify_ccurve(u0, q1, m2, p3, c)
    
    return segments

def ave(a, b):
    return (a + b)/2

def dist(a, b):
    return abs(a - b)

# Convert list of coordinates to shapley geometry objects
def point_list2shapely(d_path): 
    # is the path a point?
    if len(d_path) == 1:
        return Point(d_path[0])
    # is the path closed?
    elif d_path[0] == d_path[len(d_path) - 1]:
        p = Polygon(d_path)
        if (is_clockwise(p)):
            p = Polygon(p.exterior.coords[::-1])
        return p
    # it's a linestring
    else: 
        return LineString(d_path)
    
def load_map_svg(path, map_type):
    # geojson is a metric map so let's set the properties accordingly -- at least the map type
    map_properties = {'map_type':map_type}
    
    # Update: You can now also extract the svg-attributes by setting
    # return_svg_attributes=True, or with the convenience function svg2paths2
    paths, attributes, svg_attributes = svg2paths2(path)
    
    # map attributes to remove non-essential attributes
    attributes = map(lambda x: {'id':x['id'], 'name':x['name'], 'sm_sk_type':x['smart_skema_type'], 'feat_type':x['smart_skema_type'],
                                'descriptn':x['description']}, attributes)
    
    #features = [ ({attr1:"", attr2:"", ...}, shaplyGeometry), ..., {'Feature':{attr1:"", attr2:"", ...}, 'Geom':shaplyGeometry} ]
    shapelyGeoms = []
    
    # split curves if the ratio of the curve radius and the base (start to end) diameter is greater than the parameter c
    # 0c=0.01
    
    for p in paths:
        # we unpack each complex number representing a point into its components
        d_path = [(p.point(0).real,p.point(0).imag)]
        
        for s in p:
            sp = s.bpoints()
            if isinstance(s, Line):
                d_path.append((sp[1].real,sp[1].imag))
     
            elif isinstance(s, QuadraticBezier):
                segments = simplify_qcurve_simple(sp[0], sp[1], sp[2], segments = [])
                points = map(lambda x: (x['end'].real,x['end'].imag), segments)
                d_path.extend(points)
                
            elif isinstance(s, CubicBezier):
                segments = simplify_ccurve_simple(sp[0], sp[1], sp[2], sp[3], segments = [])
                points = map(lambda x: (x['end'].real,x['end'].imag), segments)
                d_path.extend(points)
        
        shapelyGeoms.append(point_list2shapely(d_path))
    
    # features = map( lambda x, y: {"attributes":x, "geometry":y}, attributes, shapelyGeoms)
    features = [{"attributes":x, "geometry":y} for (x, y) in zip(attributes, shapelyGeoms)]
    print ("map loaded")
    
    # map loaded, so return the data
    return map_properties, features
    