# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 12:25:10 2018

@author: s_jan001

RCC11: Captures the Topological relations between
    Polygoanl features

"""

#from de9im import pattern
from qualifier.utils_i4l import pattern


DC_pattern = pattern('FF*FF****')
ECp_pettern = pattern('FF*F0****')
ECl_pettern = pattern('FF*F1****')
PO_pettern = pattern('T*T***T**')
NTPP_pattern = pattern('T*****FF*')
NTPP_inv_pattern = pattern('T*F**F***')
TPPp_pattern = pattern('2FF10FTTT')
TPPl_pattern = pattern('2FF11FTTT')
TPPp_inv_pattern=pattern('**F*0F***')
TPPl_inv_pattern=pattern('2FF11FTTT')
equals_pattern=pattern('T*F**FFF*')

def polygonal_topology (p1, p2):

    im_pettern=p1.relate(p2)

    #return im_pettern
    if( DC_pattern.matches(im_pettern)):
        return "dc"
    elif( ECp_pettern.matches(im_pettern)):
        return "ecp"
    elif( ECl_pettern.matches(im_pettern)):
        return "ecl"
    elif(PO_pettern.matches(im_pettern)):
        return "po"
    elif( NTPP_pattern.matches(im_pettern)):
        return "ntpp"
    elif( NTPP_inv_pattern.matches(im_pettern)):
        return "ntppi"
    elif( TPPp_pattern.matches(im_pettern)):
        return "tppp"
    elif( TPPl_pattern.matches(im_pettern)):
        return "tppl"
    elif( TPPp_inv_pattern.matches(im_pettern)):
        return "tpppi"
    elif( TPPp_inv_pattern.matches(im_pettern)):
        return "tppli"
    elif( equals_pattern.matches(im_pettern)):
        return "eq"


def qualify_rcc11(data):
    # every qualifier function must specify these two parameters
    qualify_rcc11.relation_set = 'RCC11'
    qualify_rcc11.arity = 2

    return 'RCC11', 2, {}, [{'obj 1': data[i]['attributes']['id'], 'obj 2': sec['attributes']['id'],
                             'relation': polygonal_topology(data[i]['geometry'], sec['geometry'])}
                            for i in range(len(data[:-1])) for sec in data[i + 1:] if
                            (data[i]['geometry'].geom_type == 'Polygon' and sec['geometry'].geom_type == 'Polygon')]