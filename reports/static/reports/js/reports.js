$(document).ready(function() {

  var vmids = []

  // Initialize VM table in Report Page
  var vmInfoTable = $('table#vmInfoTable').DataTable({
    paging: true,
    responsive: true,
    autoWidth: false,
    fixedColumns: true,
    searching: true,
    columnDefs: [
      { orderable: false, "targets": 0 },
      { targets: 0,
        render: function(data, type, row, meta) {
          return '<input type="checkbox" name="'+ row[1] + '" value="' + row[2] +'"/>'
        }
      }
    ],
    select: {
      style: 'multi',
    },
    lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
    order: [[1, 'asc']]
  })

  // Generate rows 
  function getVmtable(vm) {

  }


  function init() {
    $.ajax({
      type: 'GET',
      url: 'getVmList',
      datatype: 'json',
      success: function(response) {
        const vmList = JSON.parse(response.vmList);
        vmList.forEach(function(val) {
          genVmTable(val);
        })
      },
      error: function(response) {
        console.log(response);
      }
    })
  }

  init();

})