$(document).ready(function() {
    
    $(".load-venues-link").click(function(e) {
            e.preventDefault();
            load_venues( $(this).attr('href') );
    });
      
    $(".wheelchair-filter-checkbox").click( update_filter );
    
    $("[rel='tooltip']").tooltip();
    
    $('#loadmorevenues-button').click(function(){ 
        load_venues( $(this).data("current-url"), $(this).data("next-page") );
    });
    
});

var load_venues = function(url, page) {
    if ( typeof page == "undefined" ) 
        page = 0

    // For the first page, clear the screen
    if ( page == 0 )
        $('#venues').html("")
        
    $load_div = $("<div>Loading venues from foursquare... <br/><img alt='Loading' src='/static/ajax-loader-big.gif'/><hr class='soften'></div>");
    
    $('#venues').append($load_div);
        
    $.ajax({
        url: "/foursquare/venues/" + url + "/" + page,
        success: function( html ) {
            $('#venues').append(html);
            $('#loadmorevenues').show();
            $('#loadmorevenues-button').data("next-page", ++page);
            $('#loadmorevenues-button').data("current-url", url);
            load_wheelmap_info();
        },
        error: function() {
            $('#venues').append("<p>There was a problem. We couldn't reach foursquare, sorry!</p>");
        },
        complete: function() {
            $load_div.remove();
        }
    });
}

var load_wheelmap_info = function() {
    $.each( $('div#venues>div.venue'), function(index, div) {
       
        // Load Wheelmap Node
        $.ajax({
        dataType: "json",
        url: "/wheelmap/nodes",
        data: {
            lat: $(div).data('lat'),
            lng: $(div).data('lng'),
            name: $(div).data('name')
        },
        success: function( r ) {
            if ( r.wheelmap ) {
                $(div).addClass("wheelchair-" + r.wheelchair);
                $(div).find('.nodeheadline').html(r.name);
                $(div).find('.wheelmapinfo>p').html("<a href='/static/img/" + r.wheelmap_id + "'>Wheelmap</a><br/>Wheelchair: " + r.wheelchair + "<br>Description: " + r.wheelchair_description);
                $(div).find('.map img.mapmarker').attr("src", "/static/img/" + r.wheelchair + ".png");
            } else {
                $(div).addClass("wheelchair-notfound");
                $(div).find('.nodeheadline').html("Not found on wheelmap");
                $(div).find('.wheelmapinfo>p').html("Look for it yourself on <a href='http://wheelmap.org/en/?lat="+$(div).data('lat')+"&lon="+$(div).data('lng')+"&zoom=17'>wheelmap</a>");
                $(div).find('.map img.mapmarker').attr("src", "/static/img/notfound.png");
            }
            // Hide the ones, that are not wanted
            update_filter();
        },
        error: function() {
            $(div).find('.nodeheadline').html("Error: There was a problem contacting wheelmap.");
        }
        });  
    });
};

var update_filter = function () {
    // Function for filtering the results by wheelchair status
    
    $(".wheelchair-filter-checkbox").each(function() {
        wheelchair_status = $(this).data("wheelchair")
        if ( $(this).is(":checked") ) {
            $(".wheelchair-" + wheelchair_status).show();
        } else {
            $(".wheelchair-" + wheelchair_status).hide();
        }
    });
}


