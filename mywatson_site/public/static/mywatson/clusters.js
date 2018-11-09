var edit_mode = false;

function allowDrop(ev) {
    if (edit_mode)
        ev.preventDefault();
}

function drag(ev) {
    if (edit_mode)
        ev.dataTransfer.setData("face", ev.target.id);
}

function drop(ev) {
    if (edit_mode) {
        ev.preventDefault();
        var data = ev.dataTransfer.getData("face");
        target = ev.target
		anchor = document.getElementById("anchor_" + data)

        if (target.classList.contains('div-cluster')){
            target.appendChild(anchor)

            // Currently appending the anchor instead of the image
            // target.appendChild(document.getElementById(data));
        }

		else if (target.classList.contains('img-thumbnail')) {
			target = target.closest('.div-cluster')
			target.appendChild(anchor)
		}

    }
}


/* ************** Edit mode toggling ************** */

function toggle_edit_mode() {
    var new_cursor;
    var status;
    edit_mode = !edit_mode;

    if (edit_mode) {
        status = 'ON'
        $('.img-thumbnail').addClass('img-movable')
        $('.div-cluster').addClass('div-droppable')
		document.getElementById("cluster-slider").disabled = true;
		document.getElementById("cluster-slider").classList.add('disabled')
    }
    else {
        status = 'OFF'
        $('.img-thumbnail').removeClass('img-movable')
        $('.div-cluster').removeClass('div-droppable')
		document.getElementById("cluster-slider").disabled = false;
		document.getElementById("cluster-slider").classList.remove('disabled')
    }
    toggle_links(edit_mode);
    toggle_editable_cluster_name(edit_mode);

    $('#edit-mode-btn').html('Edit mode is ' + status);
}

function toggle_links(edit_enabled) {
    if (edit_enabled) {
        console.log("Links disabled")
        $(".a-thumbnail").click(function(e) {
            e.preventDefault();
        })
    } else {
        $('.a-thumbnail').unbind('click')
        console.log("Links enabled")
    }

}

function toggle_editable_cluster_name(edit_enabled) {
    //h1_cluster_names = $(".h1-cluster-name")
	h1_cluster_names = $(".leg-cluster-name")
    h1_cluster_names.attr('contenteditable', edit_enabled);

    if (edit_enabled) {
        h1_cluster_names.addClass("cluster-name-editable")
    } else {
        h1_cluster_names.removeClass("cluster-name-editable")
    }
}



/* ************** Changes saving ************** */

function save_changes() {
    console.log("Saving changes")

    // dictionary: cluster_id -> list of faces in that cluster
    var clusters = {}
    var cluster_names = {}
    $('.div-cluster').each(function() {
        cluster_div = $(this)

        cluster_id = cluster_div[0].id
        clusters[cluster_id] = []
        //cluster_names[cluster_id] = $('#' +  cluster_id + '.h1-cluster-name').html()
		cluster_names[cluster_id] = $('#' +  cluster_id + '.leg-cluster-name').html()
        cluster_div.children('.a-thumbnail').each(function() {

            //id of the anchors are "anchor_##", this gets just the ##
            face_id =  $(this)[0].id.split("_")[1]
            clusters[cluster_id].push(face_id)
        })
    })

    var data = {
        'cluster_names': JSON.stringify(cluster_names),
        'clusters': JSON.stringify(clusters),
    };
    send_changes(data);

    var save_btn = $('#save-btn');
    var label = $('#save-label');
    label.css('display', 'inline-block')
    label.html('Saved changes!')
    setTimeout(function() {
        label.fadeOut(2000, function() {
            label.css('display', 'none');
        })},
        5000);

}

/* ************** Cluster display ************** */

function get_clusters_from_json(cluster_json) {
    var json_raw_data = (cluster_json.replace(/&(l|g|quo)t;/g, function(a,b){
                return {
                    l   : '<',
                    g   : '>',
                    quo : '"'
                }[b];
            }));

    data = JSON.parse(json_raw_data);

    // clusters: n_clusters -> clusterlist
    // clusterlist: list of {} containing the fields of the facecluster object
    var clusters = {}

    for (var i = 0; i < data.length; i++) {
        var obj = data[i];
        var id = obj['pk']
        var fields = obj['fields']
        var n_clusters = fields['n_clusters']
        if (!(n_clusters in clusters)) {
            clusters[n_clusters] = []
        }
        var with_id = Object.assign({'id':id}, fields);
        clusters[n_clusters].push(with_id)
    }
    return clusters
}

function display_clusters(cluster_indexes, n) {

	if (n == -1) {
		n = cluster_indexes[0]
	}

    //$('.h1-cluster-name').remove()
	$('.leg-cluster-name').remove()
    $('.div-cluster').remove()

    for (var i = 0; i < n; i++) {
        var cluster_div = document.createElement('div');
        cluster_div.className = 'div-cluster'
        cluster_div.id = i
        cluster_div.setAttribute('ondrop', 'drop(event)')
        cluster_div.setAttribute('ondragover', 'allowDrop(event)')


		/*
        var h = document.createElement('H1')
        $(h).html('')
        h.className = 'h1-cluster-name'
        h.id = i
        h.setAttribute('maxlength', '100')
		*/

        //$('.cluster-container').append(h)
		//cluster_div.append(h)
        $('.cluster-container').append(cluster_div)

		var leg = document.createElement("LEGEND");
		leg.className = 'leg-cluster-name'
		leg.id = i
		$(leg).html('')
		cluster_div.append(leg)

    }

    for (key in clusters[n]) {
        cluster = clusters[n][key]
        var cluster_id = cluster['cluster_id']
        var cluster_div = $('#' + cluster_id + '.div-cluster')
        var id = cluster['id']

        var anchor = document.createElement('a')
        anchor.className = 'a-thumbnail'
        anchor.id = 'anchor_' + cluster['face']
        anchor.href = cluster['photo_url']

        var img = document.createElement('IMG')
        img.id = cluster['face']
        img.className = 'img-thumbnail'
        img.src = MEDIA_FOLDER + '/' + cluster['face_url']
        img.width = 200
        img.setAttribute('draggable','true')
        img.setAttribute('ondragstart','drag(event)')

        anchor.append(img)
        cluster_div.append(anchor)

        //$('#' + cluster_id + '.h1-cluster-name').html(cluster['name'])
		$('#' + cluster_id + '.leg-cluster-name').html(cluster['name'])

    }

    $('.silhouete-score').html('Cluster score:<br>' + clusters[n][0]['silhouette_score'])
}


/* ************** Slider Controller ************** */

function sortProperties(obj) {
  // convert object into array
	var sortable=[];
	for(var key in obj)
		if(obj.hasOwnProperty(key))
			sortable.push([key, obj[key]]); // each item is an array in format [key, value]

	// sort items by value
	sortable.sort(function(a, b) {
	  return a[1]-b[1]; // compare numbers
	});
	return sortable.reverse(); // array in format [ [ key1, val1 ], [ key2, val2 ], ... ]
}

function init_slider(n) {

    var cl_list = Object.keys(clusters)

    /////////////////////////////////////////////////////

    // Mapping indexes to n_cluster
    var scores = {}
    for (var n_cluster in clusters) {
        score = clusters[n_cluster][0]['silhouette_score']
        if (!(n_cluster in scores)) {
            scores[n_cluster] = score
        }
    }

    var sorted = sortProperties(scores)
    var cluster_indexes = []
    for (var i = 0; i < sorted.length; i++) {
        cluster_indexes.push(parseInt(sorted[i][0]))
    }

    /////////////////////////////////////////////////////

    // Initializing the slider
    var slider = document.getElementById("cluster-slider");
    slider.min = 0
    slider.max = cl_list.length - 1;
    // slider.value = cluster_indexes.indexOf(parseInt(n))
	if (n == -1) {
		slider.value = 0
	} else {
		slider.value = cluster_indexes.indexOf(parseInt(n))
	}

    // What to do when the slider moves
    slider.oninput = function() {
        cluster = cluster_indexes[this.value]
        display_clusters(cluster_indexes, cluster);
        $('.slider-value').html(cluster_indexes[this.value]);
        // change_bubble_position(this, cluster_indexes[this.value]);
    }


    $('.slider-value').html(cluster_indexes[0])
	$(slider).trigger('input');

	return cluster_indexes
}

function change_bubble_position(slider, cluster) {
    var control = $(slider),
        controlMin = control.attr('min'),
        controlMax = control.attr('max'),
        controlVal = control.val(),
        controlThumbWidth = control.data('thumbwidth');

    var range = controlMax - controlMin;

    var position = ((controlVal - controlMin) / range) * 100;
    var positionOffset = Math.round(controlThumbWidth * position / 100) - (controlThumbWidth / 8);
    console.log(controlThumbWidth / 8)
    var output = control.next('output');

    output
        .css('left', 'calc(' + position + '% - ' + positionOffset + 'px)')
        .text(cluster);
}

/* ************** AJAX Data sending ************** */

function send_changes(data) {
    var post_url = '/mywatson/people'
    $.ajax({
      "type": "POST",
      "url": post_url,
      "data": data,
      "traditional": "true",
      "beforeSend": function(xhr, settings) {
        $.ajaxSettings.beforeSend(xhr, settings);
      },
      "success": function(data) {
        console.log("success");
      },
      "failure": function(data) {
        console.log("failure");
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
