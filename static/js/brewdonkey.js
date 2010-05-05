
(function(){
/*
 *
 * Copyright (c) 2010 Carlos Gabaldon (brewdonkey.com)

 *
 * $Date: 2010-02-02
 */


    var brewdonkey = {};


    $(document).ready(function(){

        brewdonkey.beer.init();


    });

    /**
     * BrewDonkey application
     * @class brewdonkey.beer
     */
    brewdonkey.beer = {

        init: function(){


            $("a.vote-up").click(this.vote);
            this.map();

        },

        vote: function(){
             var link = $(this)
             $.ajax({
                  type: "GET",
                  url: link.attr("href"),
                  dataType: "json",
                  success: function(json){
                       var voteCountFieldId = "#beer-" + json.beer + "-vote"
                       $(voteCountFieldId).replaceWith(json.votes)
                       link.hide();

                  }
                });

            return false;
        },

        map: function() {

            var geocoder = new google.maps.Geocoder();
            var map;
            var address =  $("#brewery_address").val();

            if(address && (address != "None Provided")){
                geocoder.geocode( { 'address': address}, function(results, status) {
                  if (status == google.maps.GeocoderStatus.OK) {

                      var myOptions = {
                        zoom: 15,
                        center: results[0].geometry.location,
                        mapTypeId: google.maps.MapTypeId.ROADMAP
                      };
                      $("#map_canvas").toggle();
                      map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);

                      var marker = new google.maps.Marker({
                          map: map,
                          position: results[0].geometry.location
                      });

                    } else {
                      alert("Geocode was not successful for the following reason: " + status);
                    }
                  });
              }

          },

    };


})();

