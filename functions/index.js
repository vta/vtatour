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
});
app.get('/api/meetups/:lat/:lon', (req, res) => {
  const lat = req.params.lat;
  const lon = req.params.lon;

  var options = {
    method: 'GET',
    url: 'https://api.meetup.com/2/open_venues',
    qs: {
      key: config.meetUpApiKey,
      sign: 'true',
      lat: lat,
      lon: lon,
      'photo-host': 'public',
      page: '20'
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
      radius_km: 1,
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
// app.get('/api/2',(request,response) => {
//  response.send("Hello 2 from Firebase!");
// });
exports.app = functions.https.onRequest(app);
