$(document).ready(function () {
  $('.report-item').on('click', function() {
      $(this).find('.chevron').toggleClass('rotated');
  });

  // Handle Form submission
  $('#filterForm').on('submit', function(e) {
    e.preventDefault();     // prevent the default action

    // Create a form element
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = 'extract_general_stat';
    
    // Append all input fields from #filterForm
    // Append all input fields from #summaryfilterForm
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

    // Append form to body and submit
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
  });

    // Handle Form submission
    $('#detailedFilterForm').on('submit', function(e) {
      e.preventDefault();     // prevent the default action
  
      // Create a form element
      var form = document.createElement('form');
      form.method = 'POST';
      form.action = 'extract_detail_stat';
      
      // Append all input fields from #detailedFilterForm
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
  
      // Append form to body and submit
      document.body.appendChild(form);
      form.submit();
      document.body.removeChild(form);
    });

});