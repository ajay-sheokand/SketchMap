from django.shortcuts import render

# Create your views here.
from django.template import loader
from django.http.response import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import pandas as pd
import os
import glob
import time


global G


def map(request):
    template = loader.get_template('../templates/generalizingmaps.html')
    return HttpResponse(template.render({}, request))

def compare(request):
    return render(request,'compare.html')


def compareResults(request):
    arrayOfResearchers = [0] * 3
    rearrangedDfAlign = [0] * 3
    diff = [0] * 10
    if (request.is_ajax()):
        for i in range(3):
            arrayOfResearchers[i] = request.FILES.get("uploadR" + str(i + 1) + "align")
            df = pd.read_csv(arrayOfResearchers[i], error_bad_lines=False)
            df = df[(df['BaseId'] != "Features drawn extra in sketch map") & (
                        df['BaseId'] != "Features missing in sketch map")]
            sorteddf = df.sort_values('Sketch Map')
            groupeddf = sorteddf.groupby('Sketch Map')
            list_groupeddf = list(groupeddf)
            rearrangedDfAlign[i] = []
            for j in range(len(list_groupeddf)):
                list_groupeddf[j][1]['BaseId'] = list_groupeddf[j][1]['BaseId'].str.split(' ')
                rearrangedDfAlign[i].append(list_groupeddf[j][1].explode('BaseId').sort_values('BaseId'))

        for j in range(10):
            diff[j] = pd.concat([rearrangedDfAlign[0][j][['BaseId', 'Generalization Type']],
                                 rearrangedDfAlign[1][j][['BaseId', 'Generalization Type']],
                                 rearrangedDfAlign[2][j][['BaseId', 'Generalization Type']]],
                                keys=['R1', 'R2', 'R3']).drop_duplicates(keep=False)
            diff[j]['Researcher'] = diff[j].index.get_level_values(0).tolist()
            diff[j]=diff[j].pivot(index='BaseId', columns='Researcher', values='Generalization Type')
            if 'R1' not in diff[j]:
                diff[j]['R1'] = pd.NA
            if 'R2' not in diff[j]:
                diff[j]['R2'] = pd.NA
            if 'R3' not in diff[j]:
                diff[j]['R3'] = pd.NA
            diff[j] = diff[j].reindex(sorted(diff[j].columns), axis=1)
            for index, row in diff[j].iterrows():
                if pd.isna(row['R1']):
                    row['R1']= rearrangedDfAlign[0][j]['Generalization Type'].loc[(rearrangedDfAlign[0][j]['BaseId'])==index]
                if pd.isna(row['R2']):
                    row['R2']= rearrangedDfAlign[1][j]['Generalization Type'].loc[(rearrangedDfAlign[1][j]['BaseId'])==index]
                if pd.isna(row['R3']):
                    row['R3']= rearrangedDfAlign[2][j]['Generalization Type'].loc[(rearrangedDfAlign[2][j]['BaseId'])==index]
            print(diff[j].to_string())
            diff[j] = diff[j].to_json(orient="split")

    return HttpResponse(json.dumps(diff))

# @ensure_csrf_cookie
# def requestFME(request):
#     template = loader.get_template('../templates/generalizingmaps.html')
#     if request.is_ajax():
#         basedata = request.POST.get('basedata')
#         sketchdata = request.POST.get('sketchdata')


#         #response = requests.get('http://desktop-f25rpfv:8080/fmedatastreaming/Generalization/generalizer.fmw?', params=query)
#         USER_PROJ_DIR = "generalizedMap"
#         baseMapdata = json.loads(basedata)
#         sketchMapdata = json.loads(sketchdata)
#         try:
#             Inputbasepath = os.path.join(USER_PROJ_DIR,"inputbaseMap"+".json")
#             Inputsketchpath = os.path.join(USER_PROJ_DIR,"inputsketchMap"+".json")
#             if os.path.exists(Inputbasepath):
#                 os.remove(Inputbasepath)
#             f = open(Inputbasepath, "a+")
#             f.write(json.dumps(baseMapdata,indent=4))
#             f.close()

#             if os.path.exists(Inputsketchpath):
#                 os.remove(Inputsketchpath)
#             f = open(Inputsketchpath, "a+")
#             f.write(json.dumps(sketchMapdata,indent=4))
#             f.close()
#         except IOError:
#             print("Files written")
#     return HttpResponse(template.render({}, request))






# #@app.route("/mmReceiver", methods=["POST", "GET"])
# def mmGeoJsonReceiver(request):
#     print ("MM receiver")
#     template = loader.get_template('../templates/generalizingmaps.html')
#     global SM_QCN_PATH
#     global MM_QCN_PATH
#     #global USER_PROJ_DIR


#     fileName_full = str(request.POST.get('metricFileName'))
#     MMGeoJsonData = request.POST.get('MMGeoJsonData')
#     MMGeoJsonData = json.loads(MMGeoJsonData)
#     fileName, extension = os.path.splitext(fileName_full)

#     data_format = "geojson"
#     map_type = "metric_map"

#     MetricMap_QCNS = qualify_map.main_loader(fileName, MMGeoJsonData, data_format, map_type)
#     USER_PROJ_DIR = "QualitativeRelationsOutput"
#     try:
#         MM_QCN_PATH = os.path.join(USER_PROJ_DIR,fileName_full+".json")
#         #filepath = './output/'+str("sketchMapID")+'.json'
#         print("final file path. sm.." + fileName_full,MM_QCN_PATH)

#         if os.path.exists(MM_QCN_PATH):
#             os.remove(MM_QCN_PATH)
#         f = open(MM_QCN_PATH, "a+")
#         f.write(json.dumps(MetricMap_QCNS,indent=4))
#         f.close()


#     except IOError:
#         print("Metric map QCNs json path problem ")
#     return HttpResponse(json.dumps(MetricMap_QCNS,indent=4))


# """
#     - load sketch map geojson into qualifier 
# """


# #@app.route("/smReceiver", methods=["POST", "GET"])
# def smGeoJsonReceiver(request):
#     print ("SM receiver")
#     template = loader.get_template('../templates/generalizingmaps.html')
#     global SM_QCN_PATH
#     global USER_PROJ_DIR

#     fileName_full = str(request.POST.get('sketchFileName'))
#     SMGeoJsonData = request.POST.get('SMGeoJsonData')
#     SMGeoJsonData = json.loads(SMGeoJsonData)
#     # print("here svg file and content:",fileName_full, svgContent)
#     fileName, extension = os.path.splitext(fileName_full)
#     #smGeoJson = request.get_json()
#     data_format = "geojson"
#     map_type = "sketch_map"

#     sketchMap_QCNS = qualify_map.main_loader(fileName, SMGeoJsonData, data_format, map_type)
#     USER_PROJ_DIR = "QualitativeRelationsOutput"
#     try:
#         SM_QCN_PATH = os.path.join(USER_PROJ_DIR,fileName_full+".json")
#         #filepath = './output/'+str("sketchMapID")+'.json'
#         print("final file path. sm.." + fileName_full,SM_QCN_PATH)

#         if os.path.exists(SM_QCN_PATH):
#             os.remove(SM_QCN_PATH)
#         f = open(SM_QCN_PATH, "a+")
#         f.write(json.dumps(sketchMap_QCNS,indent=4))
#         f.close()

#     except IOError:
#         print("Sketch map QCNs json path problem ")
#     return HttpResponse(json.dumps(sketchMap_QCNS, indent=4))


# def analyzeInputMap(request):
#         print("analyzeInput")
#         sketchFileName = str(request.POST.get('sketchFileName'))
#         metricFileName = str(request.POST.get('metricFileName'))
#         qa = str(request.POST.get('qa'))
#         sketchmapdata = request.POST.get('sketchmapdata')
#         metricmapdata = request.POST.get('metricmapdata')
#         print("name", sketchFileName, metricFileName,qa)
#         print("METRIC",metricmapdata)
#         print("SKETCH",sketchmapdata)
#         metricMap = json.loads(metricmapdata)
#         sketchMap = json.loads(sketchmapdata)

#         total_mm_landmarks = completeness.get_landmarks_mm(metricMap)
#         toal_mm_streets = completeness.get_streets_mm(metricMap)
#         #total_mm_cityblocks = completeness.get_cityblocks_mm(metricMap)

#         totalSketchedLandmarks = completeness.get_landmarks_sm(sketchMap)
#         totalSketchedStreets = completeness.get_streets_sm(sketchMap)
#         #totalSketchedCityblocks = completeness.get_cityblocks_sm(sketchMap)

#         landmarkCompleteness = completeness.get_landmarkCompleteness(totalSketchedLandmarks, total_mm_landmarks)
#         landmarkCompleteness = round(landmarkCompleteness, 2)
#         # session['landmarkCompleteness'] = landmarkCompleteness

#         streetCompleteness = completeness.get_streetCompleteness(totalSketchedStreets, toal_mm_streets)
#         streetCompleteness = round(streetCompleteness, 2)
#         # session['streetCompleteness'] = streetCompleteness

#         #cityblockCompleteness = completeness.get_cityblockCompleteness(totalSketchedCityblocks, total_mm_cityblocks)
#         #cityblockCompleteness = round(cityblockCompleteness, 2)
#         # session['cityblockCompleteness'] = cityblockCompleteness
#         overAllCompleteness = completeness.get_overall_completness(landmarkCompleteness, streetCompleteness)
#         # session['overAllCompleteness'] = overAllCompleteness
#         print ("Landmarks :",total_mm_landmarks,"Streets:", toal_mm_streets)
#         result = {"sketchMapID": sketchFileName, "total_mm_landmarks": total_mm_landmarks,
#                                "toal_mm_streets": toal_mm_streets,
#                                "totalSketchedLandmarks": totalSketchedLandmarks,
#                                "totalSketchedStreets": totalSketchedStreets,
#                                "landmarkCompleteness": landmarkCompleteness,
#                                "streetCompleteness": streetCompleteness,
#                                "overAllCompleteness": round(overAllCompleteness, 2)
#                              }

#         if qa == "true":
#             print("qualitativeaccuracy")
#             USER_PROJ_DIR = "QualitativeRelationsOutput"

#             MM_QCN_PATH = os.path.join(USER_PROJ_DIR, metricFileName + ".json")
#             SM_QCN_PATH = os.path.join(USER_PROJ_DIR, sketchFileName + ".json")

#             while not os.path.exists(MM_QCN_PATH):
#                 time.sleep(1)

#             if os.path.isfile(MM_QCN_PATH):
#                 with open(MM_QCN_PATH, 'r+') as mmjsonqcn:

#                     try:
#                         metricMapQCNs = json.load(mmjsonqcn)
#                     except IOError:
#                         print("metric_map.json is not loading ")
#             else:
#                 raise ValueError("%s isn't a file!" % MM_QCN_PATH)

#             while not os.path.exists(SM_QCN_PATH):
#                 time.sleep(1)

#             if os.path.isfile(SM_QCN_PATH):
#                 with open(SM_QCN_PATH, 'r+') as smjsonqcn:
#                     try:
#                         sketchMapQCNs = json.load(smjsonqcn)
#                     except IOError:
#                         print("sketch_map.json is not loading ")
#             else:
#                 raise ValueError("%s isn't a file!" % SM_QCN_PATH)





#             """
#                 Measure the correct relations using RCC11
#             """
#             print("insideanalyse",metricMapQCNs,sketchMapQCNs)
#             totalRCC11Relations_mm = qualitativeAnalyser.getTotalRelations_rcc8_mm(metricMapQCNs)
#             totalRCC11Relations = qualitativeAnalyser.getTotalRelations_rcc8_sm(sketchMapQCNs)
#             correctRCC11Relations = qualitativeAnalyser.getCorrrctRelation_rcc8(sketchMapQCNs, metricMapQCNs)
#             wrongMatchedRCC11rels = qualitativeAnalyser.getWrongRelations_rcc8(sketchMapQCNs, metricMapQCNs)
#             missingRCC11rels = totalRCC11Relations_mm - (correctRCC11Relations + wrongMatchedRCC11rels)
#             if correctRCC11Relations != 0 or totalRCC11Relations != 0:
#                 correctnessAccuracy_rcc11 = (correctRCC11Relations / totalRCC11Relations) * 100
#             else:
#                 correctnessAccuracy_rcc11 = 0.00


#             """
#                     Measure the correct relations using Linear Ordering 
#                     alogn the defined route 
#                 """
#             total_lO_rels_mm = qualitativeAnalyser.getTotalLinearOrderingReltions_mm(metricMapQCNs)
#             total_LO_rels_sm = qualitativeAnalyser.getTotalLinearOrderingReltions_sm(sketchMapQCNs)
#             matched_LO_rels = qualitativeAnalyser.getCorrectRelation_linearOrdering(sketchMapQCNs, metricMapQCNs)
#             wrong_matched_LO_rels = qualitativeAnalyser.getWrongRelations_linearOrdering(sketchMapQCNs, metricMapQCNs)
#             missing_LO_rels = total_lO_rels_mm - (matched_LO_rels + wrong_matched_LO_rels)
#             if matched_LO_rels != 0 or total_LO_rels_sm != 0:
#                 correctnessAccuracy_LO = (matched_LO_rels / total_LO_rels_sm) * 100
#             else:
#                 correctnessAccuracy_LO = 0.00

#             """
#                 Measure the correct relations using LeftRight
#                 alogn the defined route 
#             """
#             total_LR_rels_mm = qualitativeAnalyser.getTotalLeftRightRelations_mm(metricMapQCNs)
#             total_LR_rels_sm = qualitativeAnalyser.getTotalLeftRightRelations_sm(sketchMapQCNs)
#             matched_LR_rels = qualitativeAnalyser.getCorrectrelations_leftRight(sketchMapQCNs, metricMapQCNs)
#             wrong_matched_LR_rels = qualitativeAnalyser.getWrongCorrectrelations_leftRight(sketchMapQCNs, metricMapQCNs)
#             missing_LR_rels = total_LR_rels_mm - (matched_LR_rels + wrong_matched_LR_rels)
#             if matched_LR_rels != 0 or total_LR_rels_sm != 0:
#                 correctnessAccuracy_LR = (matched_LR_rels / total_LR_rels_sm) * 100
#             else:
#                 correctnessAccuracy_LR = 0.00

#             """
#                 Measure the correct relations using Topologocal Relations between streets and regions 
    
#             """
#             total_DE9IM_rels_mm = qualitativeAnalyser.getTotalDE9IMRelations_mm(metricMapQCNs)
#             total_DE9IM_rels_sm = qualitativeAnalyser.getTotalDE9IMRelations_sm(sketchMapQCNs)
#             matched_DE9IM_rels = qualitativeAnalyser.getCorrectrelations_DE9IM(sketchMapQCNs, metricMapQCNs)
#             wrong_matched_DE9IM_rels = qualitativeAnalyser.getWrongCorrectrelations_DE9IM(sketchMapQCNs, metricMapQCNs)
#             missing_DE9IM_rels = total_DE9IM_rels_mm - (matched_DE9IM_rels + wrong_matched_DE9IM_rels)
#             if matched_DE9IM_rels != 0 or total_DE9IM_rels_sm != 0:
#                 correctnessAccuracy_DE9IM = (matched_DE9IM_rels / total_DE9IM_rels_sm) * 100
#             else:
#                 correctnessAccuracy_DE9IM = 0.00


#             """
#                 Measure the correct relations using Topologocal Relations between streets  
#             """
#             total_streetTop_rels_mm = qualitativeAnalyser.getTotalStreetTopology_mm(metricMapQCNs)
#             total_streetTop_rels_sm = qualitativeAnalyser.getTotalStreetTopology_sm(sketchMapQCNs)
#             matched_streetTop_rels = qualitativeAnalyser.getCorrectrelations_streetTopology(sketchMapQCNs, metricMapQCNs)
#             wrong_matched_streetTop_rels = qualitativeAnalyser.getWrongCorrectrelations_streetTopology(sketchMapQCNs,
#                                                                                                        metricMapQCNs)
#             missing_streetTop_rels = total_streetTop_rels_mm - (matched_streetTop_rels + wrong_matched_streetTop_rels)
#             if matched_streetTop_rels != 0 or total_streetTop_rels_sm != 0:
#                 correctnessAccuracy_streetTop = (matched_streetTop_rels / total_streetTop_rels_sm) * 100
#             else:
#                 correctnessAccuracy_streetTop = 0.00
#             """
#                  Measure the correct relations using Orientation Relations between streets  
#              """
#             total_opra_rels_mm = qualitativeAnalyser.getTotalOPRA_mm(metricMapQCNs)
#             total_opra_rels_sm = qualitativeAnalyser.getTotalOPRA_sm(sketchMapQCNs)
#             matched_opra_rels = qualitativeAnalyser.getCorrectrelations_opra(sketchMapQCNs, metricMapQCNs)
#             wrong_matched_opra_rels = qualitativeAnalyser.getWrongCorrectrelations_opra(sketchMapQCNs, metricMapQCNs)
#             missing_opra_rels = total_opra_rels_mm - (matched_opra_rels + wrong_matched_opra_rels)
#             if matched_opra_rels != 0 or total_opra_rels_sm != 0:
#                 correctnessAccuracy_opra = (matched_opra_rels / total_opra_rels_sm) * 100
#             else:
#                 correctnessAccuracy_opra = 0.00

#             """
#                    Calculate Recision and Recall 
#              """
#             total_no_correct_rels = correctRCC11Relations + matched_LO_rels + matched_LR_rels + matched_DE9IM_rels + matched_streetTop_rels + matched_opra_rels
#             total_no_rels_sm = totalRCC11Relations + total_LO_rels_sm + total_LR_rels_sm + total_DE9IM_rels_sm + total_streetTop_rels_sm + total_opra_rels_sm
#             total_on_rels_MM = totalRCC11Relations_mm + total_lO_rels_mm + total_LR_rels_mm + total_DE9IM_rels_mm + total_streetTop_rels_mm + total_opra_rels_mm
#             precision = total_no_correct_rels / total_no_rels_sm
#             recall = total_no_correct_rels / total_on_rels_MM

#             #f_score = 2 * ((precision * recall) / (precision + recall))

#             print("precision....:", precision)
#             print("recall....:", recall)
#             #print("F-value....:", f_score)
#             # session.modified = True
#             result = {"sketchMapID": sketchFileName, "total_mm_landmarks": total_mm_landmarks,
#                                "toal_mm_streets": toal_mm_streets,
#                                "totalSketchedLandmarks": totalSketchedLandmarks,
#                                "totalSketchedStreets": totalSketchedStreets,
#                                "landmarkCompleteness": landmarkCompleteness,
#                                "streetCompleteness": streetCompleteness,
#                                "overAllCompleteness": round(overAllCompleteness, 2),
#                                "totalRCC11Relations_mm": totalRCC11Relations_mm, "totalRCC11Relations": totalRCC11Relations,
#                                "correctRCC11Relations": correctRCC11Relations,
#                                "wrongMatchedRCC11rels": wrongMatchedRCC11rels,
#                                "missingRCC11rels": missingRCC11rels,
#                                "correctnessAccuracy_rcc11": round(correctnessAccuracy_rcc11, 2),
#                                "total_lO_rels_mm": total_lO_rels_mm, "total_LO_rels_sm": total_LO_rels_sm,
#                                "matched_LO_rels": matched_LO_rels, "wrong_matched_LO_rels": wrong_matched_LO_rels,
#                                "missing_LO_rels": missing_LO_rels,
#                                "correctnessAccuracy_LO": round(correctnessAccuracy_LO, 2),
#                                "total_LR_rels_mm": total_LR_rels_mm,
#                                "total_LR_rels_sm": total_LR_rels_sm, "matched_LR_rels": matched_LR_rels,
#                                "wrong_matched_LR_rels": wrong_matched_LR_rels, "missing_LR_rels": missing_LR_rels,
#                                "correctnessAccuracy_LR": round(correctnessAccuracy_LR, 2),
#                                "total_DE9IM_rels_mm": total_DE9IM_rels_mm, "total_DE9IM_rels_sm": total_DE9IM_rels_sm,
#                                "matched_DE9IM_rels": matched_DE9IM_rels,
#                                "wrong_matched_DE9IM_rels": wrong_matched_DE9IM_rels,
#                                "missing_DE9IM_rels": missing_DE9IM_rels,
#                                "correctnessAccuracy_DE9IM": round(correctnessAccuracy_DE9IM, 2),
#                                "total_streetTop_rels_mm": total_streetTop_rels_mm,
#                                "total_streetTop_rels_sm": total_streetTop_rels_sm,
#                                "matched_streetTop_rels": matched_streetTop_rels,
#                                "wrong_matched_streetTop_rels": wrong_matched_streetTop_rels,
#                                "missing_streetTop_rels": missing_streetTop_rels,
#                                "correctnessAccuracy_streetTop": round(correctnessAccuracy_streetTop, 2),
#                                "total_opra_rels_mm": total_opra_rels_mm, "total_opra_rels_sm": total_opra_rels_sm,
#                                "matched_opra_rels": matched_opra_rels, "wrong_matched_opra_rels": wrong_matched_opra_rels,
#                                "missing_opra_rels": missing_opra_rels,
#                                "correctnessAccuracy_opra": round(correctnessAccuracy_opra, 2),
#                                "precision": round(precision, 2),
#                                "recall": round(recall, 2),
#                                "f_score": "nil"}
#         return HttpResponse(json.dumps(result), content_type="application/json")