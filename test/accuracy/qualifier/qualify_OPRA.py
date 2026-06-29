"""
    Computes the relative orientation between connected street segments at junctions
        - at the moment between all streets 
        - computes angles in Clockwise range between (P1-> P0 -> p2)
        - the angles are classified in to different ranges 
            i.e. left, right, front and so on....
@author: s_jan001

"""


import  numpy as np
from qualifier.utils_i4l import pattern


def computeAngle(l1, l2):
    l1Coord=  l1.coords[:]
    #print (l1Coord[:])
    #print ("first Point:",l1Coord[:1])
    #print ("last Point:", l1Coord[-1:])
    
    v1=np.array(l1.coords[:])[0] - np.array(l1.coords[:])[-1] 
   # print ("0........",np.array(l1.coords[:])[0])
    #print ("1........",np.array(l1.coords[:])[-1])
    v2=np.array(l2.coords[:])[-1] - np.array(l2.coords[:])[0]
        
    #print "lines", l1, l2
    #print "vectors", v1, v2
 

    #print "*v1[::-1], *v2[::-1]", v1[::-1], v2[::-1]
    ang1 = np.arctan2(*v1[::-1])
    ang2 = np.arctan2(*v2[::-1])
    #print ang1, " in degrees ", np.rad2deg((ang1) % (2 * np.pi))
    #print ang2, " in degrees ", np.rad2deg((ang2) % (2 * np.pi))
    rangle= (ang1 - ang2) % (2 * np.pi)
    dangle= np.rad2deg(rangle)
    return rangle, dangle
    
#computeAngle(LineString((Point(0,0),Point(0,1))), LineString((Point(0, 0),Point(1, -1))))

def opraRelations(angle):
    if (angle <= 25.0 and angle > 0.0):
        return "back_of"
    if (angle <= 68.0 and angle > 25.0):
        return "sharp_left_of"
    if(angle <= 112.0 and angle > 68.0):
        return "left_of"
    elif (angle <= 155.0 and angle > 112.0):
        return "half_left"
    elif (angle <= 205.0 and angle > 155.0):
        return "front_of"
    elif (angle <= 248.0 and angle > 205.0):
        return "half_right"
    elif (angle <= 292.0 and angle > 248.0):
        return "right_of"
    elif (angle <= 335.0 and angle > 292.0):
        return "sharp_right_of"
    elif (angle <= 360.0 and angle > 335):
        return "back_of"
    else:
        return "none"

    
    
def computeOPRA(l1, l2):
    touch = pattern('FF1F00102')
    im_pettern=l1.relate(l2)
    #print ("im_pattern....:",im_pettern)
    rangle, dangle = computeAngle(l1, l2)
    #print (dangle)
    if(touch.matches(im_pettern)):
        opraRelation = opraRelations(dangle)
        return opraRelation
    else:
        return "nonAdjacent"

def qualify_OPRA(data):
    #every qualifier function must specify these two parameters
    qualify_OPRA.relation_set = 'opra'
    qualify_OPRA.arity = 2
    return 'opra', 2, {}, [{'obj 1':data[i]['attributes']['id'], 'obj 2':sec['attributes']['id'], 'relation':computeOPRA(data[i]['geometry'], sec['geometry'])}
        for i in range(len(data[:-1])) for sec in data[i+1:] if (data[i]['geometry'].geom_type=='LineString'and sec['geometry'].geom_type=='LineString')]


