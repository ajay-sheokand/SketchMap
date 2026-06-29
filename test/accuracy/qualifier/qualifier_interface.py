# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 11:37:34 2018

@author: Malumbo
"""
from shapely.geometry import *

class qualifier_interface:
    
    def __init__(self, data, properties):
        self.data = data
        self.q_rep = {}
        self.q_rep['properties'] = properties
        self.q_rep['constraint_collection'] = []
        self.q_rep['features'] = []
        
        for d in data:
            x = d['attributes']
            x['geometry_type'] = d['geometry'].geom_type
            self.q_rep['features'].append(x)
        
    def qualify(self, fqualifier):
        
        qcn = {'constraints': []}
        relation_set, arity, modifiers, relations = fqualifier(self.data)
        
        qcn['relation_set'] = relation_set
        qcn['arity'] = arity

        # if the qualifier uses modifiers add them to the 
        if (not len(modifiers)==0):
            qcn['modifiers'] = modifiers
        
        for r in relations:
            if len(r) < qcn['arity']:
                raise TypeError('Expecting relations with {0}-tuples, given a {1}-tuples: {2}'.format(qcn['arity'],len(r),r)) 
            
            qcn['constraints'].append(r)
        
        self.q_rep['constraint_collection'].append(qcn)
        
        return {'features': self.q_rep['features'], 'constraint_collection': [qcn]}
    
    def current_qualitative_representation(self):
        return self.q_rep
