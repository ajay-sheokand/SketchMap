var sketchMap;
var sketchMaptitle;
var drawnSketchItems;
var alignSketchID=[];
var sketchOtypearray={};
var baseOtypearray={};
var alignBaseID=[];
var allDrawnSketchItems={};
var AlignmentArray = {};
var checkAlignnum;
var alignmentArraySingleMap={};
var id=-1;
var bid=-1;
var layerGroupBasemap = new L.LayerGroup();
var layerGroupBasemapGen = new L.LayerGroup();
var linearOrderingActive = false;
var linearOrdering = new L.LayerGroup();
var baseMap;
var baseMaptitle;
var drawnItems;
var addedClickBase = false;
var addedClickSketch = false;
var routeOrder = 0;
var allGenBaseMap = {};
var genbasemap;
var BooleanMissingFeature;
var BooleanEditSketchMode = false;
var allProcessedSketchMaps = {};


$(function() {

    $('.btn-link[aria-expanded="true"]').closest('.accordion-item').addClass('active');
  $('.collapse').on('show.bs.collapse', function () {
	  $(this).closest('.accordion-item').addClass('active');
	});

  $('.collapse').on('hidden.bs.collapse', function () {
	  $(this).closest('.accordion-item').removeClass('active');
	});



});








function loadFromImage(){
addedClickBase = false;
var imageList = document.getElementById('fromfile').files;
$("#loadbasemap").hide();
$("#imagemap").show();
    for (var i = 0; i < imageList.length; i++) {
        renderImageFile(imageList[i], location);
    }
}



function renderImageFile(file, location) {
    var reader = new FileReader();
    reader.readAsDataURL(file);

    reader.onload = function (e) {
        var container = L.DomUtil.get('baseMap');
        if (container != null) {
            container._leaflet_id = null;
        }
        var image = new Image();

        baseMaptitle = file.name;
        image.src = this.result;

        baseMap = new L.map('imagemap', {
            crs: L.CRS.Simple,
            pmIgnore: false
        });

        baseMap.pm.setGlobalOptions({
              snappable: true,
              snapDistance: 20,
              snapSegment: true,
              snapMiddle: true,
              preventMarkerRemoval: false,

              continueDrawing : true,
              pathOptions:{
                opacity:0.7,
                dashArray: [5, 5],
                weight: 5,
                color: "#e8913a",
                radius: 5},
              templineStyle: {
                color: "#e8913a",
                dashArray: [5, 5],
              },
              hintlineStyle: {
                color: "#e8913a",
                dashArray: [5, 5],
              }
});


 var bounds = [[0, 0], [600, 850]];

        var BMLoaded = new L.imageOverlay(image.src,bounds);
        BMLoaded.addTo(baseMap);
        baseMap.fitBounds(bounds);
        enableDefaultArrows(baseMap);
        addMouseCoordinateDisplay(baseMap, 'Base');

        drawnItems = new L.geoJson();
        layerGroupBasemap.addTo(baseMap);
        layerGroupBasemapGen.addTo(baseMap);
        drawnItems.addTo(layerGroupBasemap);




        var layerControl = new L.Control.Layers(null, {
            'Base Map': layerGroupBasemap,
            'Generalized Map': layerGroupBasemapGen,
            'Linear Ordering' : linearOrdering
        }).addTo(baseMap);
        labelButton.addTo(baseMap);
        missingFeatureButton.addTo(baseMap);

        }

$( "#loaded" ).prop( "checked", true );
$( "#loaded" ).prop( "disabled", false );

}






function isPlainPolyline(layer) {
  return (layer instanceof L.Polyline) && !(layer instanceof L.Polygon);
}

function attachAutoArrows(layer, { size = 10 } = {}) {
  if (!isPlainPolyline(layer) || layer._arrowDecorator) return;
  const map = layer._map;

  // create decorator
  const makeDecorator = () => L.polylineDecorator(layer, {
    patterns: [{
      offset: '10%',
      repeat: '25%',
      symbol: L.Symbol.arrowHead({
        pixelSize: size,
        polygon: true,
        pathOptions: {
          color: layer.options?.color || '#e8913a',
          opacity: layer.options?.opacity ?? 0.7,
          fillOpacity: layer.options?.opacity ?? 0.7,
          weight: 1
        }
      })
    }]
  }).addTo(map);

  layer._arrowDecorator = makeDecorator();

  // keep geometry in sync while editing
  const syncPath = () => layer._arrowDecorator && layer._arrowDecorator.setPaths(layer);
  layer.on('pm:edit', syncPath);
  layer.on('pm:vertexadded', syncPath); // for some Leaflet.pm versions

  // update arrow styling whenever the line style changes
  const origSetStyle = layer.setStyle;
  layer.setStyle = function(style) {
    const ret = origSetStyle.call(this, style);
    const color = this.options?.color || '#e8913a';
    const op    = this.options?.opacity ?? 0.7;
    if (this._arrowDecorator) {
      this._arrowDecorator.setPatterns([{
        offset: '10%',
        repeat: '25%',
        symbol: L.Symbol.arrowHead({
          pixelSize: size,
          polygon: true,
          pathOptions: { color, opacity: op, fillOpacity: op, weight: 1 }
        })
      }]);
      this._arrowDecorator.setPaths(this);
    }
    return ret;
  };

  // clean up if the line is removed
  layer.on('remove', () => {
    if (layer._arrowDecorator && layer._arrowDecorator._map) {
      layer._arrowDecorator._map.removeLayer(layer._arrowDecorator);
    }
    layer._arrowDecorator = null;
  });
}


function enableDefaultArrows(map) {
  map.on('layeradd', e => {
    const layer = e.layer;
    // wait until the layer is on the map so layer._map exists
    if (isPlainPolyline(layer)) {
      // ensure it runs after the layer is actually added
      setTimeout(() => attachAutoArrows(layer), 0);
    }
  });
}




function enableRouteSelect(btn) {
  baseMap.pm.disableDraw();
  baseMap.pm.disableGlobalEditMode();

  $($(btn)[0]._container).css('display','inline-flex');
  btn.button.style.boxShadow = 'inset 0 -1px 5px 2px rgba(81, 77, 77, 1)';

  if (!document.getElementById("clearRoute")) {
    $($(btn)[0]._container).append(
      $("<a style='outline: none;width: fit-content;' id='clearRoute' onclick='clearRoute()'>Clear Route</a>")
    );
  }

  drawnItems.eachLayer(function (blayer) {
    blayer.on("click", function (e) {
      if (blayer.feature.properties.otype === "Line") {
        if (!blayer.feature.properties.isRoute) {
          blayer.feature.properties.isRoute = "Yes";
          blayer.feature.properties.RouteSeqOrder = routeOrder + 1;
          blayer.setStyle({ color: "red" });
          routeOrder = routeOrder + 1;
        } else if (blayer.feature.properties.isRoute === "Yes") {
          blayer.feature.properties.isRoute = null;
          delete blayer.feature.properties.RouteSeqOrder;
          blayer.setStyle({ color: "#e8913a" });
          routeOrder = routeOrder - 1;
        }
      }
    });
  });
}

function disableRouteSelect(btn) {
  btn.button.style.boxShadow = null;
  $("#clearRoute").remove();

  drawnItems.eachLayer(function (blayer) {
    blayer.off("click"); // remove only our handler
  });
}


 var routeButton = L.easyButton({

 states: [{
            stateName: 'Select-Route-Mode-On',        // name the state
            icon:      'fa-arrow-trend-up',               // and define its properties
            title:     'SelectRouteOff',      //  its title
            onClick: function(btn, map) {
                 enableRouteSelect(btn);
                 btn.state('Select-Route-Mode-Off');    // change state on click!
            }
        }, {
            stateName: 'Select-Route-Mode-Off',
            icon:      'fa-arrow-trend-up',
            title:     'SelectRouteOn',
            onClick: function(btn, map) {
                disableRouteSelect(btn);
                btn.state("Select-Route-Mode-On");
            }
    }]


 });

 var multibuildingButton = L.easyButton({

 states: [{
            stateName: 'Select-MultiBuilding-Mode-On',        // name the state
            icon:      'fa fa-th-large',               // and define its properties
            title:     'SelectMultiBuildingOff',      // like its title
            onClick: function(btn, map) {
                $($(this)[0]._container).css('display','inline-flex');
                btn.button.style.boxShadow = 'inset 0 -1px 5px 2px rgba(81, 77, 77, 1)';


                drawnItems.eachLayer(function(blayer){

                    blayer.on('click',function(e){
                     if (blayer.feature.properties.otype == "Polygon"){
                    if (!blayer.feature.properties.isMultiBuilding){
                        blayer.feature.properties.isMultiBuilding = "Yes";
                        blayer.setStyle({
                            color: 'red'   //or whatever style you wish to use;
                        });
                    }
                    else if (blayer.feature.properties.isMultiBuilding == "Yes"){
                        blayer.feature.properties.isMultiBuilding = null ;
                        blayer.setStyle({
                            color: '#e8913a'   //or whatever style you wish to use;
                        });
                  }
                  }
                });
            });
             btn.state('Select-MultiBuilding-Mode-Off');    // change state on click!
            }
        }, {
            stateName: 'Select-MultiBuilding-Mode-Off',
            icon:      'fa fa-th-large',
            title:     'SelectMultiBuildingOn',
            onClick: function(btn, map) {
                btn.button.style.boxShadow = null;// and its callback
               drawnItems.eachLayer(function(blayer){
                blayer.off('click');
                });
                btn.state('Select-MultiBuilding-Mode-On');
            }
    }]


 });






function removeLayer(id) {
	layerGroupBasemapGen.eachLayer(function (layer) {
		if (layer._leaflet_id === id){
			layerGroupBasemapGen.removeLayer(layer)
		}
	});
}




function clearRoute(){
        drawnItems.eachLayer(function(blayer){
                        blayer.feature.properties.isRoute = null ;
                        delete blayer.feature.properties.RouteSeqOrder;
                        blayer.setStyle({
                            color: '#e8913a'   //or whatever style you wish to use;
                        });
                        routeOrder = 0;
    });
};

var labelButton = L.easyButton({
position: 'topright',
states: [{
            stateName: 'label-visible',        // name the state
            icon:      'fa-solid fa-info',               // and define its properties
            title:     'showlabels',      // like its title
            onClick: function(btn, map) {
                btn.button.style.boxShadow = 'inset 0 -1px 5px 2px rgba(81, 77, 77, 1)';
                drawnItems.eachLayer(function(blayer){
                    blayer.bindTooltip(String(blayer.feature.properties.id), {permanent:true});
                })
                btn.state('label-invisible');    // change state on click!

                if (allGenBaseMap[sketchMaptitle] != null){
                      allGenBaseMap[sketchMaptitle].eachLayer(function(glayer){
                            glayer.bindTooltip(String(glayer.feature.properties.gen_id), {permanent:true});
                       });
                }
            }
        }, {
            stateName: 'label-invisible',
            icon:      'fa-solid fa-info',
            title:     'hidelabels',
            onClick: function(btn, map) {
                 btn.button.style.boxShadow = null;// and its callback
                 drawnItems.eachLayer(function(blayer){
                    blayer.unbindTooltip();
                })
                if (allGenBaseMap[sketchMaptitle] != null){
                       allGenBaseMap[sketchMaptitle].eachLayer(function(glayer){
                        glayer.unbindTooltip();
                       });
                }
                btn.state('label-visible');
            }
    }]
});


var missingFeatureButton = L.easyButton({
position: 'topright',
states: [{
            stateName: 'missing-invisible',        // name the state
            icon:      'fa-solid fa-square-xmark',               // and define its properties
            title:     'hidemissingfeatures',      // like its title
            onClick: function(btn, map) {
                btn.button.style.boxShadow = 'inset 0 -1px 5px 2px rgba(81, 77, 77, 1)';
                btn.state('missing-visible');    // change state on click!
                BooleanMissingFeature = true;
                GenStyleLayers(allGenBaseMap[sketchMaptitle]);
                styleLayers();
            }
        }, {
            stateName: 'missing-visible',
            icon:      'fa-solid fa-square-xmark',
            title:     'showmissingfeatures',
            onClick: function(btn, map) {
                btn.button.style.boxShadow = null;// and its callback
                btn.state('missing-invisible');
                BooleanMissingFeature = false;
                GenStyleLayers(allGenBaseMap[sketchMaptitle]);
                styleLayers();

            }
    }]
});




var labelButtonSketchMap = L.easyButton({
position: 'topright',
states: [{
            stateName: 'label-visible',        // name the state
            icon:      'fa-solid fa-info',               // and define its properties
            title:     'showlabels',      // like its title
            onClick: function(btn, map) {
                btn.button.style.boxShadow = 'inset 0 -1px 5px 2px rgba(81, 77, 77, 1)';
                drawnSketchItems.eachLayer(function(slayer){
                var label = slayer.feature.properties.gen_id
                || slayer.feature.properties.sid
                || String(slayer.feature.properties.id);
                slayer.bindTooltip(label, {permanent:true});
                });
                btn.state('label-invisible');    // change state on click!
            }
        }, {
            stateName: 'label-invisible',
            icon:      'fa-solid fa-info',
            title:     'hidelabels',
            onClick: function(btn, map) {
                 btn.button.style.boxShadow = null;// and its callback
                 drawnSketchItems.eachLayer(function(slayer){
                    slayer.unbindTooltip();
                })
                btn.state('label-visible');
            }
    }]
});


var drawBM = document.getElementById('drawBM');
$('#drawBM').click(function(){

baseMap.pm.addControls({
    position: 'topleft',
    drawCircle: false,
    drawMarker: false,
    drawRectangle:false,
    drawText: false,
    drawCircleMarker:false,
    dragMode:false,
    rotateMode:false,
    cutPolygon:false,
    snappingOption:true
});

  baseMap.on('pm:snap', function(e) {
  });

  baseMap.on("pm:globaleditmodetoggled", (e) => {
  if (e.enabled && routeButton._currentState.stateName === "Select-Route-Mode-Off") {
    disableRouteSelect(routeButton);
    routeButton.state("Select-Route-Mode-On");
  }
});

baseMap.on("pm:globalremovalmodetoggled", (e) => {
  if (e.enabled && routeButton._currentState.stateName === "Select-Route-Mode-Off") {
    disableRouteSelect(routeButton);
    routeButton.state("Select-Route-Mode-On");
  }
});

  baseMap.on('pm:drawstart', function(e){
   if (routeButton._currentState.stateName === "Select-Route-Mode-Off") {
    disableRouteSelect(routeButton);
    routeButton.state("Select-Route-Mode-On");
  }

  });

baseMap.on('pm:create', function (event) {

    bid=bid+1;
    var layer = event.layer;


    layer.options.pmIgnore = false; // If the layer is a LayerGroup / FeatureGroup / GeoJSON this line is needed too
    layer.options.snapIgnore= false;
    L.PM.reInitLayer(layer);


    var feature = layer.feature = layer.feature || {}; // Initialize feature
    feature.type = feature.type || "Feature"; // Initialize feature.type
    var props = feature.properties = feature.properties || {}; // Initialize feature.properties
    props.id = bid;
    props.isRoute = null;
    if(event.shape == "Polygon"){
        props.feat_type = "Landmark"
    }
    else{
        props.feat_type = null;
    }
    props.selected=false;
    props.aligned=false;
    props.otype = event.shape;

    drawnItems.addLayer(layer);
      // 🔹 commit snapping to ALL existing base geometries (lines + polygons)
});

baseMap.on('pm:remove', function (e) {
    drawnItems.removeLayer(e.layer);
});





const actions = [];
baseMap.pm.Toolbar.changeActionsOfControl('Polygon', actions);
baseMap.pm.Toolbar.changeActionsOfControl('Polyline', actions);
baseMap.pm.Toolbar.changeActionsOfControl('CircleMarker', actions);


drawnItems.eachLayer(function(blayer){
        blayer.off('click');
        });
addedClickBase = false;
routeButton.addTo(baseMap);
multibuildingButton.addTo(baseMap);
});



async function saveBMHandler() {

  var routeArray = [];
  var routeIDArray = [];

  drawnItems.eachLayer(function (blayer) {
    if (blayer.feature.properties.isRoute == "Yes") {
      routeArray.push(blayer.feature.properties);
    }
  });

  var byrouteorder = routeArray.slice(0);

  byrouteorder.sort(function (a, b) {
    return a.RouteSeqOrder - b.RouteSeqOrder;
  });

  for (var i in byrouteorder) {
    routeIDArray.push(byrouteorder[i].id);
  }

  baseUrl = getServiceUrl('validation');


  // ✅ Wait for AJAX
  const response = await $.ajax({
    headers: { "X-CSRFToken": $.cookie("csrftoken") },
    url: `${baseUrl}/validation/validate/`,
    type: 'POST',
    data: {
      type: "metric",
      metricdata: JSON.stringify(drawnItems.toGeoJSON()),
      route: JSON.stringify(routeIDArray),
      action: 'preview'
    }
  });

  // ✅ Runs AFTER ajax completes
  if (response.audit.merge.length !== 0 || response.audit.snap.length !== 0) {

    await showpreviewModal(response.audit, "metric", routeIDArray);

  } else {

   await callApplyValidate(null, null, "metric", routeIDArray);

  }

}


$("#saveBM").click(async function () {
  try {
    await saveBMHandler();
    console.log("SaveBM finished");
  } catch (err) {
    console.error("Error:", err);
  }
});

let currentAudit = null; // store latest audit globally

function showpreviewModal(audit, type, routeArray) {

  return new Promise((resolve, reject) => {

    currentAudit = audit; // save for later

    let mergetext = "";
    let snaptext = "";

    audit.snap.forEach((s, i) => {
      snaptext += `
        <div class="modal_val_row">
          [${s.join(", ")}]
          <input type="checkbox" class="snapCheck" data-group="${i}">
        </div>
      `;
    });

    audit.merge.forEach((m, i) => {
      mergetext += `
        <div class="modal_val_row">
          [${m.merged_from.join(", ")}]
          <input type="checkbox" class="mergeCheck" data-group="${i}">
        </div>
      `;
    });

    const modal = document.getElementById("myModal");
    modal.style.display = "block";

    document.getElementById("mergeList").innerHTML = mergetext;
    document.getElementById("snapList").innerHTML = snaptext;

    makeModalMovable("myModal");

    const closeBtn = document.getElementById("closeModalBtn");
    const submitBtn = document.getElementById("modalSubmitBtn");

    // Remove old handlers (VERY important)
    closeBtn.onclick = null;
    submitBtn.onclick = null;

    // ✅ Close = cancel
    closeBtn.onclick = function () {

      modal.style.display = "none";

      reject("User closed preview modal");
    };


    // ✅ Submit = apply + resolve
    submitBtn.onclick = async function () {

      try {

        const selectedSnapGroups = [];
        const selectedMergeGroups = [];

        document
          .querySelectorAll(".snapCheck:checked")
          .forEach(chk => {
            const idx = parseInt(chk.dataset.group, 10);
            selectedSnapGroups.push(currentAudit.snap[idx]);
          });

        document
          .querySelectorAll(".mergeCheck:checked")
          .forEach(chk => {
            const idx = parseInt(chk.dataset.group, 10);
            selectedMergeGroups.push(currentAudit.merge[idx]);
          });

        // ✅ WAIT for apply ajax
        await callApplyValidate(
          selectedSnapGroups,
          selectedMergeGroups,
          type,
          routeArray
        );

        modal.style.display = "none";

        resolve(); // ✅ continue chain

      } catch (err) {

        reject(err);

      }
    };

  });
}




function callApplyValidate(selectedSnapGroups, selectedMergeGroups, type, routeArray) {

  if (type === "metric") {

    return $.ajax({   // ✅ RETURN
      headers: { "X-CSRFToken": $.cookie("csrftoken") },
      url: `${baseUrl}/validation/validate/`,
      type: 'POST',
      data: {
        type: "metric",
        metricdata: JSON.stringify(drawnItems.toGeoJSON()),
        route: JSON.stringify(routeArray),
        action: 'apply',
        merge: JSON.stringify(selectedMergeGroups),
        snap: JSON.stringify(selectedSnapGroups)
      }
    }).then(function (response) {

      console.log("success", response);

      // ✅ Run sync code AFTER ajax
      aftersuccessfulvalidationmetric(response.modifiedStreets);

      return response; // optional, but useful
    });

  }


  if (type === "sketch") {
    console.log("check here as well", routeArray)
    return $.ajax({   // ✅ RETURN
      headers: { "X-CSRFToken": $.cookie("csrftoken") },
      url: `${baseUrl}/validation/validate/`,
      type: 'POST',
      data: {
        type: "sketch",
        sketchdata: JSON.stringify(drawnSketchItems.toGeoJSON()),
        action: 'apply',
        route: JSON.stringify(routeArray),
        merge: JSON.stringify(selectedMergeGroups),
        snap: JSON.stringify(selectedSnapGroups),
        alignment: JSON.stringify(alignmentArraySingleMap)
      }
    }).then(function (response) {


      aftersuccessfulvalidationsketch(response);

      return response;
    });

  }

}



function aftersuccessfulvalidationmetric(response){
if (drawnItems != null) {
                        layerGroupBasemap.removeLayer(drawnItems);
                     }
                    drawnItems = L.geoJSON(response);
                    drawnItems.addTo(layerGroupBasemap);
                    styleLayers();
                    drawnItems.eachLayer(function(blayer){
                        blayer.off('click');
                    });

                    if (addedClickBase == false){
                        addClickBase();
                    }
                    $( "#marked" ).prop( "checked", true );
                    $( "#marked" ).prop( "disabled", false );
                    baseMap.pm.disableDraw();
                    baseMap.pm.removeControls();
                    drawnItems.setStyle({opacity:1});


                    baseMap.removeControl(routeButton);
                    baseMap.removeControl(multibuildingButton);

                    allDrawnSketchItems[baseMaptitle] = drawnItems;
}


function aftersuccessfulvalidationsketch(response){
if (drawnSketchItems != null) {
                    sketchMap.removeLayer(drawnSketchItems);
                 }
                drawnSketchItems = L.geoJSON(response.modifiedStreets);
                drawnSketchItems.addTo(sketchMap);
                
                styleLayers();
                hoverfunction();

                BooleanEditSketchMode = false;
                alignmentArraySingleMap = response.updated_alignment;
                saveSketchMap();
}


function makeModalMovable(modalId) {
    const modal = document.getElementById(modalId);

    let mouseX = 0, mouseY = 0;
    let modalX = 0, modalY = 0;

    modal.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        e.preventDefault();

        mouseX = e.clientX;
        mouseY = e.clientY;

        document.onmouseup = stopDragging;
        document.onmousemove = drag;
    }

    function drag(e) {
        e.preventDefault();

        const dx = e.clientX - mouseX;
        const dy = e.clientY - mouseY;

        mouseX = e.clientX;
        mouseY = e.clientY;

        modal.style.top = (modal.offsetTop + dy) + "px";
        modal.style.left = (modal.offsetLeft + dx) + "px";
    }

    function stopDragging() {
        document.onmouseup = null;
        document.onmousemove = null;
    }
}








function addClickBase(){
drawnItems.eachLayer(function(blayer){
        blayer.on('click',function(e){
        if(blayer.feature.properties.selected==false){
            blayer.feature.properties.selected=true;
            alignBaseID.push(blayer.feature.properties.id);
            baseOtypearray[blayer.feature.properties.id]=blayer.feature.properties.otype;
            styleLayers();
        }
        else{
            blayer.feature.properties.selected = false;
            alignBaseID= alignBaseID.filter(function(item) {
                return item !== blayer.feature.properties.id;
            })
            delete baseOtypearray[blayer.feature.properties.id];
            styleLayers();
        }
    });
    });

    addedClickBase = true;
}


   $('.thumbnail').click(function(e){


   if (BooleanEditSketchMode == true){
   saveSketchMap();
   }

   addedClickSketch = false;

     $('#slider').prop('checked', true);

        if (sketchMap != null) {
            sketchMap.remove();
        }
        var image = new Image();
        image.src = $(e.target).attr('src');

        sketchMap = new L.map('sketchimagemap', {
            crs: L.CRS.Simple
        });
        sketchMap.getContainer().focus = ()=>{};

        var bounds = [[0, 0], [600, 850]];
        var SMLoaded = new L.imageOverlay(image.src,bounds);
        SMLoaded.addTo(sketchMap);
        sketchMap.fitBounds(bounds);
        enableDefaultArrows(sketchMap);
        var layerControl = new L.Control.Layers(null, {
            'Linear Ordering' : linearOrdering
        }).addTo(sketchMap);
        sketchMaptitle = $(e.target).parent().attr("data-original-title");
            labelButtonSketchMap.addTo(sketchMap);
        if(allDrawnSketchItems.hasOwnProperty(sketchMaptitle)){
            drawnSketchItems=allProcessedSketchMaps.hasOwnProperty(sketchMaptitle)
                    ? allProcessedSketchMaps[sketchMaptitle]
                    : allDrawnSketchItems[sketchMaptitle];
                    drawnSketchItems.addTo(sketchMap);
            (!(sketchMaptitle in AlignmentArray))
            if (!(sketchMaptitle in AlignmentArray)){
                checkAlignnum = 1;
                alignmentArraySingleMap={};
         var idArray = Object.values(drawnSketchItems.toGeoJSON().features).map((item) => item.properties.id);
         id = Math.max.apply(Math, idArray);
                drawnSketchItems.eachLayer(function(slayer){
                    slayer.feature.properties.selected = false;
                    slayer.feature.properties.aligned = false;
                    slayer.feature.properties.isRoute = null;
                    if (slayer.feature.properties.group){
                        delete slayer.feature.properties.group;
                        delete slayer.feature.properties.groupID;
                    }
                    });
                drawnItems.eachLayer(function(blayer){
                    blayer.feature.properties.selected=false;
                    blayer.feature.properties.aligned=false;
                    if (blayer.feature.properties.group){
                        delete blayer.feature.properties.group;
                        delete blayer.feature.properties.groupID;
                    }
             if (blayer.feature.properties.missing){
                delete blayer.feature.properties.missing;
             }

        });
        styleLayers();
        }
        else{
            checkAlignnum = AlignmentArray[sketchMaptitle].checkAlignnum;
            alignmentArraySingleMap=AlignmentArray[sketchMaptitle];
         var idArray = Object.values(drawnSketchItems.toGeoJSON().features).map((item) => item.properties.id);
         id = Math.max.apply(Math, idArray);
             drawnSketchItems.eachLayer(function(slayer){
                  delete slayer.feature.properties.group;
                  delete slayer.feature.properties.groupID;
                $.each(alignmentArraySingleMap, function(i, item) {
                    if(alignmentArraySingleMap[i].genType == "Abstraction to show existence"){
                        if((alignmentArraySingleMap[i].SketchAlign[0]).includes(slayer.feature.properties.sid)){
                             slayer.feature.properties.group = true ;
                             slayer.feature.properties.groupID = i;
                        }
                }
                });
            });

            drawnItems.eachLayer(function(blayer){
                  delete blayer.feature.properties.group;
                  delete blayer.feature.properties.groupID;
                $.each(alignmentArraySingleMap, function(i, item) {
                    if(alignmentArraySingleMap[i].genType == "Abstraction to show existence"){
                        if((alignmentArraySingleMap[i].BaseAlign[0]).includes(blayer.feature.properties.id)){
                             blayer.feature.properties.group = true ;
                             blayer.feature.properties.groupID = i;
                        }
                }
                });
            });
         }


        restoreBaseAlignment(alignmentArraySingleMap);
        styleLayers();

        if (allGenBaseMap[sketchMaptitle] != null){
            layerGroupBasemapGen.clearLayers();
            genbasemap = allGenBaseMap[sketchMaptitle].addTo(layerGroupBasemapGen);
            GenStyleLayers(genbasemap);
         }
        }
        else{
        drawnSketchItems = new L.geoJson().addTo(sketchMap);
        alignmentArraySingleMap={};
        drawnItems.eachLayer(function(blayer){
            blayer.feature.properties.selected=false;
            blayer.feature.properties.aligned=false;
            if (blayer.feature.properties.missing){
                delete blayer.feature.properties.missing;
            }
            if (blayer.feature.properties.group){
                delete blayer.feature.properties.group;
                delete blayer.feature.properties.groupID;
             }
        });
        styleLayers();
        id = -1;
        checkAlignnum = 1;
        }


   });



    $('#drawSM').click(function(){

    BooleanEditSketchMode = true;

    if (addedClickBase == false){
           addClickBase();
    }


    if (addedClickSketch == false){
        drawnSketchItems.eachLayer(function(slayer){
        slayer.off('click');
        });
         drawnSketchItems.eachLayer(function(slayer){
                 slayer.on('click', function (e) {
                    clickFunctionforSketch(e.target);
                });
            });


    }
        sketchMap.pm.addControls({
            position: 'topleft',
            drawCircle: false,
            drawRectangle:false,
            drawMarker:false,
            drawCircleMarker:true,
            drawText:false,
            dragMode:false,
            rotateMode:false,
            cutPolygon:false,
            snappingOption:true
    });

    sketchMap.pm.setGlobalOptions({

              snappable: true,
              snapDistance: 20,
              snapSegment: true,
              snapMiddle: true,

            preventMarkerRemoval: false,
            continueDrawing: false,
            pathOptions:{
                opacity:0.7,
                weight: 5,
                color: "#e8913a",
                radius: 5,
                dashArray: [5, 5],
                },
            templineStyle: {
                color: "#e8913a",
                dashArray: [5, 5],
             },
            hintlineStyle: {
                color: "#e8913a",
                dashArray: [5, 5],
            }
        });

const sketchActions = [];
sketchMap.pm.Toolbar.changeActionsOfControl('Polygon', sketchActions);
sketchMap.pm.Toolbar.changeActionsOfControl('Polyline', sketchActions);
sketchMap.pm.Toolbar.changeActionsOfControl('CircleMarker', sketchActions);

          sketchMap.on('pm:drawstart', function (e) {
            drawnSketchItems.eachLayer(function(slayer){
                slayer.off('click');
            });
        });

        sketchMap.on('pm:create', function (event) {
                       id=id+1;
            var layer = event.layer;

            layer.options.pmIgnore = false; // If the layer is a LayerGroup / FeatureGroup / GeoJSON this line is needed too
            layer.options.snapIgnore= false;
            L.PM.reInitLayer(layer);

            var feature = layer.feature = layer.feature || {}; // Initialize feature
            feature.type = feature.type || "Feature"; // Initialize feature.type
            var props = feature.properties = feature.properties || {}; // Initialize feature.properties
            props.id = id;
            props.sid= 'S' + id;
            props.isRoute = null;
             if(event.shape == "Polygon"){
    props.feat_type = "Landmark"
    }
    else{
    props.feat_type = null;}
            props.selected = false;
            props.aligned = false;
            props.otype = event.shape;
            drawnSketchItems.addLayer(layer);
     });


       sketchMap.on('pm:drawend', function (e) {
            drawnSketchItems.eachLayer(function(slayer){
                 slayer.on('click', function (e) {
                    clickFunctionforSketch(e.target);
                });
            });
        });

        sketchMap.on('pm:remove', function (e) {
            checkIfAlignedAlready([e.layer.feature.properties.sid]);
            alignSketchID = [];
            alignBaseID = [];
            sketchOtypearray = [];
            baseOtypearray = [];
            drawnSketchItems.removeLayer(e.layer);
        });



    });



    function clickFunctionforSketch(layer){
         if(layer.feature.properties.selected==false){
            layer.feature.properties.selected = true;
            alignSketchID.push(layer.feature.properties.sid);
            sketchOtypearray[layer.feature.properties.sid]=layer.feature.properties.otype;
            styleLayers();
            }
        else{
            layer.feature.properties.selected = false;
            alignSketchID= alignSketchID.filter(function(item) {
                return item !== layer.feature.properties.sid;
            });
            delete sketchOtypearray[layer.feature.properties.sid];
            styleLayers();
        }

    addedClickSketch = true;

    }



    $('#alignbutton').click(function(){
        checkIfAlignedAlready(alignSketchID);
        drawnItems.eachLayer(function(blayer){
        if (alignBaseID.includes(blayer.feature.properties.id)){
        blayer.feature.properties.aligned = true;
        blayer.feature.properties.selected = false;
        styleLayers();
        if (blayer.feature.properties.isRoute == "Yes"){
            drawnSketchItems.eachLayer(function(slayer){
                if (alignSketchID.includes(slayer.feature.properties.sid)){
                slayer.feature.properties.isRoute = "Yes";
                slayer.feature.properties.SketchRouteSeqOrder = blayer.feature.properties.RouteSeqOrder;
              }

            });
        }
        }
        });
        drawnSketchItems.eachLayer(function(slayer){
        if (alignSketchID.includes(slayer.feature.properties.sid)){
        slayer.feature.properties.aligned = true;
        slayer.feature.properties.selected = false;
        styleLayers();
        }
        });

        align(alignBaseID,alignSketchID,checkAlignnum,sketchOtypearray,baseOtypearray);
        checkAlignnum=checkAlignnum+1;
    });




    function align(BID,SID,num,sketchtype,basetype){
       var degreeOfGeneralization;
       var BaseAlign={};
       var SketchAlign={};
            BaseAlign[0]=BID;
            SketchAlign[0]=SID;
       degreeOfGeneralization=(BID.length - SID.length)/BID.length;
       var genType;
       (async () => {
          genType = await predictGeneralization(sketchtype,basetype);
          if(genType!= "Generalization Not possible") {
          alignmentArraySingleMap[num]={BaseAlign,SketchAlign,genType,degreeOfGeneralization};
          }
          if(genType == "Abstraction to show existence"){
                drawnItems.eachLayer(function(blayer){
                       if(BID.includes(blayer.feature.properties.id)){
                            blayer.feature.properties.group = true;
                            blayer.feature.properties.groupID = num;
                       }
                });

                drawnSketchItems.eachLayer(function(slayer){
                       if(SID.includes(slayer.feature.properties.sid)){
                            slayer.feature.properties.group = true;
                            slayer.feature.properties.groupID = num;
                       }
                });
             }
        })()

       alignBaseID=[];
       alignSketchID=[];
       sketchOtypearray = {};
       baseOtypearray = {};
       hoverfunction();
    }
    var hoverarray = [];


    function hoverfunction(){

    drawnSketchItems.eachLayer(function(slayer){
    slayer.on('mouseover', function() {
      if (slayer.feature.properties.aligned == true){
      for (i in alignmentArraySingleMap){
           if (alignmentArraySingleMap[i].SketchAlign[0].includes(slayer.feature.properties.sid)){
               hoverarray.push(alignmentArraySingleMap[i].BaseAlign[0]);
               hoverarray.push(alignmentArraySingleMap[i].SketchAlign[0]);
               break;
           }
      }
    }

    changestyleOnHover(hoverarray);
    });

    slayer.on('mouseout', function() {
    hoverarray=[];
    styleLayers();
    });
       });
    }


  function predictGeneralization(sketchtype,basetype){
        if (checktype(sketchtype,basetype)){
            switch (sketchtype[Object.keys(sketchtype)[0]]){
                case "Line":
                    switch (checkgroupalign(sketchtype,basetype)){
                        case "one-one":
                            return "No generalization";
                            break;
                        case "one-many":
                            return predictGenSingleLine(sketchtype,basetype);
                            break;
                        case "many-many":
                            return "Abstraction to show existence";
                            break;
                        case "two-one":
                            return "Abstraction to show existence - street stub";
                            break;
                    }
                    break;
                case "Polygon":
                    switch (checkgroupalign(sketchtype,basetype)){
                        case "one-one":
                            return "No generalization";
                            break;
                        case "one-many":
                            return "Amalgamation";
                            break;
                        case "many-many":
                            return "Abstraction to show existence";
                            break;
                    }
                    break;
            }

        }
        else if(sketchtype[Object.keys(sketchtype)[0]]=="CircleMarker" || basetype[Object.keys(basetype)[0]]=="CircleMarker"){
            return "Collapse";
        }
        else{
        alert("Error Cannot Align :Basemap feature type is different from sketchmap feature type");
        return "Generalization Not possible"
        }
    }

    function checktype(sketchtype,basetype){
     const allOtype = {...sketchtype,...basetype}
     return new Set(Object.values(allOtype)).size === 1;
    }

    function checkgroupalign(sketchtype,basetype){
        if (Object.keys(sketchtype).length == 1 && Object.keys(basetype).length==1){
            return "one-one";
        }
        if (Object.keys(sketchtype).length == 1 && Object.keys(basetype).length > 1){
            return "one-many";
        }
        if(Object.keys(sketchtype).length > 1 && Object.keys(basetype).length>1){
            return "many-many";
        }
        if(Object.keys(sketchtype).length == 2 && Object.keys(basetype).length == 1){
            return "two-one";
        }
    }


    function changestyleOnHover(Array){
    Array=Array.flat();
     drawnItems.eachLayer(function(blayer){
     for (i in Array){
        if (blayer.feature.properties.id==Array[i]){
                blayer.setStyle({
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


   function saveSketchMap(){
    console.log("calledSave");
     if (sketchMap){
        sketchMap.pm.removeControls();
        sketchMap.off('pm:drawstart');
        sketchMap.off('pm:drawend');
        sketchMap.off('pm:create');
        }


     if (drawnSketchItems){
     drawnSketchItems.eachLayer(function(slayer){
        slayer.off('click');
        });

     drawnItems.eachLayer(function(blayer){
        blayer.off('click');
        });
     addedClickBase = false;
     addedClickSketch = false;


     allDrawnSketchItems[sketchMaptitle]=drawnSketchItems;
      drawnSketchItems.setStyle({opacity:1});
      AlignmentArray[sketchMaptitle]=alignmentArraySingleMap;
      AlignmentArray[sketchMaptitle].checkAlignnum = checkAlignnum;
   }
   }





async function saveSMHandler() {
 if (!drawnSketchItems) {
    return;
  }
  syncRouteOrderFromBaseToSketch();
  // new code
var sketchRouteArray = [];

drawnSketchItems.eachLayer(function (slayer) {
    if (slayer.feature.properties.isRoute == "Yes") {
        sketchRouteArray.push(slayer.feature.properties);
    }
});

var sketchRouteGroups = {};
sketchRouteArray.forEach(function(props) {
    var order = props.SketchRouteSeqOrder;
    if (!sketchRouteGroups[order]) sketchRouteGroups[order] = [];
    sketchRouteGroups[order].push(props.id);
});

var sketchIDArray = Object.keys(sketchRouteGroups)
    .map(Number)
    .sort((a, b) => a - b)
    .map(order => sketchRouteGroups[order]);


  console.log("sketch route", sketchIDArray);
  baseUrl = getServiceUrl('validation');

  // ✅ Wait for preview ajax
  const response = await $.ajax({
    headers: { "X-CSRFToken": $.cookie("csrftoken") },
    url: `${baseUrl}/validation/validate/`,
    type: 'POST',
    data: {
      type: "sketch",
      sketchdata: JSON.stringify(drawnSketchItems.toGeoJSON()),
      alignment: JSON.stringify(alignmentArraySingleMap),
      route: JSON.stringify(sketchIDArray),
      action: 'preview'
    }
  });



  if (response.audit.merge.length !== 0 || response.audit.snap.length !== 0) {


    await showpreviewModal(response.audit, "sketch", sketchIDArray);
  } else {


    await callApplyValidate(null, null, "sketch", sketchIDArray);
  }

  return response;
}

    $('#saveSM').click(async function(){
 try {
    await saveSMHandler();
    console.log("saveSM finished");
  } catch (err) {
    console.error("saveSM error:", err);
  }

    });


function restoreBaseAlignment(alignmentArraySingleMap){

drawnItems.eachLayer(function(blayer){
    blayer.feature.properties.aligned = false;
    blayer.feature.properties.selected = false;
    $.each(alignmentArraySingleMap, function(i, item) {
        if(alignmentArraySingleMap[i].BaseAlign != null && (alignmentArraySingleMap[i].BaseAlign[0]).includes(blayer.feature.properties.id)){
            blayer.feature.properties.aligned=true;
        }
    });
})

hoverfunction();
}

function checkIfAlignedAlready(alignSketchID){

for (i in alignmentArraySingleMap){

if (alignmentArraySingleMap[i].SketchAlign){
if (alignmentArraySingleMap[i].SketchAlign[0].some(item => alignSketchID.includes(item))){
 drawnSketchItems.eachLayer(function (slayer){
   if ((alignmentArraySingleMap[i].SketchAlign[0]).includes(slayer.feature.properties.sid)){
    slayer.feature.properties.aligned = false;
    slayer.feature.properties.isRoute = null;
    slayer.feature.properties.group = null;
   }
 });
     drawnItems.eachLayer(function(blayer){
     if((alignmentArraySingleMap[i].BaseAlign != null) && (alignmentArraySingleMap[i].BaseAlign[0]).includes(blayer.feature.properties.id)){
        blayer.feature.properties.aligned=false;
     }
     });
     delete alignmentArraySingleMap[i];
     styleLayers();
 }
}
}

}


function styleLayers(){

if (drawnSketchItems){

    drawnSketchItems.eachLayer(function(slayer){
            if (slayer.feature.properties.selected){
                slayer.setStyle({weight:12});
            }
            if (!slayer.feature.properties.selected && !slayer.feature.properties.aligned && !slayer.feature.properties.isRoute){
                slayer.setStyle({opacity:0.7,weight: 5,color: "#e8913a",dashArray: [5, 5]});
            }
            if (!slayer.feature.properties.selected && slayer.feature.properties.aligned && !slayer.feature.properties.isRoute){
                slayer.setStyle({opacity:0.7,weight: 5,color: "#e8913a",dashArray: null});
            }
            if (!slayer.feature.properties.selected && !slayer.feature.properties.aligned && slayer.feature.properties.isRoute=="Yes"){
                slayer.setStyle({opacity:0.7,weight: 5,color: "red",dashArray: [5, 5]});
            }
            if(!slayer.feature.properties.selected && slayer.feature.properties.aligned && slayer.feature.properties.isRoute=="Yes"){
                slayer.setStyle({opacity:0.7,weight: 5,color: "red",dashArray: null,});
            }

     });
}

if (drawnItems){
if (BooleanMissingFeature){
    drawnItems.eachLayer(function(blayer){

         if (blayer.feature.properties.selected){
                blayer.setStyle({weight:12});
            }
            if (!blayer.feature.properties.selected && !blayer.feature.properties.aligned && (!blayer.feature.properties.isRoute || !blayer.feature.properties.isMultiBuilding)){
                blayer.setStyle({opacity:0,weight: 5,color: "#e8913a",dashArray: [5, 5]});
               if(blayer.getTooltip()){
                blayer.getTooltip().getElement().style.opacity = '0';
                }
            }
            if (!blayer.feature.properties.selected && blayer.feature.properties.aligned && (!blayer.feature.properties.isRoute || !blayer.feature.properties.isMultiBuilding)){
                blayer.setStyle({opacity:0.7,weight: 5,color: "#e8913a",dashArray: null});
            }
            if (!blayer.feature.properties.selected && !blayer.feature.properties.aligned && (blayer.feature.properties.isRoute=="Yes" || blayer.feature.properties.isMultiBuilding)){
                blayer.setStyle({opacity:0,weight: 5,color: "red",dashArray: [5, 5]});
               if(blayer.getTooltip()){
                blayer.getTooltip().getElement().style.opacity = '0';
                }
            }
            if(!blayer.feature.properties.selected && blayer.feature.properties.aligned &&( blayer.feature.properties.isRoute=="Yes" || blayer.feature.properties.isMultiBuilding)){
                blayer.setStyle({opacity:0.7,weight: 5,color: "red",dashArray: null,});
            }
     });
    }
    else{
     drawnItems.eachLayer(function(blayer){

         if (blayer.feature.properties.selected){
                blayer.setStyle({weight:12});
            }
            if (!blayer.feature.properties.selected && !blayer.feature.properties.aligned && (!blayer.feature.properties.isRoute || !blayer.feature.properties.isMultiBuilding)){
                blayer.setStyle({opacity:0.7,weight: 5,color: "#e8913a",dashArray: [5, 5]});
                if(blayer.getTooltip()){
                blayer.getTooltip().getElement().style.opacity = '1';
                }
            }
            if (!blayer.feature.properties.selected && blayer.feature.properties.aligned && (!blayer.feature.properties.isRoute || !blayer.feature.properties.isMultiBuilding)){
                blayer.setStyle({opacity:0.7,weight: 5,color: "#e8913a",dashArray: null});
            }
            if (!blayer.feature.properties.selected && !blayer.feature.properties.aligned && (blayer.feature.properties.isRoute=="Yes" || blayer.feature.properties.isMultiBuilding)){
                blayer.setStyle({opacity:0.7,weight: 5,color: "red",dashArray: [5, 5]});
                if(blayer.getTooltip()){
                blayer.getTooltip().getElement().style.opacity = '1';
                }
            }
            if(!blayer.feature.properties.selected && blayer.feature.properties.aligned &&( blayer.feature.properties.isRoute=="Yes" || blayer.feature.properties.isMultiBuilding)){
                blayer.setStyle({opacity:0.7,weight: 5,color: "red",dashArray: null,});
            }
     });


    }
    }
}


function predictGenSingleLine(sketchtype, basetype) {
    var datatobesent = new L.geoJson();
    drawnItems.eachLayer(function(blayer) {
      if ((Object.keys(basetype).map(Number)).includes(blayer.feature.properties.id)) {
        datatobesent.addData(blayer.toGeoJSON());
      }
    });
    var coordinates = [];
    for (var i = 0; i < datatobesent.toGeoJSON().features.length; i++) {
    var feature = datatobesent.toGeoJSON().features[i];
    if (feature.geometry.type === "LineString") {
        coordinates.push(feature.geometry.coordinates);
    }
    }
    var result = checkOverlap(coordinates[0], coordinates[1]);
    return result
  }

function checkOverlap(line1, line2) {
var commonPair = false;
for (var i = 0; i < line1.length; i++) {
    for (var j = 0; j < line2.length; j++) {
    if (line1[i][0] == line2[j][0] && line1[i][1] == line2[j][1]) {
        commonPair = true;
        break;
    }
    }
    if (commonPair) {
    break;
    }
}
if (commonPair) {
    return "OmissionMerge";
} else {
    return "Abstraction to show existence";
}
}

 function toggleMenu(menuId) {
        // Hide all other dropdowns before opening the clicked one
        document.querySelectorAll('.menu-options').forEach(menu => {
            if (menu.id !== menuId) {
                menu.style.display = "none";
                menu.style.opacity = "0";
                menu.style.transform = "translateY(-10px)";
            }
        });

        let menu = document.getElementById(menuId);
        let menuButton = menu.parentElement.querySelector(".menu-title");

        // Toggle dropdown visibility
        if (menu.style.display === "block") {
            menu.style.opacity = "0";
            menu.style.transform = "translateY(-10px)";
            setTimeout(() => menu.style.display = "none", 300);
        } else {
            menu.style.display = "block";
            menu.style.width = `${menuButton.offsetWidth}px`;
            setTimeout(() => {
                menu.style.opacity = "1";
                menu.style.transform = "translateY(0)";
            }, 10);
        }
    }

    // Hide dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.menu-container')) {
            document.querySelectorAll('.menu-options').forEach(menu => {
                menu.style.opacity = "0";
                menu.style.transform = "translateY(-10px)";
                setTimeout(() => menu.style.display = "none", 300);
            });
        }
    });


document.querySelectorAll('.menu-options li').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.menu-options').forEach(menu => {
            menu.style.opacity = "0";
            menu.style.transform = "translateY(-10px)";
            setTimeout(() => menu.style.display = "none", 300);
        });
    });
});



function addMouseCoordinateDisplay(map, label) {
    // label is just to distinguish multiple maps, e.g. "Base" / "Sketch"
    var coordControl = L.control({ position: 'topleft' });

    coordControl.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'leaflet-coord-display');
        div.id = 'coord-display-' + label;
        div.innerHTML = label + ': x: -, y: -';
        return div;
    };

    coordControl.addTo(map);

    map.on('mousemove', function(e) {


    // pixel coords inside map container (often integers)
    const pt = map.latLngToContainerPoint(e.latlng);
    // your displayed values
    var x = e.latlng.lat.toFixed(10);
    var y = e.latlng.lng.toFixed(10);

    var el = document.getElementById('coord-display-' + label);
    if (el) {
        el.innerHTML = label + ': x: ' + x + ', y: ' + y;
    }
    });

    map.on('mouseout', function() {
        var el = document.getElementById('coord-display-' + label);
        if (el) {
            el.innerHTML = label + ': x: -, y: -';
        }
    });
}



function syncRouteOrderFromBaseToSketch() {

    if (!alignmentArraySingleMap) return;

    // loop over each alignment group
    Object.keys(alignmentArraySingleMap).forEach(key => {

        const alignObj = alignmentArraySingleMap[key];

        if (!alignObj.BaseAlign || !alignObj.SketchAlign) return;

        const baseIDs = alignObj.BaseAlign[0];
        const sketchIDs = alignObj.SketchAlign[0];

        let routeOrder = null;

        // 🔹 find route order from base layer
        drawnItems.eachLayer(function (blayer) {

            const id = blayer.feature.properties.id;

            if (baseIDs.includes(id)) {

                if (blayer.feature.properties.RouteSeqOrder !== undefined) {
                    routeOrder = blayer.feature.properties.RouteSeqOrder;
                }

            }

        });

        // 🔹 assign to sketch layer
        if (routeOrder !== null) {

            drawnSketchItems.eachLayer(function (slayer) {

                const sid = slayer.feature.properties.sid;

                if (sketchIDs.includes(sid)) {

                    slayer.feature.properties.isRoute = "Yes";
                    slayer.feature.properties.SketchRouteSeqOrder = routeOrder;

                }

            });

        }

    });

}