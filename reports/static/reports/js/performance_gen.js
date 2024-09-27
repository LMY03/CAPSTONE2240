
$(document).ready(function() {

  // Date Checking
  function checkDates(startdate, enddate) {
    var today = new Date()
    today = new Date(today.getFullYear(), today.getMonth(), today.getDate())
    if (startdate > enddate) {
      console.log('startdate > enddate')
      return false;
    }
    else if (startdate > today || enddate > today) {
      console.log('date > today')
      return false;
    }
    else {
      return true;
    }
  }

  // Data Checking
  function checkData(data) {
    var startDateInd = -1;
    var endDateInd = -1;

    // Get respective data
    for (i = 0; i < data.length; i++) {
      if(data[i].name == 'startdate')
        startDateInd = i;
      else if (data[i].name == 'enddate')
        endDateInd = i;
    }

    // Is Data Completed?
    if (startDateInd == -1 || endDateInd == -1) {
      $('.toast-container').css('display','block');
      $('div#incToast').css('display','block');

      var toast = document.getElementById("incToast");
      var myToast = new bootstrap.Toast(toast);

      myToast.show();
      return false;
    } else {
      if (data[startDateInd].value === "" || data[endDateInd].value === "" || !checkDates(new Date(data[startDateInd].value), new Date(data[endDateInd].value))) {
        $('.toast-container').css('display','block');
        $('div#datesToast').css('display','block');
  
        var toast = document.getElementById("datesToast");
        var myToast = new bootstrap.Toast(toast);
  
        myToast.show();
        return false;
      }
    }

    return true;
  }

  // Extract data into csv
  $('#extract-btn').click(function() {
    var form = $('#conditionForm');
    // set form action: go generate csv
    form.attr('action', 'extract_csv');
    var data = form.serializeArray();
    // submit form
    if(checkData(data)){
      console.log("Form data:", data);
      form.submit();
    }
  })

})