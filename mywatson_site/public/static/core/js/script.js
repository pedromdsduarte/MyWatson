/*

Style   : MobApp Script JS
Version : 1.0
Author  : Surjith S M
URI     : https://surjithctly.in/

Copyright © All rights Reserved

*/



$(function() {
    "use strict";

    $('html,body').scrollTop(0);


    /*-----------------------------------
     * FIXED  MENU - HEADER
     *-----------------------------------*/
    function menuscroll() {
        var $navmenu = $('.nav-menu');
        if ($(window).scrollTop() > 50) {
            $navmenu.addClass('is-scrolling');
        } else {
            $navmenu.removeClass("is-scrolling");
        }
    }
    menuscroll();
    $(window).on('scroll', function() {
        menuscroll();
    });
    /*-----------------------------------
     * NAVBAR CLOSE ON CLICK
     *-----------------------------------*/

    $('.navbar-nav > li:not(.dropdown) > a').on('click', function() {
        $('.navbar-collapse').collapse('hide');
    });
    /*
     * NAVBAR TOGGLE BG
     *-----------------*/
    var siteNav = $('#navbar');
    siteNav.on('show.bs.collapse', function(e) {
        $(this).parents('.nav-menu').addClass('menu-is-open');
    })
    siteNav.on('hide.bs.collapse', function(e) {
        $(this).parents('.nav-menu').removeClass('menu-is-open');
    })

    /*-----------------------------------
     * ONE PAGE SCROLLING
     *-----------------------------------*/
    // Select all links with hashes
    $('a[href*="#"]').not('[href="#"]').not('[href="#0"]').not('[data-toggle="tab"]').on('click', function(event) {
        // On-page links
        if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
            // Figure out element to scroll to
            var target = $(this.hash);
            target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
            // Does a scroll target exist?
            if (target.length) {
                // Only prevent default if animation is actually gonna happen
                event.preventDefault();
                $('html, body').animate({
                    scrollTop: target.offset().top
                }, 1000, function() {
                    // Callback after animation
                    // Must change focus!
                    var $target = $(target);
                    $target.focus();
                    if ($target.is(":focus")) { // Checking if the target was focused
                        return false;
                    } else {
                        $target.attr('tabindex', '-1'); // Adding tabindex for elements not focusable
                        $target.focus(); // Set focus again
                    };
                });
            }
        }
    });
    /*-----------------------------------
     * FORMS
     *-----------------------------------*/

    $('.form-toggle').click(function() {
        if ($(this).attr("id") == "has-acc") {
            show_form('LOGIN')
        } else {
            show_form('REGISTER')
        }
    })

    $('#login-ready').click(function() {
        show_form('LOGIN')
    })

    $('#register-ready').click(function() {
        show_form('REGISTER')
    })


    $('#click-here-signup').click(function() {
        var form = $('.form-toggle')
        if ($(form).attr('id') == 'no-acc') {
            $(form).trigger('click')
        }
    })

    if (!$('.greetings').length) {
        if (window.matchMedia('(max-width: 1200px)').matches) {
            $('.img-holder').css('padding-bottom', '35%')
        } else {
            $('.img-holder').css('padding-bottom', '30%')
        }
    }


    if ($('#login-error').length) {
        $('#login-ready').trigger('click')
        show_form('LOGIN')
        console.log("login error")
    }

    else if ($('#signup-error').length) {
        $('#login-ready').trigger('click')
        show_form('REGISTER')
        console.log("signup error")
    }

}); /* End Fn */


function show_form(form) {
    if (form === "LOGIN") {
        $('#signup').hide(500)
        $('#login').show(500)
        $('#has-acc').text("I do not have an account!")
        $('#has-acc').attr("id", "no-acc")
    }

    else if (form === "REGISTER") {
        $('#login').hide(500)
        $('#signup').show(500)
        $('#no-acc').text("I already have an account!")
        $('#no-acc').attr("id", "has-acc")
    }

    else {
        console.log("Form not recognized")
    }
}
