$(function() {
   $('.cap-expander').click(function() {
       if (this.innerHTML === '[+]') {
           this.innerHTML = '[-]';
           $(this).parent().parent().parent().children('.cap-children').addClass('show');
       }
       else {
           this.innerHTML = '[+]';
           $(this).parent().parent().parent().children('.cap-children').removeClass('show');
       }
   });
});
