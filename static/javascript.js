$(document).ready(function() {
    $("a#exploreberlin").click(function() { load_venues('explore/berlin') });
    $("a#explorehamburg").click(function() { load_venues('explore/hamburg') });
    $("a#explorelondon").click(function() { load_venues('explore/london') });
    $("a#exploremuenchen").click(function() { load_venues('explore/muenchen') });
    $("a#lastcheckins").click(function() { load_venues('lastcheckins') });
    $("a#todo").click(function() { load_venues('todo') });
    
    $("#checkbox-wheelchair-unknown").click(function(){$(".wheelchair-unknown").toggle();} );
    $("#checkbox-wheelchair-yes").click(function(){$(".wheelchair-yes").toggle();} );
    $("#checkbox-wheelchair-no").click(function(){$(".wheelchair-no").toggle();} );
    $("#checkbox-wheelchair-limited").click(function(){$(".wheelchair-limited").toggle();} );
    
});

var load_venues = function(url) {
    $('#venues').html("Loading venues from foursquare... <br/><img alt='Loading' src='/static/ajax-loader-big.gif'/>");
    $.ajax({
        url: "/foursquare/venues/" + url,
        success: function( html ) {
            $('#venues').html(html);
            load_wheelmap_info()
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
                $(div).find('.wheelmapinfo>p').html("<a href='http://wheelmap.org/nodes/" + r.wheelmap_id + "'>Wheelmap</a><br/>Wheelchair: " + r.wheelchair + "<br>Description: " + r.wheelchair_description);
                $(div).find('.map img.mapmarker').attr("src", "http://wheelmap.org/marker/" + r.wheelchair + ".png")
            } else {
                $(div).addClass("wheelchair-unknown");
                $(div).find('.nodeheadline').html("Not found on wheelmap");
                $(div).find('.wheelmapinfo>p').html("Look for it yourself on <a href='http://wheelmap.org/en/?lat="+$(div).data('lat')+"&lon="+$(div).data('lng')+"&zoom=17'>wheelmap</a>");
                $(div).find('.map img.mapmarker').attr("src", "http://wheelmap.org/marker/unknown.png")
            }
        }
        });  
    });
};


