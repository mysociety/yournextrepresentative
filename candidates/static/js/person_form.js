function enablePartyAutocompletion() {
  var partyInput = $('#id_party');
  partyInput.autocomplete({
    source: autocompletePartyURL,
    minLength: 2
  });
}

function enableConstituencySelect() {
  var constituencySelect = $('select#id_constituency');
  constituencySelect.select2({
    placeholder: 'Constituency',
    allowClear: true,
    width: '100%'
  });
}

function enableStandingCheckbox() {
  var standingCheckbox = $('#person-details input#id_standing'),
      constituencySelect = $('select#id_constituency');
  /* Disable the constituencySelect box based on whether the
     'standing' checkbox is selected or not. */
  if (standingCheckbox.length) {
    constituencySelect.prop(
      'disabled',
      !standingCheckbox.prop('checked')
    );
    /* And if the state of the statnding checkbox is changed, disable
       or enable the constituency select box. */
    standingCheckbox.on('change', function() {
      constituencySelect.prop(
        'disabled',
        !$(this).prop('checked')
      );
    });
  }
}

$(document).ready(function() {
  enablePartyAutocompletion();
  enableConstituencySelect();
  enableStandingCheckbox();
});
