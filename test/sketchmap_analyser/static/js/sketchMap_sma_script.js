var sm_map;
var sketchFileName;
var drawnItems_sm;
var drawnItems2_sm;
var val;
var val2;
var SMGeoJsonData;
var ArrowsArray_sm = [];
var labelLayer_sm = null;
var MMStreetIDs;
var MMRegionsIDs;
var MMLandmarksIDs;




function newProject(e){
    x = e.pageX;
    y = e.pageY;
    //console.log(x, y);

    $('#newProject_div').prop("style", "visibility: visible");

    $('#newProject_div').offset({
        top: y+10,
        left: x
    });


    $(document).on('keydown', function (e) {
        if (e.keyCode === 27) { // ESC
            $("#newProject_div").hide();
        }
    });

}
function browseAndSave(){
        var projectName = document.getElementById("ProjectName").value;
        //console.log("i am here in the save");
        var blob = new Blob([""], { type: "text/plain;charset=utf-8" });
        saveAs(blob, projectName+".smaproj");
        var url = window.location.pathname;
       // console.log("url:",url);
    }



function loadSketchMap(element) {
    //var location = document.getElementById("metricmapplaceholder");
    var fileList = document.getElementById('SketchMapInputbutton').files;
    console.log(fileList);
    $("sketchmapplaceholder").hide();
    for (var i = 0; i < fileList.length; i++) {
        randerLoadedSMFile(fileList[i], location);
    }
}

function randerLoadedSMFile(file, location) {
    var reader = new FileReader();
    reader.readAsDataURL(file);

    reader.onload = function (e) {

        var container = L.DomUtil.get('sm_map');
        if (container != null) {
            container._leaflet_id = null;
        }
        var image = new Image();

        image.title = file.name;
        image.src = this.result;
        //document.getElementById('mm').src = image.src;

        sm_map = new L.map('sketchmapplaceholder', {
            crs: L.CRS.Simple
        });

        sm_map.options.doubleClickZoom = false;

        var bounds = [[0, 0], [600, 850]];
        var SMLoaded = new L.imageOverlay(image.src, bounds);
        SMLoaded.addTo(sm_map);
        sm_map.fitBounds(bounds);

        sketchFileName = image.title;

  /*      $("#SMLinks").show();
        $.ajax({
            url: '/sketchFileName',
            data: {sketchFileName: sketchFileName},
            success: function (resp) {
            }
        });*/
        loadEditingToolforSM(sm_map);
        $("#stepper_load_sm").prop("style", "background: #17a2b8");

    }

}

function uploadJsonSM() {

    var fileList = document.getElementById('importSM').files;
    for (var i = 0; i < fileList.length; i++) {
        randerGeoJsonFiles_SM(fileList[i], sm_map);
    }
}

function randerGeoJsonFiles_SM(file, sm_map) {
    var fileName = file.name;
    var reader = new FileReader();
    reader.readAsDataURL(file);
    //var loadedJsonLayer;
    reader.onload = function () {
        // load GeoJSON from an external file
        $.getJSON(reader.result, function (data) {
            //passing data to qualifier
            SMGeoJsonData = data;
            loadedJsonLayerSM = L.geoJson(data, {
                opacity: 0.5,
            });
            sm_map.fitBounds(loadedJsonLayerSM.getBounds());
            loadJsonLayer_sm(sm_map);
        });
    }
}

function loadJsonLayer_sm(sm_map) {
    drawnItems_sm = new L.FeatureGroup();

    loadedJsonLayerSM.eachLayer(
        function (l) {
            drawnItems_sm.addLayer(l);
        }
    );
    drawnItems_sm.eachLayer(function (layer) {
        if (layer.feature.geometry.type == "Polygon") {
            addLandmarkPopupSM(layer);
        }
        if (layer.feature.geometry.type == "LineString") {
            arrowHead = L.polylineDecorator(layer, {
                patterns: [
                    {
                        offset: 25,
                        repeat: 50,
                        endoffset: 0,
                        symbol: L.Symbol.arrowHead({pixelSize: 15, pathOptions: {fillOpacity: 1, weight: 0}})
                    }
                ]
            }).addTo(sm_map);

            var arrowsLayerGroup = L.layerGroup([layer, arrowHead]);

            var Linie = [arrowsLayerGroup, layer, arrowHead];
            ArrowsArray_sm.push(Linie);

            addStreetPopUpSM(layer);

        }else if (layer.feature.geometry.type == "LineString" && layer.feature.properties.isRoute == 'Yes') {
            arrowHead = L.polylineDecorator(layer, {
                patterns: [
                    {
                        offset: 25,
                        repeat: 50,
                        endoffset: 0,
                        symbol: L.Symbol.arrowHead({
                            pixelSize: 15,
                            pathOptions: {fillOpacity: 1, weight: 0, color: 'red'}
                        })
                    }
                ]
            }).addTo(sm_map);

            // push LayerGroup for arrows and layers in Array
            var arrowsLayerGroup = L.layerGroup([layer, arrowHead]);
            var Linie = [arrowsLayerGroup, layer, arrowHead];
            ArrowsArray.push(Linie);

            layer.options.color = 'red';
            addStreetPopupSM(layer);
        }
    });
    $("#stepper_annotate_sm").prop("style", "background: #17a2b8");
    sm_map.addLayer(drawnItems_sm);
}


/**
 * adding toolbar in the map
 * using leaflet plugin "leaflet.pm"
 *
 */
function loadEditingToolforSM(sm_map) {
    drawnItems_sm = new L.FeatureGroup();
    drawnItems2_sm = new L.FeatureGroup();
    sm_map.addLayer(drawnItems_sm);

    var options = {
        position: 'topleft',
        drawMarker: false,
        drawPolyliine: true,
        drawRectangle: false,
        drawPolygon: true,
        drawCircle: false,
        cutPolygon: false,
        editMode: true,
        removalMode: true
    };
    sm_map.pm.addControls(options);

    /**
     * now how drawing works
     * using again leaflet plugin "leaflet.pm"
     */
    sm_map.on('pm:create', function (event) {
        var layer = event.layer;
        var type = event.shape;
        feature = layer.feature = layer.feature || {};
        feature.type = feature.type || "Feature";
        var props = feature.properties = feature.properties || {};
        props.FID = null;
        props.id = null;
        props.isRoute = null;
        props.name = null;
        props.feat_type = null;
        props.sm_sk_type = "rectangle | olopololi | some stuff";
        props.descriptn = "something";

        drawnItems_sm.addLayer(layer);
        drawnItems2_sm.addLayer(layer);
        if (type === "Line") {

            var arrowHead = L.polylineDecorator(layer, {
                patterns: [
                    {
                        offset: 25,
                        repeat: 70,
                        endoffset: 0,
                        symbol: L.Symbol.arrowHead({pixelSize: 15, pathOptions: {fillOpacity: 1, weight: 0}})
                    }
                ]
            }).addTo(sm_map);
            var arrowsLayerGroup = L.layerGroup([layer, arrowHead]);

            var Linie = [arrowsLayerGroup, layer, arrowHead]
            ArrowsArray_sm.push(Linie);
            addStreetPopUpSM(layer);
            layer.openPopup();

        }
        if (type === "Poly") {
            addLandmarkPopupSM(layer);
            layer.openPopup();
        }
        //change the color of the stepper
        $("#stepper_annotate_sm").prop("style", "background: #17a2b8");
    });


    // if drawn object get deleted remove it from geoJSON file
    sm_map.on('pm:remove', function (event) {
        var deleteButton = document.getElementsByClassName('leaflet-pm-icon-delete');
        var buttoncontrol = deleteButton[0].parentElement;

        if (buttoncontrol.classList.contains('active')) {
            loop1:
                for (var i = 0; i < ArrowsArray_sm.length; i++) {
                    for (var j = 0; j < ArrowsArray_sm[i].length; j++) {
                        if (event.layer._leaflet_id == ArrowsArray_sm[i][j]._leaflet_id) {
                            if (j == 1) {
                                sm_map.removeLayer(ArrowsArray_sm[i][j + 1]);
                                ArrowsArray_sm.splice(i, 1);
                                break loop1;
                            } else if (j == 2) {
                                sm_map.removeLayer(ArrowsArray_sm[i][j - 1]);
                                break loop1;
                            }
                        }
                    }
                }
        }

        layerid = event.layer._leaflet_id;
        deleteFunction_sm();
    });

    function deleteFunction_sm() {
        drawnItems_sm.eachLayer(function (l) {
            jsonId = l._leaflet_id;
            if (layerid == jsonId) {
                drawnItems_sm.removeLayer(l);
            }
        });
    }

}



function addStreetPopUpSM(layer, Input) {
    MMStreetIDs = [1,2,3,4,5,6,7];
    MMStreetIDs.sort();
    MMisRoute.sort();

    var tableDiv = document.createElement('div');
    tableDiv.setAttribute('class', 'table1');
    tableDiv.setAttribute('id', 'tableDiv');
    var table = document.createElement('table');
    table.setAttribute('id', 'popupTable');
    var row1 = table.insertRow(0);
    row1.setAttribute('id', 'Row1');
    var fetureID_div;
    var fetureID_div2;
    var TRoute = document.createElement('th');
    TRoute.setAttribute('id', 'TRoute');
    TRoute.innerHTML = "isRoute";
    row1.insertCell(0).append(TRoute);
    var TStreet = document.createElement('th');
    TStreet.setAttribute('id', 'TStreet');
    TStreet.innerHTML = "Streets";
    row1.insertCell(-1).append(TStreet);
    var row = table.insertRow(1);
    row.setAttribute('id', 'Row');
    var cell1 = row.insertCell(0);
    cell1.setAttribute('class', 'a');
    var cell2 = row.insertCell(-1);
    cell2.setAttribute('class', 'b');

    // If there are more Route-segments than street-segments
    if (MMisRoute.length > MMStreetIDs.length) {
        fetureID_div = document.createElement('div');
        fetureID_div.setAttribute("id", "fetureID_div");
        var checkedID1;
        fetureID_div2 = document.createElement('div');
        fetureID_div2.setAttribute("id", "fetureID_div2");
        var checkedID2;

        /**
         * Iterate over all Route-segments and add them to the
         * first column in the table
         */
        for (i = 1; i <= MMisRoute.length; i++) {
            checkedID1 = document.createElement('input');
            var label1 = document.createElement('label');

            checkedID1.setAttribute('type', 'checkbox');
            checkedID1.setAttribute('id', MMisRoute[i - 1]);
            label1.setAttribute('for', MMisRoute[i - 1]);
            label1.setAttribute('id', MMisRoute[i - 1]);
            label1.setAttribute('style', 'word-wrap:break-word');

            x = document.createTextNode(MMisRoute[i - 1]);
            label1.appendChild(x);
            var br = document.createElement('br');

            fetureID_div.appendChild(checkedID1);
            fetureID_div.appendChild(label1);
            fetureID_div.append(br);

            cell1.appendChild(fetureID_div);

            /**
             * if there are no more Street-segments do nothing
             * else add them to the second column
             */
            if (i > MMStreetIDs.length) {
               // console.log("i > " + MMStreetIDs.lenght);
            } else {
                checkedID2 = document.createElement('input');
                var label2 = document.createElement('label');

                checkedID2.setAttribute('type', 'checkbox');
                checkedID2.setAttribute('id', MMStreetIDs[i - 1]);
                label2.setAttribute('for', MMStreetIDs[i - 1]);
                label2.setAttribute('id', MMStreetIDs[i - 1]);
                label2.setAttribute('style', 'word-wrap:break-word');

                x = document.createTextNode(MMStreetIDs[i - 1]);
                label2.appendChild(x);
                var br2 = document.createElement('br');

                fetureID_div2.appendChild(checkedID2);
                fetureID_div2.appendChild(label2);
                fetureID_div2.append(br2);

                cell2.appendChild(fetureID_div2);
            }
        }
        // if there are more street-segments than route segments
    } else if (MMStreetIDs.length > MMisRoute.length) {
        fetureID_div = document.createElement('div');
        fetureID_div.setAttribute("id", "fetureID_div");
        var checkedID1;
        fetureID_div2 = document.createElement('div');
        fetureID_div2.setAttribute("id", "fetureID_div2");
        var checkedID2;

        /**
         * Iterate over all street-segments and add them to the
         * second column in the table
         */
        for (var i = 1; i <= MMStreetIDs.length; i++) {

            // if there are no more route-segments, do nothing
            // else add them to the first cell
            if (i > MMisRoute.length) {
                //console.log("i > " + MMisRoute.length);
            } else {
                checkedID1 = document.createElement('input');
                var label1 = document.createElement('label');

                checkedID1.setAttribute('type', 'checkbox');
                checkedID1.setAttribute('id', MMisRoute[i - 1]);
                label1.setAttribute('for', MMisRoute[i - 1]);
                label1.setAttribute('id', MMisRoute[i - 1]);
                label1.setAttribute('style', 'word-wrap:break-word');

                x = document.createTextNode(MMisRoute[i - 1]);
                label1.append(x);
                var br = document.createElement('br');

                fetureID_div.append(checkedID1);
                fetureID_div.append(label1);
                fetureID_div.append(br);
            }
            cell1.append(fetureID_div);

            checkedID2 = document.createElement('input');
            var label2 = document.createElement('label');

            checkedID2.setAttribute('type', 'checkbox');
            checkedID2.setAttribute('id', MMStreetIDs[i - 1]);
            label2.setAttribute('for', MMStreetIDs[i - 1]);
            label2.setAttribute('id', MMStreetIDs[i - 1]);
            label2.setAttribute('style', 'word-wrap:break-word');

            x = document.createTextNode(MMStreetIDs[i - 1]);
            label2.append(x);
            var br2 = document.createElement('br');

            fetureID_div2.append(checkedID2);
            fetureID_div2.append(label2);
            fetureID_div2.append(br2);


            cell2.append(fetureID_div2);
        }
        // same number of Route-segments and street-segments
    } else if (MMStreetIDs.length == MMisRoute.length) {
        fetureID_div = document.createElement('div');
        fetureID_div.setAttribute("id", "fetureID_div");
        var checkedID1;
        fetureID_div2 = document.createElement('div');
        fetureID_div2.setAttribute("id", "fetureID_div2");
        var checkedID2;

        /**
         * Iterate over all Route-segments and add them to the
         * first column in the table
         * add all street-segments to the second column in the table
         */
        for (i = 1; i <= MMisRoute.length; i++) {

            checkedID1 = document.createElement('input');
            var label1 = document.createElement('label');

            checkedID1.setAttribute('type', 'checkbox');
            checkedID1.setAttribute('id', MMisRoute[i - 1]);
            label1.setAttribute('for', MMisRoute[i - 1]);
            label1.setAttribute('id', MMisRoute[i - 1]);
            label1.setAttribute('style', 'word-wrap:break-word');

            x = document.createTextNode(MMisRoute[i - 1]);
            label1.append(x);
            var br = document.createElement('br');

            fetureID_div.append(checkedID1);
            fetureID_div.append(label1);
            fetureID_div.append(br);

            cell1.append(fetureID_div);

            checkedID2 = document.createElement('input');
            var label2 = document.createElement('label');

            checkedID2.setAttribute('type', 'checkbox');
            ;
            checkedID2.setAttribute('id', MMStreetIDs[i - 1]);
            label2.setAttribute('for', MMStreetIDs[i - 1]);
            label2.setAttribute('id', MMStreetIDs[i - 1]);
            label2.setAttribute('style', 'word-wrap:break-word');

            x = document.createTextNode(MMStreetIDs[i - 1]);
            label2.append(x);
            var br2 = document.createElement('br');

            fetureID_div2.append(checkedID2);
            fetureID_div2.append(label2);
            fetureID_div2.append(br2);

            cell2.append(fetureID_div2);
        }
    }

    tableDiv.append(table);

    layer.bindPopup(tableDiv);

    var popup = layer.getPopup();
    popup.options.maxHeight = 250;
    popup.options.maxWidth = 350;


    cell1.addEventListener("click", function (event) {
        if ($(event.target).is('[type="checkbox"]')) {
            if ($(event.target).is(":checked")) {
                val = event.target.id;
                changeColorSM(layer);
                $('input[type="checkbox"]').on('change', function () {
                    $('input[type="checkbox"]').not(this).prop('checked', false);
                });

            }
        }
    });

    cell2.addEventListener("click", function (event) {
        if ($(event.target).is('[type="checkbox"]')) {
            if ($(event.target).is(":checked")) {
                val2 = event.target.id;
                ChangeColorBackSM(layer);
                $('input[type="checkbox"]').on('change', function () {
                    $('input[type="checkbox"]').not(this).prop('checked', false);
                });

            }
        }
    });

    layer.on("popupopen", function () {
        for (i = 0; i < MMStreetIDs.length; i++) {
            id1 = MMStreetIDs[i];
            document.getElementById(id1).checked = false;
        }
        for (j = 0; j < MMisRoute.length; j++) {
            id2 = MMisRoute[j];
            document.getElementById(id2).checked = false;
        }

        var id = layer.feature.properties.id;
        val = layer.feature.properties.id;
        val2 = layer.feature.properties.id;
        if (id == null) {
        } else {
            document.getElementById(id).checked = true;
        }
    });

    /**
     if checkbox is checked then pass the value to feature id
     **/
    layer.on("popupclose", function () {
        var k = 0;
        var l = 0;
        for (var i = 0; i < MMisRoute.length; i++) {
            var Routes = document.getElementById(MMisRoute[i]);
            if (Routes.checked == true) {
                layer.feature.properties.id = val;
                layer.feature.properties.FID = val;
                layer.feature.properties.name = val;
                layer.feature.properties.isRoute = "Yes";
                k++;
            }
        }
        for (var j = 0; j < MMStreetIDs.length; j++) {
            var Streets = document.getElementById(MMStreetIDs[j]);
            if (Streets.checked == true) {
                layer.feature.properties.id = val2;
                layer.feature.properties.FID = val2;
                layer.feature.properties.name = val2;
                layer.feature.properties.isRoute = null;
                l++;
            }
        }
        if (k == 0 && l == 0) {
            alert("ERROR! Do not forget to give the Street a name!");
        }
    });
}
function addLandmarkPopupSM(layer) {
    MMLandmarksIDs = [1,2,3,4,5,6,7];
    MMRegionsIDs = [1,2,3,4,5,6,7];
    MMLandmarksIDs.sort();
    MMRegionsIDs.sort();

    var LMTable = document.createElement('table');
    LMTable.setAttribute('id', 'LMTable');
    var LMRow1 = LMTable.insertRow(0);
    LMRow1.setAttribute('id', 'LMRow1');
    var features_div1;
    var features_div2;
    var TLM = document.createElement('th');
    TLM.setAttribute('id', 'TLM');
    TLM.innerHTML = 'Landmark';
    LMRow1.insertCell(0).append(TLM);
    var TRegion = document.createElement('th');
    TRegion.setAttribute('id', 'TRegion');
    TRegion.innerHTML = 'Region';
    LMRow1.insertCell(-1).append(TRegion);
    var LMRow2 = LMTable.insertRow(1);
    LMRow2.setAttribute('id', 'LMRow2');
    var LMCell1 = LMRow2.insertCell(0);
    LMCell1.setAttribute('class', 'a');
    var LMCell2 = LMRow2.insertCell(-1);
    LMCell2.setAttribute('class', 'b');

    // if there are more Landmarks than Regions
    if (MMLandmarksIDs.length > MMRegionsIDs.length) {
        features_div1 = document.createElement('div');
        features_div1.setAttribute('id', 'features_div1');
        var lm_input;
        var LM_ID1;
        features_div2 = document.createElement('div');
        features_div2.setAttribute('id', 'features_div2');
        var region_input;
        var Region_ID;

        /**
         * iterate over Landmarks array and add each Landmark to the corresponding column
         * in the table for the popup
         */
        for (i = 1; i <= MMLandmarksIDs.length; i++) {
            lm_input = document.createElement('input');
            var lm_label = document.createElement('label');

            lm_input.setAttribute('type', 'checkbox');//
            lm_input.setAttribute('id', MMLandmarksIDs[i - 1]);// add rate value
            lm_label.setAttribute('for', MMLandmarksIDs[i - 1]);// set for attribute for each label
            lm_label.setAttribute('id', MMLandmarksIDs[i - 1]);// set id for label
            lm_label.setAttribute('style', 'word-wrap:break-word');

            x = document.createTextNode(MMLandmarksIDs[i - 1]);
            lm_label.append(x);
            var br = document.createElement('br');

            features_div1.append(lm_input);
            features_div1.append(lm_label);
            features_div1.append(br);
            LMCell1.append(features_div1);

            /**
             *  if there are no objects from the Regions array left do nothing
             *  else put them in the corresponding column in the table for the popup
             */
            if (i > MMRegionsIDs.length) {
                //console.log("i > MMRegionsIDs.length");
            } else {
                region_input = document.createElement('input');
                var region_label = document.createElement('label');

                region_input.setAttribute('type', 'checkbox');//
                region_input.setAttribute('id', MMRegionsIDs[i - 1]);// add rate value
                region_label.setAttribute('for', MMRegionsIDs[i - 1]);// set for attribute for each label
                region_label.setAttribute('id', MMRegionsIDs[i - 1]);// set id for label
                region_label.setAttribute('style', 'word-wrap:break-word');

                x = document.createTextNode(MMRegionsIDs[i - 1]);
                region_label.append(x);
                var br2 = document.createElement('br');

                features_div2.append(region_input);
                features_div2.append(region_label);
                features_div2.append(br2);
                LMCell2.append(features_div2);
            }
        }
        // if there are more Regions than Landmarks
    } else if (MMRegionsIDs.length > MMLandmarksIDs.length) {
        features_div1 = document.createElement('div');
        features_div1.setAttribute('id', 'features_div1');
        var lm_input;
        var LM_ID1;
        features_div2 = document.createElement('div');
        features_div2.setAttribute('id', 'features_div2');
        var region_input;
        var Region_ID;

        /**
         * iterate over Regions array and add each Regions to the corresponding column
         * in the table for the popup
         * if there are no objects from the Regions array left do nothing
         * else put them in the corresponding column in the table for the popup
         */
        for (var i = 1; i <= MMRegionsIDs.length; i++) {
            if (i > MMLandmarksIDs.length) {
                //console.log("i > MMStreetIDs.length")
            } else {
                lm_input = document.createElement('input');
                var lm_label = document.createElement('label');

                lm_input.setAttribute('type', 'checkbox');//
                lm_input.setAttribute('id', MMLandmarksIDs[i - 1]);// add rate value
                lm_label.setAttribute('for', MMLandmarksIDs[i - 1]);// set for attribute for each label
                lm_label.setAttribute('id', MMLandmarksIDs[i - 1]);// set id for label
                lm_label.setAttribute('style', 'word-wrap:break-word');

                x = document.createTextNode(MMLandmarksIDs[i - 1]);
                lm_label.append(x);
                var br = document.createElement('br');

                features_div1.append(lm_input);
                features_div1.append(lm_label);
                features_div1.append(br);
            }
            LMCell1.append(features_div1);

            region_input = document.createElement('input');
            var region_label = document.createElement('label');

            region_input.setAttribute('type', 'checkbox');//
            region_input.setAttribute('id', MMRegionsIDs[i - 1]);// add rate value
            region_label.setAttribute('for', MMRegionsIDs[i - 1]);// set for attribute for each label
            region_label.setAttribute('id', MMRegionsIDs[i - 1]);// set id for label
            region_label.setAttribute('style', 'word-wrap:break-word');


            x = document.createTextNode(MMRegionsIDs[i - 1]);
            region_label.append(x);
            var br2 = document.createElement('br');

            features_div2.append(region_input);
            features_div2.append(region_label);
            features_div2.append(br2);
            LMCell2.append(features_div2);
        }
        // if there is an identical number of Landmarks and Regions
    } else if (MMLandmarksIDs.length == MMRegionsIDs.length) {
        features_div1 = document.createElement('div');
        features_div1.setAttribute('id', 'features_div1');
        var lm_input;
        var LM_ID1;
        features_div2 = document.createElement('div');
        features_div2.setAttribute('id', 'features_div2');
        var region_input;
        var Region_ID;

        /**
         * itereate over the Landmarks array and add each Landmark and each Region to the
         * corresponding column in the table for the popup
         */
        for (i = 1; i <= MMLandmarksIDs.length; i++) {
            lm_input = document.createElement('input');
            var lm_label = document.createElement('label');

            lm_input.setAttribute('type', 'checkbox');//
            lm_input.setAttribute('id', MMLandmarksIDs[i - 1]);// add rate value
            lm_label.setAttribute('for', MMLandmarksIDs[i - 1]);// set for attribute for each label
            lm_label.setAttribute('id', MMLandmarksIDs[i - 1]);// set id for label
            lm_label.setAttribute('style', 'word-wrap:break-word');

            x = document.createTextNode(MMLandmarksIDs[i - 1]);
            lm_label.append(x);
            var br = document.createElement('br');

            features_div1.append(lm_input);
            features_div1.append(lm_label);
            features_div1.append(br);
            LMCell1.append(features_div1);


            region_input = document.createElement('input');
            var region_label = document.createElement('label');

            region_input.setAttribute('type', 'checkbox');//
            region_input.setAttribute('id', MMRegionsIDs[i - 1]);// add rate value
            region_label.setAttribute('for', MMRegionsIDs[i - 1]);// set for attribute for each label
            region_label.setAttribute('id', MMRegionsIDs[i - 1]);// set id for label
            region_label.setAttribute('style', 'word-wrap:break-word');

            x = document.createTextNode(MMRegionsIDs[i - 1]);
            region_label.append(x);
            var br2 = document.createElement('br');

            features_div2.append(region_input);
            features_div2.append(region_label);
            features_div2.append(br2);
            LMCell2.append(features_div2);
        }
    }

    layer.bindPopup(LMTable);

    var LMPopup = layer.getPopup();
    LMPopup.options.maxHeight = 250;
    LMPopup.options.maxWidth = 350;


    LMCell1.addEventListener("click", function (event) {
        if ($(event.target).is('[type="checkbox"]')) {
            if ($(event.target).is(':checked')) {
                var LM_val = event.target.id;
                LM_ID1 = LM_val;
                $('input[type="checkbox"]').on('change', function () {
                    $('input[type="checkbox"]').not(this).prop('checked', false);
                });
            }
        }
    });

    LMCell2.addEventListener("click", function (event) {
        if ($(event.target).is('[type="checkbox"]')) {
            if ($(event.target).is(':checked')) {
                var LM_val2 = event.target.id;
                Region_ID = LM_val2;
                $('input[type="checkbox"]').on('change', function () {
                    $('input[type="checkbox"]').not(this).prop('checked', false);
                });
            }
        }
    });

    layer.on("popupclose", function () {
        var k = 0;
        var l = 0;
        for (var i = 0; i < MMLandmarksIDs.length; i++) {
            var LMs = document.getElementById(MMLandmarksIDs[i]);
            if (LMs.checked == true) {
                layer.feature.properties.id = LM_ID1;
                layer.feature.properties.FID = LM_ID1;
                layer.feature.properties.name = LM_ID1;
                layer.feature.properties.feat_type = "Landmark";
                k++;
            }
        }
        for (var j = 0; j < MMRegionsIDs.length; j++) {
            var CBlocks = document.getElementById(MMRegionsIDs[j]);
            if (CBlocks.checked == true) {
                layer.feature.properties.id = Region_ID;
                layer.feature.properties.FID = Region_ID;
                layer.feature.properties.name = Region_ID;
                layer.feature.properties.feat_type = "Cityblock";
                l++
            }
        }
        if (k == 0 && l == 0) {
            alert("ERROR! Do not forget to give the Landmark/Region a name!");
        }
    });
}

//##########################################
function changeColorSM(layer) {
    drawnItems2_sm.eachLayer(function (l) {
        if (l == layer) {
            loop1:
                for (var i = 0; i < ArrowsArray_sm.length; i++) {
                    for (var j = 0; j < ArrowsArray_sm[i].length; j++) {
                        if (l._leaflet_id == ArrowsArray_sm[i][j]._leaflet_id) {
                            if (j == 1) {
                                sm_map.removeLayer(ArrowsArray_sm[i][j + 1]);
                                sm_map.removeLayer(l);
                                ArrowsArray_sm.splice(i, 1);
                                break loop1;
                            } else if (j == 2) {
                                sm_map.removeLayer(l)
                                sm_map.removeLayer(ArrowsArray_sm[i][j]);
                                ArrowsArray_sm.splice(i, 1);
                                break loop1;
                            }
                        }
                    }
                }

            function x(callback) {
                l.options.color = 'red';
                callback();
            };

            function y() {
                drawnItems_sm.addLayer(l);
                drawnItems_sm.eachLayer(function (layers) {
                    if (layers == layer) {
                        arrowHead = L.polylineDecorator(layers, {
                            patterns: [
                                {
                                    offset: 25,
                                    repeat: 50,
                                    endoffset: 0,
                                    symbol: L.Symbol.arrowHead({
                                        pixelSize: 15,
                                        pathOptions: {fillOpacity: 1, weight: 0, color: 'red'}
                                    })
                                }
                            ]
                        }).addTo(sm_map);
                        var arrowsLayerGroup = L.layerGroup([layer, arrowHead]);

                        var Linie = [arrowsLayerGroup, layer, arrowHead]
                        ArrowsArray_sm.push(Linie);
                        addStreetPopUpSM(layer);
                    }
                });
            }

            x(y);
        }
    });
}

function ChangeColorBackSM(layer) {
    drawnItems2_sm.eachLayer(function (l) {
        if (l == layer) {
            loop1:
                for (var i = 0; i < ArrowsArray_sm.length; i++) {
                    for (var j = 0; j < ArrowsArray_sm[i].length; j++) {
                        if (l._leaflet_id == ArrowsArray_sm[i][j]._leaflet_id) {
                            if (j == 1) {
                                sm_map.removeLayer(ArrowsArray_sm[i][j + 1]);
                                sm_map.removeLayer(l);
                                ArrowsArray_sm.splice(i, 1);
                                break loop1;
                            } else if (j == 2) {
                                sm_map.removeLayer(l)
                                sm_map.removeLayer(ArrowsArray_sm[i][j]);
                                ArrowsArray_sm.splice(i, 1);
                                break loop1;
                            }
                        }
                    }
                }

            function x(callback) {
                l.options.color = '#3388ff';
                callback();
            }

            function y() {
                drawnItems_sm.addLayer(l);
                drawnItems_sm.eachLayer(function (layers) {
                    if (layers == layer) {
                        arrowHead = L.polylineDecorator(layers, {
                            patterns: [
                                {
                                    offset: 25,
                                    repeat: 50,
                                    endoffset: 0,
                                    symbol: L.Symbol.arrowHead({
                                        pixelSize: 15,
                                        pathOptions: {fillOpacity: 1, weight: 0, color: '#3388ff'}
                                    })
                                }
                            ]
                        }).addTo(sm_map);
                        var arrowsLayerGroup = L.layerGroup([layer, arrowHead]);
                        var Linie = [arrowsLayerGroup, layer, arrowHead]
                        ArrowsArray_sm.push(Linie);

                        addStreetPopUpSM(layer);
                    }
                });
            }

            x(y);
        }
    });
}

//################################################################################################################

function downloadJsonSM() {
    SMGeoJsonData = drawnItems_sm.toGeoJSON();

    var SMGeoJSON = 'text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(SMGeoJsonData));
    document.getElementById('exportSketchFeatures').setAttribute('href', 'data:' + SMGeoJSON);
    document.getElementById('exportSketchFeatures').setAttribute('download', sketchFileName+'.geojson');
};


function showLabels_sm() {

    sm_map.createPane("pane200").style.zIndex = 200;
    document.getElementById("showLabels_sm").checked = true;
    document.getElementById("hideLabels_sm").checked = false;
    var data = drawnItems_sm.toGeoJSON();
    labelLayer_sm = L.geoJson(data, {
        onEachFeature: function (feature, layer) {
            var temLayer = layer;
            if (temLayer.feature.properties.isRoute == "Yes") {
                temLayer.options.color = "red";
            } else {
            }
            temLayer.bindTooltip(feature.properties.id, {permanent: true, direction: 'auto'});
            return temLayer;
        }
    });
    sm_map.addLayer(labelLayer_sm);
    //document.getElementById("showLabels_sm").disabled = true;
}

function hideLabels_sm() {

    document.getElementById("hideLabels_sm").checked = true;
    document.getElementById("showLabels_sm").checked = false;
    sm_map.removeLayer(labelLayer_sm);
    //document.getElementById("showLabels_sm").disabled = false;
}

/**
 - qualify_SM function takes the geojson from sketch maps and pass
 - it to the paython function "smReceiver" that connect qualifier plugin
 **/
function qualify_SM(callback) {
    SMGeoJsonData = drawnItems_sm.toGeoJSON();
    //console.log("SMGeoJsonData....:",SMGeoJsonData);
    // fileName = sketchFileName.split(".");
    // fileName = fName[0];

    $.ajax({
        url: '/smReceiver',
        type: 'POST',
        data: {
            sketchFileName:sketchFileName,
            SMGeoJsonData: JSON.stringify(SMGeoJsonData)
        },
        //dataType: 'json',
        success: function (resp) {
            callback();
        }
    });
}


function analyzeInputMap(){
    loc = document.getElementById("#sketchmapplaceholder");
    createProcessingRing(loc);

    //sm_map.addLayer(createProcessingRing(loc));
    //sm_map.addLayer( createProcessingRing(loc));
    qualify_MM(function () {
        //console.log("call qualify SM function");
        qualify_SM(function(){
          //  console.log("call the alignment function");
            // ajax call for getting the matches dictionary
            $.ajax({
                url: '/analyzeInputMap',
                type: 'POST',
                data: {
                    sketchFileName: sketchFileName,
                    metricFileName: metricFileName

                },
                //contentType: 'text/plain',
                success: function (resp) {
                    result = JSON.parse(resp);
                    //console.log(result);
                    setResults_in_output_div(result);
                    $('#summary_result_div').prop("style", "visibility: visible");
                    //$('#summary_result_div').refresh();

                    $("#stepper_analyze_map").prop("style", "background: #17a2b8");
                    //window.open('http://127.0.0.1:5000/resultSummary','_blank');
                    deleteProcessingRing(loc);
                }
            });
        });
    });

    $(document).on('keydown', function (e) {
        if (e.keyCode === 27) { // ESC
            $("#summary_result_div").hide();
        }
    });
}


function createProcessingRing(loc) {
    proRing = document.getElementById("processRing");
    proRing.style.visibility = "visible";

}

function deleteProcessingRing(loc) {
    proRing = document.getElementById("processRing");
    proRing.style.visibility = "hidden";

}


$(document).on('keydown', function (e) {
    if (e.keyCode === 27) { // ESC
        $("#processRing").hide();
    }
});


//To download results in the PDF





//initializeDatabase for analysing sketch maps
function initializeDatabase() {
    $.ajax({
        url: '/initializeDatabase',
        //data:{metricFileName: metricFileName, sketchFileName:sketchFileName},
        success: function (resp) {
            alert(resp);
        }
    });
}

var intermediate_results ="";

function setResults_in_output_div(resp){
   intermediate_results = resp.INTERMEDIATE_RESULT_DICT;

    $('#overAllCompleteness').text(resp.overAllCompleteness+"%");
    $('#precision').text(resp.precision);
    $('#recall').text(resp.recall);
    $('#f_score').text(resp.f_score);
    $('#sketchMapID').text(resp.sketchMapID);

    $('#toal_mm_streets').text(resp.toal_mm_streets);
    $('#totalSketchedStreets').text(resp.totalSketchedStreets);
    $('#streetCompleteness').text(resp.streetCompleteness);

    $('#total_mm_landmarks').text(resp.total_mm_landmarks);
    $('#totalSketchedLandmarks').text(resp.totalSketchedLandmarks);
    $('#landmarkCompleteness').text(resp.landmarkCompleteness);

    $('#total_mm_cityblocks').text(resp.total_mm_cityblocks);
    $('#totalSketchedCityblocks').text(resp.totalSketchedCityblocks);
    $('#cityblockCompleteness').text(resp.cityblockCompleteness);
    $('#overAllCompleteness1').text(resp.overAllCompleteness);

    $('#totalRCC11Relations_mm').text(resp.totalRCC11Relations_mm);
    $('#totalRCC11Relations').text(resp.totalRCC11Relations);
    $('#correctRCC11Relations').text(resp.correctRCC11Relations);
    $('#wrongMatchedRCC11rels').text(resp.wrongMatchedRCC11rels);
    $('#missingRCC11rels').text(resp.missingRCC11rels);
    $('#correctnessAccuracy_rcc11').text(resp.correctnessAccuracy_rcc11);

    $('#total_lO_rels_mm').text(resp.total_lO_rels_mm);
    $('#total_LO_rels_sm').text(resp.total_LO_rels_sm);
    $('#matched_LO_rels').text(resp.matched_LO_rels);
    $('#wrong_matched_LO_rels').text(resp.wrong_matched_LO_rels);
    $('#missing_LO_rels').text(resp.missing_LO_rels);
    $('#correctnessAccuracy_LO').text(resp.correctnessAccuracy_LO);

    $('#total_LR_rels_mm').text(resp.total_LR_rels_mm);
    $('#total_LR_rels_sm').text(resp.total_LR_rels_sm);
    $('#matched_LR_rels').text(resp.matched_LR_rels);
    $('#wrong_matched_LR_rels').text(resp.wrong_matched_LR_rels);
    $('#missing_LR_rels').text(resp.missing_LR_rels);
    $('#correctnessAccuracy_LR').text(resp.correctnessAccuracy_LR);

    $('#total_DE9IM_rels_mm').text(resp.total_DE9IM_rels_mm);
    $('#total_DE9IM_rels_sm').text(resp.total_DE9IM_rels_sm);
    $('#matched_DE9IM_rels').text(resp.matched_DE9IM_rels);
    $('#wrong_matched_DE9IM_rels').text(resp.wrong_matched_DE9IM_rels);
    $('#missing_DE9IM_rels').text(resp.missing_DE9IM_rels);
    $('#correctnessAccuracy_DE9IM').text(resp.correctnessAccuracy_DE9IM);

    $('#total_streetTop_rels_mm').text(resp.total_streetTop_rels_mm);
    $('#total_streetTop_rels_sm').text(resp.total_streetTop_rels_sm);
    $('#matched_streetTop_rels').text(resp.matched_streetTop_rels);
    $('#wrong_matched_streetTop_rels').text(resp.wrong_matched_streetTop_rels);
    $('#missing_streetTop_rels').text(resp.missing_streetTop_rels);
    $('#correctnessAccuracy_streetTop').text(resp.correctnessAccuracy_streetTop);

    $('#total_opra_rels_mm').text(resp.total_opra_rels_mm);
    $('#total_opra_rels_sm').text(resp.total_opra_rels_sm);
    $('#matched_opra_rels').text(resp.matched_opra_rels);
    $('#wrong_matched_opra_rels').text(resp.wrong_matched_opra_rels);
    $('#missing_opra_rels').text(resp.missing_opra_rels);
    $('#correctnessAccuracy_opra').text(resp.correctnessAccuracy_opra);
}

function downloadIntermediateResults() {
    //MMGeoJsonData = drawnItems.toGeoJSON();
    // Stringify the GeoJson
    var interMediateResult = 'text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(intermediate_results));
    // Create export
    document.getElementById('interMediateResult').setAttribute('href', 'data:' + interMediateResult);
    document.getElementById('interMediateResult').setAttribute('download', sketchFileName+'.geojson');
}