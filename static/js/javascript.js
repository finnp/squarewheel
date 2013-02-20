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
                            $('#form-update-status input:checked').val(),
                            $(this).data('$referer_div'));
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

var update_wheelmap_node = function(wheelmap_id, wheelchair_status, $refererdiv) {
      
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
                    display_wheelchair_status($refererdiv, wheelchair_status);
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
            
            // When loaded add functionality for adding comments
            $('.comment-share-button').click(comment_share_click);
            
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
                // Change the headline to the name of the venue.
                // And turn it into a link to wheelmap
                $(div).find('.nodeheadline > span').hide();
                $wheelmaplink = $(div).find('.nodeheadline > a');
                $wheelmaplink.text(r.name)
                $wheelmaplink[0].pathname += r.wheelmap_id;

                // Add the response data to the box
                $nodeinfo = $(div).find('.nodeinfo');
                $nodeinfo.find('.wheelmap-description').text(r.wheelchair_description);
                $nodeinfo.find('address').html(r.address);
                
                
                // Change the wheelchair status of the node
                display_wheelchair_status($(div), r.wheelchair);
                
                
                // Show the nodeinfo
                $nodeinfo.show();
                
                $nodeinfo.find('.edit-wheelchair-status').click(function(){
                        $('#myModalLabel').text(r.name);
                        $('#editwheelmap input[value="' + r.wheelchair + '"]').prop('checked', true);
                        $('#btn-node-update').data('wheelmap_id', r.wheelmap_id);
                        $('#btn-node-update').data('$referer_div', $(div));
                        $('#editwheelmap').modal('show');
                });
                
                // Add information for foursquare comment link
                // And enable it only if a wheelmap node was found
                $checkboxwheelmaplink = $(div).find('.checkbox-wheelmaplink')
                $checkboxwheelmaplink.removeAttr('disabled');
                $checkboxwheelmaplink.attr('checked', 'checked');
                $checkboxwheelmaplink.data('wheelmapid', r.wheelmap_id);

            } else {
                // Add class for the status for filtering of visible infos
                $(div).addClass("wheelchair-notfound");
                // Change headline to not found
                $(div).find('.nodeheadline > span').text("Not found on wheelmap");
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

var display_wheelchair_status = function($div, wheelchairstatus) {
    // Do everything to change the status
    
    // Delete the used classes for wheelchair-status
    $div.removeClass("wheelchair-yes");
    $div.removeClass("wheelchair-no");
    $div.removeClass("wheelchair-limited");
    $div.removeClass("wheelchair-unknown");
    
    // Add the proper class instead
    $div.addClass("wheelchair-" + wheelchairstatus);
    
    $nodeinfo = $div.find('.nodeinfo');
    
    // Change the text
    $nodeinfo.find('.wheelmap-status').text(wheelchairstatus);
    
    // Change the table background-color
    $nodeinfo.find('tr:first').first().attr('class', 'table-' + wheelchairstatus);
    
    // Change the marker on the map to the corresponding image    
    $div.find('.map img.mapmarker').attr("src", "/static/img/" + wheelchairstatus + ".png");
} 

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

var comment_share_click = function() {
    // Handles the clicks for the comment share button
    
    // Load state for button (sending..)
    var $this = $(this);
    
    $this.addClass('disabled').text('Sending..');
    
    params = {}
    venueid =  $this.data('venueid')
    params['venueid'] = venueid;
    params['text'] = $('#comment-text-' + venueid).val();
    $wheelmaplink = $('#checkbox-wheelmaplink-' + venueid)
    if ($wheelmaplink.prop('checked'))
        params['wheelmapid'] = $wheelmaplink.data('wheelmapid');
    else
        params['wheelmapid'] = ""    
    
    $.ajax({
        url: '/foursquare/addcomment/',
        dataType: 'json',
        type: 'POST',
        data: params,
        success: function(r) {
            if (r.success) {
                $this.text('Sent!');
                $this.unbind('click');
            } else {
                alert("Error: " + r.error);
                $this.removeClass('disabled');
                $this.text("Send");
            }
        }    
    });
};

