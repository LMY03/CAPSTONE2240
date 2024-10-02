$(document).ready(function () {
  $('.report-item').on('click', function() {
      $(this).find('.chevron').toggleClass('rotated');
  });

  // Handle Form submission
  $('#filterForm').on('submit', function(e) {
    e.preventDefault();     // prevent the default action

    $.ajax({
      url: 'extract_general_stat',
      type: "POST",
      data: $(this).serialize(),
      headers: {
        "X-CSRFToken": $('input[name=csrfmiddlewaretoken]').val()
      },
      success: function(response) {
        console.log("successful")
      },
      error: function(xhr, status, error) {
        console.log("error")
      }
    })
  })
});