# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 13:52:11 2018

@author: Malumbo
"""

#from neo4j.v1 import GraphDatabase
#import numbers
#from time import ctime
from py2neo import Graph, Node, Relationship, NodeSelector

#uri = "bolt://localhost:7687"
#driver = GraphDatabase.driver(uri)

#uri = "http://localhost:7687"
#graphObj = Graph(uri=uri)
session = driver.session()

# format parameters correctly
def param_format(key, value):
    _value = value
    if (not isinstance(value, numbers.Number)):
        _value = "'" + str(value) + "'"
    else:
        _value = str(value)
    
    return [key, _value]

# function to fetch matching pair of features
def mk_feature_pair_dict():
    smid = 2101
    mmid = 2437
    fdict = {}
    query = 'match (nm:Map),(nm_b:Map) \
                where ID(nm) = '+ str(smid) +' and nm.map_type = "\'sketch_map\'" \
                and ID(nm_b) = '+ str(mmid) +' and nm_b.map_type = "\'metric_map\'" \
                with nm, nm_b \
                match (nm)-[hpr:HAS_PARTIAL_REPRESENTATION]->(nq:QCN)-[hn:HAS_NODE]->(nqn:QCN_Node)-[sr:SPATIAL_RELATION]->(nqn1:QCN_Node) \
                with nm_b,nm,hn,nqn,nq,nqn1,sr \
                match (nm_b)-[hpr_b:HAS_PARTIAL_REPRESENTATION]->(nq_b:QCN)-[hn_b:HAS_NODE]->(nqn_b:QCN_Node)-[sr_b:SPATIAL_RELATION]->(nqn1_b:QCN_Node) \
                where nq.relation_set = nq_b.relation_set and sr.constraint = sr_b.constraint and nqn.geometry_type = nqn_b.geometry_type \
                and nqn1.geometry_type = nqn1_b.geometry_type and nqn.feat_type = nqn_b.feat_type and nqn1.feat_type = nqn1_b.feat_type \
                with nm_b,nm,hn,nqn,nq,nqn1,sr,nq_b,nqn_b,nqn1_b,sr_b \
                merge (nqn)-[:NEW_RELATION]->(nqn_b) \
                merge (nqn1)-[:NEW_RELATION]->(nqn1_b) \
                return distinct nqn.feature_id as sm_featid, nqn_b.feature_id as mm_featid' 
        
    try:
        print (query)
        params={}
        with driver.session() as session:
            qarg = session.run(query, parameters=params)

    except Exception as e:
        print (e.message)
        print (e.__dict__)
        raise Exception("Problematic Query")
    for arg in qarg:
        smfeatid = arg["sm_featid"]
        mmfeatid = arg["mm_featid"]
        print(smfeatid)
        print(mmfeatid)
        fdict[smfeatid] = mmfeatid

    print(fdict)
"""
def write_to_db_new(mapID, qualified_map):
    query00 = 'match (m:Map) return count(m) as mapcnt'
    query01 = 'match (q:QCN) return count(q) as qcncnt'
    mapcnt = 0
    qcncnt = 0

    try:
        print(query00)
        q00arg = graphObj.run(query00)

        print(query01)
        q01arg = graphObj.run(query01)

    except Exception as e:
        #        print (e.message)
        print(e.__dict__)
        raise Exception("Problematic Query")
    for arg in q00arg:
        mapcnt = arg["mapcnt"]
    for arg in q01arg:
        qcncnt = arg["qcncnt"]

    print("mapcnt=" + str(mapcnt) + " qcncnt=" + str(qcncnt))

    print('Writing query to database: %s' % ctime().split()[3])

    mapObj = Node("Map", mapid=(mapcnt + 1))
    selector = NodeSelector(graphObj)  # identifying all the nodes in graph
    mapTypeFound = selector.select(
        qualified_map['properties']['map_type'] + "s").first()  # selecting the first SKETCH/METRIC MAP node

    map_properties = qualified_map['properties']
    print(qualified_map)
    if len(map_properties):
        for attr in map_properties:
            mapObj[attr] = map_properties[
                attr]  # no need to pass the properties to Node function; instead just add them later like this before sending it to DB

    #    if (1==1):
    #        print(randomvar)
    mapRel = Relationship(mapTypeFound, "HAS_MAP_INSTANCE", mapObj)
    trans = graphObj.begin()
    #print('session started')
    trans.create(mapObj)
    trans.create(mapRel)
    #print('Done1 maps: %s' % ctime().split()[3])
    # create feature nodes and connect each to map node
    # and map the feature node id's to the database id's
    fnode_qname_map = {}
    featDict = {}  # storing feat obj in dictionary
    subG = mapRel  # creating local subgraph

    for f in range(len(qualified_map['features'])):
        fnode = qualified_map['features'][f]
        fnode_qname_map[fnode['id']] = f
        # single query version
        featobj = Node("Feature_Node")  # ISSUE with alias f%s: can be stored in an array   , fid = "f"+str(f)

        for attr in fnode:
            featobj[attr] = fnode[attr]  # adding attributes to feature nodes

        featrel = Relationship(mapObj, "HAS_FEATURE", featobj)
        featDict[fnode['id']] = featobj  # storing feat obj in dictionary, with fid as key
        # changed from fnode['FID'] to fnode['id']

        subG = subG | featrel

    trans.create(subG)
    print('Done2 features: %s' % ctime().split()[3])
    # for each qcn create a representative node and hook it to the map node
    qnodedict = {}
    for q in range(len(qualified_map['constraint_collection'])):
        qcn = qualified_map['constraint_collection'][q]
        qcncnt += 1
        relSetFound = selector.select('RelationType', name=qcn['relation_set']).first()
        qcnObj = Node("QCN", qcncnt=qcncnt)  ## storing the alias q value as property ?!  , qcnid = q
        qcnmapRel = Relationship(mapObj, "HAS_PARTIAL_REPRESENTATION", qcnObj)
        rtRel = Relationship(relSetFound, "HAS_RELATION_TYPE_INSTANCE", qcnObj)

        for prop in qcn:
            if not prop.strip().lower() == 'constraints':
                if (isinstance(qcn[prop], dict)):
                    qcnObj[prop] = str(qcn[prop])
                else:
                    qcnObj[prop] = qcn[prop]

        subG = subG | qcnmapRel
        subG = subG | rtRel

        #  enumerate all qcn nodes and store them up by feature id
        qcn_node_ids = set()
        for constraint in qcn['constraints']:
            for i in range(qcn['arity']):
                qcn_node_ids.add(constraint['obj ' + str(i + 1)])
        print('done here')
        # for each feature node in the map, if qcn refers to feature node: create the corresponding qcn node
        # add each qcn node and hook it up to the qcn's representative node and the corresponding feature node
        for fnode_id in qcn_node_ids:
            qcn_node = 'n%sq%s' % (fnode_qname_map[fnode_id], q)
            qnodeObj = Node("QCN_Node")  # storing the alias values as properties ?!  , qcnnodeid = qcn_node

            qnodeObj['feature_id'] = featDict[fnode_id]['id']  # fnode['FID']

            qnodeObj['geometry_type'] = featDict[fnode_id]['geometry_type']

            qnodeObj['feat_type'] = featDict[fnode_id]['feat_type']

            qnodedict[(qnodeObj['feature_id'], qcn['relation_set'])] = qnodeObj
            # subg = subg | qnodeobj
            qqnoderel = Relationship(qcnObj, "HAS_NODE", qnodeObj)
            fqnoderel = Relationship(featDict[fnode_id], "HAS_REPRESENTATION", qnodeObj)
            subG = subG | qqnoderel
            subG = subG | fqnoderel

        #   for each <arity> combination (constraint), N, of qcn nodes create a database and relations
        for constraint in qcn['constraints']:
            # construct a handle for each constraint to use as both a query parameter and an identifier
            if (qcn['arity'] == 2):
                print(constraint['obj 1'], qcn['relation_set'])
                print(qnodedict)
                print(qnodedict[(constraint['obj 1'], qcn['relation_set'])])
                print(qnodedict[(constraint['obj 2'], qcn['relation_set'])])
                qnodeqnoderel = Relationship(qnodedict[(constraint['obj 1'], qcn['relation_set'])], "SPATIAL_RELATION",
                                             qnodedict[(constraint['obj 2'], qcn['relation_set'])])
                qnodeqnoderel['relation'] = str(constraint['relation'])  # need to verify
                subG = subG | qnodeqnoderel
                print('merged')

            else:
                # when there are more than 2 nodes in a spatial relation then the relation is made as a node
                # and all the feature/qcn_node nodes are connected to this relation node
                spRelObj = Node("Spatial_Relation_Node")

                for i in range(qcn['arity']):
                    qnodeqRel = Relationship(qnodedict[(constraint['obj ' + str(i + 1)], qcn['relation_set'])],
                                             "RELATES", spRelObj)

                    qnodeqRel['pos'] = i
                    qnodeqRel['relation'] = constraint['relation']

                subG = subG | qnodeqRel

    trans.create(subG)

    trans.commit()

    try:
        print('Done1: %s' % ctime().split()[3])
        vmapid = mapObj['mapid']
        print(vmapid)

    #        #mk_feature_pair_dict()
    #        #print ('Done2: %s' % ctime().split()[3])

    except Exception as e:
        print(e.args)
        print(e.__dict__)
        raise Exception("Problematic Query")
    return vmapid
"""
# recieve qualified map
def write_to_db(mapID, qualified_map):
    # 
    query00 = 'match (m:Map) return count(m) as mapcnt'
    query01 = 'match (q:QCN) return count(q) as qcncnt'
    params = {}
    mapcnt = 0
    qcncnt = 0
    
    try:
        print (query00)
        with driver.session() as session:
            q00arg = session.run(query00, parameters=params)
        print (query01)
        with driver.session() as session:
            q01arg = session.run(query01, parameters=params)

    except Exception as e:
        print (e.message)
        print (e.__dict__)
        raise Exception("Problematic Query")
    for arg in q00arg:
        mapcnt = arg["mapcnt"]
    for arg in q01arg:
        qcncnt = arg["qcncnt"]
    query = ''
    print("mapcnt="+str(mapcnt)+" qcncnt="+str(qcncnt))
    
    # create map node
    query = query + 'CREATE (m:Map {mapid:%s}) MERGE (pm:%ss) MERGE (pm)-[r:HAS_MAP_INSTANCE]->(m) SET ' % (mapcnt+1,qualified_map['properties']['map_type'])
    
    map_properties = qualified_map['properties']
    for attr in map_properties:
        param = param_format(attr, map_properties[attr])
        query = query + 'm.%s=$%s,' % (param[0], param[0])
        params[param[0]] = param[1] 

    query = query[:-1]
        
    # create feature nodes and connect each to  map node
    # and map the feature node id's to the database id's
    fnode_qname_map= {}
    
    for f in range(len(qualified_map['features'])):
        fnode = qualified_map['features'][f]
        fnode_qname_map[fnode['id']] = f
        
        # single query version
        query = query + ' CREATE (m)-[:HAS_FEATURE]->(f%s:Feature_Node) SET ' % f

        for attr in fnode:
            param = param_format(attr, fnode[attr])
            param.append(str(attr)+str(f))
            query = query + 'f%s.%s=$%s,' % (f, param[0], param[2])
            params[param[2]] = param[1] 

        query = query[:-1]    
    
    # for each qcn create a representative node and hook it to the map node               
    for q in range(len(qualified_map['constraint_collection'])):
        qcn = qualified_map['constraint_collection'][q]
        qcncnt += 1
        query = query + ' MERGE (rt%s:RelationType {name:\'%s\'}) MERGE (q%s:QCN {qcncnt:\'%s\'}) MERGE (rt%s)-[:HAS_RELATION_TYPE_INSTANCE]->(q%s) MERGE (q%s)<-[:HAS_PARTIAL_REPRESENTATION]-(m) SET ' % (qcn['relation_set'],qcn['relation_set'],q,qcncnt,qcn['relation_set'],q,q)
        
        for prop in qcn:
            if not prop.strip().lower() == 'constraints':
                param = param_format(prop, qcn[prop])
                param.append(str(prop)+str(q))
                query = query + 'q%s.%s=$%s,' % (q, param[0], param[2])
                params[param[2]] = param[1] 
       
        query = query[:-1]
        
        #  enumerate all qcn nodes and store them up by feature id
        qcn_node_ids = set()
        for constraint in qcn['constraints']: 
            for i in range(qcn['arity']):
                qcn_node_ids.add(constraint['obj '+str(i+1)])
        
        # for each feature node in the map, if qcn refers to feature node: create the corresponding qcn node
        # add each qcn node and hook it up to the qcn's representative node and the corresponding feature node
        tmpquery = ''
        for fnode_id in qcn_node_ids:
            qcn_node = 'n%sq%s' % (fnode_qname_map[fnode_id], q)
            tmpquery = tmpquery + ' CREATE (q%s)-[:HAS_NODE]->(%s:QCN_Node)<-[:HAS_REPRESENTATION]-(f%s) SET ' % (q, qcn_node, fnode_qname_map[fnode_id])
            tmpquery = tmpquery + '%s.feature_id=f%s.id, ' % (qcn_node, fnode_qname_map[fnode_id])
            tmpquery = tmpquery + '%s.geometry_type = f%s.geometry_type, ' % (qcn_node, fnode_qname_map[fnode_id])
            tmpquery = tmpquery + '%s.feat_type = f%s.feat_type' % (qcn_node, fnode_qname_map[fnode_id])

        #   for each <arity> combination (constraint), N, of qcn nodes create a database and relations
        for constraint in qcn['constraints']: 
            # construct a handle for each constraint to use as both a query parameter and an identifier
            current_constraint = 'q%sr' % q
            if (qcn['arity'] == 2):
                qcn_node_1 = 'n%sq%s' % (fnode_qname_map[constraint['obj 1']], q)
                qcn_node_2 = 'n%sq%s' % (fnode_qname_map[constraint['obj 2']], q)
                current_constraint = current_constraint + '_' + str(fnode_qname_map[constraint['obj 1']]) + '_' + str(fnode_qname_map[constraint['obj 2']])
                tmpquery = tmpquery + ' CREATE (%s)-[{0}:SPATIAL_RELATION]->(%s) ' % (qcn_node_1, qcn_node_2)
                
            else:
                tmpquery = tmpquery + ' CREATE ({0}:SPATIAL_RELATION), '
                for i in range(qcn['arity']):
                    qcn_node_i = 'n%sq%s' % (fnode_qname_map[constraint['obj '+ str(i+1)]], q)
                    tmpquery = tmpquery + ' (n%s)-[role:RELATES {pos: %d }]->({0}),' % (qcn_node_i, i)
                    current_constraint = current_constraint + '_' + str(fnode_qname_map[constraint['obj '+ str(i+1)]])
                
                tmpquery = tmpquery.format(current_constraint)[:-1]
                            
            tmpquery = tmpquery + ' SET {0}.constraint=${0}'
            tmpquery = tmpquery.format(current_constraint)
            param = param_format(current_constraint, constraint['relation'])
            params[param[0]] = param[1]

        query = query + tmpquery
    try:
        query = query + ' return ID(m) as map_id '
        session = driver.session()
        print ('Writing query to database: %s' % ctime().split()[3])
        print ("final Query....",query)
        qarg = session.run(query, parameters=params)
        for arg in qarg:
            mapid = arg["map_id"]
        
        print ('Done1: %s' % ctime().split()[3])
        
#        mk_feature_pair_dict()
        
#        print ('Done2: %s' % ctime().split()[3])
        
    except Exception as e:
        #print (e.message)
        print (e.__dict__)
        raise Exception("Problematic Query")
    session.close()
    return mapid