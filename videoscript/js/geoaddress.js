// This example displays an address form, using the autocomplete feature
// of the Google Places API to help users fill in the information.

var placeSearch, autocomplete, autocomplete2;
var componentForm = {
  street_number: 'short_name',
  route: 'long_name',
  locality: 'long_name',
  administrative_area_level_1: 'short_name',
  country: 'long_name',
  postal_code: 'short_name'
};

function initAutocomplete() {
  // Create the autocomplete object, restricting the search to geographical
  // location types.
  startpoint = new google.maps.places.Autocomplete(
    /** @type {!HTMLInputElement} */
    (document.getElementById('startpoint')), {
      types: ['geocode']
    });

  // When the user selects an address from the dropdown, populate the address
  // fields in the form.
  startpoint.addListener('place_changed', function() {
    fillInAddress(startpoint, "start");
  });

  endpoint = new google.maps.places.Autocomplete(
    /** @type {!HTMLInputElement} */
    (document.getElementById('endpoint')), {
      types: ['geocode']
    });
  endpoint.addListener('place_changed', function() {
    fillInAddress(endpoint, "end");
  });

}

function fillInAddress(autocomplete, unique) {
  // Get the place details from the autocomplete object.
  var place = autocomplete.getPlace(); 
  console.log(place);
  var lat = place.geometry.location.lat();
  var lng = place.geometry.location.lng();
  for (var component in componentForm) {
    if (!!document.getElementById(component + unique)) {
      document.getElementById(component + unique).value = '';
      document.getElementById(component + unique).disabled = false;
    }
  }
 
  document.getElementById(unique+"_cordinates").value = lat+","+lng;
   
  
}
google.maps.event.addDomListener(window, "load", initAutocomplete);

function geolocate() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
      var geolocation = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      };
      var circle = new google.maps.Circle({
        center: geolocation,
        radius: position.coords.accuracy
      });
      autocomplete.setBounds(circle.getBounds());
    });
  }
}
