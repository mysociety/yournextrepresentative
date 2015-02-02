$(function() {
  var toggleFullVersion = function toggleFullVersion($fullVersion){
    if($fullVersion.is(':visible')){
      $fullVersion.hide().siblings('.js-toggle-full-version-json').text('Show full version');
    } else {
      $fullVersion.show().siblings('.js-toggle-full-version-json').text('Hide full version');
    }
  }

  toggleFullVersion($('.full-version-json'));

  $('.js-toggle-full-version-json').on('click', function(){
    toggleFullVersion($(this).siblings('.full-version-json'));
  });
});
