/* Javascript for the constituency page, dealing with:
   - Popping up the source attribution boxes
   - Hiding or revealing the the new candidate form
*/

$(function() {

  /* If Javascript's enabled, hide the source-confirmation
     boxes and the add new candidate form. */
  $('.source-confirmation-standing').hide();
  $('.source-confirmation-not-standing').hide();
  $('.source-confirmation-delete-other-name').hide()
  $('.candidates__new').hide();

  function getNewCandidateDiv(element) {
    var target = $(element),
      allCandidates = target.closest('.candidates-for-post');
    return allCandidates.find('.candidates__new');
  }

  /* Set up the hide / reveal for the add new candidate form */
  $('.show-new-candidate-form').on('click', function(e){
    var newCandidate = getNewCandidateDiv(e.target);
    newCandidate.slideDown(function(){
      newCandidate.find('input:text').eq(0).focus();
    });
  });
  $('.hide-new-candidate-form').on('click', function(e){
    var newCandidate = getNewCandidateDiv(e.target);
    newCandidate.slideUp();
  });

  function toggleSourceConfirmation(button, classSuffix, target) {
    var allConfirmationBoxes = $(button).parents('li').children('.source-confirmation'),
    confirmationClass = '.source-confirmation-' + classSuffix,
    confirmation = $(button).parents('li').children(confirmationClass);
    if(confirmation.is(':visible')){
      confirmation.hide();
    } else {
      allConfirmationBoxes.hide();
      confirmation.show().find('input:text').focus();
    }
  }

  /* Handle showing/hiding the source confirmation box */
  $('.js-toggle-source-confirmation').on('click', function(event){
    var i, validClass, target = $(event.target),
    validClasses = ['standing', 'not-standing', 'delete-other-name'];
    for (i = 0; i < validClasses.length; ++i ) {
      validClass = validClasses[i];
      if (target.hasClass(validClass)) {
        toggleSourceConfirmation(this, validClass, target);
        return;
      }
    }
  });

  $('.winner-confirm').submit(function(e) {
    var enclosingDiv = $(e.target).parent(),
      candidateName=enclosingDiv.find('.candidate-name').text(),
      constituencyName=$('#constituency-name').text(),
      partyName=enclosingDiv.find('.party').text(),
      message;
    message = interpolate(gettext("Are you sure that %s (%s) was elected in %s?"),
        [candidateName, partyName, constituencyName]);
    return confirm(message);
  });

});
