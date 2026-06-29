/*function loadfromosm(){
$("#map").show();
}




var merging_degreeOfgeneralisation = 0;
var existence_degreeOfgeneralisation = 0;
var connectivity_degree_of_generalisation = 0;
var junctionmerge_degree_of_generalisation = 0;
var roundabout_collapse_degree_of_generalisation = 0;
var amalgamation_degree_of_generalisation = 0;
var collapse_degree_of_generalisation = 0;
var houseexistence_degreeOfgeneralisation = 0;
var regionalization_degree_of_generalisation = 0;

var map;
var boundingboxCount = 0;
var latlng;
var layer;
var layerGroup_raw_map = new L.LayerGroup();
var layerGroup_experiment_map = new L.LayerGroup();
var layerGroup_generalised_map = new L.LayerGroup();
var raw_geojson_edges;
var raw_geojson_nodes;
var raw_geojson_polygon;
var raw_geojson_region;
var geojson_edges;
var geojson_nodes;
var geojson_polygon;
var geojson_region;
var boolean_check_control_street=false;
var boolean_check_control_buildings=false;
var layer_temp;
var button;
var save_button;
var delete_button;
var geojson_polygon_selected;
var geojson_edges_selected;
var geojson_region_selected;
var m_noOfobjects;
var s_noOfobjects;
var degree_of_generalisation;
var layerGroup_street = new L.LayerGroup();
var layerGroup_buildings = new L.LayerGroup();
var layerGroup_openspaces = new L.LayerGroup();
var featuresbeforegen,featuresaftergen;



var styleForexperiment = {
                    "color": "#000099",
                    "weight" : 4,
                    "opacity":0.65
};

var styleForexperiment_polygon = {
                    "color": "#000099",
                    "weight" : 2
};




//styling for nodes in the street network
 var geojsonMarkerOptions = {
                      radius: 4,
                      fillColor: "#ff7800",
                      color: "#000",
                      weight: 1,
                      opacity: 1,
                      fillOpacity: 0.8
                };

//adding base map layer to leaflet
(function() {
    map = L.map('map',

    {editable:true}).setView([51.9387371, 7.6069584], 13);
})();


L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);


//layerGroup that contains the street and landmark and houses
layerGroup_raw_map.addTo(map);
layerGroup_experiment_map.addTo(map);
layerGroup_generalised_map.addTo(map);
layerGroup_street.addTo(map);
layerGroup_buildings.addTo(map);
layerGroup_openspaces.addTo(map);



// Leaflet geosearch
//var GeoSearchControl = window.GeoSearch.GeoSearchControl;
//var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;
//var provider = new OpenStreetMapProvider();

//var searchControl = new GeoSearchControl({
  //provider: provider,
  //showMarker: false,
//});

//map.addControl(searchControl);


//for drawing bounding box to fetch data from osm
var boundingbox = new L.FeatureGroup();
map.addLayer(boundingbox);

var boundingbox_bbox = new L.FeatureGroup();
map.addLayer(boundingbox_bbox);

var drawControl = new L.Control.Draw({
         draw: {
             rectangle: false,
             polyline: true,
             marker: true,
             polygon: {
                shapeOptions:{
                    fill: true,
                    weight: 2,
                    color: '#0b2375'
                    }},
             circle: false
         },

     });

map.addControl(drawControl);

map.on('draw:drawstart', function (e) {
            boundingboxCount = boundingboxCount + 1;
        });


map.on('draw:created', function (e){
     layer = e.layer;
     layer.editing.enable();
       if (boundingboxCount >= 1){
         boundingbox.clearLayers();
      }
      boundingbox.addLayer(layer);
});

function experiment_map(){



removeOtherControls();

var myStyle = {
                    "color": "",
                    "weight": 5,
                    "opacity": 0.65
           };

var selected_geojson_edges = [];
var selected_geojson_polygon = [];
var selected_geojson_region = [];
var edges_node_id = [];
button = L.easyButton('fa-mouse-pointer', function(){
    raw_geojson_edges.eachLayer(function (layer) {
        layer.on('click', function (e) {
                          e.target.setStyle(myStyle);
                          selected_geojson_edges.push(e.target.feature);
                          edges_node_id.push(e.target.feature.properties.from,e.target.feature.properties.to);
                        });
    });

    raw_geojson_polygon.eachLayer(function(layer){
        layer.on('click',function (e){
                e.target.setStyle(myStyle);
                selected_geojson_polygon.push(e.target.feature);
        });
    });


   /* raw_geojson_region.eachLayer(function(layer){
        layer.on('click',function (e){
                e.target.setStyle(myStyle);
                selected_geojson_region.push(e.target.feature);
                console.log(e.target.feature);
        });
    });*/

/*});
button.addTo(map);








function is_end_node(node_id){
var count_edges_node_id = _.countBy(edges_node_id);
    if   (count_edges_node_id[node_id]>=3 || count_edges_node_id[node_id]==1){
        return true;
    }
    else{
        return false;
    }
}

function is_connecting_node(node_id){
var count_edges_node_id = _.countBy(edges_node_id);
    if   (count_edges_node_id[node_id]==2){
        return true;
    }
    else{
        return false;
    }
}


save_button = L.easyButton('fa-save',function(){
var new_merged_selected_geojson_edges = [];
var linedirection = [];
var new_merged_lineString = [];
var crossed_lines = [];
var merged_line_from ;
var merged_line_to;
var lines_to_be_removed = [];
var sliced_selected_geojson_edges = [];
var index = 0;
for(var i in selected_geojson_edges){
if (is_end_node(selected_geojson_edges[i].properties.from) && !( crossed_lines.includes(selected_geojson_edges[i]))){
 crossed_lines.push(selected_geojson_edges[i]);
 merged_line_from = selected_geojson_edges[i].properties.from;
 new_merged_lineString.push(selected_geojson_edges[i].geometry.coordinates);
 linedirection.push(0);
 lines_to_be_removed.push(selected_geojson_edges[i]);
 remove_lines(lines_to_be_removed);
 if(is_end_node(selected_geojson_edges[i].properties.to)){
    merged_line_to = selected_geojson_edges[i].properties.to;
    complete_lineString();
}
else{
for (var o=0; o < sliced_selected_geojson_edges.length;o++){
if((sliced_selected_geojson_edges[o].properties.from == selected_geojson_edges[i].properties.to || sliced_selected_geojson_edges[o].properties.to == selected_geojson_edges[i].properties.to) && is_connecting_node(selected_geojson_edges[i].properties.to)){
add_next_nodes(selected_geojson_edges[i].properties.to,sliced_selected_geojson_edges[o]);
o = sliced_selected_geojson_edges.length + 100;
}}
}
} else{
if (is_end_node(selected_geojson_edges[i].properties.to) && !( crossed_lines.includes(selected_geojson_edges[i]))){
 crossed_lines.push(selected_geojson_edges[i]);
 merged_line_from = selected_geojson_edges[i].properties.to;
 new_merged_lineString.push(selected_geojson_edges[i].geometry.coordinates);
 linedirection.push(1);
 lines_to_be_removed.push(selected_geojson_edges[i]);
 remove_lines(lines_to_be_removed);
 if(is_end_node(selected_geojson_edges[i].properties.from)){
 merged_line_to = selected_geojson_edges[i].properties.from;
 complete_lineString();
 }
 else{
 for (var o=0; o < sliced_selected_geojson_edges.length;o++){
    if((sliced_selected_geojson_edges[o].properties.from == selected_geojson_edges[i].properties.from || sliced_selected_geojson_edges[o].properties.to == selected_geojson_edges[i].properties.from) && is_connecting_node(selected_geojson_edges[i].properties.from)){
        add_next_nodes(selected_geojson_edges[i].properties.from,sliced_selected_geojson_edges[o]);
        o = sliced_selected_geojson_edges.length + 100;
}}
 }
}}
}


function remove_lines(lines_to_be_removed){
sliced_selected_geojson_edges = [];
    for (var i = 0;i < selected_geojson_edges.length;i++){
        if(!(lines_to_be_removed.includes(selected_geojson_edges[i]))){
            sliced_selected_geojson_edges.push(selected_geojson_edges[i]);
    }
}
}



function add_next_nodes(current_node,sliced_selected_geojson_edges_single){
if(is_connecting_node(current_node)){
if(current_node==sliced_selected_geojson_edges_single.properties.from){
new_merged_lineString.push(sliced_selected_geojson_edges_single.geometry.coordinates);
linedirection.push(0);
crossed_lines.push(sliced_selected_geojson_edges_single);
current_node=sliced_selected_geojson_edges_single.properties.to;
lines_to_be_removed.push(sliced_selected_geojson_edges_single);
remove_lines(lines_to_be_removed);
if(is_end_node(current_node)){
merged_line_to = current_node;
complete_lineString();
}
else{
for (var o = 0; o < sliced_selected_geojson_edges.length; o++){
if((sliced_selected_geojson_edges[o].properties.from == current_node || sliced_selected_geojson_edges[o].properties.to == current_node) && is_connecting_node(current_node)){
add_next_nodes(current_node,sliced_selected_geojson_edges[o]);
o = sliced_selected_geojson_edges.length + 100;
}}
}
}else{
if(current_node==sliced_selected_geojson_edges_single.properties.to){
linedirection.push(1);
new_merged_lineString.push(sliced_selected_geojson_edges_single.geometry.coordinates);
crossed_lines.push(sliced_selected_geojson_edges_single);
current_node=sliced_selected_geojson_edges_single.properties.from;
lines_to_be_removed.push(sliced_selected_geojson_edges_single);
remove_lines(lines_to_be_removed);
if(is_end_node(current_node)){
merged_line_to = current_node;
complete_lineString();
}
else{
for (var o =0;o<sliced_selected_geojson_edges.length;o++){
if((sliced_selected_geojson_edges[o].properties.from == current_node || sliced_selected_geojson_edges[o].properties.to == current_node) && is_connecting_node(current_node)){
add_next_nodes(current_node,sliced_selected_geojson_edges[o]);
 o = sliced_selected_geojson_edges.length + 100;
}}
}
}
}
}
}

function complete_lineString(){
var indexOf1 = [];
if(linedirection.includes(1)){
for (var i in linedirection){
    if (linedirection[i] == 1){
        indexOf1.push(parseInt(i));

    }
}


for (var i in indexOf1){
var j = indexOf1[i];
new_merged_lineString[j] = new_merged_lineString[j].reverse();
}
}

new_merged_lineString = _.flatten(new_merged_lineString,true);
new_merged_selected_geojson_edges.push(turf.lineString(new_merged_lineString,{from: merged_line_from,to: merged_line_to}));
new_merged_lineString = [];
linedirection = [];
}

             geojson_edges = L.geoJSON(new_merged_selected_geojson_edges, {
                     style: myStyle,
                     onEachFeature: function(feature,layer){
                      layer.bindPopup('<p>From: ' + feature.properties.from + 'To:' + feature.properties.to + '</p>');
                      }}).addTo(map);

             geojson_polygon = L.geoJSON(selected_geojson_polygon, {
                     style: myStyle,
                     onEachFeature: function(feature,layer){
                      }}).addTo(map);

               geojson_region = L.geoJSON(selected_geojson_region, {
                     style: myStyle,
                     onEachFeature: function(feature,layer){
                      }}).addTo(map);
              layerGroup_experiment_map.addLayer(geojson_polygon);
              layerGroup_buildings.addLayer(geojson_polygon);
              layerGroup_experiment_map.addLayer(geojson_edges);
              layerGroup_street.addLayer(geojson_edges);
              layerGroup_experiment_map.addLayer(geojson_region);
              layerGroup_openspaces.addLayer(geojson_region);


});
save_button.addTo(map);
}




 var options = {
        position: 'topleft',
        drawMarker: true,
        drawPolyliine: true,
        drawRectangle: false,
        drawPolygon: true,
        drawCircleMarker: false,
        drawCircle: false,
        cutPolygon: false,
        editMode: true,
        removalMode: true,
        dragMode: false,
        snappingOption: true,
    };



var download_button = L.easyButton( 'fa-cloud-download-alt', function(){
                                latlng = layer.getLatLngs();
                                var polygon_lnglat = [];

                                for (var i in latlng[0]){
                                 polygon_lnglat.push([latlng[0][i].lng,latlng[0][i].lat]);
                                }

                                $.ajax({type: 'POST',
                                       headers: { "X-CSRFToken": $.cookie("csrftoken") },
                                       url: 'fetch_data/',                            // some data url
                                       data: {polygon_lnglat},       // some params
                                       success: function (response) {
                                                   boundingbox.clearLayers();
                                                   request_for_fetching_data("streetnetwork_simplified_edges");
                                                   request_for_fetching_data("streetnetwork_simplified_nodes");
                                                   request_for_fetching_data("buildings");
                                                //   request_for_fetching_data("openregions");
                                                   map.removeControl(drawControl);
                                                   map.removeControl(download_button);

                                       }
                               });

});
download_button.addTo(map);


function geometric_merging() {

removeOtherControls();

var myStyle = {
                    "color": "#006400",
                    "weight": 5,
                    "opacity": 0.65
           };

var selected_geojson_edges = [];
var selected_geojson_polygon = [];
var selected_geojson_region = [];
var edges_node_id = [];
button = L.easyButton('fa-mouse-pointer', function(){
    geojson_edges.eachLayer(function (layer) {
        layer.on('click', function (e) {
                          e.target.setStyle(myStyle);
                          selected_geojson_edges.push(e.target.feature);
                          edges_node_id.push(e.target.feature.properties.from,e.target.feature.properties.to);

                        });
    });


});
button.addTo(map);




function is_end_node(node_id){
var count_edges_node_id = _.countBy(edges_node_id);
    if   (count_edges_node_id[node_id]>=3 || count_edges_node_id[node_id]==1){
        return true;
    }
    else{
        return false;
    }
}

function is_connecting_node(node_id){
var count_edges_node_id = _.countBy(edges_node_id);
    if   (count_edges_node_id[node_id]==2){
        return true;
    }
    else{
        return false;
    }
}


save_button = L.easyButton('fa-save',function(){
var new_merged_selected_geojson_edges = [];
var linedirection = [];
var new_merged_lineString = [];
var crossed_lines = [];
var merged_line_from ;
var merged_line_to;
var lines_to_be_removed = [];
var sliced_selected_geojson_edges = [];
var index = 0;
for(var i in selected_geojson_edges){
if (is_end_node(selected_geojson_edges[i].properties.from) && !( crossed_lines.includes(selected_geojson_edges[i]))){
 crossed_lines.push(selected_geojson_edges[i]);
 merged_line_from = selected_geojson_edges[i].properties.from;
 new_merged_lineString.push(selected_geojson_edges[i].geometry.coordinates);
 linedirection.push(0);
 lines_to_be_removed.push(selected_geojson_edges[i]);
 remove_lines(lines_to_be_removed);
 if(is_end_node(selected_geojson_edges[i].properties.to)){
    merged_line_to = selected_geojson_edges[i].properties.to;
    complete_lineString();
}
else{
for (var o=0; o < sliced_selected_geojson_edges.length;o++){
if((sliced_selected_geojson_edges[o].properties.from == selected_geojson_edges[i].properties.to || sliced_selected_geojson_edges[o].properties.to == selected_geojson_edges[i].properties.to) && is_connecting_node(selected_geojson_edges[i].properties.to)){
add_next_nodes(selected_geojson_edges[i].properties.to,sliced_selected_geojson_edges[o]);
o = sliced_selected_geojson_edges.length + 100;
}}
}
} else{
if (is_end_node(selected_geojson_edges[i].properties.to) && !( crossed_lines.includes(selected_geojson_edges[i]))){
 crossed_lines.push(selected_geojson_edges[i]);
 merged_line_from = selected_geojson_edges[i].properties.to;
 new_merged_lineString.push(selected_geojson_edges[i].geometry.coordinates);
 linedirection.push(1);
 lines_to_be_removed.push(selected_geojson_edges[i]);
 remove_lines(lines_to_be_removed);
 if(is_end_node(selected_geojson_edges[i].properties.from)){
 merged_line_to = selected_geojson_edges[i].properties.from;
 complete_lineString();
 }
 else{
 for (var o=0; o < sliced_selected_geojson_edges.length;o++){
    if((sliced_selected_geojson_edges[o].properties.from == selected_geojson_edges[i].properties.from || sliced_selected_geojson_edges[o].properties.to == selected_geojson_edges[i].properties.from) && is_connecting_node(selected_geojson_edges[i].properties.from)){
        add_next_nodes(selected_geojson_edges[i].properties.from,sliced_selected_geojson_edges[o]);
        o = sliced_selected_geojson_edges.length + 100;
}}
 }
}}
}


function remove_lines(lines_to_be_removed){
sliced_selected_geojson_edges = [];
    for (var i = 0;i < selected_geojson_edges.length;i++){
        if(!(lines_to_be_removed.includes(selected_geojson_edges[i]))){
            sliced_selected_geojson_edges.push(selected_geojson_edges[i]);
    }
}
}



function add_next_nodes(current_node,sliced_selected_geojson_edges_single){
if(is_connecting_node(current_node)){
if(current_node==sliced_selected_geojson_edges_single.properties.from){
new_merged_lineString.push(sliced_selected_geojson_edges_single.geometry.coordinates);
linedirection.push(0);
crossed_lines.push(sliced_selected_geojson_edges_single);
current_node=sliced_selected_geojson_edges_single.properties.to;
lines_to_be_removed.push(sliced_selected_geojson_edges_single);
remove_lines(lines_to_be_removed);
if(is_end_node(current_node)){
merged_line_to = current_node;
complete_lineString();
}
else{
for (var o = 0; o < sliced_selected_geojson_edges.length; o++){
if((sliced_selected_geojson_edges[o].properties.from == current_node || sliced_selected_geojson_edges[o].properties.to == current_node) && is_connecting_node(current_node)){
add_next_nodes(current_node,sliced_selected_geojson_edges[o]);
o = sliced_selected_geojson_edges.length + 100;
}}
}
}else{
if(current_node==sliced_selected_geojson_edges_single.properties.to){
linedirection.push(1);
new_merged_lineString.push(sliced_selected_geojson_edges_single.geometry.coordinates);
crossed_lines.push(sliced_selected_geojson_edges_single);
current_node=sliced_selected_geojson_edges_single.properties.from;
lines_to_be_removed.push(sliced_selected_geojson_edges_single);
remove_lines(lines_to_be_removed);
if(is_end_node(current_node)){
merged_line_to = current_node;
complete_lineString();
}
else{
for (var o =0;o<sliced_selected_geojson_edges.length;o++){
if((sliced_selected_geojson_edges[o].properties.from == current_node || sliced_selected_geojson_edges[o].properties.to == current_node) && is_connecting_node(current_node)){
add_next_nodes(current_node,sliced_selected_geojson_edges[o]);
 o = sliced_selected_geojson_edges.length + 100;
}}
}
}
}
}
}

function complete_lineString(){
var indexOf1 = [];
if(linedirection.includes(1)){
for (var i in linedirection){
    if (linedirection[i] == 1){
        indexOf1.push(parseInt(i));

    }
}

for (var i in indexOf1){
var j = indexOf1[i];
new_merged_lineString[j] = new_merged_lineString[j].reverse();
}
}

new_merged_lineString = _.flatten(new_merged_lineString,true);
new_merged_selected_geojson_edges.push(turf.lineString(new_merged_lineString,{from: merged_line_from,to: merged_line_to}));
new_merged_lineString = [];
linedirection = [];
}

             var temp_geojson_edges = L.geoJSON(new_merged_selected_geojson_edges, {
                     style: myStyle,
                     onEachFeature: function(feature,layer){
                      layer.bindPopup('<p>From: ' + feature.properties.from + 'To:' + feature.properties.to + '</p>');
                      }}).addTo(map);



              layerGroup_experiment_map.addLayer(tempgeojson_edges);
              layerGroup_street.addLayer(geojson_edges);


});
save_button.addTo(map);

}

function omission(){
removeOtherControls();

var redStyle = {
                    "color": "#FF0000",
                    "weight": 5,
                    "opacity": 0.65
           };

var selected_geojson_edges = [];
var selected_geojson_polygon = [];
var selected_geojson_region = [];
var edges_node_id = [];
button = L.easyButton('fa-mouse-pointer', function(){

    geojson_edges.eachLayer(function (layer) {
        layer.on('click', function (e) {
                          e.target.setStyle(redStyle);
                          selected_geojson_edges.push(e.target.feature);
                          edges_node_id.push(e.target.feature.properties.from,e.target.feature.properties.to);

                        });
});

    geojson_polygon.eachLayer(function(layer){
        layer.on('click',function (e){
                e.target.setStyle(redStyle);
                selected_geojson_polygon.push(e.target.feature);

        });
    });


   /* geojson_region.eachLayer(function(layer){
        layer.on('click',function (e){
                e.target.setStyle(redStyle);
                selected_geojson_region.push(e.target.feature);
                console.log(e.target.feature);
        });
    });*/
/*});
button.addTo(map);




function is_end_node(node_id){
var count_edges_node_id = _.countBy(edges_node_id);
    if   (count_edges_node_id[node_id]>=3 || count_edges_node_id[node_id]==1){
        return true;
    }
    else{
        return false;
    }
}

function is_connecting_node(node_id){
var count_edges_node_id = _.countBy(edges_node_id);
    if   (count_edges_node_id[node_id]==2){
        return true;
    }
    else{
        return false;
    }
}


save_button = L.easyButton('fa-save',function(){
var numberoffeaturesinExpMap = geojson_polygon.getLayers().length + geojson_edges.getLayers().length;
 var numberoffeaturesinGenMap = selected_geojson_edges.length + selected_geojson_polygon.length;
  featuresbeforegen = numberoffeaturesinGenMap;
 var completeness = (numberoffeaturesinExpMap - numberoffeaturesinGenMap)/numberoffeaturesinExpMap;
 $( "#comp" ).html(completeness);
 $( "#FeaturesinEM" ).html(numberoffeaturesinExpMap);
 $( "#FeaturesinSM" ).html(numberoffeaturesinGenMap);
var new_merged_selected_geojson_edges = [];
var linedirection = [];
var new_merged_lineString = [];
var crossed_lines = [];
var merged_line_from ;
var merged_line_to;
var lines_to_be_removed = [];
var sliced_selected_geojson_edges = [];
var index = 0;
for(var i in selected_geojson_edges){
index = 0;
if (is_end_node(selected_geojson_edges[i].properties.from) && !( crossed_lines.includes(selected_geojson_edges[i]))){
 crossed_lines.push(selected_geojson_edges[i]);
 merged_line_from = selected_geojson_edges[i].properties.from;
 new_merged_lineString.push(selected_geojson_edges[i].geometry.coordinates);
 linedirection.push(0);
 lines_to_be_removed.push(selected_geojson_edges[i]);
 remove_lines(lines_to_be_removed);
 if(is_end_node(selected_geojson_edges[i].properties.to)){
    merged_line_to = selected_geojson_edges[i].properties.to;
    complete_lineString();
}
else{
for (var o=0; o < sliced_selected_geojson_edges.length;o++){
if((sliced_selected_geojson_edges[o].properties.from == selected_geojson_edges[i].properties.to || sliced_selected_geojson_edges[o].properties.to == selected_geojson_edges[i].properties.to) && is_connecting_node(selected_geojson_edges[i].properties.to)){
add_next_nodes(selected_geojson_edges[i].properties.to,sliced_selected_geojson_edges[o]);
o = sliced_selected_geojson_edges.length + 100;
}}
}
} else{
if (is_end_node(selected_geojson_edges[i].properties.to) && !( crossed_lines.includes(selected_geojson_edges[i]))){
 crossed_lines.push(selected_geojson_edges[i]);
 merged_line_to = selected_geojson_edges[i].properties.to;
 new_merged_lineString.push(selected_geojson_edges[i].geometry.coordinates);
 linedirection.push(1);
 lines_to_be_removed.push(selected_geojson_edges[i]);
 remove_lines(lines_to_be_removed);
 if(is_end_node(selected_geojson_edges[i].properties.from)){
 merged_line_from = selected_geojson_edges[i].properties.from;
 complete_lineString();
 }
 else{
 for (var o=0; o < sliced_selected_geojson_edges.length;o++){
      if((sliced_selected_geojson_edges[o].properties.from == selected_geojson_edges[i].properties.from || sliced_selected_geojson_edges[o].properties.to == selected_geojson_edges[i].properties.from) && is_connecting_node(selected_geojson_edges[i].properties.from)){
        add_next_nodes(selected_geojson_edges[i].properties.from,sliced_selected_geojson_edges[o]);
        o = sliced_selected_geojson_edges.length + 100;
}}
 }
}}
}


function remove_lines(lines_to_be_removed){
sliced_selected_geojson_edges = [];
    for (var i = 0;i < selected_geojson_edges.length;i++){
        if(!(lines_to_be_removed.includes(selected_geojson_edges[i]))){
            sliced_selected_geojson_edges.push(selected_geojson_edges[i]);
    }
}
}



function add_next_nodes(current_node,sliced_selected_geojson_edges_single){
if(is_connecting_node(current_node)){
if(current_node==sliced_selected_geojson_edges_single.properties.from){
new_merged_lineString.push(sliced_selected_geojson_edges_single.geometry.coordinates);
linedirection.push(0);
crossed_lines.push(sliced_selected_geojson_edges_single);
current_node=sliced_selected_geojson_edges_single.properties.to;
lines_to_be_removed.push(sliced_selected_geojson_edges_single);
remove_lines(lines_to_be_removed);
if(is_end_node(current_node)){
merged_line_to = current_node;
complete_lineString();
}
else{
if(sliced_selected_geojson_edges[index] && is_connecting_node(current_node)){
for (var o=0; o < sliced_selected_geojson_edges.length;o++){
if((sliced_selected_geojson_edges[o].properties.from == current_node || sliced_selected_geojson_edges[o].properties.to == current_node) && is_connecting_node(current_node)){
add_next_nodes(current_node,sliced_selected_geojson_edges[o]);
o = sliced_selected_geojson_edges.length + 100;
}}
}
}
}else{
if(current_node==sliced_selected_geojson_edges_single.properties.to){
linedirection.push(1);
new_merged_lineString.push(sliced_selected_geojson_edges_single.geometry.coordinates);
crossed_lines.push(sliced_selected_geojson_edges_single);
current_node=sliced_selected_geojson_edges_single.properties.from;
lines_to_be_removed.push(sliced_selected_geojson_edges_single);
remove_lines(lines_to_be_removed);
if(is_end_node(current_node)){
merged_line_from = current_node;
complete_lineString();
}
else{
if(sliced_selected_geojson_edges[index] && is_connecting_node(current_node)){
for (var o=0; o < sliced_selected_geojson_edges.length;o++){
if((sliced_selected_geojson_edges[o].properties.from == current_node || sliced_selected_geojson_edges[o].properties.to == current_node) && is_connecting_node(current_node)){
add_next_nodes(current_node,sliced_selected_geojson_edges[o]);
o = sliced_selected_geojson_edges.length + 100;
}}
}
}
}
}
}
}

function complete_lineString(){
var indexOf1 = [];
if(linedirection.includes(1)){
for (var i in linedirection){
    if (linedirection[i] == 1){
        indexOf1.push(parseInt(i));

    }
}


for (var i in indexOf1){
var j = indexOf1[i];
new_merged_lineString[j] = new_merged_lineString[j].reverse();
}
}
var merging_degreeOfgeneralisation_single = (new_merged_lineString.length-1)/(new_merged_lineString.length);
console.log(new_merged_lineString.length);
merging_degreeOfgeneralisation = merging_degreeOfgeneralisation + merging_degreeOfgeneralisation_single;

$( "#M_DG" ).html(merging_degreeOfgeneralisation);
new_merged_lineString = _.flatten(new_merged_lineString,true);
new_merged_selected_geojson_edges.push(turf.lineString(new_merged_lineString,{from: merged_line_from,to: merged_line_to}));
new_merged_lineString = [];
linedirection = [];
}

var redStyle = {
                    "color": "#FF0000",
                    "weight": 5,
                    "opacity": 0.65
           };

             geojson_edges_selected = L.geoJSON(new_merged_selected_geojson_edges, {
                     style: redStyle,
                     onEachFeature: function(feature,layer){
                      layer.bindPopup('<p>From: ' + feature.properties.from + 'To:' + feature.properties.to + '</p>');
                      }}).addTo(map);

             geojson_polygon_selected = L.geoJSON(selected_geojson_polygon, {
                     style: redStyle,
                     onEachFeature: function(feature,layer){
                      }}).addTo(map);

               geojson_region_selected = L.geoJSON(selected_geojson_region, {
                     style: redStyle,
                     onEachFeature: function(feature,layer){
                      }}).addTo(map);
              layerGroup_generalised_map.addLayer(geojson_polygon_selected);
              layerGroup_buildings.addLayer(geojson_polygon_selected);
              layerGroup_generalised_map.addLayer(geojson_edges_selected);
              layerGroup_street.addLayer(geojson_edges_selected);
              layerGroup_generalised_map.addLayer(geojson_region_selected);
              layerGroup_openspaces.addLayer(geojson_region_selected);


});
save_button.addTo(map);
/*var total_noOfObjects_metric_map = geojson_edges.toGeoJSON().length;
var total_noOfObjects_merged = geojson_edges_selected.toGeoJSON().length;
var total_noOfObjects_omitted = total_noOfObjects_metric_map - selected_geojson_edges.length;*/

/*}


function abstraction_to_show_existence(){
removeOtherControls();




var group_of_objects_street = [];
var group_of_objects_polygon = [];
var group_id_streets = 1;
var group_id_polygons = 1;

var redStyle = {
                    "color": "#FF0000",
                    "weight": 5,
                    "opacity": 0.65
           };
button = L.easyButton('fa-mouse-pointer', function(){
    geojson_edges_selected.eachLayer(function (layer) {
        layer.on('click', function (e) {
                          e.target.setStyle(redStyle);
                          group_of_objects_street.push(e.target.feature);
                        });
});

    geojson_polygon_selected.eachLayer(function(layer){
        layer.on('click',function (e){
                e.target.setStyle(redStyle);
                group_of_objects_polygon.push(e.target.feature);

        });
    });



});

button.addTo(map);

var button_groupinSketchMap = L.easyButton('fa-keyboard', function(){
$('#sketchgroupnum').css('visibility', 'visible');

});

button_groupinSketchMap.addTo(map);

save_button = L.easyButton('fa-save',function(){
var sketchgroupnum = parseInt($('#sketchgroupnum').val());
var existence_degreeOfgeneralisation_single_polygon = (group_of_objects_polygon.length - sketchgroupnum)/(group_of_objects_polygon.length);
var existence_degreeOfgeneralisation_single_street = (group_of_objects_street.length - sketchgroupnum)/(group_of_objects_street.length);
existence_degreeOfgeneralisation = existence_degreeOfgeneralisation + existence_degreeOfgeneralisation_single_polygon + existence_degreeOfgeneralisation_single_street;

$( "#E_DG" ).html(existence_degreeOfgeneralisation);

$('#sketchgroupnum').css('visibility', 'hidden');

var group_polygons  = L.geoJSON(group_of_objects_polygon, {
                     onEachFeature: function(feature,layer){
                      layer.bindPopup('<p>Group_id: ' + group_id_polygons +  '</p>');
                      },
            }).addTo(map);


var group_streets  = L.geoJSON(group_of_objects_street, {
                     onEachFeature: function(feature,layer){
                      layer.bindPopup('<p>Group_id: ' + group_id_streets + '</p>');
                      },
            }).addTo(map);

group_id_streets = group_id_streets +1;
group_id_polygons = group_id_polygons + 1;
group_of_objects_street = [];
group_of_objects_polygon = [];


$('#sketchgroupnum').val('0');
var existence_degreeOfgeneralisation_single_polygon = 0;
var existence_degreeOfgeneralisation_single_street = 0;

}).addTo(map);

save_button.addTo(map);


}



function merged_junctions(){
removeOtherControls();
map.addControl(drawControl);
var j = 0;
var linesegments_within_box = [];
var id_from = [];
var id_to = [];
let set_id_to;
let set_id_from;
var linesegments = [];
var poly;
button = L.easyButton( 'fa-minus-circle', function(){
var streets = geojson_edges_selected.toGeoJSON();
latlng = layer.getLatLngs();
var polygon_lnglat = [];
                                for (var i in latlng[0]){
                                 polygon_lnglat.push([latlng[0][i].lng,latlng[0][i].lat]);
                                }
                                polygon_lnglat.push([latlng[0][0].lng,latlng[0][0].lat]);

poly = turf.polygon([polygon_lnglat]);
           var line_coordinates = [];
           turf.featureEach(streets,function(currentFeature,featureIndex){
           if (turf.booleanCrosses(currentFeature,poly) || turf.booleanWithin(currentFeature,poly)){
           linesegments_within_box.push(currentFeature);
           id_from.push(currentFeature.properties.from);
           id_to.push(currentFeature.properties.to);
           line_coordinates.push(currentFeature.geometry.coordinates);
           }
           });

           m_noOfobjects = linesegments_within_box.length;
           var junctionmerging_degreeOfgeneralisation_single = (m_noOfobjects-1)/m_noOfobjects;
           junctionmerge_degree_of_generalisation = junctionmerge_degree_of_generalisation + junctionmerging_degreeOfgeneralisation_single;
           $( "#J_DG" ).html( junctionmerge_degree_of_generalisation);

           var linesegments_collection = turf.featureCollection(linesegments_within_box);
           var arr1d = _.flatten(line_coordinates,true);

           var arr1d_unique = arr1d.map(JSON.stringify).reverse()
           .filter(function(item, index, arr1d){ return arr1d.indexOf(item, index + 1) === -1; }).reverse().map(JSON.parse);

           var count_node = {};

           for (var m=0; m < arr1d_unique.length+1; m++){
            var count = 0;
                for (var n = 0; n < arr1d.length; n++){
                 if (_.isEqual(arr1d[n],arr1d_unique[m])){
                  var temp = (arr1d_unique[m]).toString();
                  count = count + 1;
                  count_node[temp] = count;
                 }
                }
            }


    var temp_arr = Object.values(count_node);
    var max = Math.max.apply(null, temp_arr);
    temp_arr.splice(temp_arr.indexOf(max), 1);
    var second_max =  Math.max.apply(null, temp_arr);
    var key_1;
    var key_2;

           if (max == second_max){
           key_1 = Object.keys(count_node).filter(function(key) {return count_node[key] === max})[0];
           key_2 = Object.keys(count_node).filter(function(key) {return count_node[key] === max})[1];
           }
           else{
           key_1 = Object.keys(count_node).filter(function(key) {return count_node[key] === max})[0];
           key_2 = Object.keys(count_node).filter(function(key) {return count_node[key] === second_max})[0];
           }



          var intersect_coord1 = key_1.split(',').map(Number);
          var intersect_coord2 = key_2.split(',').map(Number);



          var path ;
          var merged_junctions = [];
          var newline;
          var temp_coordIndex_1;
          var temp_coordIndex_2;
          var newline_array_temp =[];
          var start;
          if (max == second_max){
           start = turf.midpoint(intersect_coord1,intersect_coord2);
          }
          else{
           start = turf.point(intersect_coord1);
          }


          turf.featureEach(linesegments_collection,function(currentFeature,featureIndex){
           if(!(((_.isEqual(intersect_coord1,currentFeature.geometry.coordinates[0]) || _.isEqual(intersect_coord1,currentFeature.geometry.coordinates[1]))) && ((_.isEqual(intersect_coord2,currentFeature.geometry.coordinates[0]) || _.isEqual(intersect_coord2,currentFeature.geometry.coordinates[1]))))){
           newline_array_temp.push(currentFeature);
          }
          });

          var newline_array_temp_collection = turf.featureCollection(newline_array_temp);


          turf.featureEach(newline_array_temp_collection,function(currentFeature,featureIndex){
          for (var i in currentFeature.geometry.coordinates){
           if(_.isEqual(intersect_coord1,currentFeature.geometry.coordinates[i]) || _.isEqual(intersect_coord2,currentFeature.geometry.coordinates[i])){
               currentFeature.geometry.coordinates[i]=start.geometry.coordinates;
           }
           }
           merged_junctions.push(currentFeature);
          });


           var myStyle = {
                    "color": "#ff7800",
                    "weight": 5,
                    "opacity": 0.65
           };

            linesegments[j] = L.geoJSON(merged_junctions, {
                     style: myStyle,
                     onEachFeature:  function(feature,layer){
                       layer.on('click', function (e) {
                             e.target.editing.enable();
                        });
                        }
            }).addTo(map);



            set_id_from = new Set(id_from);
            set_id_to  = new Set(id_to);
            boundingbox.clearLayers();
            layerGroup_generalised_map.addLayer(linesegments[j]);
            j=j+1;
});
button.addTo(map);

save_button = L.easyButton('fa-save',function(){
geojson_edges_selected.eachLayer(function(layer) {
  	if ((set_id_from.has(layer.feature.properties.from)) && (set_id_to.has(layer.feature.properties.to))) {

    	geojson_edges_selected.removeLayer(layer);
    }
  });
  var last_layer = (linesegments[linesegments.length-1]).toGeoJSON();

  geojson_edges_selected.addData(last_layer);
  for (var i=0;i<linesegments.length;i++){
  layerGroup_generalised_map.removeLayer(linesegments[i]);
}
linesegments_within_box=[];
});
save_button.addTo(map);
}

function roundabout_collapse(){
removeOtherControls();
map.addControl(drawControl);

var j = 0;
var linesegments_within_box = [];
var id_from = [];
var id_to = [];
let set_id_to;
let set_id_from;
var linesegments = [];
var poly;
button = L.easyButton( 'fa-minus-circle', function(){
var streets = geojson_edges_selected.toGeoJSON();
latlng = layer.getLatLngs();
var polygon_lnglat = [];
                                for (var i in latlng[0]){
                                 polygon_lnglat.push([latlng[0][i].lng,latlng[0][i].lat]);
                                }
                                polygon_lnglat.push([latlng[0][0].lng,latlng[0][0].lat]);

poly = turf.polygon([polygon_lnglat]);
           var line_coordinates = [];
           turf.featureEach(streets,function(currentFeature,featureIndex){
           if (turf.booleanCrosses(currentFeature,poly) || turf.booleanWithin(currentFeature,poly)){
           linesegments_within_box.push(currentFeature);
           id_from.push(currentFeature.properties.from);
           id_to.push(currentFeature.properties.to);
           line_coordinates.push(currentFeature.geometry.coordinates);
           }
           });

          console.log(linesegments_within_box);
           var linesegments_collection = turf.featureCollection(linesegments_within_box);










           var myStyle = {
                    "color": "#ff7800",
                    "weight": 5,
                    "opacity": 0.65
           };

            linesegments[j] = L.geoJSON(merged_junctions, {
                     style: myStyle,
                     onEachFeature:  function(feature,layer){
                       layer.on('click', function (e) {
                             e.target.editing.enable();
                        });
                        }
            }).addTo(map);



            set_id_from = new Set(id_from);
            set_id_to  = new Set(id_to);
            boundingbox.clearLayers();
            layerGroup_generalised_map.addLayer(linesegments[j]);
            j=j+1;
});
button.addTo(map);

save_button = L.easyButton('fa-save',function(){
geojson_edges_selected.eachLayer(function(layer) {
  	if ((set_id_from.has(layer.feature.properties.from)) && (set_id_to.has(layer.feature.properties.to))) {

    	geojson_edges_selected.removeLayer(layer);
    }
  });
  var last_layer = (linesegments[linesegments.length-1]).toGeoJSON();

  geojson_edges_selected.addData(last_layer);
  for (var i=0;i<linesegments.length;i++){
  layerGroup_generalised_map.removeLayer(linesegments[i]);
}
linesegments_within_box=[];
});
save_button.addTo(map);

}

function collapse(){
removeOtherControls();
map.addControl(drawControl);
var j = 0;
var polygons_within_box = [];
var id = [];
let set_id;
var polygons = [];
var poly;
button = L.easyButton( 'fa-compress-arrows-alt', function(){
var buildings = geojson_polygon_selected.toGeoJSON();
latlng = layer.getLatLngs();
//bbox = [latlng[0][0].lng, latlng[0][0].lat, latlng[0][2].lng, latlng[0][1].lat];
                                var polygon_lnglat = [];

                                for (var i in latlng[0]){
                                 polygon_lnglat.push([latlng[0][i].lng,latlng[0][i].lat]);
                                }
                                polygon_lnglat.push([latlng[0][0].lng,latlng[0][0].lat]);

poly = turf.polygon([polygon_lnglat]);

           var each_polygon_within_box;
           turf.featureEach(buildings,function(currentFeature,featureIndex){
           if (currentFeature.geometry.type === 'MultiPolygon'){
            for (var i=0; i < currentFeature.geometry.coordinates.length; i++){
                var polygon = turf.polygon(currentFeature.geometry.coordinates[i], { name: currentFeature.properties.ID });
                each_polygon_within_box =turf.booleanWithin(polygon,poly);
                if (each_polygon_within_box){

                 polygons_within_box.push(currentFeature);
                 id.push(currentFeature.properties.ID);
            }
            }
           }
           if (currentFeature.geometry.type === 'Polygon'){
           each_polygon_within_box =  turf.booleanWithin(currentFeature,poly);
           if (each_polygon_within_box){
                 polygons_within_box.push(currentFeature);
                 id.push(currentFeature.properties.ID);
            }
           }
           });

           var point = turf.pointOnFeature(turf.featureCollection(polygons_within_box));


           m_noOfobjects = turf.area(turf.featureCollection(polygons_within_box));
           var degree_of_generalisation_collapse_single = 1-(1/m_noOfobjects) ;
           collapse_degree_of_generalisation = collapse_degree_of_generalisation + degree_of_generalisation_collapse_single;
              $( "#C_DG" ).html( collapse_degree_of_generalisation);


            polygons[j] = L.geoJSON(point, {
                      pointToLayer: function (feature, latlng) {
                      return L.circleMarker(latlng, geojsonMarkerOptions);
                      }
                }).addTo(map);

            set_id = new Set(id);
            boundingbox.clearLayers();
            layerGroup_generalised_map.addLayer(polygons[j]);
            j=j+1;
});
button.addTo(map);

save_button = L.easyButton('fa-save',function(){
geojson_polygon_selected.eachLayer(function(layer) {
  	if (set_id.has(layer.feature.properties.ID) ) {
    	geojson_polygon_selected.removeLayer(layer);
    }
  });
  var last_layer = (polygons[polygons.length-1]).toGeoJSON();

  geojson_polygon_selected.addData(last_layer);
for (var i=0;i<polygons.length;i++){
  layerGroup_generalised_map.removeLayer(polygons[i]);
    }

polygons_within_box=[];
});
save_button.addTo(map);
}

function amalgamation(){
removeOtherControls();
map.addControl(drawControl);
var j = 0;
var polygons_within_box = [];
var id = [];
let set_id;
var polygons = [];
var count = [];
var poly;
button = L.easyButton( 'fa-object-group', function(){
var buildings = geojson_polygon_selected.toGeoJSON();
latlng = layer.getLatLngs();
var polygon_lnglat = [];

                                for (var i in latlng[0]){
                                 polygon_lnglat.push([latlng[0][i].lng,latlng[0][i].lat]);
                                }
                                polygon_lnglat.push([latlng[0][0].lng,latlng[0][0].lat]);

poly = turf.polygon([polygon_lnglat]);
           var each_polygon_within_box;
           turf.featureEach(buildings,function(currentFeature,featureIndex){
           if (currentFeature.geometry.type === 'MultiPolygon'){
            for (var i=0; i < currentFeature.geometry.coordinates.length; i++){
                var polygon = turf.polygon(currentFeature.geometry.coordinates[i], { name: currentFeature.properties.ID });
                each_polygon_within_box =turf.booleanWithin(polygon,poly);
                if (each_polygon_within_box){
                count.push(1);
                var point_featureCollection = turf.explode(currentFeature);
                 turf.featureEach(point_featureCollection,function(currentFeaturepoint,featureIndex){
                 var latlng = {lng: currentFeaturepoint.geometry.coordinates[0], lat: currentFeaturepoint.geometry.coordinates[1]};
                 polygons_within_box.push(latlng);
                 });
                 id.push(currentFeature.properties.ID);
            }
            }
           }
           if (currentFeature.geometry.type === 'Polygon'){
           each_polygon_within_box =  turf.booleanWithin(currentFeature,poly);
           if (each_polygon_within_box){
           count.push(1);
                 var point_featureCollection = turf.explode(currentFeature);
                 turf.featureEach(point_featureCollection,function(currentFeaturepoint,featureIndex){
                 var latlng = {lng: currentFeaturepoint.geometry.coordinates[0], lat: currentFeaturepoint.geometry.coordinates[1]};
                 polygons_within_box.push(latlng);
                 });
                 id.push(currentFeature.properties.ID);
            }
            }
           });


            amalgamation_degree_of_generalisation_single = (count.length - 1)/count.length;
            amalgamation_degree_of_generalisation = amalgamation_degree_of_generalisation + amalgamation_degree_of_generalisation_single;
             $( "#A_DG" ).html(amalgamation_degree_of_generalisation);

           var  hull_points = polygons_within_box.map(map.latLngToContainerPoint.bind(map));
           hull_points = hull(hull_points, 80, ['.x', '.y']);
            hull_points = hull_points.map(function(pt) {
                return map.containerPointToLatLng(L.point(pt.x, pt.y));
            });

           var hull_points_turf = [];
           for (var i in hull_points){
           hull_points_turf.push([hull_points[i].lng,hull_points[i].lat]);
           }


           var envelope = turf.polygon([hull_points_turf],{name: 'hull'});
           var myStyle = {
                    "color": "#ff7800",
                    "weight": 5,
                    "opacity": 0.65
           };

            polygons[j] = L.geoJSON(envelope, {
                     style: myStyle
            }).addTo(map);

            set_id = new Set(id);
            boundingbox.clearLayers();
            layerGroup_generalised_map.addLayer(polygons[j]);
            j=j+1;
});
button.addTo(map);

save_button = L.easyButton('fa-save',function(){
count = [];
geojson_polygon_selected.eachLayer(function(layer) {
  	if (set_id.has(layer.feature.properties.ID) ) {
    	geojson_polygon_selected.removeLayer(layer);
    }
  });


  var last_layer = (polygons[polygons.length-1]).toGeoJSON();

  geojson_polygon_selected.addData(last_layer);
  for (var i=0;i<polygons.length;i++){
  layerGroup_generalised_map.removeLayer(polygons[i]);
    }
polygons_within_box=[];
});
save_button.addTo(map);


}

function regionalization(){
removeOtherControls();



}







function request_for_fetching_data(data_name){
                const xhr = new XMLHttpRequest();
                xhr.open('GET', '/static/geojson_files/' + data_name + '.geojson');
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.responseType = 'json';
                xhr.onload = function() {
                if (data_name.includes("edges")){
                if (xhr.status !== 200 ) return
                      raw_geojson_edges = L.geoJSON(xhr.response,{
                      style: styleForexperiment,
                      onEachFeature: function(feature,layer){
                      //layer.bindPopup('<p>From: ' + feature.properties.from + 'To:' + feature.properties.to + '<br> Name:' + feature.properties.name + '<br> Highway: ' + feature.properties.highway + '<br> Oneway:' + feature.properties.oneway + '<br> Lanes:' + feature.properties.lanes + '</p>');
                       /*layer.on('click', function (e) {
                             e.target.editing.enable();
                        });*//*
                      }}).addTo(map);

                      layerGroup_raw_map.addLayer(raw_geojson_edges);
                      layerGroup_street.addLayer(raw_geojson_edges);
                }
                if (data_name.includes("nodes")){
                if (xhr.status !== 200) return
                 raw_geojson_nodes=L.geoJSON(xhr.response, {
                      pointToLayer: function (feature, latlng) {
                      return L.circleMarker(latlng, geojsonMarkerOptions);
                      },
                      onEachFeature : function(feature, layer){
                      layer.bindPopup('<p> Osmid: ' + feature.properties.osmid + '<br>highway:' + feature.properties.highway + '</p>');
                      },
                      pmIgnore:true
                });
               // layerGroup_raw_map.addLayer(raw_geojson_nodes);

                }
                if(data_name.includes("buildings")){
                if (xhr.status !== 200) return
                    var tempID = 1;
                    raw_geojson_polygon = L.geoJSON(xhr.response, {
                      style: styleForexperiment_polygon,
                    filter: function(feature){
                        if (feature.geometry.type == "Polygon" || feature.geometry.type == "MultiPolygon"){
                            return true;
                        }
                    },
                    onEachFeature: function(feature, layer){
                    layer.feature.properties.ID = tempID;
                    layer.bindPopup('<p> Building: ' + feature.properties.name + '<br>Id:' + feature.properties.ID + '</p');
                    tempID+=1;
                    },
                    pmIgnore:true
                }).addTo(map);

                layerGroup_raw_map.addLayer(raw_geojson_polygon);
                layerGroup_buildings.addLayer(raw_geojson_polygon);

                }
                if(data_name.includes("openregions")){
                if (xhr.status !== 200) return
                    raw_geojson_region = L.geoJSON(xhr.response, {
                    style: styleForexperiment_polygon,
                    filter: function(feature){
                        if (feature.geometry.type != "Point"){
                            return true;
                        }
                    },
                    onEachFeature: function(feature, layer){
                    tempID = tempID + 1;
                    layer.feature.properties.ID = tempID;
                    layer.bindPopup('<p> Openregion: ' + feature.properties.name + '<br>Id:' + feature.properties.ID + '</p');
                    },
                    pmIgnore:true
                }).addTo(map);
                layerGroup_raw_map.addLayer(raw_geojson_region);
                layerGroup_openspaces.addLayer(raw_geojson_region);
                }
               };
               xhr.send();
}

//layer_control
var layers = {
     "Raw map": layerGroup_raw_map,
     "Experiment map" : layerGroup_experiment_map,
     "Generalised map" : layerGroup_generalised_map,
     "Streets" : layerGroup_street,
     "Buildings" : layerGroup_buildings,
     "Open spaces" : layerGroup_openspaces
};

L.control.layers(null,layers).addTo(map);


function downloadRawJsonMM() {
    var save_raw_edges = raw_geojson_edges.toGeoJSON();
    var save_raw_polygon = raw_geojson_polygon.toGeoJSON();
    var save_raw_region = raw_geojson_region.toGeoJSON();

    var GeoJSON_raw_edges = JSON.stringify(save_raw_edges);
    var GeoJSON_raw_polygon = JSON.stringify(save_raw_polygon);
    var GeoJSON_raw_region = JSON.stringify(save_raw_region);

    var zip = new JSZip();
     zip.file("raw_edges.geojson",GeoJSON_raw_edges);
     zip.file("raw_polygon.geojson",GeoJSON_raw_polygon);
     zip.file("raw_region.geojson",GeoJSON_raw_region);
     zip.generateAsync({type:"blob"})
        .then(function(content) {

    saveAs(content, "raw_map.zip");
});

}

function downloadExperimentJsonMM() {
    var save_geojson_edges = geojson_edges.toGeoJSON();
    var save_geojson_polygon = geojson_polygon.toGeoJSON();
    var save_geojson_region = geojson_region.toGeoJSON();

    var GeoJSON_geojson_edges = JSON.stringify(save_geojson_edges);
    var GeoJSON_geojson_polygon = JSON.stringify(save_geojson_polygon);
    var GeoJSON_geojson_region = JSON.stringify(save_geojson_region);

    var zip = new JSZip();
     zip.file("geojson_edges.geojson",GeoJSON_geojson_edges);
     zip.file("geojson_polygon.geojson",GeoJSON_geojson_polygon);
     zip.file("geojson_region.geojson",GeoJSON_geojson_region);
     zip.generateAsync({type:"blob"})
        .then(function(content) {

    saveAs(content, "experiment_map.zip");
});

}


function downloadGeneralisedmap(){
var all_feature = layerGroup_generalised_map.toGeoJSON();
var features_generalised= 'text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(all_feature));
    document.getElementById('exportgeneralisedmap').setAttribute('href', 'data:' + SMGeoJSON);
    document.getElementById('exportgeneralisedmap').setAttribute('download', sketchFileName+'.geojson');
}

function downloadGeneralisedJsonMM() {
    var save_generalised_edges = geojson_edges_selected.toGeoJSON();
    var save_generalised_polygon = geojson_polygon_selected.toGeoJSON();
    var save_generalised_region = geojson_region_selected.toGeoJSON();

    var GeoJSON_generalised_edges = JSON.stringify(save_generalised_edges);
    var GeoJSON_generalised_polygon = JSON.stringify(save_generalised_polygon);
    var GeoJSON_generalised_region = JSON.stringify(save_generalised_region);

  var GeoJSON_all = {
    "type" : "FeatureCollection",
    "features": [... save_generalised_edges.features, ... save_generalised_polygon.features, ... save_generalised_region.features]
}


    var mergedgeoJSONfile = JSON.stringify(GeoJSON_all);

    var zip = new JSZip();
     zip.file("generalised_edges.geojson",GeoJSON_generalised_edges);
     zip.file("generalised_polygon.geojson",GeoJSON_generalised_polygon);
     zip.file("generalised_region.geojson",GeoJSON_generalised_region);
     zip.file("generalisedall.geojson",mergedgeoJSONfile);
     zip.generateAsync({type:"blob"})
        .then(function(content) {

    saveAs(content, "generalised_map.zip");
});

}

function loadRawJsonMM() {

    var fileList = document.getElementById('importMM').files;
    for (var i = 0; i < fileList.length; i++) {
        randerGeoJsonFiles_RM(fileList[i], map);

    }
}

function randerGeoJsonFiles_RM(file, map) {
    var fileName = file.name;
    var reader = new FileReader();
    reader.readAsDataURL(file);
    if (fileName.includes('edges')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
           raw_geojson_edges = L.geoJSON(data,{
                      onEachFeature: function(feature,layer){
                      }}).addTo(map);
                      layerGroup_raw_map.addLayer(raw_geojson_edges);
                      layerGroup_street.addLayer(raw_geojson_edges);
        });
    }}

    if (fileName.includes('polygon')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
           raw_geojson_polygon = L.geoJSON(data,{
                      onEachFeature: function(feature,layer){
                      }}).addTo(map);
                      layerGroup_raw_map.addLayer(raw_geojson_polygon);
                      layerGroup_buildings.addLayer(raw_geojson_polygon);
        });
    }}

    if (fileName.includes('region')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
        console.log(data);
           raw_geojson_polygon.addData(data);
                      layerGroup_raw_map.addLayer(raw_geojson_polygon);
                      layerGroup_openspaces.addLayer(raw_geojson_polygon);
        });
    }}
}


function loadExperimentJsonMM() {

    var fileList = document.getElementById('importEM').files;
    for (var i = 0; i < fileList.length; i++) {
        randerGeoJsonFiles_EM(fileList[i], map);

    }
}

function randerGeoJsonFiles_EM(file, map) {
    var fileName = file.name;
    var reader = new FileReader();
    reader.readAsDataURL(file);
    if (fileName.includes('edges')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
           geojson_edges = L.geoJSON(data,{
                      style: styleForexperiment,
                      onEachFeature: function(feature,layer){
                      }}).addTo(map);
                      layerGroup_experiment_map.addLayer(geojson_edges);
                      layerGroup_street.addLayer(geojson_edges);
        });
    }}

    if (fileName.includes('polygon')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
           geojson_polygon = L.geoJSON(data,{
                      style: styleForexperiment_polygon,
                      onEachFeature: function(feature,layer){
                      }}).addTo(map);
                      layerGroup_experiment_map.addLayer(geojson_polygon);
                      layerGroup_buildings.addLayer(geojson_polygon);
        });
    }}

    if (fileName.includes('region')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
           geojson_region = L.geoJSON(data,{
                      style: styleForexperiment_polygon,
                      onEachFeature: function(feature,layer){
                      }}).addTo(map);
                      layerGroup_experiment_map.addLayer(geojson_region);
                      layerGroup_openspaces.addLayer(geojson_region);
        });
    }}
}


function loadGeneralisedJsonMM() {

    var fileList = document.getElementById('importGM').files;
    for (var i = 0; i < fileList.length; i++) {
        randerGeoJsonFiles_GM(fileList[i], map);

    }
}

function randerGeoJsonFiles_GM(file, map) {
    var fileName = file.name;
    var reader = new FileReader();
    reader.readAsDataURL(file);
    if (fileName.includes('edges')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
           geojson_edges_selected = L.geoJSON(data,{
                      onEachFeature: function(feature,layer){
                      }}).addTo(map);
                      layerGroup_generalised_map.addLayer(geojson_edges_selected);

        });
    }}

    if (fileName.includes('polygon')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
           geojson_polygon_selected = L.geoJSON(data,{
                      onEachFeature: function(feature,layer){
                      }}).addTo(map);
                      layerGroup_generalised_map.addLayer(geojson_polygon_selected);
        });
    }}

    if (fileName.includes('region')){
    reader.onload = function () {
        $.getJSON(reader.result, function (data) {
           geojson_region_selected = L.geoJSON(data,{
                      onEachFeature: function(feature,layer){
                      }}).addTo(map);
                      layerGroup_generalised_map.addLayer(geojson_region_selected);
        });
    }}
}


    $('.dropdown-submenu a.test').on("click", function(e){
    $(this).next('ul').toggle();
    e.stopPropagation();
    e.preventDefault();
  });


function removeOtherControls(){

if (options){
map.pm.removeControls(options);}

if (drawControl){
map.removeControl(drawControl);
}

if (save_button){
map.removeControl(save_button);
}
if (download_button){
map.removeControl(download_button);
}

if (button){
map.removeControl(button);
}

}

var MMStreetIDs = [];
var MMisRoute = [];
var MMLandmarksIDs = [];
var MMRegionsIDs = [];

function addIDforQualitativeAnalysis(){
featuresaftergen = geojson_edges_selected.getLayers().length + geojson_polygon_selected.getLayers().length;
var overallgeneralisation  = (featuresbeforegen-featuresaftergen)/featuresbeforegen;

$('#overallgen').html(overallgeneralisation);
$('#FeaturesbeforeGen').html(featuresbeforegen);
$('#FeaturesafterGen').html(featuresaftergen);

 geojson_edges_selected.eachLayer(function (layer){
    layer.feature.properties.isRoute = null;
    layer.feature.properties.feat_type = null;

 });

 geojson_polygon_selected.eachLayer(function (layer){
    layer.feature.properties.isRoute = null;
    layer.feature.properties.feat_type = null;


 });

 geojson_regions_selected.eachLayer(function (layer){
     layer.feature.properties.isRoute = null;
     layer.feature.properties.feat_type = null;

 });

}
*/


