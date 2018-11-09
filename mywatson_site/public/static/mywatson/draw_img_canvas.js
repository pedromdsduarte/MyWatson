var canvas = document.getElementById('img_canvas')
var context = canvas.getContext('2d')
var ctx = context

make_base(imgurl)

var drawn = {}

function make_base(imgurl) {

  var dpr = window.devicePixelRatio; //used to remove pixelization
  canvas.width = 1024 * dpr;
  canvas.height = 576 * dpr;

  base_image = new Image();
  base_image.src = imgurl;

  base_image.onload = function() {
    context.drawImage(base_image, 0, 0, canvas.width, canvas.height);
  }

}
