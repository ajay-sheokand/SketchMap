"""
Spyder Editor

This is a temporary script file.

Captures the TOPOLOGICAL RELATIONS between 
    (
        LINE-POLYGON

    )features 

@s_jan

"""

from qualifier.utils_i4l import pattern
from shapely.geometry import *
from shapely import geometry, ops
from shapely.ops import nearest_points
from shapely.geometry import LineString

from qualifier.utils_i4l import left_or_right


def vertex_distances(polygon, line):

    distances = []

    # Exterior ring
    for x, y in polygon.exterior.coords:
        pt = Point(x, y)
        d = pt.distance(line)
        distances.append(d)

    # Interior rings (holes)
    for ring in polygon.interiors:
        for x, y in ring.coords:
            pt = Point(x, y)
            d = pt.distance(line)
            distances.append(d)

    return distances







def topological_relation_line_polygon(line, polygon, tol=1e-3):

    # Create buffered versions
    poly_buf = polygon.buffer(tol)
    line_buf = line.buffer(tol)

    distance = line.distance(polygon)
    p1, p2 = nearest_points(line, polygon)
    shortest_distance = p1.distance(p2)

    dists = vertex_distances(polygon, line)


    lr_relation = left_or_right(line,polygon.exterior)


    matrix = line.relate(polygon)


    # 1. Disjoint (no contact even with tolerance)
    if (line.relate_pattern(polygon, "FF*FF****") and distance <= tol) or (line.relate_pattern(polygon, "T*T******") and lr_relation!= 'crosses') :
        return "touch"

    # 4. In (line fully inside polygon with tolerance)
    if line.within(poly_buf):
        return "in"

        # 2. Cross (true interior crossing)
    if line.relate_pattern(polygon, "T*T******"):
        return "cross"

    if line.relate_pattern(polygon, "FF*FF****"):
        return "disjoint"

    return "unknown"




def qualify_DE9IM_linepolygon(data):

    qualify_DE9IM_linepolygon.relation_set = 'DE9IM'
    qualify_DE9IM_linepolygon.arity = 2

    results = []

    for i in range(len(data) - 1):
        for sec in data[i + 1:]:

            g1 = data[i]['geometry']
            g2 = sec['geometry']

            if (
                (g1.geom_type == 'Polygon' and g2.geom_type == 'LineString')
                or
                (g1.geom_type == 'LineString' and g2.geom_type == 'Polygon')
            ):

                id1 = data[i]['attributes']['id']
                id2 = sec['attributes']['id']



                if g1.geom_type == "Polygon":
                    polygon, line = g1, g2
                else:
                    polygon, line = g2, g1

                relation = topological_relation_line_polygon(line, polygon)

                results.append({
                    'obj 1': id1,
                    'obj 2': id2,
                    'relation': relation
                })

    return 'DE9IM : line_polygon', 2, {}, results



