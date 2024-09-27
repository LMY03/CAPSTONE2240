
$(document).ready(function() {

  // Extract data into csv
  $('#extract-btn').click(function() {
    var form = $('#conditionForm');

    // set form action: go generate csv
    form.attr('action', 'extract_csv');
    var data = form.serializeArray();
    // submit form
    // if(checkData(data))
    //   console.log("Form data:", data);
    form.submit();
  })

})