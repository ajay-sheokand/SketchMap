# -*- coding: utf-8 -*-
"""
Function captures:
        - topological relations between  streets
Created on Wed Jan 31 11:05:43 2018

@author: s_jan001
"""
from qualifier.utils_i4l import pattern

#disjoint = pattern('FF*FF****')
touch1 = pattern('FF1F00102')
touch2 = pattern('FF10F0102')
#contains = pattern('T*****FF*')
#within = pattern('T*F**F***')
#covers = pattern('T*****FF*' or '*T****FF*'or '***T**FF*'or '****T*FF*')
#covered_by = pattern('T*F**F***'or'*TF**F***'or '**FT*F***' or '**F*TF***')
#crosses = pattern('T*T******' or 'T*****T**' or '0********' )
#overlaps = pattern('T*T***T**' or '1*T***T**')

def compute_street_topology (st1, st2):
    im_pettern=st1.relate(st2)
    #return im_pettern
    if( touch1.matches(im_pettern)):
        return "connected" 
    if( touch2.matches(im_pettern)):
        return "connected" 
    else:
        return "disconnected"


def qualify_street_connectivity(data):
    qualify_street_connectivity.relation_set = 'streetTopology'
    qualify_street_connectivity.arity = 2,
    return 'streetTopology', 2, {},[{'obj 1':data[i]['attributes']['id'], 'obj 2':sec['attributes']['id'], 'relation':compute_street_topology(data[i]['geometry'], sec['geometry'])} 
        for i in range(len(data[:-1])) for sec in data[i+1:] if (data[i]['geometry'].geom_type=='LineString'and sec['geometry'].geom_type=='LineString') ]
 