
# -*- coding: utf-8 -*-
"""
    - Get object ID
    - Relations 
    - Feature Type
"""

from . import inverses


#def get_sub_name(bj_sm, jb_mm):

 #   return sub_id_sm


def get_objects_relations(qcn, features):
    obj1 = qcn['obj 1']
    obj2 = qcn['obj 2']
    rel = qcn['relation']
    try:
        for feat in features:
            if (obj1 == feat['id']):
                featurType_obj1= feat['feat_type']
            if (obj2 == feat['id']):
                featurType_obj2= feat['feat_type']
    except IndexError:
       print( "Problem in fatching IDs, Relations, and FeatureType")
    return obj1,obj2, rel, featurType_obj1, featurType_obj2

"""
    ----------Collect Features---------------
"""

def get_features(features):
    featureList = []
    try:
        for feat in features:
            featureList.append(feat)
    except IOError:
        print("Map features are not found")
    return featureList

"""
    ----------RCC11---------------
"""

def get_rcc8_constraints (qcns):

    rcc11constraints = []
    try:
        for item in qcns:
            for rcc11_const in item['constraints']:
                if item['relation_set']=="RCC8":
                    rcc11constraints.append(rcc11_const)
    except IOError:
         print("NO RCC relations found")
    return rcc11constraints

"""
    ----------Linear Ordering---------------
"""

def get_linearOrdering_constraints (qcns):
    loConstraints = []
    try:
        for item in qcns:
            for lo_const in item['constraints']:
                if item['relation_set']=="linearOrdering":
                    if lo_const['relation'] !="nonAdjacent" or lo_const['relation'] != "None":
                        loConstraints.append(lo_const)
    except IOError:
         print("NO Linear Ordering relations found")
    return loConstraints
"""
    ----------LeftRight---------------
"""

def get_leftRight_constraints (qcns):
    lrConstraints = []
    try:
        for item in qcns:
            for lr_const in item['constraints']:
                if item['relation_set']=="leftRight":
                    if lr_const['relation'] !="nonAdjacent":

                       lrConstraints.append(lr_const)
    except IOError:
         print("NO LeftRight relations found")
    return lrConstraints


"""
    DE9IM
"""

def get_de9im_constraints (qcns):
    de9imConstraints = []
    try:
        for item in qcns:
            for de9im_const in item['constraints']:
                if item['relation_set']=="DE9IM":
                    if de9im_const['relation'] !="nonAdjacent":
                        #print("lr constraints...",de9im_const)
                        de9imConstraints.append(de9im_const)
    except IOError:
         print("NO DE9IM relations found")
    return de9imConstraints


"""
   Street Topology
"""
def get_strTop_constraints (qcns):
    strTopConstraints = []
    try:
        for item in qcns:
            for  strTop_const in item['constraints']:
                if item['relation_set']=="streetTopology":
                    if  strTop_const['relation'] !="nonAdjacent":
                        strTopConstraints.append( strTop_const)
    except IOError:
         print("NO Street Topology relations found")
    return  strTopConstraints

"""
   Relative Orientation -OPRA
"""
def get_opra_constraints (qcns):
    opraConstraints = []
    try:
        for item in qcns:
            for  opra_const in item['constraints']:
                if item['relation_set']=="opra":
                    if  opra_const['relation'] !="nonAdjacent":
                        opraConstraints.append( opra_const)
    except IOError:
         print("NO OPRA relations found")
    return  opraConstraints
#====================================rcc11================================================

def getTotalRelations_rcc8_mm(mm_qcns):

    total_rels_rcc11_mm = 0

    if mm_qcns['properties']['map_type'] == "metric_map":
        constriantList_rcc11=  get_rcc8_constraints(mm_qcns['constraint_collection'])
        for  rel in constriantList_rcc11:
            total_rels_rcc11_mm +=1
    return total_rels_rcc11_mm


def getTotalRelations_rcc8_sm(sm_qcns):
    total_rels_rcc11_sm = 0

    if sm_qcns['properties']['map_type'] == "sketch_map":
        constriantList_rcc11 = get_rcc8_constraints(sm_qcns['constraint_collection'])
        for rel in constriantList_rcc11:
            total_rels_rcc11_sm += 1
    return total_rels_rcc11_sm


def getCorrectRelation_rcc8(sm_qcns, mm_qcns):
    matchedRelations = 0

    # Get constraints and features
    qcns_sm = get_rcc8_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_rcc8_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    try:
        # Build a lookup for `mm_qcns` to speed up comparison
        mm_lookup = {}
        for qcn_mm in qcns_mm:
            obj1_mm, obj2_mm, rel_mm, featTyp_obj1_mm, featTyp_obj2_mm = get_objects_relations(qcn_mm, feats_mm)
            mm_lookup[(obj1_mm, obj2_mm, featTyp_obj1_mm, featTyp_obj2_mm)] = rel_mm
            mm_lookup[(obj2_mm, obj1_mm, featTyp_obj2_mm, featTyp_obj1_mm)] = inverses.get_rcc8_inv_rel(rel_mm)

        # Compare with `qcns_sm`
        for qcn_sm in qcns_sm:
            obj1_sm, obj2_sm, rel_sm, featTyp_obj1_sm, featTyp_obj2_sm = get_objects_relations(qcn_sm, feats_sm)
            key = (obj1_sm, obj2_sm, featTyp_obj1_sm, featTyp_obj2_sm)
            swapped_key = (obj2_sm, obj1_sm, featTyp_obj2_sm, featTyp_obj1_sm)

            # Check for correct match using dictionary lookup
            if key in mm_lookup and mm_lookup[key] == rel_sm:
                matchedRelations += 1
            elif swapped_key in mm_lookup and inverses.get_rcc8_inv_rel(rel_sm) == mm_lookup[swapped_key]:
                matchedRelations += 1

    except IndexError:
        print("Problem in computing RCC8 correct relations")

    return matchedRelations


def getWrongRelations_rcc8(sm_qcns, mm_qcns):
    wrong_matched_rcc11 = 0
    qcns_sm = get_rcc8_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_rcc8_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    try:
        # Build lookup for `mm_qcns` to speed up comparison
        mm_lookup = {}
        for qcn_mm in qcns_mm:
            obj1_mm, obj2_mm, rel_mm, featTyp_obj1_mm, featTyp_obj2_mm = get_objects_relations(qcn_mm, feats_mm)
            mm_lookup[(obj1_mm, obj2_mm, featTyp_obj1_mm, featTyp_obj2_mm)] = rel_mm
            mm_lookup[(obj2_mm, obj1_mm, featTyp_obj2_mm, featTyp_obj1_mm)] = inverses.get_rcc8_inv_rel(rel_mm)

        # Compare with `qcns_sm`
        for qcn_sm in qcns_sm:
            obj1_sm, obj2_sm, rel_sm, featTyp_obj1_sm, featTyp_obj2_sm = get_objects_relations(qcn_sm, feats_sm)
            key = (obj1_sm, obj2_sm, featTyp_obj1_sm, featTyp_obj2_sm)
            swapped_key = (obj2_sm, obj1_sm, featTyp_obj2_sm, featTyp_obj1_sm)

            # Check for wrong match using dictionary lookup
            if key in mm_lookup and mm_lookup[key] != rel_sm:
                wrong_matched_rcc11 += 1
            elif swapped_key in mm_lookup and inverses.get_rcc8_inv_rel(rel_sm) != mm_lookup[swapped_key]:
                wrong_matched_rcc11 += 1

    except IndexError:
        print("Problem in computing RCC8 wrong relations")

    return wrong_matched_rcc11


#============================================= Linear Ordering===========================================



def getTotalLinearOrderingReltions_mm(mm_qcns):

    total_rels_lo_mm = 0

    if mm_qcns['properties']['map_type'] == "metric_map":
        constriantList_rcc11=  get_linearOrdering_constraints(mm_qcns['constraint_collection'])
        for  rel in constriantList_rcc11:
            total_rels_lo_mm +=1
    return total_rels_lo_mm


def getTotalLinearOrderingReltions_sm(sm_qcns):
    total_rels_lo_sm = 0

    if sm_qcns['properties']['map_type'] == "sketch_map":
        constriantList_lo = get_linearOrdering_constraints(sm_qcns['constraint_collection'])
        for rel in constriantList_lo:
            total_rels_lo_sm += 1
    return total_rels_lo_sm


def getCorrectRelation_linearOrdering(sm_qcns, mm_qcns):
    matchedRelations_lo = 0
    qcns_sm = get_linearOrdering_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_linearOrdering_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    # Preprocess mm_qcns into a dictionary for O(1) access
    mm_lookup = {}
    for qcn_mm in qcns_mm:
        obj1, obj2, rel, f1, f2 = get_objects_relations(qcn_mm, feats_mm)
        key = (obj1, obj2, f1, f2)
        inv_key = (obj2, obj1, f2, f1)
        mm_lookup[key] = rel
        mm_lookup[inv_key] = inverses.get_linearOrdering_inv_rel(rel)

    # Check each sm_qcn against the lookup
    for qcn_sm in qcns_sm:
        obj1, obj2, rel, f1, f2 = get_objects_relations(qcn_sm, feats_sm)
        key = (obj1, obj2, f1, f2)
        if key in mm_lookup and mm_lookup[key] == rel:
            matchedRelations_lo += 1

    return matchedRelations_lo



def getWrongRelations_linearOrdering(sm_qcns, mm_qcns):
    wrong_matched_lo = 0
    qcns_sm = get_linearOrdering_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_linearOrdering_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    # Build a lookup for MM constraints
    mm_lookup = {}
    for qcn_mm in qcns_mm:
        obj1, obj2, rel_mm, f1, f2 = get_objects_relations(qcn_mm, feats_mm)
        mm_lookup[(obj1, obj2, f1, f2)] = rel_mm
        mm_lookup[(obj2, obj1, f2, f1)] = inverses.get_linearOrdering_inv_rel(rel_mm)

    for qcn_sm in qcns_sm:
        obj1, obj2, rel_sm, f1, f2 = get_objects_relations(qcn_sm, feats_sm)
        key = (obj1, obj2, f1, f2)
        if key in mm_lookup and mm_lookup[key] != rel_sm:
            wrong_matched_lo += 1

    return wrong_matched_lo

#============================================= Left-Right ===========================================


def getTotalLeftRightRelations_mm(mm_qcns):

    total_rels_lr_mm = 0

    if mm_qcns['properties']['map_type'] == "metric_map":
        constriantList_lr=  get_leftRight_constraints(mm_qcns['constraint_collection'])
        #print("total Relations in LR_MM", constriantList_lr)
        for  rel in constriantList_lr:
            total_rels_lr_mm +=1
    return total_rels_lr_mm


def getTotalLeftRightRelations_sm(sm_qcns):
    total_rels_lr_sm = 0
    if sm_qcns['properties']['map_type'] == "sketch_map":
        constriantList_lr = get_leftRight_constraints(sm_qcns['constraint_collection'])
        #print("total Relations in LR_SM", constriantList_lr)
        for rel in constriantList_lr:
            total_rels_lr_sm += 1
    return total_rels_lr_sm


def getCorrectrelations_leftRight(sm_qcns, mm_qcns):
    matchedRelations_lr = 0
    qcns_sm = get_leftRight_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_leftRight_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    # Build MM relation lookup with normal and inverse key mappings
    mm_lookup = {}
    for qcn_mm in qcns_mm:
        obj1, obj2, rel_mm, f1, f2 = get_objects_relations(qcn_mm, feats_mm)
        mm_lookup[(obj1, obj2, f1, f2)] = rel_mm
        mm_lookup[(obj2, obj1, f2, f1)] = inverses.get_leftRight_inv_rel(rel_mm)

    for qcn_sm in qcns_sm:
        obj1, obj2, rel_sm, f1, f2 = get_objects_relations(qcn_sm, feats_sm)
        key = (obj1, obj2, f1, f2)
        if key in mm_lookup and mm_lookup[key] == rel_sm:
            matchedRelations_lr += 1

    return matchedRelations_lr



def getWrongCorrectrelations_leftRight(sm_qcns, mm_qcns):
    wrong_matched_lr = 0
    qcns_sm = get_leftRight_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_leftRight_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    # Build MM relation lookup with normal and inverse key mappings
    mm_lookup = {}
    for qcn_mm in qcns_mm:
        obj1, obj2, rel_mm, f1, f2 = get_objects_relations(qcn_mm, feats_mm)
        mm_lookup[(obj1, obj2, f1, f2)] = rel_mm
        mm_lookup[(obj2, obj1, f2, f1)] = inverses.get_leftRight_inv_rel(rel_mm)

    for qcn_sm in qcns_sm:
        obj1, obj2, rel_sm, f1, f2 = get_objects_relations(qcn_sm, feats_sm)
        key = (obj1, obj2, f1, f2)
        if key in mm_lookup and mm_lookup[key] != rel_sm:
            wrong_matched_lr += 1

    return wrong_matched_lr



#============================================= DE9IM ===========================================


def getTotalDE9IMRelations_mm(mm_qcns):

    total_rels_de9im_mm = 0

    if mm_qcns['properties']['map_type'] == "metric_map":
        constriantList_de9im=  get_de9im_constraints(mm_qcns['constraint_collection'])
        for  rel in constriantList_de9im:
            total_rels_de9im_mm +=1
    return total_rels_de9im_mm


def getTotalDE9IMRelations_sm(sm_qcns):
    total_rels_de9im_sm = 0
    if sm_qcns['properties']['map_type'] == "sketch_map":
        constriantList_de9im = get_de9im_constraints(sm_qcns['constraint_collection'])
        for rel in constriantList_de9im:
            total_rels_de9im_sm += 1
    return total_rels_de9im_sm


def getCorrectrelations_DE9IM(sm_qcns, mm_qcns):
    matchedRelations_de9im = 0
    qcns_sm = get_de9im_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_de9im_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    # Build a fast lookup with direct and inverse keys
    mm_lookup = {}
    for qcn_mm in qcns_mm:
        obj1, obj2, rel_mm, f1, f2 = get_objects_relations(qcn_mm, feats_mm)
        mm_lookup[(obj1, obj2, f1, f2)] = rel_mm
        mm_lookup[(obj2, obj1, f2, f1)] = inverses.get_de9im_inv_rel(rel_mm)

    for qcn_sm in qcns_sm:
        obj1, obj2, rel_sm, f1, f2 = get_objects_relations(qcn_sm, feats_sm)
        key = (obj1, obj2, f1, f2)
        if key in mm_lookup and mm_lookup[key] == rel_sm:
            matchedRelations_de9im += 1

    return matchedRelations_de9im



def getWrongCorrectrelations_DE9IM(sm_qcns, mm_qcns):
    wrong_matched_de9im = 0
    qcns_sm = get_de9im_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_de9im_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    # Build a fast lookup with direct and inverse keys
    mm_lookup = {}
    for qcn_mm in qcns_mm:
        obj1, obj2, rel_mm, f1, f2 = get_objects_relations(qcn_mm, feats_mm)
        mm_lookup[(obj1, obj2, f1, f2)] = rel_mm
        mm_lookup[(obj2, obj1, f2, f1)] = inverses.get_de9im_inv_rel(rel_mm)

    for qcn_sm in qcns_sm:
        obj1, obj2, rel_sm, f1, f2 = get_objects_relations(qcn_sm, feats_sm)
        key = (obj1, obj2, f1, f2)
        if key in mm_lookup and mm_lookup[key] != rel_sm:
            wrong_matched_de9im += 1

    return wrong_matched_de9im




#============================================= StreetTopology ===========================================


def getTotalStreetTopology_mm(mm_qcns):

    total_rels_strTop_mm = 0
    if mm_qcns['properties']['map_type'] == "metric_map":
        constriantList_strTop=  get_strTop_constraints(mm_qcns['constraint_collection'])
        for  rel in constriantList_strTop:
            total_rels_strTop_mm +=1
    return total_rels_strTop_mm


def getTotalStreetTopology_sm(sm_qcns):
    total_rels_strTop_sm = 0
    if sm_qcns['properties']['map_type'] == "sketch_map":
        constriantList_strTop = get_strTop_constraints(sm_qcns['constraint_collection'])
        for rel in constriantList_strTop:
            total_rels_strTop_sm += 1
    return total_rels_strTop_sm


def getCorrectrelations_streetTopology(sm_qcns, mm_qcns):
    matchedRelations_strTop = 0
    qcns_sm = get_strTop_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_strTop_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    # Preprocess mm constraints into a set for fast lookup
    mm_lookup = set()

    for qcn_mm in qcns_mm:
        obj1_mm, obj2_mm, rel_mm, f1_mm, f2_mm = get_objects_relations(qcn_mm, feats_mm)
        inv_rel_mm = inverses.get_topStreets_inv_rel(rel_mm)
        # Add both directions
        mm_lookup.add((obj1_mm, obj2_mm, f1_mm, f2_mm, rel_mm))
        mm_lookup.add((obj2_mm, obj1_mm, f2_mm, f1_mm, inv_rel_mm))

    # Loop over sketch constraints once
    for qcn_sm in qcns_sm:
        obj1_sm, obj2_sm, rel_sm, f1_sm, f2_sm = get_objects_relations(qcn_sm, feats_sm)
        inv_rel_sm = inverses.get_topStreets_inv_rel(rel_sm)

        # Check if any matching relation exists
        if (
            (obj1_sm, obj2_sm, f1_sm, f2_sm, rel_sm) in mm_lookup
            or (obj2_sm, obj1_sm, f2_sm, f1_sm, inv_rel_sm) in mm_lookup
        ):
            matchedRelations_strTop += 1



    return matchedRelations_strTop


def getWrongCorrectrelations_streetTopology(sm_qcns, mm_qcns):
    wrong_matched_strTop = 0

    qcns_sm = get_strTop_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_strTop_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    try:
        # Precompute inverse relations once
        inverse_rel_lookup = {
            rel: inverses.get_topStreets_inv_rel(rel) for _, _, rel, *_ in map(lambda q: get_objects_relations(q, feats_mm), qcns_mm)
        }

        # Create a lookup for `qcns_mm` constraints
        mm_lookup = {}
        for qcn_mm in qcns_mm:
            obj1_mm, obj2_mm, rel_mm, type1_mm, type2_mm = get_objects_relations(qcn_mm, feats_mm)
            mm_lookup[(obj1_mm, obj2_mm, type1_mm, type2_mm)] = rel_mm
            mm_lookup[(obj2_mm, obj1_mm, type2_mm, type1_mm)] = inverse_rel_lookup.get(rel_mm)

        # Now iterate over `qcns_sm` constraints and check for mismatches
        for qcn_sm in qcns_sm:
            obj1_sm, obj2_sm, rel_sm, type1_sm, type2_sm = get_objects_relations(qcn_sm, feats_sm)
            key = (obj1_sm, obj2_sm, type1_sm, type2_sm)
            swapped_key = (obj2_sm, obj1_sm, type2_sm, type1_sm)

            # Check for correct match in `mm_lookup`
            if key in mm_lookup and mm_lookup[key] != rel_sm:
                wrong_matched_strTop += 1
            elif swapped_key in mm_lookup and inverse_rel_lookup.get(rel_sm) != mm_lookup[swapped_key]:
                wrong_matched_strTop += 1

    except IndexError:
        print("Problem in computing Street Topology wrong relations")

    return wrong_matched_strTop




#============================================= OPRA ===========================================

def getTotalOPRA_mm(mm_qcns):
    total_rels_opra_mm = 0
    if mm_qcns['properties']['map_type'] == "metric_map":
        constriantList_strTop=  get_opra_constraints(mm_qcns['constraint_collection'])
        for  rel in constriantList_strTop:
            total_rels_opra_mm +=1
    return total_rels_opra_mm


def getTotalOPRA_sm(sm_qcns):
    total_rels_opra_sm = 0
    if sm_qcns['properties']['map_type'] == "sketch_map":
        constriantList_opra = get_opra_constraints(sm_qcns['constraint_collection'])
        for rel in constriantList_opra:
            total_rels_opra_sm += 1
    return total_rels_opra_sm


def getCorrectrelations_opra(sm_qcns, mm_qcns):
    matchedRelations_opra = 0
    qcns_sm = get_opra_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_opra_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    # Build a fast lookup with direct and inverse keys
    mm_lookup = {}
    for qcn_mm in qcns_mm:
        obj1, obj2, rel_mm, f1, f2 = get_objects_relations(qcn_mm, feats_mm)
        mm_lookup[(obj1, obj2, f1, f2)] = rel_mm
        mm_lookup[(obj2, obj1, f2, f1)] = inverses.get_opra_inv_rel(rel_mm)

    for qcn_sm in qcns_sm:
        obj1, obj2, rel_sm, f1, f2 = get_objects_relations(qcn_sm, feats_sm)
        key = (obj1, obj2, f1, f2)
        if key in mm_lookup and mm_lookup[key] == rel_sm:
            matchedRelations_opra += 1

    return matchedRelations_opra




def getWrongCorrectrelations_opra(sm_qcns, mm_qcns):
    wrong_matched_opra = 0
    qcns_sm = get_opra_constraints(sm_qcns['constraint_collection'])
    qcns_mm = get_opra_constraints(mm_qcns['constraint_collection'])
    feats_sm = get_features(sm_qcns['features'])
    feats_mm = get_features(mm_qcns['features'])

    # Build a fast lookup with direct and inverse keys
    mm_lookup = {}
    for qcn_mm in qcns_mm:
        obj1, obj2, rel_mm, f1, f2 = get_objects_relations(qcn_mm, feats_mm)
        mm_lookup[(obj1, obj2, f1, f2)] = rel_mm
        mm_lookup[(obj2, obj1, f2, f1)] = inverses.get_opra_inv_rel(rel_mm)

    for qcn_sm in qcns_sm:
        obj1, obj2, rel_sm, f1, f2 = get_objects_relations(qcn_sm, feats_sm)
        key = (obj1, obj2, f1, f2)
        if key in mm_lookup and mm_lookup[key] != rel_sm:
            wrong_matched_opra += 1

    return wrong_matched_opra
