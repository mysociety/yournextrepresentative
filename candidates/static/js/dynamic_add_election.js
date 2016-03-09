/* This is called to display a new election form on the edit person
   page, if the dynamic "add new election" button is being used. */

function showElectionsForm() {
  $.getJSON("/api/current-elections/").done(function( data ) {
    var select_data = $.map(data, function(obj, key) {
      return { id: key, text: obj.name + ' (' + obj.election_date + ')' };
    })
    $('#add_more_elections').select2({
      data: select_data,
    }).on('change', function(e) {
      var url = window.location.pathname + '/single_election_form/' + e.val;
      $.get(url, function(data) {
        $('.extra_elections_forms').html(data);
        setUpStandingCheckbox();
        setUpPartySelect2s();
        setUpPostSelect2s();
        updateFields();
      });
    });
    $('.add_more_elections_field').show();
    $('#add_election_button').hide();
  });
  return false;
}

$(function() {
  $('.add-candidacy-link').each(function() {
    // Replace the link with an election selector:
    $(this).find('a').each(function() {
      $(this).attr('href', '#');
      /* Now enable the "add an extra election" button if it's present */
      $('#add_election_button').on('click', showElectionsForm);
      $('.add_more_elections_field').hide();
    });
  });
});
