
# -*- coding: utf-8 -*-
"""
Created on Mon 09 July 15:20:54 2018

@author: s_jan001

"""

def get_rcc8_inv_rel(rel):
    if rel=="dc":
        return "dc"
    elif rel=="ec":
        return "ec"
    elif rel=="po":
        return "po"
    elif rel== "tpp":
        return "tppi"
    elif rel=="tppi":
        return "tpp"
    elif rel=="ntpp":
        return "ntppi"
    elif rel == "ntppi":
        return "ntpp"
    elif rel == "eq":
        return "eq"
    else:
        return "None"



def get_linearOrdering_inv_rel(rel):
    if rel=="before":
        return "after"
    elif rel=="after":
        return "before"
    elif rel=="meets":
        return "meet_by"
    elif rel== "meet_by":
        return "meets"
    elif rel=="overlaps":
        return "overlapped_by"
    elif rel=="overlapped_by":
        return "overlaps"
    elif rel == "during":
        return "during_inv"
    elif rel == "during_inv":
        return "during"
    elif rel =="starts":
        return "started_by"
    elif rel =="started_by":
        return "starts"
    elif rel =="finishes":
        return "finished_by"
    elif rel == "finished_by":
        return "finishes"
    elif rel == "equals":
        return "equals"
    else:
        return "None"


def get_leftRight_inv_rel(rel):
    if rel=="left":
        return "right"
    elif rel=="right":
        return "left"
    elif rel=="crosses":
        return "crosses"
    else:
        return "None"


def get_de9im_inv_rel(rel):
    if rel == "disjoint":
        return "disjoint"
    elif rel == "touches":
        return "touches"
    elif rel == "intersects":
        return "intersects"
    elif rel == "within":
        return "within"
    elif rel == "crosses":
        return "crosses"
    else:
        return "None"


def get_topStreets_inv_rel(rel):
    if rel == "connected":
        return "connected"
    elif rel == "disconnected":
        return "disconnected"
    else:
        return "None"


def get_opra_inv_rel(rel):
    if rel == "left_of":
        return "right_of"
    elif rel == "right_of":
        return "left_of"
    elif rel == "half_left":
        return "half_right"
    elif rel == "half_right":
        return "half_left"
    elif rel == "front_of":
        return "back_of"
    elif rel == "back_of":
        return "front_of"
    else:
        return "None"


def createUserRecord(name,username,password,confirm,affiliation,email):
    userRecord= {
            "name": name,
            "username": username,
            "password": password,
            "confirm":confirm,
            "affiliation":affiliation,
            "email":email
             }
    return userRecord