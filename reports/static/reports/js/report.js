$(document).ready(function () {
  $('.report-item').on('click', function() {
      $(this).find('.chevron').toggleClass('rotated');
  });
});