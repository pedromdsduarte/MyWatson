var canvas = document.getElementById('img_canvas')
var context = img_canvas.getContext('2d'),
        ctx = context

var img = new Image();
img.src = imgurl;

img.onload = function() {

  var dpr = window.devicePixelRatio; //used to remove pixelization
  canvas.width = img.width * dpr;
  canvas.height = img.height * dpr;

  base_image = new Image();
  base_image.src = imgurl;

  base_image.onload = function() {
    context.drawImage(base_image, 0, 0, canvas.width, canvas.height);
  }
  context.strokeStyle = 'blue';
  context.lineWidth = 5;
}

var rect = {}
drag = false;
var mouse_down = false;
////////////////////////////////////////////////////////////////////////////////

function init() {
  canvas.addEventListener('mousedown', mouseDown, false);
  canvas.addEventListener('mouseup', mouseUp, false);
  canvas.addEventListener('mousemove', mouseMove, false);
}

function mouseDown(e) {

  var mouseX = e.clientX - context.canvas.offsetLeft;
  var mouseY = e.clientY - context.canvas.offsetTop;

  rect.startX = mouseX * canvas.width / canvas.clientWidth;
  rect.startY = mouseY * canvas.height / canvas.clientHeight;

  mouse_down = true;
  remove_button();
}

function mouseUp() {

  rect.endX = rect.startX + rect.w
  rect.endY = rect.startY + rect.h
  //console.log("Rectangle: ("+rect.startX+", "+ rect.startY+") -> " + "("+rect.endX+", "+ rect.endY+")")
  if (drag && rect.w > 0 && rect.h > 0) {
    spawn_button();

  }
  drag = false;
  mouse_down = false;

  //context.globalAlpha = 1
  //context.drawImage(base_image, 0, 0, canvas.width, canvas.height);
  //context.strokeRect(rect.startX, rect.startY, rect.w, rect.h);
}

function mouseMove(e) {
  if (mouse_down) {
    drag = true;
    var mouseX = e.clientX - context.canvas.offsetLeft;
    var mouseY = e.clientY - context.canvas.offsetTop;

    var canvasX = mouseX * canvas.width / canvas.clientWidth;
    var canvasY = mouseY * canvas.height / canvas.clientHeight;

    rect.w = canvasX - rect.startX;
    rect.h = canvasY - rect.startY;

    draw();
  }
}

function draw() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.globalAlpha = 0.7
  context.drawImage(base_image, 0, 0, canvas.width, canvas.height);
  context.globalAlpha = 1
  context.strokeRect(rect.startX, rect.startY, rect.w, rect.h);
}

function spawn_button() {
  remove_button()

  var BUTTON_WIDTH = 45
  var BUTTON_HEIGHT = 25
  var DIST_BETWEEN_BTN_INPUT = 3
  var DIST_BETWEEN_BTN_CANVAS_H = 0
  var DIST_BETWEEN_BTN_CANVAS_V = -40

  button_coordinates = to_abs_coordinates(rect.startX, rect.startY)
  button_x = button_coordinates[0] + DIST_BETWEEN_BTN_CANVAS_H
  button_y = button_coordinates[1] - context.lineWidth - DIST_BETWEEN_BTN_CANVAS_V

  var button = document.createElement("button")
  button.id = 'add_button'
  button.style.width = BUTTON_WIDTH + "px"
  button.style.height = BUTTON_HEIGHT + "px"
  button.style.left = button_x + "px"
  button.style.top = button_y + "px"
  button.innerHTML = "Add"
  button.addEventListener("click", button_pressed);

  var input = document.createElement('input')
  input.id = 'add_input'
  input.type = "text"
  input.placeholder = "Label..."
  //input.style.position = "absolute"
  input.style.left = button_x + BUTTON_WIDTH + DIST_BETWEEN_BTN_INPUT + "px"
  input.style.top = button_y + "px"
  input.style.height = BUTTON_HEIGHT
  //console.log("input:", input.style.left, ",", input.style.top)

  document.body.appendChild(button)
  document.body.appendChild(input)
}

function remove_button() {
  var btn = document.getElementById('add_button')
  var input = document.getElementById('add_input')
  if (btn != null)
    btn.parentNode.removeChild(btn)
  if (input != null)
    input.parentNode.removeChild(input)
}

////////////////////////////////////////////////////////////////////////////////

function to_canvas_coordinates(x, y) {
  var canvasX = x * canvas.width / canvas.clientWidth;
  var canvasY = y * canvas.height / canvas.clientHeight;
  return [canvasX, canvasY]
}

function to_abs_coordinates(x, y) {
  var absX = x * canvas.clientWidth / canvas.width;
  var absY = y * canvas.clientHeight / canvas.height;
  return [absX, absY]
}

function button_pressed() {
  var input = document.getElementById('add_input')
  var tag = input.value
  if (tag == '')
    return

  var post_url = '/mywatson/' + photo_id + '/add-tag'
  var res_w = canvas.width
  var res_h = canvas.height
  var data = {
    'photo_id': photo_id,
    'tag': tag,
    'startX': rect.startX,
    'startY': rect.startY,
    'endX': rect.endX,
    'endY': rect.endY,
    'resized_w': res_w,
    'resized_h': res_h,
  }

  context.clearRect(0, 0, canvas.width, canvas.height);
  context.strokeStyle = '#7FFF00';
  draw();
  context.strokeStyle = 'blue';

  $.ajax({
    "type": "POST",
    "url": post_url,
    "data": data,
    "beforeSend": function(xhr, settings) {
      console.log("Before Send");
      $.ajaxSettings.beforeSend(xhr, settings);
    },
    "success": function(data) {
      console.log("success");
    },
    "failure": function(data) {
      console.log("failure");
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.strokeStyle = 'red';
      draw();
      context.strokeStyle = 'blue';
    },
  });
}

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
      // Only send the token to relative URLs i.e. locally.
      xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
  }
});

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie != '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = jQuery.trim(cookies[i]);
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) == (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

init()
