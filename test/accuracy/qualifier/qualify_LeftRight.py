from qualifier.utils_i4l import left_or_right
from qualifier.utils_i4l import computeMinMaxDist, computeAdjacency

def qualify_LeftRight(data):
    #every qualifier function must specify these two parameters\n",
    relation_set = 'leftRight'
    arity = 2
    polygonList = []
    streetList = []
    polygonPointList=[]
    polygonPointSet= set()
    lineStringList = []
    adjacentObjectList=[]
    rels =[]

    for i in range(len(data)):
        if(data[i]['geometry'].geom_type=='Polygon'):
            polygonList.append((i, data[i]['geometry']))
        elif(data[i]['geometry'].geom_type=='LineString'):
            streetList.append((i, data[i]['geometry']))

    maxMinDist = computeMinMaxDist(polygonList, streetList)
    #print(maxMinDist)
    for sec in data:
        if (sec['geometry'].geom_type=='LineString' and sec['attributes']['isRoute']=='Yes'):
            for i in range(len(data)):
                if (data[i]['geometry'].geom_type=='Polygon'):
                    #check that the two geoms are adjacent
                    isAdjacent= computeAdjacency(data[i]['geometry'], sec['geometry'], maxMinDist)
                    #print ("is adjacent...:",isAdjacent)
                    if(isAdjacent == "Adjacent"):
                        rel={'obj 1':sec['attributes']['id'], 'obj 2':data[i]['attributes']['id'], 'relation': left_or_right(sec['geometry'],data[i]['geometry'].exterior)}
                        rels.append(rel)
                    if not (isAdjacent == "Adjacent"):
                        rel={'obj 1':sec['attributes']['id'], 'obj 2':data[i]['attributes']['id'], 'relation': "nonAdjacent"}
                        rels.append(rel)
    return relation_set, arity, {},rels