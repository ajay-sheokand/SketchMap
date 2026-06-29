import os
import json
from django.shortcuts import render
from django.http import HttpResponse


def get_landmarkCompleteness(totalSketchedLandmarks, total_mm_landmark):
    if totalSketchedLandmarks != 0 or total_mm_landmark != 0:
        landmarkCompleteness = (totalSketchedLandmarks / total_mm_landmark) * 100
    else:
        landmarkCompleteness = 0.00
    return landmarkCompleteness


# get stree_completness
def get_streetCompleteness(totalSketchedStreets, toal_mm_streets):
    if totalSketchedStreets != 0 or toal_mm_streets != 0:
        streetCompleteness = (totalSketchedStreets / toal_mm_streets) * 100
    else:
        streetCompleteness = 0.00
    return streetCompleteness


# get cityblock_completeness
def get_cityblockCompleteness(totalSketchedCityblocks, total_mm_cityblocks):
    if totalSketchedCityblocks != 0 or total_mm_cityblocks != 0:
        cityblockCompleteness = (totalSketchedCityblocks / total_mm_cityblocks) * 100
    else:
        cityblockCompleteness = 0.00
    return cityblockCompleteness


# get overall accuracy
def get_overall_completness(landmarkCompleteness, streetCompleteness):
    overAllCompleteness = 0.00
    overAllCompleteness = (landmarkCompleteness + streetCompleteness) / 2

    return overAllCompleteness





def get_streets_mm(mmqcns):
    st_count = 0

    for feature in mmqcns['features']:
        if feature['geometry']['type'] == "LineString":
            st_count += 1
    return st_count


def get_landmarks_mm(mmqcns):
    lm_count = 0
    for feature in mmqcns['features']:
        print (feature, "check check")
        if feature['properties']['feat_type'] == "Landmark":
            lm_count += 1
    return lm_count


"""
    - get total number of drawn street segments
"""


def get_streets_sm(smqcns):
    st_count = 0

    for feature in smqcns['features']:
        if feature['geometry']['type'] == "LineString":
            st_count += 1
    return st_count


"""
    - get total number of drawn landmarks
"""


def get_landmarks_sm(smqcns):
    lm_count = 0

    for feature in smqcns['features']:
        if feature['properties']['feat_type'] == "Landmark":
            lm_count += 1

    return lm_count


def analyzeCompleteness(request):
    sketchFileName = request.POST.get('sketchFileName')
    metricFileName = request.POST.get('metricFileName')
    print("check check", sketchFileName, metricFileName)
    sketchmapdata = request.POST.get('sketchdata')
    metricmapdata = request.POST.get('metricdata')

    metricMap = json.loads(metricmapdata)
    sketchMap = json.loads(sketchmapdata)

    total_mm_landmarks = get_landmarks_mm(metricMap)
    toal_mm_streets = get_streets_mm(metricMap)
    # total_mm_cityblocks = completeness.get_cityblocks_mm(metricMap)

    totalSketchedLandmarks = get_landmarks_sm(sketchMap)
    totalSketchedStreets = get_streets_sm(sketchMap)
    # totalSketchedCityblocks = completeness.get_cityblocks_sm(sketchMap)

    landmarkCompleteness = get_landmarkCompleteness(totalSketchedLandmarks, total_mm_landmarks)
    landmarkCompleteness = round(landmarkCompleteness, 2)
    # session['landmarkCompleteness'] = landmarkCompleteness

    streetCompleteness = get_streetCompleteness(totalSketchedStreets, toal_mm_streets)
    streetCompleteness = round(streetCompleteness, 2)

    overAllCompleteness = get_overall_completness(landmarkCompleteness, streetCompleteness)
    # session['overAllCompleteness'] = overAllCompleteness
    print("Landmarks :", total_mm_landmarks, "Streets:", toal_mm_streets)
    completeness_results = {"sketchMapID": sketchFileName, "total_mm_landmarks": total_mm_landmarks,
              "toal_mm_streets": toal_mm_streets,
              "totalSketchedLandmarks": totalSketchedLandmarks,
              "totalSketchedStreets": totalSketchedStreets,
              "landmarkCompleteness": landmarkCompleteness,
              "streetCompleteness": streetCompleteness,
              "overAllCompleteness": round(overAllCompleteness, 2)
              }

    # breakpoint()
    print(completeness_results)
    return HttpResponse(json.dumps(completeness_results), content_type="application/json")
