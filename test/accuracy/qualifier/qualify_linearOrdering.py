# -*- coding: utf-8 -*-
"""
Created on Fri Feb 02 14:02:12 2018
  -Computes linear ordering betweeen adjacent landmarks and street

@author: s_jan001
"""
from qualifier.utils_i4l import (
    computeMinMaxDist,
    computeAdjacency,
    linear_referencing,
    get_defined_route
)
from shapely.ops import substring
from shapely.geometry import mapping


# --------------------------------------------------
# Allen Interval Algebra (clean implementation)
# --------------------------------------------------

def linear_ordering(interval_a, interval_b):
    """
    Compute Allen interval relation between two intervals.
    interval format: {'interval': [start, end]}
    """

    A1, A2 = interval_a['interval']
    B1, B2 = interval_b['interval']

    # Normalize intervals
    if A1 > A2:
        A1, A2 = A2, A1
    if B1 > B2:
        B1, B2 = B2, B1

    if A2 < B1:
        return "before"
    if A1 > B2:
        return "after"
    if A2 == B1:
        return "meets"
    if A1 == B2:
        return "met_by"
    if A1 == B1 and A2 == B2:
        return "equals"
    if A1 == B1:
        return "starts"
    if A2 == B2:
        return "finishes"
    if A1 > B1 and A2 < B2:
        return "during"
    if A1 < B1 and A2 > B2:
        return "contains"
    if A1 < B1 < A2 < B2:
        return "overlaps"
    if B1 < A1 < B2 < A2:
        return "overlapped_by"

    return "undefined"


# --------------------------------------------------
# Main qualification function
# --------------------------------------------------

def qualify_linear_ordering(data):
    """
    Computes linear ordering relations between adjacent polygons
    projected onto a defined route.
    """

    relation_set = "linearOrdering"
    arity = 2

    # --------------------------------------
    # Step 1: Extract route
    # --------------------------------------

    defined_route = get_defined_route(data)


    if defined_route is None:
        raise ValueError("No route defined in dataset.")

    # --------------------------------------
    # Step 2: Separate polygons and route
    # --------------------------------------

    polygons = [
        obj for obj in data
        if obj['geometry'].geom_type == 'Polygon'
    ]


    # --------------------------------------
    # Step 3: Compute adjacency threshold
    # --------------------------------------

    polygon_list = [(i, obj['geometry']) for i, obj in enumerate(data)
                    if obj['geometry'].geom_type == 'Polygon']

    street_list = [(i, obj['geometry']) for i, obj in enumerate(data)
                   if obj['geometry'].geom_type == 'LineString']

    max_min_dist = computeMinMaxDist(polygon_list, street_list)

    # --------------------------------------
    # Step 4: Project adjacent polygons
    # --------------------------------------
    projected_features = []
    route_length = defined_route.length

    for poly in polygons:

        is_adjacent = computeAdjacency(
            poly['geometry'],
            defined_route,
            max_min_dist
        )

        if is_adjacent == "Adjacent":
            intA, intB = linear_referencing(
                poly['geometry'],
                defined_route
            )

            start = min(intA, intB)
            end = max(intA, intB)

            # Extract route segment
            segment = substring(defined_route, start, end)

            feature = {
                "type": "Feature",
                "geometry": mapping(segment),
                "properties": {
                    "id": poly['attributes']['id'],
                    "start": start,
                    "end": end,
                    "length": end - start
                }
            }

            projected_features.append(feature)

    # --------------------------------------
    # Step 5: Pairwise interval relations
    # --------------------------------------
    projected_intervals = [
        {
            "id": f["properties"]["id"],
            "interval": [
                f["properties"]["start"],
                f["properties"]["end"]
            ]
        }
        for f in projected_features
    ]

    results = []

    for i in range(len(projected_intervals)):
        for j in range(i + 1, len(projected_intervals)):

            A = projected_intervals[i]
            B = projected_intervals[j]

            relation = linear_ordering(A, B)

            results.append({
                "obj 1": A["id"],
                "obj 2": B["id"],
                "relation": relation
            })
    visualization_data = {
        "route_length": route_length,
        "interval_features": projected_features
    }


    return relation_set, arity, visualization_data, results
