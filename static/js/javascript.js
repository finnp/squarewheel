$(document).ready(function() {
    
    // Add clickhandler for navbar navigation
    $('.load-content').click(function(e) {        
            e.preventDefault();
    
            // Clear the view and stop the ajax calls
            $('#alert-navigation').hide();
            $.ajaxQ.abortAll();
            
            $this = $(this);
            if ( $this.hasClass('load-venues') ) {
                // Load venues
                loadVenues( $this.attr('href') );
            } else {
                // Load non-venue content
                loadingDisplay(false, true);
                $('#loadmorevenues').hide();
                $.get("/", function(r){
                    $('#venues').html(r); 
                    $('#loading').hide();
                });
            }
    });
    
    // Add clickhandler for the explore search
    $('#btn-explore-search').click(function(e){
        e.preventDefault();          
        $location = $("#input-explore-location");
        $query = $("#input-explore-query");
        params = {
            geolocation: $location.val() ? $location.val() : $location.attr('placeholder'),
            query: $query.val() ? $query.val() : $query.attr('placeholder')
        };
        loadVenues("explore/", params);
    });
       
    // Add clickhandler for the load more venues button
    $('#loadmorevenues-button').click(function(){ 
        loadVenues( $(this).data("current-url"), $(this).data("params") );
    });
      
    // Add clickhandler to the filter so it gets updates
    $(".wheelchair-filter-checkbox").click( updateFilter );
    
    // Activate the helping tooltips (for filter)
    $("[rel='tooltip']").tooltip();
       
    // Add clickhandler for the update button in the modal
    $('#node-update-send').click(function(){
        updateWheelmapNode( $(this).data('wheelmapId'),
                            $('#form-update-status input:checked').val(),
                            $(this).data('$refererDiv'));
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

var updateWheelmapNode = function(wheelmapId,  wheelchairStatus, $refererdiv) {
        $alert = $('#alert-edit-node');
        $.ajax({
            dataType: "json",
            url: "/wheelmap/update_node/",
            type: "POST",
            data: {
                wheelmapid: wheelmapId,
                wheelchairstatus:  wheelchairStatus
            },
            success: function(r) {
                if (r.success) {          
                    $alert.addClass('alert-success');  
                    $alert.text("You successfully updated the node. It will take some time until the change affects wheelmap.");
                    displayWheelchairStatus($refererdiv,  wheelchairStatus);
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

var loadVenues = function(url, params) {
    if ( typeof params == "undefined" ) 
        params = {}
    if ( typeof params.page == "undefined" ) 
        params.page = 0
   
    loadingDisplay(true, params.page == 0);
    
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
            $('.comment-share-button').click(commentShareClick);
            
            loadWheelmapInfo();
        },
        error: function(xhr) {
            if (xhr.responseText)
                $('#alert-navigation').html(xhr.responseText);
            else
                $('#alert-navigation').html("There was a problem with your request, sorry!");
            $('#alert-navigation').show();
        },
        complete: function() {
            $('#loading').hide();
        }
    });
}

var loadWheelmapInfo = function() {
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
                $wheelmaplink[0].pathname += r.wheelmapId;

                // Add the response data to the box
                $nodeinfo = $(div).find('.nodeinfo');
                $nodeinfo.find('.wheelmap-description').text(r.wheelchairDescription);
                $nodeinfo.find('address').html(r.address);
                
                
                // Change the wheelchair status of the node
                displayWheelchairStatus($(div), r.wheelchair);
                
                
                // Show the nodeinfo
                $nodeinfo.show();
                
                $nodeinfo.find('.edit-wheelchair-status').click(function(){
                        $('#myModalLabel').text(r.name);
                        $('#editwheelmap input[value="' + r.wheelchair + '"]').prop('checked', true);
                        $('#node-update-send').data('wheelmapId', r.wheelmapId);
                        $('#node-update-send').data('$refererDiv', $(div));
                        $('#editwheelmap').modal('show');
                });
                
                // Add information for foursquare comment link
                // And enable it only if a wheelmap node was found
                $checkboxwheelmaplink = $(div).find('.checkbox-wheelmaplink');
                $checkboxwheelmaplink.removeAttr('disabled');
                $checkboxwheelmaplink.attr('checked', 'checked');
                $checkboxwheelmaplink.data('wheelmapid', r.wheelmapId);
                
                // Add information to add hashtag toggle
                if( r.wheelchair != 'unknown' ) {
                    $checkboxhashtags = $(div).find('.checkbox-hashtags');
                    $checkboxhashtags.removeAttr('disabled');
                    $checkboxhashtags.data('wheelmapstatus', r.wheelchair);
                    $checkboxhashtags.parent().append(' ' + wheelchairstatusToHashtag(r.wheelchair));
                    $checkboxhashtags.click(function() {
                        $this = $(this);
                        $textarea = $this.parent().siblings('textarea');
                        if ( $this.prop('checked') ) {
                            $textarea.val($textarea.val() + wheelchairstatusToHashtag(r.wheelchair));
                        } else {
                            // Removes all hashtags now, should be only the added ones
                            var hashtagregexp = new RegExp('#access(pass|limited|fail)','g');
                            $textarea.val( $textarea.val().replace(hashtagregexp, '') );
                        }
                    });
                }


            } else {
                // Add class for the status for filtering of visible infos
                $(div).addClass("wheelchair-notfound");
                // Change headline to not found
                $(div).find('.nodeheadline > span').text("Not found on wheelmap");
                $nodenotfound = $(div).find(".nodenotfound");
                $searchLink = $nodenotfound.find(".wheelmap-search-link")[0];
                $searchLink.href = $searchLink.href.replace("0lat0", $(div).data('lat'));
                $searchLink.href = $searchLink.href.replace("0lon0", $(div).data('lng'));
                $nodenotfound.show();
                               
                $(div).find('.map img.mapmarker').attr("src", "/static/img/notfound.png");
            }
            // Hide the ones, that are not wanted
            updateFilter();
        },
        error: function() {
            $(div).find('.nodeheadline').html("Error: There was a problem contacting wheelmap.");
        }
        });  
    });
};

var displayWheelchairStatus = function($div, wheelchairstatus) {
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

var updateFilter = function () {
    // Function for filtering the results by wheelchair status
    
    $(".wheelchair-filter-checkbox").each(function() {
         wheelchairStatus = $(this).data("wheelchair");
        if ( $(this).is(":checked") ) {
            $(".wheelchair-" +  wheelchairStatus).each(function(){
                if( !$(this).hasClass('in') ) {
                    $(this).collapse('show');
                }
            });
        } else {
            $(".wheelchair-" +  wheelchairStatus).each(function(){
                if( $(this).hasClass('in') ) {
                    $(this).collapse('hide');
                }
            });
        }
    });
}

var commentShareClick = function() {
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

var wheelchairstatusToHashtag = function(wheelchair) {
    switch(wheelchair)
        {
        case 'yes':
            return '#accesspass';
        case 'limited':
            return '#accesslimited';
        case 'no':
            return '#accessfail';
        default:
            return '';
        }
};

var loadingDisplay = function(venue, clear) {

    // Clear the current content if given
    if (clear) {
        $('#venues').empty();
    }
    
    // Adjust the loading text
    if (venue) {
        $('#loading-text').text('Loading venues from foursquare.');
    } else {
        $('#loading-text').text('Loading page.');
    }
    
    $('#loading').show();

}
