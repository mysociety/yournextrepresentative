function setUpPartySelect2s() {
  $('#id_party_gb').select2({width: '100%'});
  $('#id_party_ni').select2({width: '100%'});
}

function setUpConstituencySelect2() {
  var constituencySelect = $('#id_constituency'),
      hidden = constituencySelect.prop('tagName') == 'INPUT' &&
        constituencySelect.attr('type') == 'hidden';
  if (!hidden) {
    constituencySelect.select2({
      placeholder: 'Constituency',
      allowClear: true,
      width: '100%'
    });
  }
  $('#id_constituency').on('change', function (e) {
    update2015Selects(e['val']);
  });
  update2015Selects(constituencySelect.val());
}

function getSelect2Enclosure(select2ID) {
  /* This assumes that there's a label that's a sibling of the
   * Select2, and that they're the only elements in a containing
   * element (the one that will be returned by this function) */
  return $(select2ID).select2('container').parent();
}

function getStandingCheckbox() {
  return $('#person-details input#id_standing');
}

function setSelect2Visibility(select2ID, visibility) {
  /* If visibility is false, this both disables the Select2 boxes and
   * hides them by hiding their enclosing element. Otherwise it
   * enables it and makes the enclosure visible. */
  var element = $(select2ID),
      enclosure = getSelect2Enclosure(select2ID);
  element.prop(
    'disabled',
    !visibility
  );
  if (visibility) {
    enclosure.show()
  } else {
    enclosure.hide();
  }
}

function update2015Selects(constituencyID) {
  /* If constituencyID is falsy, hide all 2015-related data entry
   * fields; otherwise enable them all, making sure that the correct
   * party select is installed */
  if (constituencyID) {
    var ni = isNorthernIreland[constituencyID],
    idToHide = ni ? '#id_party_gb' : '#id_party_ni',
    idToShow = ni ? '#id_party_ni' : '#id_party_gb';
    setSelect2Visibility(idToHide, false);
    setSelect2Visibility(idToShow, true);
    setSelect2Visibility('#id_constituency', true);
  } else {
    setSelect2Visibility('#id_party_gb', false);
    setSelect2Visibility('#id_party_ni', false);
    setSelect2Visibility('#id_constituency', false);
  }
}

function updateFields() {
  var standingCheckbox = getStandingCheckbox(),
      constituencySelect = $('#id_constituency'),
      makeFieldsVisible = standingCheckbox.prop('checked'),
      constituencyValue = constituencySelect.val();
  if (standingCheckbox.length == 0) {
    /* If there is no such checkbox on the page, just return */
    return;
  }
  update2015Selects(constituencyValue);
  if (!makeFieldsVisible) {
    update2015Selects('');
  }
}

function setUpStandingCheckbox() {
  updateFields();
  getStandingCheckbox().on('change', function() {
    updateFields();
  });
}

$(document).ready(function() {
  setUpPartySelect2s();
  setUpConstituencySelect2();
  setUpStandingCheckbox();
});
