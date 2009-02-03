
(function(){
/*
 *
 * Copyright (c) 2007 Carlos Gabaldon (brewdonkey.com)

 *
 * $Date: 2009-02-02
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
        }

    };
        
    
})();