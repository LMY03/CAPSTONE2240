$(document).ready(function() {

  var vmInfoTable;

  // Listener for clicking the select all checkbox for all of the machines 
  $('#cb-select-all').on('click', function() {
    var rows = vmInfoTable.rows({'search': 'applied'}).nodes();
    $('input[type="checkbox"]', rows).prop('checked', this.checked)
  })

  $('#vmInfoTable tbody').on('change', 'input[type="checkbox"]', function(){
    if(!this.checked) {
      var sel = $('#cb-select-all').get(0);
      if(sel && sel.checked && ('indeterminate' in sel)) {
          sel.indeterminate = true;
      }
    }
  })

  // Generate rows 
  function genVmTable(vm) {

    // let vmInfo = [vm.id, vm.id, vm.name, vm.type, vm.node]
    let vmInfo = [vm.id, vm.id, vm.name, vm.node, vm.type]
    vmInfoTable.row.add(vmInfo).draw();
  }

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

  // Error Checking
  function checkData(data) {
    var startDateInd = -1;
    var endDateInd = -1;
    var metric = false;
    var vmSelected = false;

    // Get respective data
    for (i = 0; i < data.length; i++) {
      if(data[i].name == 'startdate')
        startDateInd = i;
      else if (data[i].name == 'enddate')
        endDateInd = i;
      else if (data[i].name == 'cpuUsage' 
        || data[i].name == 'memoryUsage' 
        || data[i].name == 'netin' 
        || data[i].name == 'netout')
        metric = true;
      else if (data[i].name != 'csrfmiddlewaretoken' 
        && data[i].name != 'categoryFilter' 
        && data[i].name != 'vmInfoTable_length')
        vmSelected = true;
    }

    // Is Data Completed?
    if (startDateInd == -1 || endDateInd == -1 || !metric || !vmSelected) {
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
    var form = $('#filterForm');

    // change URL -> csv
    form.attr('action', 'index_csv');
    var data = form.serializeArray();
    // submit form
    if(checkData(data))
      console.log("Form data:", data);
      form.submit();
  })

  $('#report-btn').click(function() {
    var form = $('#filterForm');
    
  })
  
  function init() {
    $.ajax({
      type: 'GET',
      url: 'getVmList',
      datatype: 'json',
      success: function(response) {

        // Initializes the VM Table in the Reports Page
        vmInfoTable = $('table#vmInfoTable').DataTable({
          paging: true,
          responsive: true,
          autoWidth: false,
          fixedColumns: true,
          searching: true,
          columnDefs :[
              {   orderable: false, "targets": 0 },
              {   targets: 0,
                  render: function(data, type, row, meta){
                      return '<input type="checkbox" name="selectedVMs" value="'+ row[2] +'"/>'
                  }
              }
          ],
          select : {
              style: 'multi',
          },
          lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
          order: [[1, 'asc']]
        });

        // Generates the VM table for each item in the list of machines
        for (i = 0; i < response.vmList.length; i++) {
          genVmTable(response.vmList[i])
        }

      },
      error: function(response) {
        console.log(response);
      }
    })
  }

  init();

})