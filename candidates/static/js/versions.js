$(function() {
  $('.full-version-json').hide();
  $('.js-toggle-full-version-json').text('Show');
  $('.js-toggle-full-version-json').on('click', function(event){
    var target = $(event.target),
      fullVersion = target.parent().next();
    if (target.text() == 'Show') {
      target.text('Hide');
      fullVersion.show()
    } else {
      target.text('Show');
      fullVersion.hide()
    }
  });
});
