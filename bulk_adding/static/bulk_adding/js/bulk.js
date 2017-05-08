$(function(){
    $('.js-bulk-known-person-alternate-name').on('click', function(e){
        e.preventDefault();

        $person = $(this).parents('li');
        $form = $( $('.js-bulk-known-person-alternate-name-form').html() );
        $form.appendTo($person);
        $form.find('input[type="text"]').focus();

        $form.on('submit', function(){
            console.log( $form.serializeArray() );
            // :TODO: $.post(...)
        });

        $form.on('click', '.js-bulk-known-person-alternate-name-cancel', function(){
            $form.remove();
        });
    });
});
