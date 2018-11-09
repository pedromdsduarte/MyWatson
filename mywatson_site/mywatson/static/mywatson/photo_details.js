/* ++++++++++++++++++++++++++++++++
			TOOLTIPS
++++++++++++++++++++++++++++++++ */

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});



/* ++++++++++++++++++++++++++++++++
			  ADD TAG
++++++++++++++++++++++++++++++++ */

var wrapper = document.createElement('div')
wrapper.className = 'add-tag-wrapper'
// var add_tag = document.createElement('div')
// add_tag.className = 'add-tag-btn'
// $(add_tag).append('<span class=\'ti-plus\'></span>')
// $(wrapper).append(add_tag)


$('#add-tag-btn').click(function(e) {

    var adding = $('#add-tag-btn')[0].classList.toggle('ti-minus')

    e.preventDefault();


    if (adding) {

        /* ****************** CREATE FORM ****************** */

        var form = document.createElement('form')
        form.className = 'add-tag-form'
        $(form).css('width', '0px')
        $('<input>').attr({'type': 'text', 'maxlength': 100}).appendTo(form);


        /* ****************** CREATE ANCHOR ****************** */

        var new_tag_li = document.createElement('li')
        var new_tag_a = document.createElement('a')
        $(new_tag_a).hide()
        var category = 'label'

        new_tag_a.className = 'tag-a ' + category
        new_tag_a.id = 'new-tag'
        $(new_tag_a).append(form)

        $(new_tag_a).append('<span class=\'ti-check add-tag-submit-btn\'></span>')

        $(new_tag_li).append(new_tag_a)
        $('.tags-list').append(new_tag_li)


        $(new_tag_a).show()
        $(form).animate({'width': '130px'})


        var offset = $(new_tag_a).offset();
        offset.left -= 20;
        offset.top -= 20;
        $('html, body').animate({
            scrollTop: offset.top,
            scrollLeft: offset.left
        }, 'slow');


        $('.add-tag-submit-btn').click(function(e) {
    		e.preventDefault();
    		var new_tag = $(this).siblings('.add-tag-form').find('input').val()

    		create_tag(new_tag)

            $('#add-tag-btn')[0].classList.toggle('ti-minus')

    		// $(add_tag).trigger('click')

    	})

        $(form).keypress(function(e) {
            if (e.which == 13) {
                $('.add-tag-submit-btn').trigger('click')
                return false;
            }
        })


    }

    else {

        /* ****************** REMOVE FORM ****************** */


        $('#new-tag').find('form').animate({'width': '0px'}, function(){
            $('#new-tag').remove();
        })


    }


});

$('.tags-wrapper').append(wrapper)
// $('.tags-wrapper').append('<span id=\'retag-btn\' class=\'ti-reload\' data-toggle=\'modal\' data-target=\'#confirmation-retag-modal\'></span>')


function create_tag(tag) {

    /* ***************** CREATE NEW TAG ELEMENT ***************** */

    var new_tag_element = $('#new-tag')
    $(new_tag_element).find('form').remove()

    $(new_tag_element).text(tag)

    /* ***************** CREATE REMOVAL BUTTON ***************** */

    var rem_icon = document.createElement("span")
    rem_icon.className = 'rem-tag ti-close'

    $(rem_icon).attr("data-toggle", "confirmation");
    $(rem_icon).attr("data-placement", "top");
    $(rem_icon).attr("data-singleton", "true");
    $(rem_icon).attr("data-title", " ");

    $(rem_icon).click(function(e) {
        if (!e) var e = window.event;
        e.cancelBubble = true;
        if (e.stopPropagation) e.stopPropagation();
    });

    $(new_tag_element).append(rem_icon)


    data = {'new_tag': tag}
    post_data(CONST_URL, data, function(){}).done(function(result) {
        $(new_tag_element).attr('id', result['new_tag_id'])
    })


    $('[data-toggle="confirmation"]').confirmation({
        rootSelector: '[data-toggle=confirmation]',
        title: 'Delete tag?',
        btnOkClass: 'btn btn-sm btn-danger',
    	onConfirm: function() {

            var tag = $(this).parent()
            remove_tag(tag)
    	}
    });

}

/* ++++++++++++++++++++++++++++++++
			REMOVE TAG
++++++++++++++++++++++++++++++++ */

$('[data-toggle="confirmation"]').confirmation({
    rootSelector: '[data-toggle=confirmation]',
    title: 'Delete tag?',
    btnOkClass: 'btn btn-sm btn-danger',
	onConfirm: function() {

        var tag = $(this).parent()
        remove_tag(tag)
		// e.preventDefault();
        //
        // if (!e) var e = window.event;
    	// e.cancelBubble = true;
    	// if (e.stopPropagation) e.stopPropagation();
        //
		// var tag = element.parent()
		// remove_tag(tag)
	}
});

/* ++++++++++++++++++++++++++++++++
			  CONTROL
++++++++++++++++++++++++++++++++ */

$('.navbar').removeClass('navbar-fixed-top')

$('#confirm-delete-photo').click(function() {
	$('#remove-photo-input').trigger('click');
})

$("#prev-btn").click(function(event) {
	document.location.href = CONST_PREV_URL;
});
$("#next-btn").click(function(event) {
	document.location.href = CONST_NEXT_URL;
});


/* ++++++++++++++++++++++++++++++++
			RETAG PHOTO
++++++++++++++++++++++++++++++++ */

$('#confirm-retag-photo').click(function() {
	photo_id = document.location.href.split('/')[4]
	document.title = "Re-tagging photo..."
	$('.dim').show()
	$('#loading-modal').show()
	post_data(CONST_URL, {'retag': photo_id}, function(){
		location.reload()
	})
})

/* ++++++++++++++++++++++++++++++++
			CANVAS DRAWING
++++++++++++++++++++++++++++++++ */

$(".tag-a.face").click(function(e) {

	var tag = $(this).text()
	var id = $(this).attr('id')
	if (CONST_TAGS[id] == null) {
		return
	}
	var box = CONST_TAGS[id][0]
	if ($(this).hasClass('displaying')) {
		$(this).removeClass('displaying')
		delete CONST_ENABLED_BOXES[id];
		clear()
		redraw_all()

	}
	else {
		$(this).addClass('displaying')
		draw(box)
		CONST_ENABLED_BOXES[id] = box
	}

});

var canvas = document.getElementById("cv");
var dpr = window.devicePixelRatio; //used to remove pixelization
canvas.width = 1024 * dpr;
canvas.height = 576 * dpr;

var ctx = canvas.getContext("2d");


function remove_tag(tag) {
	var tag_id = tag.attr('id')
	var url = CONST_URL

	data = {'remove_tag': 'True', 'tag_id': tag_id},
	post_data(url, data, function(){})

    // $(tag).hide(500, function() {
    //     $(tag).remove();
    // })

    $(tag).animate({'opacity': '0'}, function() {
        $(tag).remove();
    })

	delete CONST_ENABLED_BOXES[tag_id];
	clear()
	redraw_all()
}

function post_data(url, data, callback) {

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

	data = $.ajax({
		"type": "POST",
		"url": url,
		"data": data,
		"traditional": "true",
		"beforeSend": function(xhr, settings) {
			$.ajaxSettings.beforeSend(xhr, settings);
		},
		"success": function(data) {
			callback()
			console.log("success");
		},
		"failure": function(data) {
			console.log("failure");
		},
	});

	return data;

}

function clear() {
	ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function redraw_all() {
	for (var id in CONST_ENABLED_BOXES) {
		if (CONST_ENABLED_BOXES.hasOwnProperty(id)) {
			draw(CONST_ENABLED_BOXES[id])
		}
	}
}

function draw(rect) {
	// console.log("drawing")
	ctx.strokeStyle = '#7FFF00';
	ctx.lineWidth = 4;

	var coords = correct_coords(rect)

	x1 = coords[0]
	y1 = coords[1]

	x2 = coords[2]
	y2 = coords[3]
	width = x2 - x1
	height = y2 - y1
	ctx.strokeRect(x1, y1, width, height);

}

function resize_coords(coords) {
	Rx = canvas.width / CONST_VIEW_WIDTH
	Ry = canvas.height / CONST_VIEW_HEIGHT
	var new_coords = [coords[0] * Rx, coords[1] * Ry,
	coords[2] * Rx, coords[3] * Ry
	]
	return new_coords
}

function correct_coords(rect) {
	coords = []
	for (i = 0; i < rect.length; i++)
		coords.push(parseInt(rect[i]))

	coords = resize_coords(coords)

	return coords
}



$('.menu-wrapper').click(function() {
    var toggled = $(this)[0].classList.toggle('change');
    var menu = $('.menu-panel')

    if (toggled) {
        $(menu).slideToggle('fast')
    } else {
        $(menu).slideToggle('fast')
    }


})
