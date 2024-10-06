$(document).ready(function () {
  $('.report-item').on('click', function() {
      $(this).find('.chevron').toggleClass('rotated');
  });

  function showLoading() {
      // TODO: Implement loading indicator
      console.log('Loading...');
  }

  function hideLoading() {
      // TODO: Hide loading indicator
      console.log('Loading complete');
  }

  function handleFormSubmit(formId, actionUrl) {
      $(formId).on('submit', function(e) {
          e.preventDefault();
          showLoading();

          $.ajax({
              url: actionUrl,
              type: 'POST',
              data: $(this).serialize(),
              success: function(response) {
                  console.log('Success:', response);
                  // TODO: Update the page with the response data
                  // For example:
                  // $('#resultContainer').html(response);
              },
              error: function(xhr, status, error) {
                  console.error('Error:', error);
                  // TODO: Show error message to user
                  // For example:
                  // $('#errorContainer').text('An error occurred. Please try again.');
              },
              complete: function() {
                  hideLoading();
              }
          });
      });
  }

  // Handle Summary Form submission
  handleFormSubmit('#summaryfilterForm', 'extract_general_stat');

  // Handle Detailed Form submission
  handleFormSubmit('#detailedFilterForm', 'extract_detail_stat');
});