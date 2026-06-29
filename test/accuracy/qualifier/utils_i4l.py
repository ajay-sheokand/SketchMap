# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 11:31:48 2018

@author: Malumbo

This file contains a bunch of utility functions

"""
import numpy as np
from functools import reduce
from collections import deque
from sklearn.cluster import KMeans
from shapely.geometry import *
from shapely import geometry, ops


###################### General polygon stuff #########################################
# If the vertices of the polygon are listed in counterclockwise order or not
def is_clockwise(poly):
    x = poly.exterior.coords[:-1]
    N = len(x)
    return (sum([(x[(i+1) % N][0] - x[i][0]) * (x[(i+1) % N][1] + x[i][1]) for i in range(N)]) > 0)
	
###################### Directinal relations #########################################

def calculate_sectors(rot, rng, num_sectors):
    sector_size, sector_rot = rng/num_sectors, rng/(num_sectors*2) 
    return [((rot + i * sector_size - sector_rot)%rng, (rot + i * sector_size + sector_rot)%rng) for i in range(num_sectors)]

def get_sector(angle, rng, sectors):
    for sector in range(len(sectors)):
        if (0 <=  (angle - sectors[sector][0]) % rng < (sectors[sector][1] - sectors[sector][0]) % rng):
            return sector

def vector_angle(v):
    return (np.arctan2(*v[::-1])+2*np.pi)%(2*np.pi)

def directional_relation(referent, relatum, front, rng, sectors):
    # get centroid cntr of referent polygon
    cntr = referent.convex_hull.centroid
    
    # if relatum is point find single sector and return
    if isinstance(relatum, Point):
        v = np.array(relatum.coords[:][0]) - np.array(cntr.coords[:][0])
        dir = np.rad2deg(vector_angle(v))
        return set((get_sector(dir, rng, sectors),))

    # otherwise go ahead and do more processing for polygons
    # slice the vertices of the relatum to 
    coords = relatum.exterior.coords[:]
    sectors_covered = set()
    
    for i in range(len(coords)-1):
        # which way should we be counting sectors
        delta_dir = 0
        #create triangle for checking vertex orientation (CW/CCW)
        if (is_clockwise(Polygon([coords[i], coords[(i+1)], cntr.coords[:][0]]))):
            delta_dir = -1
        else:
            delta_dir = 1
        
        # calculate the vectors representing the rays from cntr to the ith and (i+1)th vertices of the relatum
        start_v = np.array(coords[i]) - np.array(cntr.coords[:][0])
        end_v = np.array(coords[i+1]) - np.array(cntr.coords[:][0])

        # find the base directions of the ray vectors using the arctan2 convention (i.e. relative to the x-axis)
        if (rng == 360):
            start_dir = np.rad2deg(vector_angle(start_v))
            end_dir = np.rad2deg(vector_angle(end_v))
        elif (rng == 2*np.pi):
            start_dir = vector_angle(start_v)
            end_dir = vector_angle(end_v)
        
        # find the sectors with respect to the referent that contain the current and next vertex  
        current_sector = get_sector(start_dir, rng, sectors)
        end_sector = get_sector(end_dir, rng, sectors)
        
        # count out all the sectors crossed by the line from the ith to the (i+1)th vertex and 
        # add them to the sector covering the relatum 
        sectors_covered.add(current_sector)
        while (current_sector != end_sector):
            current_sector = (current_sector + delta_dir) % len(sectors)
            sectors_covered.add(current_sector)
            
    return sectors_covered

################## for left-right relations #########################################################


EPS = 1e-3


def _cross(ax, ay, bx, by):
    """2D cross product of vectors a and b"""
    return ax * by - ay * bx


def _closest_segment_index(polyline: LineString, p: Point):
    """
    Returns the index i of the segment (coords[i] -> coords[i+1]) of polyline
    that is closest to point p.
    """
    coords = list(polyline.coords)
    px, py = p.x, p.y

    best_i = 0
    best_d2 = float("inf")

    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]

        # project point onto segment
        dx = x2 - x1
        dy = y2 - y1
        seg_len2 = dx * dx + dy * dy

        if seg_len2 < EPS:
            # degenerate segment
            d2 = (px - x1) ** 2 + (py - y1) ** 2
        else:
            t = ((px - x1) * dx + (py - y1) * dy) / seg_len2
            t = max(0.0, min(1.0, t))
            projx = x1 + t * dx
            projy = y1 + t * dy
            d2 = (px - projx) ** 2 + (py - projy) ** 2

        if d2 < best_d2:
            best_d2 = d2
            best_i = i

    return best_i


def left_or_right(polyline: LineString, other: LineString):

    coords = list(polyline.coords)
    left = 0
    right = 0

    for ox, oy in other.coords:
        p = Point(ox, oy)

        # nearest segment of polyline
        i = _closest_segment_index(polyline, p)
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]

        # vector along segment
        sx, sy = (x2 - x1), (y2 - y1)
        # vector from segment start to point
        px, py = (ox - x1), (oy - y1)

        c = _cross(sx, sy, px, py)

        if abs(c) <= EPS:
            pass  # ignore
        elif c > 0:
            left += 1
        else:
            right += 1

        # early exit if already crosses
        if left > 0 and right > 0:
            return "crosses"

    if left > 0:
        return "left"
    if right > 0:
        return "right"
    return "crosses"  # fallback if all points were on the line


############################### relative distance and adjacency ##########################################
def computeMinMaxDist(polygonList, StreetList):
    #distances =[]
    minDistList = []
    
    for poly in polygonList[:]:
        distances =[]
        for street in StreetList[:]:
            #print(street,poly)
            if not ((poly[1].touches(street[1])) or (poly[1].intersects(street[1]))):
                distances.append(poly[1].distance(street[1]))
                #print(poly[1].distance(street[1]))
        #print ("---------")

        minDistList.append(min(distances))
    #print("mindistance----",minDistList)
    maxMinDist = max(minDistList)

    return maxMinDist+5


############################### Compute Adjacency ##########################################
   
def computeAdjacency(poly, street, maxdist):
   touches_pattern = pattern("212101212")
   streetBuffer = street.buffer(maxdist)
   im_pattern = streetBuffer.relate(poly)
   #print(im_pattern)
   if(streetBuffer.intersects(poly) or
           streetBuffer.touches(poly) or
           streetBuffer.overlaps(poly) or
           streetBuffer.covers(poly) or
           streetBuffer.contains(poly)  or
           streetBuffer.within(poly) or
           streetBuffer.crosses(poly)
            ):
       return "Adjacent"
   elif touches_pattern.matches(im_pattern):
       return "Adjacent"
   else:
       return "nonAdjacent"


def distanceRelation(o1, o2, near_end, far_end):
    dist = compute_Distance(o1, o2)
    if(dist <= near_end):
        return "near"
    elif(dist <= far_end):
        return "far"
    else:
        return "vfar"
    
def compute_Distance(geom1, geom2):
    dist = geom1.distance(geom2)
    return dist

def clustering_Distances(minDist_data):
    minDist_data1 = np.array (minDist_data)
    minDist_data2 = minDist_data1.reshape(-1, 1)
    #print minDist_data2
    km = KMeans(n_clusters=3, init='k-means++', n_init=10)
    km.fit(minDist_data2)
    x = km.fit_predict(minDist_data2)
    return x

def computeRelativeDistRanges(polygonlist):
    minDistList = []
    for poly1 in polygonlist[:-1]:
        for poly2 in polygonlist[1:]:
            minDistList.append(poly1.distance(poly2))
    
    x = clustering_Distances(minDistList)
    near_dists = []
    far_dists = []
    vfar_dists = []
    
    for i in range(len(x)):
        if x[i] == 2:
            near_dists.append(minDistList[i])
        elif x[i] == 1:
            far_dists.append(minDistList[i])
        elif x[i] == 0:
            vfar_dists.append(minDistList[i])
            
    near_range = (min(near_dists), max(near_dists))
    far_range = (min(far_dists), max(far_dists))
    vfar_range =(min(vfar_dists), max(vfar_dists))
    
    ''' clusters are returned in arbitrary order so we have to sort them to 
        have each distance name refer to the correct  distance (i.e. [1,2,3] could be cluster 1
        while [31, 43, 39] is cluster 2 and [5, 9, 13] is cluster 3
    '''
    near_range, far_range, vfar_range =  sorted((near_range, far_range, vfar_range))
    
    return near_range[1], vfar_range[0]

###################################### Getting defined route##########################
"""
Returns defined route
"""

def get_defined_route(data):

    route_segments = []

    for i in range(len(data)):
        if (
            data[i]['geometry'].geom_type == 'LineString'
            and data[i]['attributes']['isRoute'] == 'Yes'
        ):
            route_segments.append(data[i]['geometry'])

    if not route_segments:
        return None

    # merge segments
    merged = ops.linemerge(route_segments)

    # if already LineString → done
    if merged.geom_type == "LineString":
        return merged

    # if MultiLineString → force single line
    if merged.geom_type == "MultiLineString":

        coords = []

        for g in merged.geoms:
            coords.extend(list(g.coords))

        return LineString(coords)

    # fallback
    return merged

######################################################### linear referencing for ordering and ####################

    
def linear_referencing (poly, line):
    distances =[] 
    polyCoords = poly.exterior.coords[:]#[::-1]
    for i in range(len(polyCoords)):
        #print polyCoords[i]
        pd = line.project(Point(polyCoords[i]))
        distances.append(pd)
   # print "distances:", distances
    minDist = min(distances)
    maxDist = max (distances)

    #startInterval = line.interpolate(minDist,normalized =True)
    #endInterval = line.interpolate(maxDist,normalized =True)

    return minDist, maxDist

############################## RCC and 9-Intersections #######################################
'''
Taken from the de9im 0.1 package by Sean Gillies: http://bitbucket.org/sgillies/de9im/
'''

DIMS = {
    'F': frozenset('F'),
    'T': frozenset('012'),
    '*': frozenset('F012'),
    '0': frozenset('0'),
    '1': frozenset('1'),
    '2': frozenset('2'),
    }

def pattern(pattern_string):
    return Pattern(pattern_string)


class Pattern(object):
    def __init__(self, pattern_string):
        self.pattern = tuple(pattern_string.upper())
    def __str__(self):
        return ''.join(self.pattern)
    def __repr__(self):
        return "DE-9IM pattern: '%s'" % str(self)
    def matches(self, matrix_string):
        matrix = tuple(matrix_string.upper())
        def onematch(p, m):
            return m in DIMS[p]
        return bool(
            reduce(lambda x, y: x * onematch(*y), zip(self.pattern, matrix), 1)
            )

class AntiPattern(object):
    def __init__(self, anti_pattern_string):
        self.anti_pattern = tuple(anti_pattern_string.upper())
    def __str__(self):
        return '!' + ''.join(self.anti_pattern)
    def __repr__(self):
        return "DE-9IM anti-pattern: '%s'" % str(self)
    def matches(self, matrix_string):
        matrix = tuple(matrix_string.upper())
        def onematch(p, m):
            return m in DIMS[p]
        return not (
            reduce(lambda x, y: x * onematch(*y), 
                   zip(self.anti_pattern, matrix),
                   1)
            )

class NOrPattern(object):
    def __init__(self, pattern_strings):
        self.patterns = [tuple(s.upper()) for s in pattern_strings]
    def __str__(self):
        return '||'.join([''.join(list(s)) for s in self.patterns])
    def __repr__(self):
        return "DE-9IM or-pattern: '%s'" % str(self)
    def matches(self, matrix_string):
        matrix = tuple(matrix_string.upper())
        def onematch(p, m):
            return m in DIMS[p]
        for pattern in self.patterns:
            val = bool(
                reduce(lambda x, y: x * onematch(*y), zip(pattern, matrix), 1))
            if val is True:
                break
        return val

