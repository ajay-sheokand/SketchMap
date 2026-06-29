var GenBaseMap;
var ProcSketchMap;
var StreetGroup;
var BuildingGroup;
var extraFeaturesCount = 0;
var extraFeaturesIds = [];
var missingFeaturesCount = 0;
var missingFeaturesIds = [];
var roundaboutids = {};
var junctionmergeids = {};
var qualRelationsBaseMap = [];
var qualRelationsSketchMap = [];
var multiOmiMergeids = {};
var TemporaryAlignmentArray={};
var MMGeoJsonDataFiltered = {};
var SMGeoJsonDataFiltered = {};
var responseArray = {};
var qualresponseArray = {};
var genResultArray = {};
var orderedGenResult = [];
var orderedCompResult = [];
var rows = [];
var cells = [];
var numbOfSM;
var tempallDrawnSketchItems;
var streetCountBeforeGen = 0;
var lmCountBeforeGen = 0;
var hostName
var intervalLookup = {};
var intervalLookupSM = {};









function uploadProject(){
     var fileList = document.getElementById('upload').files;
    for (var i = 0; i < fileList.length; i++) {
        renderGeoJsonFiles(fileList[i]);
    }
}

function renderGeoJsonFiles(file) {
    var fileName = file.name;
    var reader = new FileReader();
    reader.readAsDataURL(file);

    console.log(fileName, baseMaptitle);
    if (fileName.includes('alignment')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
          AlignmentArray = data;
        });
    }}

    if (fileName == baseMaptitle+'.geojson'){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
         var bidArray = Object.values(data.features).map((item) => item.properties.id);
         var RouteSeqOrderArray = Object.values(data.features).map((item) => item.properties.RouteSeqOrder);
         routeOrder = Math.max.apply(Math,RouteSeqOrderArray);
         bid = Math.max.apply(Math, bidArray);


           drawnItems = L.geoJSON(data);
           drawnItems.addTo(layerGroupBasemap);
           allDrawnSketchItems[baseMaptitle] = drawnItems;
            styleLayers();

        });
    }}

    if (fileName != baseMaptitle + '.geojson' && !(fileName.includes('alignment')) ){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
         sketchMaptitle = fileName.replace('.geojson','');
         drawnSketchItems =  L.geoJSON(data,{
          pointToLayer: function (feature, latlng) {
                return L.circleMarker(latlng);
          }
         });


          styleLayers();
          allDrawnSketchItems[sketchMaptitle]=drawnSketchItems;
        });
    }}


}




async function downloadProject() {
download = true;
  try {

    console.log("Starting validation...");

    // ✅ Wait for both validations
    await saveBMHandler();

    console.log("Validations done. Creating ZIP...");

    var zip = new JSZip();

    var alignment = JSON.stringify(AlignmentArray);
    zip.file("alignment.json", alignment);

   allDrawnSketchItems[sketchMaptitle] = drawnSketchItems;
    for (var key in allDrawnSketchItems) {
      zip.file(
        key + ".geojson",
        JSON.stringify(allDrawnSketchItems[key].toGeoJSON())
      );
    }

    const content = await zip.generateAsync({ type: "blob" });

    saveAs(content, "InputFiles.zip");

    console.log("Download finished");

    await computeGMDAFromAllGenBaseMap();

  } catch (err) {

    console.error("Download failed:", err);

  }
}



// Compute GMDA results from already-generated generalized base maps (allGenBaseMap)
async function computeGMDAFromAllGenBaseMap() {
    if (!allGenBaseMap || Object.keys(allGenBaseMap).length === 0) {
        alert('Please run Analyse first before using the GMDA Calculator.');
        return;
    }

    $('#loading-spinner').show()
    const baseUrl = getServiceUrl('gmda');

    for (const sketchmap of Object.keys(allGenBaseMap)) {
        try {
            const genLayer = allGenBaseMap[sketchmap]
            const sketchLayer = allProcessedSketchMaps[sketchmap];
            if (!genLayer || !sketchLayer) continue;

            const response = await $.ajax({
                headers: { "X-CSRFToken": $.cookie("csrftoken")},
                url: `${baseUrl}/gmda/calculateGMDA/`,
                type: 'POST',
                data: {
                    basemapdata: JSON.stringify(genLayer.toGeoJSON()),
                    sketchmapdata: JSON.stringify(sketchLayer.toGeoJSON())
                }
            });
            
            if (!genResultArray[sketchmap]) genResultArray[sketchmap] = {};
            genResultArray[sketchmap].CanOrg = response.CanOrg;
            genResultArray[sketchmap].CanAcc = response.CanAcc;
            genResultArray[sketchmap].ScaBias = response.ScaBias;
            genResultArray[sketchmap].DistAcc = response.DistAcc;
            genResultArray[sketchmap].RotBias = response.RotBias;
            genResultArray[sketchmap].AngAcc = response.AngAcc;
        } catch (e) {
            console.error('GMDA failed for', sketchmap, e);
        }
    }
    $('#loading-spinner').hide();
    $('#summary_result_div').prop("style", 
        "height:500px; overflow:auto; visibility:visible; position:absolute; z-index:10000000; background-color:white");
    populateGMDAResults();
}


async function computeJunctionGMDAFromAllGenBaseMap() {
    if (!allGenBaseMap || Object.keys(allGenBaseMap).length === 0) {
        alert('Please run Analyse first before using the GMDA Calculator.');
        return;
    }

    $('#loading-spinner').show();
    const baseUrl = getServiceUrl('gmda');

    for (const sketchmap of Object.keys(allGenBaseMap)) {
        try {
            const genLayer = allGenBaseMap[sketchmap];
            const sketchLayer = allProcessedSketchMaps[sketchmap];
            if (!genLayer || !sketchLayer) continue;

            const response = await $.ajax({
                headers: {"X-CSRFToken": $.cookie('csrftoken')},
                url: `${baseUrl}/gmda/calculateJunctionGMDA/`,
                type: 'POST',
                data: {
                    basemapdata: JSON.stringify(genLayer.toGeoJSON()),
                    sketchmapdata: JSON.stringify(sketchLayer.toGeoJSON())
                }
            });

            if (!genResultArray[sketchmap]) genResultArray[sketchmap] = {};
            genResultArray[sketchmap].Junc_CanOrg = response.CanOrg;
            genResultArray[sketchmap].Junc_CanAcc = response.CanAcc;
            genResultArray[sketchmap].Junc_ScaBias = response.ScaBias;
            genResultArray[sketchmap].Junc_DistAcc = response.DistAcc;
            genResultArray[sketchmap].Junc_RotBias = response.RotBias;
            genResultArray[sketchmap].Junc_AngAcc = response.AngAcc;
        
        } catch (e) {
            console.error('Junction GMDA failed for', sketchmap, e);
        }
    }

    $('#loading-spinner').hide();
    $('#summary_result_div').prop("style",
        "height:500px; overflow:auto; visibility:visible; position:absolute; z-index:10000000; background-color:white");
    populateGMDAResults();
}


async function bdrLandmarksFromAllGenBaseMap() {
    if (!allGenBaseMap || Object.keys(allGenBaseMap).length === 0) {
        alert('Please run Analyse first before using the BDR Calculator.');
        return;
    }
    
    $('#loading-spinner').show()
    const baseUrl = getServiceUrl('bdr');

    for (const sketchmap of Object.keys(allGenBaseMap)) {
        try {
            const genLayer = allGenBaseMap[sketchmap]
            const sketchLayer = allProcessedSketchMaps[sketchmap];
            if (!genLayer || !sketchLayer) continue;

            const response = await $.ajax({
                headers: { "X-CSRFToken": $.cookie("csrftoken")},
                url: `${baseUrl}/bdr/calculateLandmarksBDR/`,
                type: 'POST',
                data: {
                    basemapdata: JSON.stringify(genLayer.toGeoJSON()),
                    sketchmapdata: JSON.stringify(sketchLayer.toGeoJSON())
                }
            });
            
            if (!genResultArray[sketchmap]) genResultArray[sketchmap] = {};
            genResultArray[sketchmap].Land_r = response.r;
            genResultArray[sketchmap].Land_DI = response.DI;
            genResultArray[sketchmap].Land_phi = response.phi;
            genResultArray[sketchmap].Land_theta = response.theta;
            genResultArray[sketchmap].Land_alpha1 = response.alpha1;
            genResultArray[sketchmap].Land_alpha2 = response.alpha2;
        } catch (e) {
            console.error('BDR failed for', sketchmap, e);
        }
    }
    $('#loading-spinner').hide();
    $('#summary_result_div').prop("style", 
        "height:500px; overflow:auto; visibility:visible; position:absolute; z-index:10000000; background-color:white");
    populateBDRResults();
}


async function bdrJunctionsFromAllGenBaseMap() {
    if (!allGenBaseMap || Object.keys(allGenBaseMap).length === 0) {
        alert('Please run Analyse first before using the BDR Calculator.');
        return;
    }

    $('#loading-spinner').show()
    const baseUrl = getServiceUrl('bdr');

    for (const sketchmap of Object.keys(allGenBaseMap)) {
        try {
            const genLayer = allGenBaseMap[sketchmap]
            const sketchLayer = allProcessedSketchMaps[sketchmap];
            if (!genLayer || !sketchLayer) continue;

            const response = await $.ajax({
                headers: { "X-CSRFToken": $.cookie("csrftoken")},
                url: `${baseUrl}/bdr/calculateJunctionsBDR/`,
                type: 'POST',
                data: {
                    basemapdata: JSON.stringify(genLayer.toGeoJSON()),
                    sketchmapdata: JSON.stringify(sketchLayer.toGeoJSON())
                }
            });
            
            if (!genResultArray[sketchmap]) genResultArray[sketchmap] = {};
            genResultArray[sketchmap].Junc_r = response.r;
            genResultArray[sketchmap].Junc_DI = response.DI;
            genResultArray[sketchmap].Junc_phi = response.phi;
            genResultArray[sketchmap].Junc_theta = response.theta;
            genResultArray[sketchmap].Junc_alpha1 = response.alpha1;
            genResultArray[sketchmap].Junc_alpha2 = response.alpha2;
        } catch (e) {
            console.error('BDR failed for', sketchmap, e);
        }
    }
    $('#loading-spinner').hide();
    $('#summary_result_div').prop("style", 
        "height:500px; overflow:auto; visibility:visible; position:absolute; z-index:10000000; background-color:white");
    populateBDRResults();
}


async function prepareDataForQualifier(index,GenBaseMap){
MMGeoJsonData = GenBaseMap.toGeoJSON();
    var count = 0;
    MMGeoJsonDataFiltered = {};
    SMGeoJsonDataFiltered = {};
    MMGeoJsonDataFiltered.type = "FeatureCollection";
    MMGeoJsonDataFiltered.features = [];

    for (var i in MMGeoJsonData.features){

        var group = MMGeoJsonData.features[i].properties.group;

        if(group != true){
            MMGeoJsonDataFiltered.features[count]=MMGeoJsonData.features[i];
            count = count + 1;
        }
        if(MMGeoJsonData.features[i].properties.genType3 != undefined && MMGeoJsonData.features[i].properties.genType3.includes("Multi-MultiOmissionMerge")){
            MMGeoJsonData.features[i].properties.id = 'G' + MMGeoJsonData.features[i].properties.groupID;
            MMGeoJsonDataFiltered.features[count]=MMGeoJsonData.features[i];
            count = count + 1;

        }
    }


SMGeoJsonData = ProcSketchMap.toGeoJSON();
    var count = 0;
    var streetGroupIdÁrray = [];
    var buildingGroupIdArray = [];


    SMGeoJsonDataFiltered.type = "FeatureCollection";
    SMGeoJsonDataFiltered.features = [];
    for (var i in SMGeoJsonData.features){
        var group = SMGeoJsonData.features[i].properties.group;
        var alignBoolean = SMGeoJsonData.features[i].properties.aligned;
        if(group != true && alignBoolean == true){
            SMGeoJsonDataFiltered.features[count]= SMGeoJsonData.features[i];
            count = count + 1;
        }
        else{
           if(group == true){
           if(SMGeoJsonData.features[i].properties.genType3 != undefined && SMGeoJsonData.features[i].properties.genType3.includes("Multi-MultiOmissionMerge")){
            SMGeoJsonData.features[i].properties.id = 'G' + SMGeoJsonData.features[i].properties.groupID;
            SMGeoJsonDataFiltered.features[count]=SMGeoJsonData.features[i];
            count = count + 1;
            }
            if(SMGeoJsonData.features[i].properties.otype == "Line"){
                streetGroupIdÁrray.push(SMGeoJsonData.features[i].properties.groupID);
            }
            if(SMGeoJsonData.features[i].properties.otype == "Polygon"){
                buildingGroupIdArray.push(SMGeoJsonData.features[i].properties.groupID);
            }
           }
        }

        if(alignBoolean == false){
             extraFeaturesCount = extraFeaturesCount + 1;
             extraFeaturesIds[index].push(SMGeoJsonData.features[i].properties.sid);
        }
    }
    // fileName = sketchFileName.split(".");
    // fileName = fName[0];
    StreetGroup = new Set(streetGroupIdÁrray);
    BuildingGroup = new Set(buildingGroupIdArray);


    return {metricdata: MMGeoJsonDataFiltered, sketchdata : SMGeoJsonDataFiltered}
}

function removeMissingFeatures(featureCollection) {

    return {
        type: "FeatureCollection",
        features: featureCollection.features.filter(feature => {

            const props = feature.properties;

            // remove unaligned
            if (props.aligned === false) return false;

            // remove explicitly missing
            if (props.missing === true) return false;

            // remove grouped raw elements
            if (props.group === true) return false;

            return true;
        })
    };
}


var GenHoverArray = [];

function Genhoverfunction(GenBaseMap){
    drawnSketchItems.eachLayer(function(slayer){
    slayer.on('mouseover', function() {
       let hoveredID;
     hoveredID = slayer.feature.properties.id;
     console.log(sketchMaptitle, intervalLookupSM,hoveredID);
       if (sketchMap.hasLayer(linearOrdering)) {
                const projectionSM = intervalLookupSM[sketchMaptitle]?.[hoveredID];
                if (projectionSM) {
                    projectionLayerSM.clearLayers();
                    projectionLayerSM.addData(projectionSM);
                    projectionLayerSM.addTo(sketchMap);
                }
            }
        if(slayer.feature.properties.group != true){
        GenHoverArray.push(slayer.feature.properties.id);
        GenchangestyleOnHover(GenHoverArray,slayer.feature.properties.group,GenBaseMap);
        }
        else
        {
        GenHoverArray.push(slayer.feature.properties.groupID);
        GenchangestyleOnHover(GenHoverArray,slayer.feature.properties.group,GenBaseMap);
        }
    });
    slayer.on('mouseout', function() {
    GenHoverArray=[];
    GenStyleLayers(GenBaseMap);
    projectionLayerSM.clearLayers();
    });
    });

    GenBaseMap.eachLayer(function (glayer){
    glayer.on('mouseover', function(){
     let hoveredID;
     hoveredID = glayer.feature.properties.id;

       if (baseMap.hasLayer(linearOrdering)) {
                const projection = intervalLookup[sketchMaptitle]?.[hoveredID];
                if (projection) {
                    projectionLayer.clearLayers();
                    projectionLayer.addData(projection);
                    projectionLayer.addTo(baseMap);
                }
            }
    });
    glayer.on('mouseout', function() {
            projectionLayer.clearLayers();

        });


    });









    }

function GenchangestyleOnHover(Array,BooleanGroup,GenBaseMap){
    Array=Array.flat();
    if (BooleanGroup != true){
     GenBaseMap.eachLayer(function(glayer){
     for (i in Array){
        if (glayer.feature.properties.id==Array[i]){
                glayer.setStyle({
            color: 'blue'   //or whatever style you wish to use;
        });
        }
    }

     });
     drawnSketchItems.eachLayer(function(slayer){
     for (i in Array){
        if (slayer.feature.properties.sid==Array[i]){
            slayer.setStyle({
            color: 'blue'   //or whatever style you wish to use;
        });
        }
    }
   });
   }
   else {

     GenBaseMap.eachLayer(function(glayer){
     for (i in Array){
        if (glayer.feature.properties.groupID==Array[i]){
                glayer.setStyle({
            color: 'blue'   //or whatever style you wish to use;
        });
        }
    }

     });
     drawnSketchItems.eachLayer(function(slayer){
     for (i in Array){
        if (slayer.feature.properties.groupID==Array[i]){
            slayer.setStyle({
            color: 'blue'   //or whatever style you wish to use;
        });
        }
    }
   });


   }

    }







async function analyseMultiMap (comp,acc) {
if (BooleanEditSketchMode){
         saveSketchMap();
}
    responseArray = {};
    genResultArray = {};
    qualresponseArray = {};



    //Clear the Result table and add number of rows and columns in the table as per the number of uploaded sketch maps
    $("#OrderingofMaps tbody tr").remove();
    drawnItems = allDrawnSketchItems[baseMaptitle] ;
    numbOfSM = document.getElementById("SMholder").childElementCount;
    var resultTable = document.getElementById("resultRows");
    for (var i = 0; i<numbOfSM-3;i++){
        rows[i] = resultTable.insertRow(i);
        cells[i] = new Array(4)
        for (var j=0;j<4;j++){
            cells[i][j]=rows[i].insertCell(j);
        }
   }

    //Empty the variable tempallDrawnSketchItems
    tempallDrawnSketchItems = JSON.parse(JSON.stringify({}));


   //Load all the sketchmaps into temporary variable
    for ( var i in Object.keys(allDrawnSketchItems)){
        if (Object.keys(allDrawnSketchItems)[i] != baseMaptitle){
            tempallDrawnSketchItems[Object.keys(allDrawnSketchItems)[i]] = allDrawnSketchItems[Object.keys(allDrawnSketchItems)[i]]
        }
    }


    for (var i in Object.keys(tempallDrawnSketchItems)){
        var index = i;
        missingFeaturesIds[index]=[];
        extraFeaturesIds[index]=[];
        streetCountBeforeGen = 0;
        lmCountBeforeGen = 0;
        currentsketchMap = Object.keys(tempallDrawnSketchItems)[i];

            GenBaseMap = null;
        ProcSketchMap = null;
        MMGeoJsonDataFiltered = {};
        SMGeoJsonDataFiltered = {};
        delete responseArray[currentsketchMap];
        delete qualresponseArray[currentsketchMap];
        delete genResultArray[currentsketchMap];
        qualRelationsBaseMap[index] = null;
        qualRelationsSketchMap[index] = null;
        drawnItems.eachLayer(function(blayer){
            if (blayer.feature.properties.group){
                        delete blayer.feature.properties.group;
                        delete blayer.feature.properties.groupID;
            }
                if (blayer.feature.properties.missing){
                delete blayer.feature.properties.missing;
            }
            $.each(AlignmentArray[currentsketchMap], function(j, item) {
                if(AlignmentArray[currentsketchMap][j].genType == "Abstraction to show existence"){
                    if((AlignmentArray[currentsketchMap][j].BaseAlign[0]).includes(blayer.feature.properties.id)){
                         blayer.feature.properties.group = true ;
                         blayer.feature.properties.groupID = j;
                    }
                }
            });
        });

        restoreBaseAlignment(AlignmentArray[currentsketchMap]);
        drawnSketchItems = allDrawnSketchItems[currentsketchMap];

        missingFeaturesCount = 0;
        extraFeaturesCount = 0;
        drawnItems.eachLayer(function(blayer){
            if (blayer.feature.properties.otype == "Line"){
                streetCountBeforeGen = streetCountBeforeGen + 1;
            }

            if (blayer.feature.properties.otype == "Polygon"){
                lmCountBeforeGen = lmCountBeforeGen + 1;
            }

            if (!blayer.feature.properties.aligned ){
                blayer.feature.properties.missing = true;
                missingFeaturesCount = missingFeaturesCount + 1;
                missingFeaturesIds[index].push(blayer.feature.properties.id);
            }
            else{
                delete blayer.feature.properties.missing;
            }
        });






        drawnSketchItems.eachLayer(function(slayer){
                if (slayer.feature.properties.group){
                        delete slayer.feature.properties.group;
                        delete slayer.feature.properties.groupID;
                    }
                $.each(AlignmentArray[currentsketchMap], function(j, item) {
                    if(AlignmentArray[currentsketchMap][j].genType == "Abstraction to show existence"){
                        if((AlignmentArray[currentsketchMap][j].SketchAlign[0]).includes(slayer.feature.properties.sid)){
                             slayer.feature.properties.group = true ;
                             slayer.feature.properties.groupID = j;
                        }
                }
                });
            });




// Construct the base URL dynamically
baseUrl = getServiceUrl('generalizations');

 $('#loading-spinner').show();

try {
    const resp = await $.ajax({
      headers: { "X-CSRFToken": $.cookie("csrftoken") },
      url:  `${baseUrl}/generalizations/requestFME/`,
      type: 'POST',
      data: {
        csrfmiddlewaretoken: $.cookie("csrftoken"),
        basedata: JSON.stringify(drawnItems.toGeoJSON()),
        sketchdata: JSON.stringify(drawnSketchItems.toGeoJSON()),
        aligndata: JSON.stringify(AlignmentArray[currentsketchMap]),
        sketchmapName: JSON.stringify(currentsketchMap)
      }
    });

    const fixedIndex = index;

    $('#summary_result_div').prop("style", "height:500px; overflow:auto; visibility:visible; position:absolute; z-index:10000000; background-color:white");

    const GenBasemapjson = await generalizedMapExtract(
      fixedIndex,
      currentsketchMap,
      { [currentsketchMap]: AlignmentArray[currentsketchMap] },
      resp
    );

    const processeddata = await prepareDataForQualifier(fixedIndex, GenBasemapjson.generalizedbasemap);
    console.log(processeddata, "check here")

    let responseData = {};

    const completenessPromise = comp
      ? analyzeCompleteness(fixedIndex, currentsketchMap, processeddata.sketchdata, processeddata.metricdata)
      : Promise.resolve({});



    const qualitativePromise = acc
      ? analyzeQualitative(fixedIndex, currentsketchMap, removeMissingFeatures(processeddata.sketchdata), removeMissingFeatures(processeddata.metricdata))
      : Promise.resolve({});

    const [completenessResponse, qualitativeResponse] = await Promise.all([
      completenessPromise,
      qualitativePromise
    ]);

    Object.assign(responseData, completenessResponse, qualitativeResponse);

    TemporaryAlignmentArray = JSON.parse(JSON.stringify(AlignmentArray));
    setResults_in_output_div(fixedIndex, responseData);

  } catch (error) {
    console.error("Error during analysis:", error);
    delete responseArray[currentsketchMap];
    delete qualresponseArray[currentsketchMap];
    delete genResultArray[currentsketchMap];
    if (cells[index]) {
        cells[index][0].innerHTML = currentsketchMap;
        cells[index][1].innerHTML = "ERROR";
        cells[index][2].innerHTML = "ERROR";
        cells[index][3].innerHTML = "ERROR";
        }
  } finally {
    $('#loading-spinner').hide();
  }
}

}

function getServiceUrl(serviceName) {
    const hostName = window.location.hostname;
    const protocol = window.location.protocol;

    // If local dev, use direct ports from Docker
    if (hostName === 'localhost' || hostName === '127.0.0.1') {
        const portMap = {
            generalizations: 8001,
            completeness: 8002,
            qualitativerelations: 8003,
            validation:8004,
            gmda:8005,
            bdr:8006
        };
        return `${protocol}//${hostName}:${portMap[serviceName]}`;
    }

    // On cloud: use Apache reverse proxy paths
    return `${protocol}//${hostName}`;
}

function generalizedMapExtract(index,currentsketchMap,alignmentArraySingleMap,resp){
 var amalgamation = 0;
 var collapse = 0 ;
 var omissionmerge = 0;
 var junctionmergecount = 0;
 var roundaboutcount = 0;
 var multibuildingscountMissing = 0;

 multiOmiMergeids[currentsketchMap] = [];
 roundaboutids[currentsketchMap] = [];
 junctionmergeids[currentsketchMap] = [];



                var randomnum = 110111;
                var wholeMapProc = JSON.parse(resp);
                var sketchMapProc=[];
                var baseMapProc=[];
                var multiOmiMergeCount = 0;
                var abstExiStreetscount = 0
                var abstExiBuildingsscount = 0;


  for (var i in Object.values(alignmentArraySingleMap)[0]){

  if (Object.values(alignmentArraySingleMap)[0][i].genType == "Amalgamation"){
   amalgamation = amalgamation + 1 ;
  }
  if (Object.values(alignmentArraySingleMap)[0][i].genType == "OmissionMerge"){
   omissionmerge = omissionmerge + 1 ;
  }
  if (Object.values(alignmentArraySingleMap)[0][i].genType == "Collapse"){
   collapse = collapse + 1 ;
  }
  }
                 $.each(wholeMapProc.features, function(i, item) {

                   if(item.properties.Missingmultibuilding != null ) {
                    multibuildingscountMissing = item.properties.Missingmultibuilding;
                 }


                 if(item.properties.RoundAboutCount != null ) {
                    roundaboutcount = item.properties.RoundAboutCount;
                 }

                 if(item.properties.JunctionMergeCount != null ) {
                    junctionmergecount = item.properties.JunctionMergeCount;
                 }

                 if(item.properties.genType2 != null && item.properties.genType2.includes("JunctionMerge")){
                    junctionmergeids[currentsketchMap].push(item.properties.id);

                 }

                 if (item.properties.genType3 != null && item.properties.genType3.includes("Multi-MultiOmissionMerge") && item.properties.mapType != "Sketch"){
                    multiOmiMergeCount = multiOmiMergeCount + 1 ;
                    multiOmiMergeids[currentsketchMap].push(item.properties.id)
                 }
                 if(item.properties.genType1 != null && item.properties.genType1.includes("RoundAbout")){
                    roundaboutids[currentsketchMap].push(item.properties.id);
                 }

                  if (item.properties.genType != null && item.properties.genType.includes("Abstraction to show existence streets")){
                    abstExiStreetscount = abstExiStreetscount + 1 ;
                 }

                 if (item.properties.genType != null && item.properties.genType.includes("Abstraction to show existence buildings")){
                    abstExiBuildingsscount = abstExiBuildingsscount + 1 ;
                 }

                 if(item.properties.mapType == "Sketch"){
                    if (item.properties.groupID) {
                        const groupidNumeric = String(item.properties.groupID).replace(/\D/g, ''); // Extract numeric part
                        item.properties.id = groupidNumeric ? 'G' + groupidNumeric : ''; // Prefix 'g' to the numeric value
                    } else {
                        if (typeof item.properties.id != 'undefined')
                        item.properties.id = item.properties.id.toString();
                    }
                    if(item.properties.otype == "CircleMarker"){
                        item.properties.feat_type="Landmark";
                        }
                    console.log(item, "check sketchfeature")
                    sketchMapProc.push(item);
                 }
                 else{
                  if (item.properties.missing){
                  item.properties.id = randomnum;
                  }
                   if (item.properties.SketchAlign){
                    const sketchAlignValue = Object.values(item.properties.SketchAlign);

                    // Check for 'groupid' property first
                    if (item.properties.groupID) {
                        const groupidNumeric = String(item.properties.groupID).replace(/\D/g, ''); // Extract numeric part
                        item.properties.id = groupidNumeric ? 'G' + groupidNumeric : ''; // Prefix 'g' to the numeric value
                    } else {
                        // Fallback to use the first numeric value in SketchAlign
                        const numericPart = sketchAlignValue.toString().replace(/\D/g, '');
                        item.properties.id = numericPart ? String(numericPart) : '';
                    }
                //    if((JSON.parse(item.properties.SketchAlign)).toString() === item.properties.SketchAlign){
                //         item.properties.id=item.properties.SketchAlign
                //    }
                //    else{
                //         item.properties.id = Object.values(JSON.parse(item.properties.SketchAlign))[0][0].replace(/\D/g,'');
                //     }
                 }
                  baseMapProc.push(item);
                  randomnum = randomnum + 1;
                 }
                 });

               ProcSketchMap = L.geoJSON(sketchMapProc);
                allProcessedSketchMaps[currentsketchMap] = ProcSketchMap;
                drawnSketchItems = ProcSketchMap;          // ← this line is required

                if (GenBaseMap != null) {
                    layerGroupBasemapGen.removeLayer(GenBaseMap);
                }

                GenBaseMap = L.geoJSON(baseMapProc);
                allGenBaseMap[currentsketchMap] = GenBaseMap;
                GenStyleLayers(GenBaseMap);
                Genhoverfunction(GenBaseMap);

                if (currentsketchMap == sketchMaptitle) {
                    allGenBaseMap[sketchMaptitle].addTo(layerGroupBasemapGen);
                }

            genResultArray[currentsketchMap] = {};
            genResultArray[currentsketchMap].om = omissionmerge;
            genResultArray[currentsketchMap].abstExiStreets = abstExiStreetscount;
            genResultArray[currentsketchMap].amalgamation = amalgamation;
            genResultArray[currentsketchMap].junctionmerge = junctionmergecount;
            genResultArray[currentsketchMap].roundabout = roundaboutcount;
            genResultArray[currentsketchMap].collapse = collapse;
            genResultArray[currentsketchMap].om_multi = multiOmiMergeCount;
            genResultArray[currentsketchMap].absExiBuildings = abstExiBuildingsscount;
            genResultArray[currentsketchMap].totalGenStreets = parseInt(omissionmerge) + parseInt(multiOmiMergeCount)+ + parseInt(junctionmergecount) + parseInt(roundaboutcount) + parseInt(abstExiStreetscount);
            genResultArray[currentsketchMap].totalGenBuildings = parseInt(amalgamation) + parseInt(collapse) + parseInt(abstExiBuildingsscount);
            genResultArray[currentsketchMap].overallGen =  genResultArray[currentsketchMap].totalGenStreets +  genResultArray[currentsketchMap].totalGenBuildings ;
             return {generalizedbasemap : GenBaseMap, generalizationresult : genResultArray}

 }




async function analyzeCompleteness(index, currentsketchMap, processedSketch, processedMetric) {

    return new Promise((resolve, reject) => {
        // Use service URL builder function to build the base URL
        baseUrl = getServiceUrl('completeness');
        $.ajax({
            headers: { "X-CSRFToken": $.cookie("csrftoken") },
            url: `${baseUrl}/completeness/analyzeCompleteness/`,
            type: 'POST',
            data: {
                sketchFileName: currentsketchMap,
                metricFileName: "basemapFor" + currentsketchMap,
                sketchdata: JSON.stringify(processedSketch),
                metricdata: JSON.stringify(processedMetric)
            },
            success: function(response) {
                responseArray[currentsketchMap] = response;
                resolve(response); // ✅ Resolving the response
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error in completeness analysis:', errorThrown);
                reject(errorThrown); // ✅ Rejecting in case of error
            }
        });
    });
}

const projectionLayer = L.geoJSON(null, {
  style: {
    color: "#0ced10",
    weight: 8
  }
});

const projectionLayerSM = L.geoJSON(null, {
  style: {
    color: "#0ced10",
    weight: 8
  }
});
async function analyzeQualitative(index, currentsketchMap, processedSketch, processedMetric) {
    return new Promise((resolve, reject) => {
        // Use service URL builder function to build the base URL
        baseUrl = getServiceUrl('qualitativerelations');
        $.ajax({
            headers: { "X-CSRFToken": $.cookie("csrftoken") },
            url:  `${baseUrl}/accuracy/analyzeQualitative/`,
            type: 'POST',
            data: {
                sketchFileName: currentsketchMap,
                metricFileName: "basemapFor" + currentsketchMap,
                sketchdata: JSON.stringify(processedSketch),
                metricdata: JSON.stringify(processedMetric)
            },
            success: function(response) {
                const linearOrderingEntry = response.mmqcn.constraint_collection.find(c => c.relation_set === "linearOrdering");
                const intervalFeatures = linearOrderingEntry?.modifiers?.interval_features || [];

                if (!intervalLookup[currentsketchMap]) {
                        intervalLookup[currentsketchMap] = {};
                }
                if (!intervalLookupSM[currentsketchMap]) {
                        intervalLookupSM[currentsketchMap] = {};
                }

                intervalFeatures.forEach(f => {
                    intervalLookup[currentsketchMap][f.properties.id] = f;
                });

                const linearOrderingEntrySM = response.smqcn.constraint_collection.find(c => c.relation_set === "linearOrdering");
                const intervalFeaturesSM = linearOrderingEntrySM?.modifiers?.interval_features || [];
                intervalFeaturesSM.forEach(f => {
                    intervalLookupSM[currentsketchMap][f.properties.id] = f;
                });
                qualresponseArray[currentsketchMap] = response.qualitative_results;
                qualRelationsBaseMap[index] = response.mmqcn;
                qualRelationsSketchMap[index] = response.smqcn;
                resolve(response.qualitative_results);
                $('#loading-spinner').show();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error in qualitative analysis:', errorThrown);
                reject(errorThrown);
            },
        });
    });
}



function GenStyleLayers(generalizedmap){


if (BooleanMissingFeature){
generalizedmap.eachLayer(function(glayer){
            if (!glayer.feature.properties.selected && glayer.feature.properties.missing == true && !glayer.feature.properties.isRoute){
                glayer.setStyle({opacity:0,weight: 0,color: "#e8913a",dashArray: [5, 5]});
                if(glayer.getTooltip()){
                glayer.getTooltip().getElement().style.opacity = '0';
                }
            }
            if (!glayer.feature.properties.selected && !glayer.feature.properties.missing && !glayer.feature.properties.isRoute){
                glayer.setStyle({opacity:0.7,weight: 5,color: "#e8913a",dashArray: null});
            }
            if (!glayer.feature.properties.selected && glayer.feature.properties.missing == true && glayer.feature.properties.isRoute=="Yes"){
                glayer.setStyle({opacity:0,weight: 0,color: "red",dashArray: [5, 5]});
               if(glayer.getTooltip()){
                glayer.getTooltip().getElement().style.opacity = '0';
                }
            }
            if(!glayer.feature.properties.selected && !glayer.feature.properties.missing && glayer.feature.properties.isRoute=="Yes"){
                glayer.setStyle({opacity:0.7,weight: 5,color: "red",dashArray: null,});
            }
     });

    }
    else {

    generalizedmap.eachLayer(function(glayer){
            if (!glayer.feature.properties.selected && glayer.feature.properties.missing == true && !glayer.feature.properties.isRoute){
                glayer.setStyle({opacity:0.7,weight: 5,color: "#e8913a",dashArray: [5, 5]});
                if(glayer.getTooltip()){
                glayer.getTooltip().getElement().style.opacity = '1';
                }
            }
            if (!glayer.feature.properties.selected && !glayer.feature.properties.missing && !glayer.feature.properties.isRoute){
                glayer.setStyle({opacity:0.7,weight: 5,color: "#e8913a",dashArray: null});
            }
            if (!glayer.feature.properties.selected && glayer.feature.properties.missing == true && glayer.feature.properties.isRoute=="Yes"){
                glayer.setStyle({opacity:0.7,weight: 5,color: "red",dashArray: [5, 5]});
                if(glayer.getTooltip()){
                glayer.getTooltip().getElement().style.opacity = '1';
                }
            }
            if(!glayer.feature.properties.selected && !glayer.feature.properties.missing && glayer.feature.properties.isRoute=="Yes"){
                glayer.setStyle({opacity:0.7,weight: 5,color: "red",dashArray: null,});
            }
     });




    }
    }




function setResults_in_output_div(index,resp){
       cells[index][0].innerHTML = resp.sketchMapID;
       cells[index][2].innerHTML = genResultArray[resp.sketchMapID].overallGen;
       cells[index][1].innerHTML = ((resp.totalSketchedStreets+genResultArray[resp.sketchMapID].abstExiStreets)/(resp.toal_mm_streets +genResultArray[resp.sketchMapID].abstExiStreets)*100).toFixed(2) + "   " + ((resp.totalSketchedLandmarks+ genResultArray[resp.sketchMapID].absExiBuildings)/(resp.total_mm_landmarks+ genResultArray[resp.sketchMapID].absExiBuildings)*100).toFixed(2);
       cells[index][3].innerHTML = resp.precision + "    " + resp.recall;

}

function findCommonElements3(arr1, arr2) {
    return arr1.some(item => arr2.includes(item))
}


$( "#exportAsCSV" ).on( "click", function() {
var GeneralizationCSV = [];
var QualRelationsBaseMapCSV = [];
var QualRelationsSketchMapCSV = [];
var CompletenessSummaryCSV = [];
var GeneralizationSummaryCSV = [];
var QASummaryCSV = [];
var OverallSummaryCsv = [];


//COMPLETENESS


if (Object.keys(responseArray)!=0){
for (var i in Object.keys(responseArray)){
        var sketchmap = Object.keys(responseArray)[i];
        var OverallCompleteness = (parseInt(responseArray[sketchmap].totalSketchedStreets) + parseInt(responseArray[sketchmap].totalSketchedLandmarks))/(parseInt(responseArray[sketchmap].toal_mm_streets) + parseInt(responseArray[sketchmap].total_mm_landmarks))
        CompletenessSummaryCSV.push(sketchmap);
        CompletenessSummaryCSV.push("Completeness");
        CompletenessSummaryCSV.push("Spatial Features , Features in Original Metric map, Features in Generalized Metric map (Excluding Groups) , Drawn Features in Sketch map (Excluding Group), Completeness");
        CompletenessSummaryCSV.push("Street segments(excluding group alignments)" + "," + streetCountBeforeGen + "," + responseArray[sketchmap].toal_mm_streets + "," + responseArray[sketchmap].totalSketchedStreets + ',' + responseArray[sketchmap].streetCompleteness );
        CompletenessSummaryCSV.push("Landmarks(excluding group alignments)" + "," + lmCountBeforeGen + "," + responseArray[sketchmap].total_mm_landmarks + "," + responseArray[sketchmap].totalSketchedLandmarks + ',' + responseArray[sketchmap].landmarkCompleteness);
        CompletenessSummaryCSV.push("No. of group alignments in Streets" + "," + genResultArray[sketchmap].abstExiStreets);
        CompletenessSummaryCSV.push("No. of groups alignments in Landmarks" + "," + genResultArray[sketchmap].absExiBuildings);
        CompletenessSummaryCSV.push("Street segments(including group alignments)" + "," + streetCountBeforeGen + "," + (responseArray[sketchmap].toal_mm_streets +genResultArray[sketchmap].abstExiStreets)  + "," + (responseArray[sketchmap].totalSketchedStreets+genResultArray[sketchmap].abstExiStreets) + ',' + (responseArray[sketchmap].totalSketchedStreets+genResultArray[sketchmap].abstExiStreets)/(responseArray[sketchmap].toal_mm_streets +genResultArray[sketchmap].abstExiStreets)*100);
        CompletenessSummaryCSV.push("Landmarks(including group alignments)" + "," + lmCountBeforeGen + "," + (responseArray[sketchmap].total_mm_landmarks+ genResultArray[sketchmap].absExiBuildings) + "," + (responseArray[sketchmap].totalSketchedLandmarks+ genResultArray[sketchmap].absExiBuildings) + ',' + (responseArray[sketchmap].totalSketchedLandmarks+ genResultArray[sketchmap].absExiBuildings)/(responseArray[sketchmap].total_mm_landmarks+ genResultArray[sketchmap].absExiBuildings)*100);
        CompletenessSummaryCSV.push("Missing Features,\"" + missingFeaturesIds[i].join(",") + "\"");
        CompletenessSummaryCSV.push("ExtraFeatures" + "," + extraFeaturesIds[i]);
        var streetcomp = (responseArray[sketchmap].totalSketchedStreets+genResultArray[sketchmap].abstExiStreets)/(responseArray[sketchmap].toal_mm_streets +genResultArray[sketchmap].abstExiStreets)*100;
        var buildingcomp = (responseArray[sketchmap].totalSketchedLandmarks+ genResultArray[sketchmap].absExiBuildings)/(responseArray[sketchmap].total_mm_landmarks+ genResultArray[sketchmap].absExiBuildings)*100
        CompletenessSummaryCSV.push("AverageCompleteness" + "," + (streetcomp + buildingcomp)/2);
        var totalFeaturecountinBasemap = (responseArray[sketchmap].toal_mm_streets +genResultArray[sketchmap].abstExiStreets)+(responseArray[sketchmap].total_mm_landmarks+ genResultArray[sketchmap].absExiBuildings)
        var totalFeaturecountinSketchmap = (responseArray[sketchmap].totalSketchedStreets+genResultArray[sketchmap].abstExiStreets) + (responseArray[sketchmap].totalSketchedLandmarks+ genResultArray[sketchmap].absExiBuildings)
        CompletenessSummaryCSV.push("OverallCompleteness" + "," + totalFeaturecountinSketchmap/totalFeaturecountinBasemap*100 );
        CompletenessSummaryCSV.push("   ");
}
}

//GENERALIZATION
/*for (var i in Object.keys(genResultArray)){
        var sketchmap = Object.keys(genResultArray)[i];
        GeneralizationSummaryCSV.push(sketchmap);
        GeneralizationSummaryCSV.push("Generalization");
        GeneralizationSummaryCSV.push("Generalization in Streets , Count");
        GeneralizationSummaryCSV.push("Omission Merge" + "," + genResultArray[sketchmap].om);
        GeneralizationSummaryCSV.push("Omission Merge (many-many)" + ',' + genResultArray[sketchmap].om_multi);
        GeneralizationSummaryCSV.push("Abstraction to show existence" + ',' + genResultArray[sketchmap].abstExiStreets);
        GeneralizationSummaryCSV.push("Junction Merge" + "," + genResultArray[sketchmap].junctionmerge);
        GeneralizationSummaryCSV.push("Roundabout Collapse" + "," + genResultArray[sketchmap].roundabout);
        GeneralizationSummaryCSV.push("Total" + ',' + genResultArray[sketchmap].totalGenStreets );
        GeneralizationSummaryCSV.push("   ");
        GeneralizationSummaryCSV.push("Generalization in Buildings , Count");
        GeneralizationSummaryCSV.push("Amalgamation" + ',' + genResultArray[sketchmap].amalgamation);
        GeneralizationSummaryCSV.push("Collapse" + ',' + genResultArray[sketchmap].collapse);
        GeneralizationSummaryCSV.push("Abstraction to show existence" + ',' + genResultArray[sketchmap].absExiBuildings);
        GeneralizationSummaryCSV.push("Total" + ',' + genResultArray[sketchmap].totalGenBuildings);
        GeneralizationSummaryCSV.push("   ");
        GeneralizationSummaryCSV.push("Overall Generalization" + ',' + genResultArray[sketchmap].overallGen);
        GeneralizationSummaryCSV.push("    ");
        GeneralizationSummaryCSV.push("   ");
}*/


//QUALITATIVE ACCURACY

if (Object.keys(qualresponseArray)!=0){
     for (var i = 0; i < numbOfSM - 3; i++){
    QualRelationsBaseMapCSV[i]   = ["Object 1 , Object 2, Relations"];
    QualRelationsSketchMapCSV[i] = ["Object 1, Object 2, Relations"];

    const sketchmap = Object.keys(qualresponseArray)[i];
    const lookups   = buildGenIdLookups(TemporaryAlignmentArray[sketchmap]);

    if (qualRelationsBaseMap[i]){
        for (var x in qualRelationsBaseMap[i].constraint_collection){
            QualRelationsBaseMapCSV[i].push(" " + ',' + qualRelationsBaseMap[i].constraint_collection[x].relation_set + ',' + " ");
            for (var y in qualRelationsBaseMap[i].constraint_collection[x].constraints){
                const c = qualRelationsBaseMap[i].constraint_collection[x].constraints[y];
                QualRelationsBaseMapCSV[i].push(
                    resolveGenId(c["obj 1"], lookups) + ',' +
                    resolveGenId(c["obj 2"], lookups) + ',' +
                    c["relation"]
                );
            }
        }

        for (var x in qualRelationsSketchMap[i].constraint_collection){
            QualRelationsSketchMapCSV[i].push(" " + ',' + qualRelationsSketchMap[i].constraint_collection[x].relation_set + ',' + " ");
            for (var y in qualRelationsSketchMap[i].constraint_collection[x].constraints){
                const c = qualRelationsSketchMap[i].constraint_collection[x].constraints[y];
                QualRelationsSketchMapCSV[i].push(
                    resolveGenId(c["obj 1"], lookups) + ',' +
                    resolveGenId(c["obj 2"], lookups) + ',' +
                    c["relation"]
                );
            }
        }
    }
}


for (var i in Object.keys(qualresponseArray)){
        var sketchmap = Object.keys(qualresponseArray)[i];
        console.log(sketchmap);
        QASummaryCSV.push(sketchmap);
        QASummaryCSV.push("Correctness");
        QASummaryCSV.push("Qualitative Spatial Aspects , Relations in Base map , Relations in Sketch Map , Correct Relations, Wrong Relations, Missing Relations, Accuracy Rate (%)");
        QASummaryCSV.push("Topological Relations between Landmarks and Regions" + "," + qualresponseArray[sketchmap].totalRCC11Relations_mm + "," + qualresponseArray[sketchmap].totalRCC11Relations + ',' + qualresponseArray[sketchmap].correctRCC11Relations + ',' + qualresponseArray[sketchmap].wrongMatchedRCC11rels + ',' + qualresponseArray[sketchmap].missingRCC11rels + ',' + qualresponseArray[sketchmap].correctnessAccuracy_rcc11 );
        QASummaryCSV.push("Linear Ordering of Landmarks along Street Segments" + "," + qualresponseArray[sketchmap].total_lO_rels_mm + "," + qualresponseArray[sketchmap].total_LO_rels_sm + ',' + qualresponseArray[sketchmap].matched_LO_rels + ',' + qualresponseArray[sketchmap].wrong_matched_LO_rels + ',' + qualresponseArray[sketchmap].missing_LO_rels + ',' + qualresponseArray[sketchmap].correctnessAccuracy_LO);
        QASummaryCSV.push("Left-Right Relations of Landmarks wrt. Street-segments" + "," + qualresponseArray[sketchmap].total_LR_rels_mm + "," + qualresponseArray[sketchmap].total_LR_rels_sm + ',' + qualresponseArray[sketchmap].matched_LR_rels + ',' + qualresponseArray[sketchmap].wrong_matched_LR_rels + ',' + qualresponseArray[sketchmap].missing_LR_rels + ',' + qualresponseArray[sketchmap].correctnessAccuracy_LR);
        QASummaryCSV.push("Topological Relations between street-segments and regions/landmarks" + "," + qualresponseArray[sketchmap].total_DE9IM_rels_mm + ',' + qualresponseArray[sketchmap].total_DE9IM_rels_sm + ',' + qualresponseArray[sketchmap].matched_DE9IM_rels + ',' + qualresponseArray[sketchmap].wrong_matched_DE9IM_rels + ',' + qualresponseArray[sketchmap].missing_DE9IM_rels + ',' + qualresponseArray[sketchmap].correctnessAccuracy_DE9IM );
        QASummaryCSV.push("Connectivity of street segments" + "," + qualresponseArray[sketchmap].total_streetTop_rels_mm + "," + qualresponseArray[sketchmap].total_streetTop_rels_sm + "," + qualresponseArray[sketchmap].matched_streetTop_rels + "," + qualresponseArray[sketchmap].wrong_matched_streetTop_rels + "," + qualresponseArray[sketchmap].missing_streetTop_rels + "," + qualresponseArray[sketchmap].correctnessAccuracy_streetTop);
        QASummaryCSV.push("Relative Orientation of Connected Street-segments" + "," + qualresponseArray[sketchmap].total_opra_rels_mm + "," + qualresponseArray[sketchmap].total_opra_rels_sm+ "," + qualresponseArray[sketchmap].matched_opra_rels + "," + qualresponseArray[sketchmap].wrong_matched_opra_rels + "," + qualresponseArray[sketchmap].missing_opra_rels + "," + qualresponseArray[sketchmap].correctnessAccuracy_opra);
        QASummaryCSV.push("    ");
}

}





for (var i in Object.keys(tempallDrawnSketchItems)){

    // ... (missing/extra lines unchanged)
}


GeneralizationCSV.push("Sketch Map , BaseId , SketchId , GenId , Generalization Type");

 for (var i in Object.keys(tempallDrawnSketchItems)){

  var sketchmap = Object.keys(tempallDrawnSketchItems)[i];
    const lookups = buildGenIdLookups(TemporaryAlignmentArray[sketchmap]);

    if (TemporaryAlignmentArray[sketchmap]){
        // ... (your existing genType adjustments, unchanged)

        Object.keys(TemporaryAlignmentArray[sketchmap]).forEach(function(key) {
            if (key === "checkAlignnum") return;
            // ... (your existing genType mutation block, unchanged)

            const entry  = TemporaryAlignmentArray[sketchmap][key];
            const baseIds = entry.BaseAlign[0] || [];
            const sorted  = Array.from(new Set(baseIds.map(Number))).sort((a,b) => a - b);
            const genId   = 'g.' + sorted.join('.');

            GeneralizationCSV.push(
                (sketchmap ?? "") + ',' +
                (baseIds?.toString()?.replaceAll(",", " ") ?? "") + ',' +
                (entry?.SketchAlign?.[0]?.toString()?.replaceAll(",", " ") ?? "") + ',' +
                (genId ?? "") + ',' +
                (entry?.genType?.toString() ?? "")
            );
        });
    }

       GeneralizationCSV.push(sketchmap + ',' + "Features missing in sketch map,\"" + missingFeaturesIds[i].join(",") + "\"");
        GeneralizationCSV.push(sketchmap + ',' + "Features drawn extra in sketch map, " + extraFeaturesIds[i].toString());
        GeneralizationCSV.push("   ");

     }



  OverallSummaryCsv.push(
    "Base Map,Sketch Maps,Generalization,Completeness_Streets(%),Completeness_Buildings(%),QualitativeAccuracy_Recall,QualitativeAccuracy_Precision,Generalization_OmissionMerge,Generalization_OmissionMerge(many-many),Generalization_Street_AbstractionToShowExistence,Generalization_JuctionMerge,Generalization_RoundaboutCollapse,Generalization_Amalgamation,Generalization_Collapse,Generalization_Building_AbstractionToShowExistence,QualitativeAccuracy_BuildingTopology(RCC8),QualitativeAccuracy_StreetBuildingTopology(DE9IM),QualitativeAccuracy_StreetsOrientation(OPRA),QualitativeAccuracy_StreetsConnectedness,QualitativeAccuracy_BuildingRoute_LeftRight,QualitativeAccuracy_BuildingRoute_LinearOrdering"
);

for (var i in Object.keys(genResultArray)) {


    var sketchmap = Object.keys(genResultArray)[i];
    console.log("CHECK", sketchmap);
    var comp = responseArray[sketchmap];
    var qa = qualresponseArray[sketchmap];

    // Safety checks
    if (!comp) continue;

    var streetCompleteness =
        (comp.totalSketchedStreets + genResultArray[sketchmap].abstExiStreets) /
        (comp.toal_mm_streets + genResultArray[sketchmap].abstExiStreets) * 100;

    var landmarkCompleteness =
        (comp.totalSketchedLandmarks + genResultArray[sketchmap].absExiBuildings) /
        (comp.total_mm_landmarks + genResultArray[sketchmap].absExiBuildings) * 100;

var recall = qa ? qa.recall : "";
var precision = qa ? qa.precision : "";

    OverallSummaryCsv.push(
        baseMaptitle + "," +
        sketchmap + "," +
        genResultArray[sketchmap].overallGen + "," +
        streetCompleteness.toFixed(2) + "," +
        landmarkCompleteness.toFixed(2) + "," +
        recall + "," +
        precision+ "," +
        genResultArray[sketchmap].om + "," +
        genResultArray[sketchmap].om_multi + "," +
        genResultArray[sketchmap].abstExiStreets + "," +
        genResultArray[sketchmap].junctionmerge+ "," +
        genResultArray[sketchmap].roundabout +','+
        genResultArray[sketchmap].amalgamation + ','+
        genResultArray[sketchmap].collapse+ ','+
        genResultArray[sketchmap].absExiBuildings + "," +
        qualresponseArray[sketchmap].correctnessAccuracy_rcc11  + "," +
        qualresponseArray[sketchmap].correctnessAccuracy_DE9IM + "," +
        qualresponseArray[sketchmap].correctnessAccuracy_opra + "," +
        qualresponseArray[sketchmap].correctnessAccuracy_streetTop+ "," +
        qualresponseArray[sketchmap].correctnessAccuracy_LR +','+
       qualresponseArray[sketchmap].correctnessAccuracy_LO
    );
}


    var zip = new JSZip();
        zip.file("CompletenessDetailedOutput.csv", CompletenessSummaryCSV.join("\n"));
        /*zip.file("GeneralizationSummary.csv", GeneralizationSummaryCSV.join("\n"));*/
        zip.file("ResultSummary.csv", OverallSummaryCsv.join("\n"));
        zip.file("GeneralizationDetailedOutput.csv",GeneralizationCSV.join("\n"));

if (Object.keys(qualresponseArray)!=0){
        for (var i = 0;i<numbOfSM-3;i++){
                zip.folder("QualitativeRelations").file("BaseMapFor" + Object.keys(qualresponseArray)[i] + ".csv",QualRelationsBaseMapCSV[i].join("\n"));
                zip.folder("QualitativeRelations").file(Object.keys(qualresponseArray)[i] + ".csv",QualRelationsSketchMapCSV[i].join("\n"));
        }

                zip.file("QADetailedOutput.csv", QASummaryCSV.join("\n"));
}
        for (var i in Object.keys(allGenBaseMap)){
        zip.folder("GeneralizedBaseMap").file(Object.keys(allGenBaseMap)[i]+".geojson", JSON.stringify(allGenBaseMap[Object.keys(allGenBaseMap)[i]].toGeoJSON()));
        }
        zip.generateAsync({type:"blob"})
        .then(function(content) {
        saveAs(content, "Results.zip");
      });

});

// Build gen_id lookups for one sketchmap's alignment.
// gen_id = "g." + sorted unique base IDs joined by "."
// Example: BaseAlign [5, 3] -> "g.3.5"
function buildGenIdLookups(alignmentForMap) {
    const baseIdToGenId  = {};
    const sketchIdToGenId = {};
    const groupIdToGenId = {};   // maps alignment key -> gen_id, for "G<key>" ids

    if (!alignmentForMap) return { baseIdToGenId, sketchIdToGenId, groupIdToGenId };

    Object.keys(alignmentForMap).forEach(key => {
        if (key === 'checkAlignnum') return;
        const entry = alignmentForMap[key];
        if (!entry || !entry.BaseAlign || !entry.BaseAlign[0]) return;

        const baseIds   = entry.BaseAlign[0];
        const sketchIds = (entry.SketchAlign && entry.SketchAlign[0]) || [];

        const sorted = Array.from(new Set(baseIds.map(Number))).sort((a,b) => a - b);
        const genId  = 'g.' + sorted.join('.');

        baseIds.forEach(bid => { baseIdToGenId[String(bid)] = genId; });
        sketchIds.forEach(sid => { sketchIdToGenId[String(sid)] = genId; });
        groupIdToGenId[String(key)] = genId;
    });

    return { baseIdToGenId, sketchIdToGenId, groupIdToGenId };
}

// Translate any raw id used in CSVs into gen_id.
// Handles: "G<key>" group ids, sketch sids ("S12"), numeric base ids, and
// falls back to "g.<n>" for unmapped numeric base ids (missing features).
function resolveGenId(rawId, lookups) {
    if (rawId == null || rawId === '') return rawId;
    const s = String(rawId).trim();

    // 'G<key>' group id (e.g. "G5")
    if (s.length > 1 && s[0] === 'G') {
        const groupKey = s.substring(1);
        if (lookups.groupIdToGenId[groupKey]) return lookups.groupIdToGenId[groupKey];
    }

    // Exact sid (e.g. "S13") — covers cases where the full sid is used
    if (lookups.sketchIdToGenId[s]) return lookups.sketchIdToGenId[s];

    // Numeric input: in the QA relations, "13" actually means sid "S13"
    // because prepareDataForQualifier rewrites IDs to the numeric part of the sid.
    if (/^\d+$/.test(s)) {
        const sidForm = 'S' + s;
        if (lookups.sketchIdToGenId[sidForm]) return lookups.sketchIdToGenId[sidForm];
        if (lookups.baseIdToGenId[s])         return lookups.baseIdToGenId[s];
        return 'g.' + s;
    }

    if (lookups.baseIdToGenId[s]) return lookups.baseIdToGenId[s];
    return s;
}


// Populate and toggle the GMDA summary panel from genResultArray
function populateGMDAResults() {
    const tbody = document.getElementById('gmda_rows');
    if (!tbody) return;
    tbody.innerHTML = '';
    const keys = Object.keys(genResultArray || {});
    if (keys.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7">No GMDA results available</td></tr>';
    } else {
        keys.forEach(function(sketchmap) {
            const g = genResultArray[sketchmap] || {};
            const tr = document.createElement('tr');
            
            // Dynamically fall back to Junc_ keys if the standard keys are missing
            const canOrg  = g.CanOrg  !== undefined ? g.CanOrg  : (g.Junc_CanOrg  || 0);
            const canAcc  = g.CanAcc  !== undefined ? g.CanAcc  : (g.Junc_CanAcc  || 0);
            const scaBias = g.ScaBias !== undefined ? g.ScaBias : (g.Junc_ScaBias || 0);
            const distAcc = g.DistAcc !== undefined ? g.DistAcc : (g.Junc_DistAcc || 0);
            const rotBias = g.RotBias !== undefined ? g.RotBias : (g.Junc_RotBias || 0);
            const angAcc  = g.AngAcc  !== undefined ? g.AngAcc  : (g.Junc_AngAcc  || 0);

            tr.innerHTML = '<td>' + sketchmap + '</td>' +
                           '<td>' + canOrg + '</td>' +
                           '<td>' + canAcc + '</td>' +
                           '<td>' + scaBias + '</td>' +
                           '<td>' + distAcc + '</td>' +
                           '<td>' + rotBias + '</td>' +
                           '<td>' + angAcc + '</td>';
            tbody.appendChild(tr);
        });
    }
    const panel = document.getElementById('gmda_summary');
    if (panel) panel.style.display = (panel.style.display === 'none' ? 'block' : 'none');
}


// Populate and toggle the BDR summary panel from genResultArray
function populateBDRResults() {
    const tbody = document.getElementById('bdr_rows');
    if (!tbody) return;
    tbody.innerHTML = '';
    const keys = Object.keys(genResultArray || {});
    if (keys.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7">No BDR results available</td></tr>';
    } else {
        keys.forEach(function(sketchmap) {
            const g = genResultArray[sketchmap] || {};
            const tr = document.createElement('tr');
            
            // Dynamically fall back to Junc_ keys if the standard keys are missing
            const r = g.Land_r  !== undefined ? g.Land_r  : (g.Junc_r || 0);
            const DI = g.Land_DI  !== undefined ? g.Land_DI  : (g.Junc_DI || 0);
            const phi = g.Land_phi !== undefined ? g.Land_phi : (g.Junc_phi || 0);
            const theta = g.Land_theta !== undefined ? g.Land_theta : (g.Junc_theta || 0);
            const alpha1 = g.Land_alpha1 !== undefined ? g.Land_alpha1 : (g.Junc_alpha1 || 0);
            const alpha2 = g.Land_alpha2  !== undefined ? g.Land_alpha2  : (g.Junc_alpha2 || 0);

            tr.innerHTML = '<td>' + sketchmap + '</td>' +
                           '<td>' + r + '</td>' +
                           '<td>' + DI + '</td>' +
                           '<td>' + phi + '</td>' +
                           '<td>' + theta + '</td>' +
                           '<td>' + alpha1 + '</td>' +
                           '<td>' + alpha2 + '</td>';
            tbody.appendChild(tr);
        });
    }
    const panel = document.getElementById('bdr_summary');
    if (panel) panel.style.display = (panel.style.display === 'none' ? 'block' : 'none');
}