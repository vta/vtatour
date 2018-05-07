/*
Copyright (c) 2015 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/

(function(document) {
  'use strict';

  window.onerror = function (msg, url, lineNo, columnNo, error) {
    // ... handle error ...
    console.log('Error Debugging');
    console.log('Line No:'+lineNo);
    console.log('Message:'+msg);
    console.log('error details');
    console.log(error);


    return false;
  }
  // Learn more about auto-binding templates at http://goo.gl/Dx1u2g
  var app = document.querySelector('#app');
  var poisBtn;
  var backBtn;
  var viewsBtn;

  // Sets app default base URL
  app.baseUrl = '/';
  if (window.location.port === '') {  // if production
    // Uncomment app.baseURL below and
    // set app.baseURL to '/your-pathname/' if running from folder in production
    // app.baseUrl = '/polymer-starter-kit/';
  }

  app.displayInstalledToast = function() {
    // Check to make sure caching is actually enabled—it won't be in the dev environment.
    if (!Polymer.dom(document).querySelector('platinum-sw-cache').disabled) {
      Polymer.dom(document).querySelector('#caching-complete').show();
    }
  };

  // Listen for template bound event to know when bindings
  // have resolved and content has been stamped to the page
  app.addEventListener('dom-change', function() {
    console.log('Our app is ready to rock!');

    poisBtn = Polymer.dom(document).querySelector('#poisBtn');
    backBtn = Polymer.dom(document).querySelector('#backBtn');
    viewsBtn = Polymer.dom(document).querySelector('#viewsBtn');

    backBtn.addEventListener('click', app.back);
  });

  // See https://github.com/Polymer/polymer/issues/1381
  window.addEventListener('WebComponentsReady', function() {
    // imports are loaded and elements have been registered
  });

  // Listen for size changes to display menu options accordingly
  window.addEventListener('resize', function() {

  });

  // Main area's paper-scroll-header-panel custom condensing transformation of
  // the appName in the middle-container and the bottom title in the bottom-container.
  // The appName is moved to top and shrunk on condensing. The bottom sub title
  // is shrunk to nothing on condensing.
  window.addEventListener('paper-header-transform', function(e) {
    var appName = Polymer.dom(document).querySelector('#mainToolbar .app-name');
    var middleContainer = Polymer.dom(document).querySelector('#mainToolbar .middle-container');
    var bottomContainer = Polymer.dom(document).querySelector('#mainToolbar .bottom-container');
    var detail = e.detail;
    var heightDiff = detail.height - detail.condensedHeight;
    var yRatio = Math.min(1, detail.y / heightDiff);
    // appName max size when condensed. The smaller the number the smaller the condensed size.
    var maxMiddleScale = 0.50;
    var auxHeight = heightDiff - detail.y;
    var auxScale = heightDiff / (1 - maxMiddleScale);
    var scaleMiddle = Math.max(maxMiddleScale, auxHeight / auxScale + maxMiddleScale);
    var scaleBottom = 1 - yRatio;

    // Move/translate middleContainer
    Polymer.Base.transform('translate3d(0,' + yRatio * 100 + '%,0)', middleContainer);

    // Scale bottomContainer and bottom sub title to nothing and back
    Polymer.Base.transform('scale(' + scaleBottom + ') translateZ(0)', bottomContainer);

    // Scale middleContainer appName
    Polymer.Base.transform('scale(' + scaleMiddle + ') translateZ(0)', appName);
  });

  // Scroll page to top and expand header
  app.scrollPageToTop = function() {
    app.$.headerPanelMain.scrollToTop(true);
  };

  app.setAppName = function(appName) {
    app.$.appName.attributes['data-app-name'] = app.$.appName.innerText;
    app.$.appName.innerText = appName;
  };

  app.resetAppName = function() {
    var dataAppName = app.$.appName.attributes['data-app-name'];

    if (dataAppName) {
      app.$.appName.innerText = dataAppName;
    }
  };

  app.showBackBtn = function() {
    if (backBtn) {
      backBtn.style.display = 'block';
    }
  };

  app.hideBackBtn = function() {
    if (backBtn) {
      backBtn.style.display = 'none';
    }
  };

  app.showViewsBtn = function() {
    if (viewsBtn) {
      viewsBtn.style.display = 'block';
    }
  };

  app.hideViewsBtn = function() {
    if (viewsBtn) {
      viewsBtn.style.display = 'none';
    }
  };



  app.showPOIsBtn = function() {
    if (poisBtn) {
      poisBtn.style.display = 'block';
    }
  };

  app.hidePOIsBtn = function() {
    if (poisBtn) {
      poisBtn.style.display = 'none';
    }
  };

  app.condenseHeader = function() {
    app.$.headerPanelMain.scrollToTop(true);
  };

  app.back = function(){
    page.back("/");
  };

})(document);
