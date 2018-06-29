const functions = require('firebase-functions');
const firebase = require("firebase-admin");
const express = require('express');
const app = express();
var request = require("request");
let config = {};

const firebaseApp = firebase.initializeApp(functions.config().firebase);
function getConfig(){
  const ref = firebaseApp.database().ref('integrations');
  return ref.once("value").then(snap=>snap.val());
}

getConfig().then((mainConfigs) => {
  console.log('check below configs');
  console.log(mainConfigs);
  config = mainConfigs;
  return true;
}).catch((err) => {
  console.log('errors below');
  console.log(err);
});
app.get('/api/meetups/:lat/:lon', (req, res) => {
  const lat = req.params.lat;
  const lon = req.params.lon;

  var options = {
    method: 'GET',
    url: 'https://api.meetup.com/2/groups/',
    qs: {
      key: config.meetUpApiKey,
      // sign: 'true',
      lat: lat,
      lon: lon,
      radius: '5'
      // 'photo-host': 'public',
      // page: '20'
    },
    headers: {
      'cache-control': 'no-cache'
    }
  };

  request(options, (error, response, body) => {
    if (error)
      throw new Error(error);

    console.log(body);
    return res.json(JSON.parse(body))
  });
});
app.get('/api/coords/:lat/:lon', (req, res) => {
  const lat = req.params.lat;
  const lon = req.params.lon;

  var options = {
    method: 'GET',
    url: 'https://api.coord.co/v1/bike/location',
    qs: {
      access_key: config.coordApiKey,
      latitude: lat,
      longitude: lon,
      radius_km: 100,
    },
    headers: {
      'cache-control': 'no-cache'
    }
  };

  request(options, (error, response, body) => {
    if (error)
      throw new Error(error);

    console.log(body);
    return res.json(JSON.parse(body))
  });
});

app.post('/api/route-details/:route_code/:direction', (req, res) => {
  try{
    const route_code = req.params.route_code;
    const direction =  req.params.direction;
    if(!route_code){
      return res.status(400).json({
        status:'error',
        message:'please specify route code in url'
      });
    }
    if(!direction || (direction !=='a' && direction !=='b' )){
      return res.status(400).json({
        status:'error',
        message:'please specify direction code in url e.g. a or b'
      });
    }

      const latestResources = req.body.latestResources;
      if(!latestResources){
        return res.status(400).json({
          status:'error',
          message:'latestResources node not present in request body'
        });
      }

      if(!latestResources.videoUrl){
        return res.status(400).json({
          status:'error',
          message:'videoUrl node not present inside latestResources node'
        });
      }
      if(!latestResources.videoLeftUrl){
        return res.status(400).json({
          status:'error',
          message:'videoLeftUrl node not present inside latestResources node'
        });
      }
      if(!latestResources.videoRightUrl){
        return res.status(400).json({
          status:'error',
          message:'videoRightUrl node not present inside latestResources node'
        });
      }
      if(!latestResources.videoBackUrl){
        return res.status(400).json({
          status:'error',
          message:'videoBackUrl node not present inside latestResources node'
        });
      }
      if(!latestResources.KmlUrl){
        return res.status(400).json({
          status:'error',
          message:'KmlUrl node not present inside latestResources node'
        });
      }


      const ref = firebaseApp.database().ref();
      const update = {};
      update['route-details/'+route_code+'/latestResources/'+direction] = latestResources;
      ref.update(update, (error) => {
        if (error) {
          console.log("Error updating data:", error);
          return res.status(500).json({
            status:'ok',
            message:'error while saving the data in firebase'
          });
        }else{
          console.log('Write Success');
        }
        return res.status(200).json({
          status:'ok',
          message:'resources updated successfully'
        });
      });
  }catch(err){
    return res.status(400).json({
      status:'error',
      message:err.message,
      error_data: err.stack
    });
  }

});
// app.get('/api/2',(request,response) => {
//  response.send("Hello 2 from Firebase!");
// });
exports.app = functions.https.onRequest(app);
