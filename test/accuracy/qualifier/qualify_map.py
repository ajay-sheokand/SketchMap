# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 12:28:47 2018

@author: Malumbo
"""
from qualifier.geojsonLoader import load_map_geojson
from qualifier.svgLoader import load_map_svg
#from qualifier.qualifier_database_writer import write_to_db
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

def main_loader(mapID, geoJson,data_format, map_type ):
   # path = sys.argv[1]
    #data_format = sys.argv[2]
    #map_type = sys.argv[3]
    
    path = geoJson
    data_format = data_format
    map_type = map_type 
    
    data_properties, data = 0,0
    
    # load the data
    if data_format.strip().lower() == 'geojson'.lower():
        data_properties, data = load_map_geojson(path, map_type)
    elif data_format.strip().lower() == 'svg'.lower():
        data_properties, data = load_map_svg(path, map_type)
    
    # if load is successful continue to generate qualitative representation 
    # and write the data to the database
    if (not (data_properties == 0 or data == 0)):
        # get the qualitative representation for the whole map

        qualitative_representation = qualify(data, data_properties)
        #print ("QCN....:",qualitative_representation)


        # write the qualitative representation to the database
        #write_to_db(mapID, qualitative_representation)
    
    #print (qualitative_representation)
    #return "Exited Successfully!"

    return qualitative_representation
#if __name__=='__main__':
 #   main()