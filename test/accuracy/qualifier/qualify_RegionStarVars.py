# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 12:09:26 2018

@author: Malumbo
"""

import random as rnd
import numpy as np
from shapely.geometry import *
from qualifier.utils_i4l import vector_angle, calculate_sectors,directional_relation

class relative_direction_relations: 
    def __init__(self, num_sectors):
        self.num_sectors = num_sectors
        
    def sector_range(self, sectors):
        min_sector = min(sectors)
        max_sector = min(sectors)
        
        sectors.remove(min_sector)
        
        while ((min_sector - 1) in sectors):
            min_sector = (min_sector - 1) % self.num_sectors
            sectors.remove(min_sector)
        
        while ((max_sector + 1) in sectors):
            max_sector = (max_sector + 1) % self.num_sectors
            sectors.remove(max_sector)
            
        return (min_sector, max_sector)
        
    def qualify_relative_direction(self, data):
        #every qualifier function must specify these two parameters
        #qualify_relative_direction.relation_set = 'RegionStarVars'
        relation_set = 'RegionStarVars'
        #qualify_relative_direction.arity = 2
        arity = 2

        # get random pair of polygons
        polys = [(i,data[i]['geometry']) for i in range(len(data)) if data[i]['geometry'].geom_type=='Polygon']
        or_obj1 = rnd.choice(polys)
        or_obj2 = rnd.choice(polys)

        while or_obj1 == or_obj2:
            or_obj2 = rnd.choice(polys)
            
        modifiers = {'base_obj': data[or_obj1[0]]['attributes']['id'], 'target_obj': data[or_obj2[0]]['attributes']['id'], 'number_of_sectors':self.num_sectors}

        # determine the centroids of their convex hulls
        cntr1 = or_obj1[1].convex_hull.centroid
        cntr2 = or_obj2[1].convex_hull.centroid

        # determine the global orientation of the ray from centroid 1 to centroid 2 
        v = np.array(cntr2.coords[:][0]) - np.array(cntr1.coords[:][0])
        # using degrees instead of radians
        dir_deg = np.rad2deg(vector_angle(v))
        d_sectors = calculate_sectors(dir_deg, 360.0, self.num_sectors)
        
        return relation_set, arity, modifiers, [{'obj 1':data[i]['attributes']['id'], 'obj 2':sec['attributes']['id'], 'relation':
                 [self.sector_range(directional_relation(data[i]['geometry'], sec['geometry'], dir_deg, 360.0, d_sectors)), 
                  self.sector_range(directional_relation(sec['geometry'], data[i]['geometry'], dir_deg, 360.0, d_sectors))]} 
                    for i in range(len(data[:-1])) for sec in data[i+1:] if (data[i]['geometry'].geom_type=='Polygon' and sec['geometry'].geom_type=='Polygon')]