  let basemapLeafletholder = [];
  let sketchmapLeafletholder = [];
  let basemapfeature= [];
  let sketchmapfeature = [];
  let sketchmapnames = [];
  let hoveralignarray = [];

function displayDiff() {
     const R1 =  $('#uploadR1align')[0].files;
     const R2 =  $('#uploadR2align')[0].files;
     const R3 =  $('#uploadR3align')[0].files;
     var formData = new FormData();
     formData.append("uploadR1align", R1[0]);
     formData.append("uploadR2align", R2[0]);
     formData.append("uploadR3align", R3[0]);
       $.ajax({
                    headers: { "X-CSRFToken": $.cookie("csrftoken") },
                    url: 'compareResults/',
                    type: 'POST',
                    processData: false,
                    contentType: false,
                    mimeType: "multipart/form-data",
                    data: formData,
                    success: async function (resp) {
                        var response = JSON.parse(resp);
                        var numofresearchers;
                        for (var i =0;i<response.length;i++){
                            var diffdata = JSON.parse(response[i]);
                            numofresearchers = diffdata.columns.length;
                            var sketchmap=document.createElement("p");
                            sketchmap.id = "SketchMap" + i;
                            var table = document.createElement("table");
                            const header = table.createTHead();
                            const headerrow = header.insertRow(0);
                            const headercell1 = headerrow.insertCell(0);
                            const headercell2 = headerrow.insertCell(1);
                            const headercell3 = headerrow.insertCell(2);
                            const headercell4 = headerrow.insertCell(3);
                            headercell1.innerHTML = "<b>Base Map Id</b>";
                            headercell2.innerHTML = "<b> R1 </b>";
                            headercell3.innerHTML = "<b> R2 </b>";
                            headercell4.innerHTML = "<b> R3 </b>";
                            var mapcontainer = document.createElement("div");
                            mapcontainer.id = "map"+ i;
                            mapcontainer.className = "row";
                            for (var j = 0; j < diffdata.data.length ; j++) {
                                const tr = table.insertRow();
                                const bid = tr.insertCell(0);
                                bid.innerText = diffdata.index[j]
                                for (var x = 0; x < diffdata.columns.length ; x++){
                                    const td = tr.insertCell();
                                    td.innerText = diffdata.data[j][x];
                                }
                            }
                            for (var y = 0;y< diffdata.columns.length; y++){
                                var basemapdiv = document.createElement("div");
                                basemapdiv.id = "basemap" + i + y;
                                basemapdiv.className = "column";
                                var sketchmapdiv = document.createElement("div");
                                sketchmapdiv.id = "sketchmap" + i + y;
                                sketchmapdiv.className = "column";
                                mapcontainer.appendChild(basemapdiv);
                                mapcontainer.appendChild(sketchmapdiv);
                            }
                            document.getElementById('ResultContainer').appendChild(sketchmap);
                            document.getElementById('ResultContainer').appendChild(table);
                            document.getElementById('ResultContainer').appendChild(mapcontainer);
                        }
                       await addMaps(response.length,numofresearchers).then((result)=>{readLayers(response.length,numofresearchers,response)});
                    }
                });

}




async function addMaps(sketchmapnumber,researchernumber){

     $( document ).ready(async function() {
        try{
            var BaseMapImage = $('#BaseMapImage')[0].files[0];
            var SketchMapImage = $('#SketchMapImage')[0].files;

            //reading all the input files
            var reader = new FileReader();
            reader.readAsDataURL(BaseMapImage);
            reader.onload = await function (e) {
                var image = new Image();
                image.title = BaseMapImage.name;
                image.src = this.result;
                for (let i = 0 ;i<researchernumber;i++){
                        basemapLeafletholder[i] = [];
                    for (let j = 0;j<sketchmapnumber;j++){
                        var basemapleaflet = new L.map( "basemap" + j + i, {
                                         crs: L.CRS.Simple
                        });
                        var bounds = [[0, 0], [600, 850]];
                        var BMLoaded = new L.imageOverlay(image.src,bounds);
                        BMLoaded.addTo(basemapleaflet);
                        basemapleaflet.fitBounds(bounds);
                        basemapLeafletholder[i][j] = basemapleaflet;
                        }
                    }
                }


         //reading base map file


        //reading sketch map
        var sketchmapfilesArray = Array.from(SketchMapImage);
        sketchmapfilesArray.sort((a, b) => a.name.localeCompare(b.name));

         for (let i=0;i<sketchmapfilesArray.length;i++){
             sketchmapLeafletholder[i]=[];
             sketchmapnames.push(sketchmapfilesArray[i].name);
            $('#SketchMap' + i).text(sketchmapfilesArray[i].name);
            for (let j = 0;j<researchernumber;j++){
              let sketchmap = new L.map( "sketchmap" + i + j, {
                                            crs: L.CRS.Simple
                            });
              var sketchReader = new FileReader();
              sketchReader.readAsDataURL(sketchmapfilesArray[i]);
              sketchReader.onload = await function (e) {
                    var image = new Image();
                    image.title = e.name;
                    image.src = this.result;
                        var bounds = [[0, 0], [600, 850]];
                        var SMLoaded = new L.imageOverlay(image.src,bounds);
                SMLoaded.addTo(sketchmap);
                sketchmap.fitBounds(bounds);
                sketchmapLeafletholder[i][j] = sketchmap;
            }

         }

        }
    } catch (error) {
    }
 });
}


async function readLayers(sketchmapnumber,researchernumber,response){
 return new Promise((resolve, reject) => {
        try{
                let allInputFiles = [];
                let alignmentdatafiles = [];
                let basemapgjsonfiles = [];
                let sketchmapgjsonfiles = [];
                for (let i = 0; i< researchernumber; i++){
                    allInputFiles[i] = [];
                    allInputFiles[i] =  $('#uploadR' + (i+1).toString())[0].files;
                    basemapgjsonfiles[i] = Array.from(allInputFiles[i]).filter(n => n.name.includes('basemap'));
                    alignmentdatafiles[i] = Array.from(allInputFiles[i]).filter(n => n.name.includes('alignment'));
                    sketchmapgjsonfiles[i] = Array.from(allInputFiles[i]).filter(n => ! n.name.includes('basemap') && ! n.name.includes('alignment') );

                     console.log(basemapgjsonfiles,alignmentdatafiles,sketchmapgjsonfiles);
                   addBaseLayers(basemapgjsonfiles[i],response,i).then((result)=>{
                        console.log("check2");
                        filteralignment(alignmentdatafiles[i],response,i,sketchmapgjsonfiles[i])});


                 }

              resolve("done");

             }catch(error){
                console.log(error);
                    }
 });
}

function addBaseLayers(basemapfile,response,researcher){
 return new Promise((resolve, reject) => {
    try{
             basemapfeature[researcher]=[];
             var featureReader = new FileReader();
             featureReader.readAsDataURL(basemapfile[0]);
             featureReader.onload =  async function (e) {
             $.getJSON(this.result, function (data) {
             }).then((data)=>{
                for(var j= 0;j<response.length;j++){
                    var IdsForFilter = (JSON.parse(response[j]).index).map(Number);
                    var filtereddata;
                    filtereddata = data.features.filter(n => IdsForFilter.includes(n.properties.id));
                    if (filtereddata.length != 0){
                            basemapfeature[researcher][j] = L.geoJSON(filtereddata);
                            basemapfeature[researcher][j].eachLayer(function (layer) {
                                    layer.bindTooltip(String(layer.feature.properties.id),{permanent:true});
                            });
                            basemapfeature[researcher][j].addTo(basemapLeafletholder[researcher][j]);
                            basemapLeafletholder[researcher][j].fitBounds(basemapfeature[researcher][j].getBounds());
                    }
                }
             });
            resolve("done");
            }
            }catch(error){
            console.log(error);
            }
 });
}

async function filteralignment(alignmentfiles,response,researcher,sketchmapgjsonfile){
    return new Promise((resolve, reject) => {
        try{
            hoveralignarray[researcher]=[];
             var featureReader = new FileReader();
             featureReader.readAsDataURL(alignmentfiles[0]);
             featureReader.onload =  async function (e) {
              $.getJSON(this.result, function (data) {
             }).then((data)=>{
                  console.log(data);
                  for (var i =0;i<Object.keys(data).length;i++){
                        hoveralignarray[researcher][i]= [];
                        let diffbaseids = JSON.parse(response[i]).index;
                        Object.keys(data[sketchmapnames[i]]).forEach(function(key){
                        if (key != "checkAlignnum"){
                            var tempdiffarray = diffbaseids.map(Number);
                            var tempalignarray = data[sketchmapnames[i]][key].BaseAlign[0];
                            if(tempdiffarray.some(v => tempalignarray.includes(v))){
                                hoveralignarray[researcher][i].push(data[sketchmapnames[i]][key]);
                            }
                        }
                        });
                 }
                 addSketchLayers(sketchmapgjsonfile,researcher,hoveralignarray);
             });

 }
 }catch(error){
 console.log(error);
 }


 });

}


function addSketchLayers(sketchfiles,researcher,filteredalign){
    return new Promise((resolve, reject) => {
    try{
        console.log("is this even running");
        sketchmapfeature[researcher]=[];
        var sketchmapjsonfilesArray = Array.from(sketchfiles);
        sketchmapjsonfilesArray.sort((a, b) => a.name.localeCompare(b.name));
        for (let i = 0; i<sketchmapjsonfilesArray.length;i++){
           var featureReader = new FileReader();
           featureReader.readAsDataURL(sketchmapjsonfilesArray[i]);
           featureReader.onload =  async function (e) {
                 $.getJSON(this.result, function (data) {
                 }).then((data)=>{
                      var IdsForFilter = [];
                      var filtereddata;
                        for(let j= 0;j<filteredalign[researcher][i].length;j++){
                        console.log(filteredalign[researcher][i][j])
                        IdsForFilter.push(filteredalign[researcher][i][j].SketchAlign[0]);
                        }
                        IdsForFilter = IdsForFilter.flat();
                        filtereddata = data.features.filter(n => IdsForFilter.includes(n.properties.sid));
                        console.log(filtereddata);
                        if (filtereddata.length != 0){
                                sketchmapfeature[researcher][i] = L.geoJSON(filtereddata);
                                sketchmapfeature[researcher][i].eachLayer(function (layer) {
                                        layer.bindTooltip(String(layer.feature.properties.id),{permanent:true});
                                });
                                sketchmapfeature[researcher][i].addTo(sketchmapLeafletholder[i][researcher]);
                                sketchmapLeafletholder[i][researcher].fitBounds(sketchmapfeature[researcher][i].getBounds());
                        }
                    });



        }



     resolve(researcher);
    }
    }
    catch(error){
    console.log(error)
    }



     });


}



function hoverfunction(researcher,sketch,hoveralignarray){
    hoveralignarray = hoveralignarray.flat();
    basemapfeature[researcher][sketch].eachLayer(function(layer){
        layer.on('mouseover', function() {
            console.log("yes",hoveralignarray,layer.feature.properties.id);
            for (i in hoveralignarray){
                if (layer.feature.properties.id==hoveralignarray[i]){
                    console.log("true");
                    layer.setStyle({
                    color: 'red'   //or whatever style you wish to use;
                    });
                }
            }
            sketchmapfeature[sketch][researcher].eachLayer(function(slayer){
                for (i in hoveralignarray){
                    if (slayer.feature.properties.sid==hoveralignarray[i]){
                        slayer.setStyle({
                            color: 'red'   //or whatever style you wish to use;
                        });
                    }
                }
            });
        });

        layer.on('mouseout', function() {
        hoveralignarray=[];
        });
    });
 }

