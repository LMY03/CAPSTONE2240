$(document).ready(function() {

  var vmids = []
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
    console.log(vm)

    // let vmInfo = [vm.id, vm.id, vm.name, vm.type, vm.node]
    let vmInfo = [vm.id, vm.id, vm.name, vm.node, vm.type]
    vmInfoTable.row.add(vmInfo).draw();
  }
  
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
                      return '<input type="checkbox" name="'+ row[1] +'" value="'+ row[2] +'"/>'
                  }
              }
          ],
          // columns: [
          //   { title: "Select" },
          //   { title: "ID" },
          //   { title: "name" },
          //   { title: "type" },
          //   { title: "node" }
          // ],
          select : {
              style: 'multi',
          },
          lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
          order: [[1, 'asc']]
        });

        // Generates the VM table for each item in the list of machines
        for (i = 0; i < response.vmList.length; i++) {
          console.log(response.vmList)
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