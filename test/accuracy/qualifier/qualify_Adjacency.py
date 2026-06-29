from qualifier.utils_i4l import computeMinMaxDist, computeAdjacency


def qualify_Adjacency(data):
    qualify_Adjacency.relation_set = 'adj'
    qualify_Adjacency.arity = 2
    polygonList = []
    streetList = []
    for i in range(len(data)):
        if(data[i]['geometry'].geom_type=='Polygon'):
            polygonList.append((i, data[i]['geometry']))
        elif(data[i]['geometry'].geom_type=='LineString'):
            streetList.append((i, data[i]['geometry']))
    
    if len(polygonList) > 0 and len(streetList) > 0: 
        maxMinDist = computeMinMaxDist(polygonList, streetList)
        
        #print "objects:", [{'obj 1':data[poly[0]]['attributes']['id'], 'obj 2':data[line[0]]['attributes']['id'], 'relation':computeAdjacency(poly[1], line[1], maxMinDist)} for poly in polygonList for line in streetList]
    
        return 'adjacency', 2, {},[{'obj 1':data[i]['attributes']['id'], 'obj 2':sec['attributes']['id'], 'relation':computeAdjacency(data[i]['geometry'], sec['geometry'], maxMinDist)} for i in range(len(data))
                         for sec in data if (data[i]['geometry'].geom_type=='Polygon'and sec['geometry'].geom_type=='LineString') ]
    else:
        return 'adjacency', 2, {}, []



