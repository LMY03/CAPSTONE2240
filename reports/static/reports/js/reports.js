$(document).ready(function () {
  // Toggle chevron rotation
  $('.report-item').on('click', function() {
      $(this).find('.chevron').toggleClass('rotated');
  });

  // Generic form submission handler
  function handleFormSubmit(formId, actionUrl) {
      $(formId).on('submit', function(e) {
          e.preventDefault();

          var form = document.createElement('form');
          form.method = 'POST';
          form.action = actionUrl;

          // Append all input fields from the original form
          $(this).find('input, select').each(function() {
              var input = document.createElement('input');
              input.type = 'hidden';
              input.name = this.name;
              input.value = this.value;
              form.appendChild(input);
          });

          // Append CSRF token
          var csrfInput = document.createElement('input');
          csrfInput.type = 'hidden';
          csrfInput.name = 'csrfmiddlewaretoken';
          csrfInput.value = $('input[name=csrfmiddlewaretoken]').val();
          form.appendChild(csrfInput);

          // Append form to body, submit, and remove
          document.body.appendChild(form);
          form.submit();
          document.body.removeChild(form);
      });
  }

  // Handle summary filter form submission
  handleFormSubmit('#summaryfilterForm', 'extract_general_stat');

  // Handle detailed filter form submission
  handleFormSubmit('#detailedFilterForm', 'extract_detail_stat');
});