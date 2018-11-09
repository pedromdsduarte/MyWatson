var total_files = 0;
var uploaded_files = 0;

$(function () {



    $(".js-upload-photos").click(function () {
        $("#fileupload").click();
    });

    $('#dialog-ok').click(function() {
    	$('#complete-modal').hide();
        $('.dim').hide();

        document.title = 'Upload photos';
    })


    $("#fileupload").fileupload({


        add: function(e, data) {
            var uploadErrors = [];
            var acceptFileTypes = /^image\/(gif|jpe?g|png)$/i;

            file = data.files[0]
            total_files = total_files + 1;

            // console.log("Added file ", file)


            if(data.files.length && !acceptFileTypes.test(file['type'])) {
                uploadErrors.push('The file ' + file['name'] +
                                ' is not an acceptable image!');
            }
            if(data.files.length && file['size'] > 10000000) {
                uploadErrors.push('The file ' + file['name'] +
                                ' is larger than 10MB!');
            }

            if(uploadErrors.length > 0) {
                for (var i = 0; i < uploadErrors.length; i++) {
                    error = uploadErrors[i]
                    $('.div-errors').append(
                        "<span class=\"alert-icon ti-alert\"/>"
                        + "<p class=\"error\">"
                        + error
                        + "</p>")
                }
            } else {
                uploaded_files = uploaded_files + 1;
                data.submit();
            }
        },

        dataType: 'json',
        sequentialUploads: true,  /* 1. SEND THE FILES ONE BY ONE */

        start: function (e) {  /* 2. WHEN THE UPLOADING PROCESS STARTS, SHOW THE MODAL */
            //$("#modal-progress").modal("show");

            document.title = 'Uploading photos...';

            // $('.div-errors').hide(function() {
            //
            // })
            $(".progress-bar").text('0%');
            // $(".progress-bar").animate({"width": 0});
			$(".progress-bar").css('width', '0px');
			$(".progress-bar").css('color', 'white');


            $('.loader').css('display', 'block');
            $('#check-mark').css('display', 'none');
            // $(".progress-bar").css('background-color', '#337ab7');
            $(".progress-bar").css('background', 'linear-gradient(90deg, #003459 0%, #00A8E8 100%)');
            $("#wrapper-tag-progress").css('display', 'none');

            $('.all-progress').css('display', 'block')



        },
        stop: function (e, data) {  /* 3. WHEN THE UPLOADING PROCESS FINALIZE, HIDE THE MODAL */
            // $("#modal-progress").modal("hide");
            uploadDone();
        },
        progressall: function (e, data) {  /* 4. UPDATE THE PROGRESS BAR */
            var progress = parseInt(data.loaded / data.total * 100, 10);
            var strProgress = progress + "%";
            $(".progress-bar").css({"width": strProgress});

			// var anim_queue;
			// $(".progress-bar").stop();
            // $(".progress-bar").animate({"width": strProgress},
			// 							{
			// 								duration: 100,
			// 								easing: "linear",
			// 								queue: "anim_queue"
			// 							});
            $(".progress-bar").text(strProgress);
        },
        done: function (e, data) {

            if (data.result.is_valid) {
                var valid = "Yes"
            }

            else {
                var valid = "No"
            }
            $("#table-progress tbody").prepend(
                "<tr><td class=\"td-img-name\">" + data.result.name + "</td>" +
                "<td>" + data.result.size + "</td>" +
                "<td>" + valid + "</td></tr>")
        }

    });

});

function taggingDone() {

    document.title = 'Upload complete';

    $('.loader').css('display', 'none');
    $('#check-mark').css('display', 'block');
    $('.dim').show();
    $('#complete-modal').show();
}


function uploadDone() {

    document.title = 'Tagging photos...';

    $(".progress-bar").text("Complete! (" + uploaded_files + "/" + total_files + ")");

    if (uploaded_files == total_files) {
        // $(".progress-bar").css('background-color', '#0ba26f');
        // $(".progress-bar").css('color', 'white');
    } else {
        // $(".progress-bar").css('background-color', '#ffe800');
        $(".progress-bar").css('background', 'linear-gradient(135deg, #ffe800 0%, #ffe800 100%)');
        $(".progress-bar").css('color', 'black');
    }

    $("#wrapper-tag-progress").css('display', 'block');

    uploaded_files = 0;
    total_files = 0;

    var post_url = '/mywatson/upload/'
    var data = {
        'upload_done': 'true'
    }

    var ajax_request = $.ajax({
      "type": "POST",
      "url": post_url,
      "data": data,
      "beforeSend": function(xhr, settings) {
        $.ajaxSettings.beforeSend(xhr, settings);
      },
      "success": function(data) {
          taggingDone();

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
