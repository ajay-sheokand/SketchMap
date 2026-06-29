# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 12:09:22 2018

@author: Malumbo
"""

from qualifier.utils_i4l import is_clockwise
from shapely.geometry import Polygon, shape,LineString

import shapely.ops as shp


#def load_map(path, map_type):
def load_map_geojson(jsonData, map_type):
    map_properties = {'map_type': map_type}
    feature_attributes=[]
    shapelyGeomList=[]
    #jsonData= path
    #with open(path) as file:
     #   jsonData=json.load(file)
     
    #jsonData=json.loads(map_data)
    # geojson is a metric map so let's set the properties accordingly -- at least the map type
    # map_properties = {'map_type':'base_map'} # already dynamically set from arguments
    
    for i in jsonData['features']:
        geom=i['geometry']
        if i["geometry"]["type"] == "Polygon":
            coords = i["geometry"]["coordinates"][0]
            if len(coords) <= 2:
                line = LineString(coords[:])
                dilated = line.buffer(0.1)
                shapelyGeom = shape(dilated)
            else:
                shapelyGeom = shape(geom)
        else:
            shapelyGeom=shape(geom)

        if (shapelyGeom.geom_type == 'MultiPolygon'):
            shapelyGeom=shp.unary_union(shapelyGeom.geoms)
            
        if (shapelyGeom.geom_type=='Polygon'):
            if (is_clockwise(shapelyGeom)):
                shapelyGeom = Polygon(shapelyGeom.exterior.coords[::-1])
                
        shapelyGeomList.append(shapelyGeom)
        
        attributes= i['properties']
        feature_attributes.append(attributes)
    
    features= list(map(lambda x,y: {"attributes":x, "geometry":y}, feature_attributes,shapelyGeomList))
    #print("feature....:",features)
    print ("map loaded")
    return map_properties, features