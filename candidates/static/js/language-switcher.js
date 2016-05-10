$(function(){
  $('.js-language-switcher select').on('change', function(){
    this.form.submit();
  });
});
