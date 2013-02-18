$(document).ready(function() {
    
    $(".load-venues-link").click(function(e) {
            e.preventDefault();
            load_venues( $(this).attr('href') );
    });
      
    $(".wheelchair-filter-checkbox").click( update_filter );
    
    $("[rel='tooltip']").tooltip();
    
    $('#loadmorevenues-button').click(function(){ 
        load_venues( $(this).data("current-url"), $(this).data("params") );
    });
    
    $('.brand').click(function(e){
        e.preventDefault();
        $('#venues').html("Loading..");
        $('#alert-navigation').hide();
        $('#loadmorevenues').hide();
        $.ajaxQ.abortAll();
        $.get("/", function(r){
            $('#venues').html(r); 
        });
    });
    
    $('#btn-explore-search').click(function(e){
        e.preventDefault();          
        params = {}
        params.geolocation = $("#input-explore-location").val() ? $("#input-explore-location").val() : $("#input-explore-location").attr('placeholder');
        params.query = $("#input-explore-query").val() ? $("#input-explore-query").val() : $("#input-explore-query").attr('placeholder');
            
        load_venues("explore/", params);
    });
    
    $('#btn-node-update').click(function(){
        update_wheelmap_node($(this).data('wheelmap_id'),
                            $('#form-update-status input:checked').val());
    });
    
    // Removing the success/error alert when closed in the modal
    $('#editwheelmap').on('hidden', function () {
        $('#alert-edit-node').removeClass('alert-success alert-error').hide();        
    })
    
    // Keeping track of the ajax calls to abort them
    // From: http://stackoverflow.com/a/11612641/1462065
    $.ajaxQ = (function(){
      var id = 0, Q = {};

      $(document).ajaxSend(function(e, jqx){
        jqx._id = ++id;
        Q[jqx._id] = jqx;
      });
      $(document).ajaxComplete(function(e, jqx){
        delete Q[jqx._id];
      });

      return {
        abortAll: function(){
          var r = [];
          $.each(Q, function(i, jqx){
            r.push(jqx._id);
            jqx.abort();
          });
          return r;
        }
      };

    })();
    
});

var update_wheelmap_node = function(wheelmap_id, wheelchair_status) {
      
        $alert = $('#alert-edit-node');
        $.ajax({
            dataType: "json",
            url: "/wheelmap/update_node/",
            type: "POST",
            data: {
                wheelmapid: wheelmap_id,
                wheelchairstatus: wheelchair_status
            },
            success: function(r) {
                if (r.success) {          
                    $alert.addClass('alert-success');  
                    $alert.text("You successfully updated the node. It will take some time until the change affects wheelmap.");
                } else {
                    $alert.removeClass('alert-success').addClass('alert-error');  
                    $alert.text("Sorry, there was an error updating the node.");
                }
            },
            error: function() {
                $alert.addClass('alert-error');  
                $alert.text("Sorry, there was an error updating the node.");
            },
            complete: function() {
                 $alert.show();
            }
        });
}

var load_venues = function(url, params) {
    if ( typeof params == "undefined" ) 
        params = {}
    if ( typeof params.page == "undefined" ) 
        params.page = 0

    // For the first page, clear the screen
    if ( params.page == 0 )
        $('#venues').html("")
           
    $('#alert-navigation').hide();
    
    $load_div = $("<div>Loading venues from foursquare... <br/><img alt='Loading' src='/static/img/ajax-loader-big.gif'/><hr class='soften'></div>");
    
    $('#venues').append($load_div);
    
    $('#loadmorevenues').hide();
           
    $.ajax({
        url: url,
        data: params,
        success: function( html ) {
            $('#venues').append(html);
            $('#loadmorevenues').show();
            params.page++;
            $('#loadmorevenues-button').data("current-url", url);
            $('#loadmorevenues-button').data("params", params)
            load_wheelmap_info();
        },
        error: function(xhr) {
            if (xhr.responseText)
                $('#alert-navigation').html(xhr.responseText);
            else
                $('#alert-navigation').html("There was a problem with your request, sorry!");
            $('#alert-navigation').show();
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
                // Add class for the status for filtering of visible infos
                $(div).addClass("wheelchair-" + r.wheelchair);
                // Change the headline to the name of the venue.
                $(div).find('.nodeheadline').html(r.name);
                // Add the response data to the box
                $nodeinfo = $(div).find('.nodeinfo');
                $nodeinfo.find('.wheelmap-link')[0].pathname += r.wheelmap_id;
                $nodeinfo.find('.wheelmap-status').text(r.wheelchair);
                $nodeinfo.find('.wheelmap-description').text(r.wheelchair_description);
                $nodeinfo.show();
                
                $nodeinfo.find('.edit-wheelchair-status').click(function(){
                        $('#myModalLabel').text(r.name);
                        $('#editwheelmap input[value="' + r.wheelchair + '"]').prop('checked', true);
                        $('#btn-node-update').data('wheelmap_id', r.wheelmap_id);
                        $('#editwheelmap').modal('show');
                });
                
                $(div).find('.map img.mapmarker').attr("src", "/static/img/" + r.wheelchair + ".png");
            } else {
                // Add class for the status for filtering of visible infos
                $(div).addClass("wheelchair-notfound");
                // Change headline to not found
                $(div).find('.nodeheadline').html("Not found on wheelmap");
                $nodenotfound = $(div).find(".nodenotfound");
                $search_link = $nodenotfound.find(".wheelmap-search-link")[0];
                $search_link.href = $search_link.href.replace("0lat0", $(div).data('lat'));
                $search_link.href = $search_link.href.replace("0lon0", $(div).data('lng'));
                $nodenotfound.show();
                               
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
        wheelchair_status = $(this).data("wheelchair");
        if ( $(this).is(":checked") ) {
            $(".wheelchair-" + wheelchair_status).each(function(){
                if( !$(this).hasClass('in') ) {
                    $(this).collapse('show');
                }
            });
        } else {
            $(".wheelchair-" + wheelchair_status).each(function(){
                if( $(this).hasClass('in') ) {
                    $(this).collapse('hide');
                }
            });
        }
    });
}
