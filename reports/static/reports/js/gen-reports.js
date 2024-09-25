$(document).ready(function() {


  function init() {
    $.ajax({
      type: 'GET',
      url: 'report_gen',
      datatype: 'json',
      success: function(response) {
        console.log("Received Data" + response)
      },
      error: function(xhr) {
        console.log(xhr.responseText)
      }
    })
  }

  init();
})