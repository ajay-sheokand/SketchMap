# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 12:28:47 2018

@author: Malumbo
"""

import geojsonLoader, svgLoader
from qualifier.qualifier_database_writer import write_to_db
from qualifier.qualifier_interface import qualifier_interface
from qualifier.qualifier_collection import qualifier_functions

# this function computes the qualitative representation of the input data
# and returns it. At the moment the qualifiers for each set of relations are 
# specified manually in qualifier_collection. Later we will load them from a settings file.
def qualify(data, data_properties):
    qualifier = qualifier_interface(data, data_properties)
    
    # qualify each aspect in turn
    for f in qualifier_functions():
        qualifier.qualify(f)
    
    return qualifier.current_qualitative_representation()

# =============================================================================
# path = './Data/Polygons_test.geojson' 
# data_format = 'geojson' 
# map_type = 'metric_map' 
# =============================================================================

path = './Data/sample.svg' 
data_format = 'svg' 
map_type = 'sketch_map' 

data_properties, data = 0,0

# load the data
if data_format.strip().lower() == 'geojson'.lower():
    data_properties, data = geojsonLoader.load_map(path, map_type)
elif data_format.strip().lower() == 'svg'.lower():
    data_properties, data = svgLoader.load_map(path, map_type)

# if load is successful continue to generate qualitative representation 
# and write the data to the database
if (not (data_properties == 0 or data == 0)):
    # get the qualitative representation for the whole map
    qualitative_representation = qualify(data, data_properties)
    # write the qualitative representation to the database
    write_to_db(qualitative_representation)


