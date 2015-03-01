jQuery(function($) {

  function setVisibilityFromDecision() {
    var value = $('#id_decision').val();
    if (value == 'rejected') {
      $('.rejection_reason').show();
      $('.justification_for_use').hide();
      $('#decision-submit').val('Reject');
      $('#decision-submit').show();
    } else if (value == 'approved') {
      $('.rejection_reason').hide();
      $('.justification_for_use').show();
      $('#decision-submit').val('Approve');
      $('#decision-submit').show();
    } else if (value == 'undecided') {
      $('.rejection_reason').hide();
      $('.justification_for_use').show();
      $('#decision-submit').hide();
    }
  }

  $('.crop-coordinates').hide();
  setVisibilityFromDecision();

  $('#id_decision').change(function() {
    setVisibilityFromDecision()
  });

  function adjustFormValues(c) {
    $('input#id_x_min').attr('value', Math.round(c.x));
    $('input#id_x_max').attr('value', Math.round(c.x2));
    $('input#id_y_min').attr('value', Math.round(c.y));
    $('input#id_y_max').attr('value', Math.round(c.y2));
  }

  $('#image-for-review').Jcrop({
    onSelect: adjustFormValues,
    onChange: adjustFormValues,
    boxWidth: 600,
    boxHeight: 600
  });

});
