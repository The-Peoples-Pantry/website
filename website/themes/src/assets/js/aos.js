//
// aos.js
// Theme module
//

'use strict';

(function() {

  //
  // Functions
  //

  function init() {
    var options = {
      duration: 700,
      easing: 'ease-out-quad',
      once: true,
      startEvent: 'load'
    }
    AOS.init(options);
  }


  //
  // Events
  //

  if (typeof AOS !== 'undefined') {
    init();
  }

})();