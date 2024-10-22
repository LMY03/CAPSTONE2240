// // 在reports.js中
// window.addEventListener('load', function() {  // 使用load而不是DOMContentLoaded
//     console.log("Window fully loaded");
//     // 移除加载遮罩
//     // const loadingOverlay = document.getElementById('loading-overlay');
//     // if (loadingOverlay) {
//     //     loadingOverlay.style.display = 'none';
//     // }
    
//     // 显示主内容
//     // document.querySelector('.content').style.visibility = 'visible';
    
//     // 然后再执行原有的初始化代码
//     show();
//     console.log("Page loaded");
//     console.log("Current URL:", window.location.href);
// });


const base_url = ""

var table_data = []; //formdata
var selected_metrics = [];

var vmTable;

// Define the order of columns as they appear in the table
const columnOrder = [
    "Type", "Node", "Subject", "Name", "ID", "VM#", "LXC#", "CPU", 
    "CPU Usage(%)", "RAM(Gib)", "RAM Usage(%)", "Storage(Gib)", "Storage Usage(%)", 
    "Network In(K)", "Network Out(K)", "Uptime"
];

// Create a mapping between the table column names and the possible keys in tb_data
const columnMapping = {
    "Name": ["name", "Name"],
    "Type": ["type", "Type"],
    "Node": ["nodename", "Node"],
    "Subject": ["subject", "Subject"],
    "ID": ["vmid", "ID"],
    "VM#": ["vm number", "VM#"],
    "LXC#": ["lxc number", "LXC#"],
    "CPU": ["cpu", "CPU"],
    "CPU Usage(%)": ["cpu usage", "CPU Usage(%)"],
    "RAM(Gib)": ["mem", "RAM(Gib)"],
    "RAM Usage(%)": ["mem usage", "RAM Usage(%)"],
    "Storage(Gib)": ["storage", "Storage(Gib)"],
    "Storage Usage(%)": ["storage usage", "Storage Usage(%)"],
    "Network In(K)": ["netin", "Network In(K)"],
    "Network Out(K)": ["netout", "Network Out(K)"],
    "Uptime": ["uptime", "Uptime"]
};
    

function getTableData(start_time, end_time) {
    return new Promise((resolve, reject) => {

        const pathSegments = window.location.pathname.split('/');
        let type = 'system';  
        
        if (pathSegments.includes('system')) {
            type = 'system';
        } else if (pathSegments.includes('subject')) {
            type = 'subject';
        } else if (pathSegments.includes('vm')) {
            type = 'vm';
        }

        console.log("Current report type:", type);

        var params = {
            "start_time": start_time,
            "end_time": end_time,
            "type": type,
        };

        var xhr = new XMLHttpRequest();
        var queryString = Object.keys(params)
            .map(key => encodeURIComponent(key) + '=' + encodeURIComponent(params[key]))
            .join('&');
        var fullUrl = '/reports/formdata?' + queryString;

        xhr.open('GET', fullUrl, true);
        xhr.responseType = 'json';

        xhr.onload = function () {
            if (xhr.status === 200) {
                let data = xhr.response;
                resolve(data.data);

            } else {
                reject(new Error("Data interface exception"));
            }
        };

        xhr.onerror = function () {
            reject(new Error("Request failed"));
        };

        xhr.send();
    });
}


function getChartData(start_time, end_time, _type = "system", name = "system", nodename = "none", subject =
    "none", vmid = -1) {
    return new Promise((resolve, reject) => {
        var params = {
            "type": _type,
            "name": name,
            "nodename": nodename,
            "subject": subject,
            "vmid": vmid,
            "start_time": start_time, 
            "end_time": end_time
        };

        var xhr = new XMLHttpRequest();
        var queryString = Object.keys(params)
            .map(key => encodeURIComponent(key) + '=' + encodeURIComponent(params[key]))
            .join('&');
        var fullUrl = '/reports/graphdata?' + queryString;

        xhr.open('GET', fullUrl, true);
        xhr.responseType = 'json';

        xhr.onload = function () {
            if (xhr.status === 200) {
                let label_data = {};
                let data = xhr.response.data;
                let x_labels = [];

                data.forEach((element, index) => {
                    x_labels.push(data[index].time); // timestamp
                    let keys = Object.keys(element);
                    keys.forEach(e => {
                        if (e !== "time") {
                            if (e in label_data) {
                            label_data[e].push(element[e]); 
                        } else {
                            label_data[e] = [element[e]]; 
                        }
                        }
                    });
                });

                let result_data = []; 
                let keys = Object.keys(label_data);
                keys.forEach(e => {
                    result_data.push({
                        label: e,
                        data: label_data[e],
                        // borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        fill: false,
                    });
                });

                resolve({
                    x_labels,
                    result_data
                }); 
            } else {
                reject(new Error("Data interface exception")); 
            }
        };

        xhr.onerror = function () {
            reject(new Error("Request failed")); 
        };

        xhr.send(); 
    });
}


// graph-start

// deep copy
var copy_data = {};

var myChart = undefined;
function showchart(labels, datasets, title = "system"){
    if (myChart === undefined){     // no chart yet
        const data = {
            labels: labels,
            datasets : datasets
        }
        copy_data = JSON.parse(JSON.stringify(data))
        const cpuDataset = datasets.find(ds => ds.label === 'cpu') || datasets[0];
        const initialData = {
            labels: labels,
            datasets: [cpuDataset]
        };
        const config = {
                type: 'line',
                data: initialData,
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: title,
                            font: {
                                size: 20,
                                family: "'Baloo 2', sans-serif",
                                weight: 'bold'                                        
                            },
                            padding: {
                                top: 10,
                                bottom: 10
                            }
                        },
                        legend: {
                            position: 'top',
                            labels: {
                                font: {
                                    family: "'Ubuntu', sans-serif"
                                }
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(255, 255, 255, 0.8)',
                            titleColor: '#000',
                            bodyColor: '#000',
                            borderColor: '#d96a00',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Time',
                                font: {
                                    family: "'Ubuntu', sans-serif",
                                    size: 14
                                }
                            },
                            ticks: {
                                font: {
                                    family: "'Ubuntu', sans-serif"
                                }
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Value',
                                font: {
                                    family: "'Ubuntu', sans-serif",
                                    size: 14
                                }
                            },
                            ticks: {
                                font: {
                                    family: "'Ubuntu', sans-serif"
                                }
                            }
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeOutQuart'
                    },
                    elements: {
                        line: {
                            tension: 0.3
                        },
                        point: {
                            radius: 4,
                            hoverRadius: 6
                        }
                    }
                }
            };
        myChart = new Chart(document.getElementById('myChart'),config);
    } else {            // mychart exists
        myChart.data.labels = labels;
        // get selected metrics
        const selectedMetric = getSelectedMetric();
        // filter database
        const selectedDataset = datasets.find(ds => ds.label === selectedMetric) || datasets[0];
        // filteredDatasets can be nothing
        myChart.data.datasets = [selectedDataset];
        myChart.options.plugins.title.text = title;
        myChart.update();

        // Store the new data for later use
        copy_data = {
            labels: labels,
            datasets: datasets
        };

        const initialMetric = datasets[0].label;
        document.querySelector(`input[type="radio"][value="${initialMetric}"]`).checked = true;
    }

};

// Helper function to get selected metric
function getSelectedMetric() {
    const selectedRadio = document.querySelector('.radio-group input[type="radio"]:checked');
    return selectedRadio ? selectedRadio.value : null;
}

function updateChart() {
    const selectedMetric = getSelectedMetric();
    if (selectedMetric && copy_data && copy_data.datasets) {
        const dataset = copy_data.datasets.find(ds => ds.label === selectedMetric);
        if (dataset) {
            myChart.data.datasets = [{
                ...dataset,
                borderColor: getRandomColor(),
                backgroundColor: 'rgba(255, 255, 255, 0.1)'
            }];
            myChart.update();
        }
    }
    if (myChart) {
        myChart.update();
        updateTableHighlighting(vmTable);   
    }
}

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// default is cpu
document.querySelector('.radio-group input[type="radio"][value="cpu"]').checked = true;


// chart-end

// form - start

function showtable(tb_data) {
    // Store the original data for later use
    window.table_data = tb_data;

    // Define columns based on columnOrder and columnMapping
    let columns = columnOrder.map(columnName => {
        return {
            data: function(row, type, val, meta) {
                for (let key of columnMapping[columnName]) {
                    if (row.hasOwnProperty(key)) {
                        return row[key];
                    }
                }
                return null;
            },
            title: columnName
        }
    })

    // Check if DataTable already exists
    if ($.fn.DataTable.isDataTable('#VMtable')) {
        // Destroy the existing DataTable
        $('#VMtable').DataTable().destroy();
        // Clear the table content
        $('#VMtable').empty();
    }

    console.log("inside the show table")

    vmTable = $('table#VMtable').DataTable({
        data: tb_data,
        columns: columns,
        "pagingType": "simple_numbers",
        "autoWidth": false,
        "responsive": true,
        "select": true,
        'columnDefs': [
            { "type": "numeric", "targets": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14] },
            { className: "tdUptime", type: "natural", "targets": [15] }
        ],
        "rowCallback": function(row, data, index) {
            if (data.type === 'system') {
                $('td', row).css('background-color', '#e6f7ff');
            } else if (data.type === 'node') {
                $('td', row).css('background-color', '#fff1f0');
            } else if (data.type === 'subject') {
                $('td', row).css('background-color', '#f6ffed');
            }
        },
        "drawCallback": function(settings) {
            // Apply the cursor style to all rows after each draw
            $('#VMtable tbody tr').css('cursor', 'pointer');
            updateTableHighlighting(this.api());
        }
    });

    // Add click event listener to the entire table body
    $('#VMtable tbody').on('click', 'tr', function() {
        var data = vmTable.row(this).data();
        
        // Toggle selected class
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
        } else {
            vmTable.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }

        if (data) {  // Check if data exists (row is not empty)
            let {startDate, endDate} = getDateRange();
            getChartData(startDate, endDate, data.type, data.name, data.nodename, data.subject, data.vmid)
                .then(({x_labels, result_data}) => {
                    showchart(x_labels, result_data, data.name);
                    updateChart();
                });
        }
    });

    // Apply the cursor style initially
    $('#VMtable tbody tr').css('cursor', 'pointer');
}


function getDateRange(){
    const startDate_input = document.getElementById('startDate');
    const endDate_input = document.getElementById('endDate');
    const date = new Date(startDate_input.value);
    const startDate = date.getFullYear() + '-' +
        String(date.getMonth() + 1).padStart(2, '0') + '-' +
        String(date.getDate()).padStart(2, '0') + ' ' +
        String(date.getHours()).padStart(2, '0') + ':' +
        String(date.getMinutes()).padStart(2, '0') + ':' +
        String(date.getSeconds()).padStart(2, '0');

    const date_str = new Date(endDate_input.value);
    const endDate = date_str.getFullYear() + '-' +
        String(date_str.getMonth() + 1).padStart(2, '0') + '-' +
        String(date_str.getDate()).padStart(2, '0') + ' ' +
        String(date_str.getHours()).padStart(2, '0') + ':' +
        String(date_str.getMinutes()).padStart(2, '0') + ':' +
        String(date_str.getSeconds()).padStart(2, '0');

    return {startDate, endDate}
};

// export data
function exporeData() {
    const ws = XLSX.utils.json_to_sheet(table_data);
    // create sheet
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Sheet1");
    XLSX.writeFile(wb, "data.xlsx");
}

function exporeDataChart(){
    let chart_data = [];
    let labels = myChart.data.labels;
    let dataset = myChart.data.datasets.reduce((acc, item) => {
        acc[item.label] = item.data; 
        return acc;
        }, {});
    
    labels.forEach((element,index)=>{
        chart_data.push({
            "time" : element,
            "cpu" :  dataset.cpu[index],
            "cpu usage" : dataset["cpu usage"][index],
            "mem" : dataset["mem"][index],
            "mem usage" : dataset["mem usage"][index],
            "netin" : dataset["netin" ][index],
            "netout" : dataset[ 'netout'][index],
            "storage" : dataset['storage'][index],
            "storage usage" :dataset['storage'][index],
        })
    })
    const ws = XLSX.utils.json_to_sheet(chart_data);
    // create sheet
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Sheet1");
    XLSX.writeFile(wb, "data.xlsx");

}

// table -end
function show(){
    const startDate_input = document.getElementById('startDate');
    const endDate_input = document.getElementById('endDate');

    // get start date and end date
    if (!startDate_input.value || !endDate_input.value) {
        const now = new Date();
        now.setMinutes(now.getMinutes() + 480);
        const currentDateTime = now.toISOString().slice(0, 16);
        endDate_input.value = currentDateTime;
        now.setMinutes(now.getMinutes() - 1440);
        const pastOneDay = now.toISOString().slice(0, 16);
        startDate_input.value = pastOneDay
    };

    const date = new Date(startDate_input.value);
    const startDate = date.getFullYear() + '-' +
        String(date.getMonth() + 1).padStart(2, '0') + '-' +
        String(date.getDate()).padStart(2, '0') + ' ' +
        String(date.getHours()).padStart(2, '0') + ':' +
        String(date.getMinutes()).padStart(2, '0') + ':' +
        String(date.getSeconds()).padStart(2, '0');

    const date_str = new Date(endDate_input.value);
    const endDate = date_str.getFullYear() + '-' +
        String(date_str.getMonth() + 1).padStart(2, '0') + '-' +
        String(date_str.getDate()).padStart(2, '0') + ' ' +
        String(date_str.getHours()).padStart(2, '0') + ':' +
        String(date_str.getMinutes()).padStart(2, '0') + ':' +
        String(date_str.getSeconds()).padStart(2, '0');

    // get table data
    getTableData(startDate, endDate).then(tb_data=>{
        
        // Format uptime if it's a number
        tb_data = tb_data.map(row => {
            if (typeof row.uptime === 'number') {
                row.uptime = secondsToHHMMSS(row.uptime);
            }
            return row;
        });

        console.log("tb_data", tb_data);

        showtable(tb_data);
        table_data = tb_data;
    })
    // get chart data
    getChartData(startDate, endDate).then(
        ({x_labels, result_data}) =>{
            var labels, dataset;
            showchart(x_labels,result_data);
            updateChart();
        }
    );
};

show();

// Function to set cell background color based on value and thresholds
function setCellColor(cell, value, lowThreshold, midThreshold, highThreshold) {
    if (value > highThreshold) {
        $(cell).css('background-color', 'rgb(204, 0, 0, 0.5)');
        $(cell).css('border', '2.5px solid rgb(204,0,0)');
    } else if (value > midThreshold) {
        $(cell).css('background-color', 'rgb(259, 155, 0, 0.5)');
        $(cell).css('border', '2.5px solid rgb(239,155,0)');
    } else if (value > lowThreshold) {
        $(cell).css('background-color', 'rgb(253, 223, 46, 0.51)');
        $(cell).css('border', '2.5px solid rgb(232,204,39)');
    }
    // If value is 0 or below thresholds, we don't change the styling
}

// Function to update table highlighting
function updateTableHighlighting(table) {
    table.rows().every(function(rowIdx, tableLoop, rowLoop) {
        var data = this.data();

        // CPU Usage (index 8)
        var cpuUsage = parseFloat(data['cpu usage']);
        setCellColor(table.cell(rowIdx, 8).node(), cpuUsage, 25, 50, 75);

        // RAM Usage (index 10)
        var ramUsage = parseFloat(data['mem usage']);
        setCellColor(table.cell(rowIdx, 10).node(), ramUsage, 25, 50, 75);

        // Storage Usage (index 12)
        var storageUsage = parseFloat(data['storage usage']);
        setCellColor(table.cell(rowIdx, 12).node(), storageUsage, 25, 50, 75);
    });
}

function secondsToHHMMSS(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    return [hours, minutes, remainingSeconds]
        .map(v => v < 10 ? "0" + v : v)
        .filter((v,i) => v !== "00" || i > 0)
        .join(":");
}

