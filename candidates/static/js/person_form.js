function setUpPartySelect2s() {
  $('#id_party_gb').select2({width: '100%'});
  $('#id_party_ni').select2({width: '100%'});
}

function setUpConstituencySelect2() {
  var constituencySelect = $('#id_constituency'),
      hidden = constituencySelect.prop('tagName') == 'INPUT' &&
        constituencySelect.attr('type') == 'hidden';
  /* If it's a real select box (not a hidden input) make it into a
   * Select2 box */
  if (!hidden) {
    constituencySelect.select2({
      placeholder: 'Constituency',
      allowClear: true,
      width: '100%'
    });
  }
  $('#id_constituency').on('change', function (e) {
    update2015Selects(showSelects(), e['val']);
  });
  update2015Selects(showSelects(), constituencySelect.val());
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

function showSelects() {
  var standingCheckbox = getStandingCheckbox();
  if (standingCheckbox.length == 0) {
    return true;
  } else {
    return standingCheckbox.prop('checked');
  }
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

function update2015Selects(show, constituencyID) {
  /* Whether we should show the party and constituency selects is
     determined by the boolean 'show'.  If 'constituencyID' is also
     specified then the right party selection is shown; if not just
     default to showing parties registered in Great Britain. */
  var ni, idToHide, idToShow,
      idNI = '#id_party_ni',
      idGB = '#id_party_gb';
  if (show) {
    if (constituencyID) {
      ni = isNorthernIreland[constituencyID],
      idToHide = ni ? idGB : idNI,
      idToShow = ni ? idNI : idGB;
    } else {
      idToHide = idNI
      idToShow = idGB
    }
    setSelect2Visibility(idToHide, false);
    setSelect2Visibility(idToShow, true);
  } else {
    setSelect2Visibility(idGB, false);
    setSelect2Visibility(idNI, false);
  }
  setSelect2Visibility('#id_constituency', show);
}

function updateFields() {
  var constituencySelect = $('#id_constituency'),
      constituencyValue = constituencySelect.val();
  update2015Selects(showSelects(), constituencyValue);
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
