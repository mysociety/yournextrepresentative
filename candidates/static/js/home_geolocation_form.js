var constructGeolocationLink = function constructGeolocationLink($wrapper){
    var geolocationIsSupported = false;
    if ("geolocation" in navigator) {
        geolocationIsSupported = true;
    }

    if(geolocationIsSupported) {
        var t1 = $wrapper.attr('data-link-text') || 'Use my current location';
        var t2 = $wrapper.attr('data-loading-text') || 'Getting location\u2026';

        var $a = $('<a>').text(t1).addClass('geolocation-link');
        $a.on('click', function(){
            var that = this;
            $(this).text(t2);
            navigator.geolocation.getCurrentPosition(function(position) {
              $.getJSON(
                  '/geolocator/' + position.coords.latitude + ',' + position.coords.longitude,
                  function ( data ) {
                    if ( data['error'] ) {
                      $(that).text(data['error']);
                    } else if ( data['url'] ) {
                        window.location=data['url']
                    } else {
                      $(that).text(data['error']);
                    }
                  });
            });
        })
        $a.appendTo($wrapper);
    }
}

$(function(){
    $('.js-geolocation-link').each(function(){
        constructGeolocationLink( $(this) );
    });
});
