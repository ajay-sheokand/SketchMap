
from qualifier.utils_i4l import computeRelativeDistRanges, distanceRelation

def qualify_relativeDist(data):
        #every qualifier function must specify these two parameters\n",
        qualify_relativeDist.relation_set = 'relDist'
        qualify_relativeDist.arity = 2,
       #relations will have format {'near'=(dmin, dmax), 'far'=(dmin, dmax), 'vfar'=(dmin, dmax)}\n",
        polygonList=[]
        for i in range(len(data)):
            if (data[i]['geometry'].geom_type=='Polygon'):
                polygonList.append(data[i]['geometry'])
        near_end, far_end = computeRelativeDistRanges(polygonList)
        return 'relDist', 2, {},[{'obj 1':data[i]['attributes']['id'], 'obj 2':sec['attributes']['id'], 'relation':distanceRelation(data[i]['geometry'], sec['geometry'], near_end, far_end)} 
           for i in range(len(data[:-1])) for sec in data[i+1:] if (data[i]['geometry'].geom_type=='Polygon'and sec['geometry'].geom_type=='Polygon') ]
 

