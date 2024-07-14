$(document).ready(function () {
    function drawLineGraph(dataSets, element, title, valueKey, valueKey2 = null) {
        var parentElement = d3.select(element).node().parentNode;
        var margin = { top: 20, right: 10, bottom: 30, left: 20 },
            width = parentElement.clientWidth - margin.left - margin.right,
            height = parentElement.clientHeight - margin.top - margin.bottom;

        var svg = d3.select(element)
            .append("svg")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("viewBox", `0 0 ${parentElement.clientWidth} ${parentElement.clientHeight}`)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var x = d3.scaleTime()
            .domain(d3.extent(dataSets.flatMap(d => d.data), function (d) { return new Date(d.time); }))
            .range([0, width]);

        svg.append("g")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(x));

        var y = d3.scaleLinear()
            .domain([0, d3.max(dataSets.flatMap(d => d.data), function (d) { return d[valueKey]; })])
            .range([height, 0]);

        svg.append("g")
            .call(d3.axisLeft(y));

        // Define a color scale to differentiate between hosts and metrics
        var color = d3.scaleOrdinal(d3.schemeCategory10);

        // Draw a line for each host and metric
        dataSets.forEach((hostData, index) => {
            var line = d3.line()
                .x(function (d) { return x(new Date(d.time)); })
                .y(function (d) { return y(d[valueKey]); });

            svg.append("path")
                .datum(hostData.data)
                .attr("fill", "none")
                .attr("stroke", color(index + 1))
                .attr("stroke-width", 1.5)
                .attr("d", line);


            svg.append("text")
                .attr("x", width - 150)
                .attr("y", ((index + 1) * 20) + 10)
                .attr("fill", color(index + 1))
                .text(`${hostData.host} (${valueKey.replace('_', ' ')})`);

        });

    }

    function drawMultiLineGraph(dataSets, datasets2, element, title, valueKey1, valueKey2) {
        var parentElement = d3.select(element).node().parentNode;
        var margin = { top: 20, right: 10, bottom: 30, left: 20 },
            width = parentElement.clientWidth - margin.left - margin.right,
            height = parentElement.clientHeight - margin.top - margin.bottom;

        var svg = d3.select(element)
            .append("svg")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("viewBox", `0 0 ${parentElement.clientWidth} ${parentElement.clientHeight}`)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var x = d3.scaleTime()
            .domain(d3.extent(dataSets.flatMap(d => d.data), d => new Date(d.time)))
            .range([0, width]);

        svg.append("g")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(x));

        var y = d3.scaleLinear()
            .domain([0, d3.max(dataSets.flatMap(d => d.data), function (d) { return d[valueKey1] })])
            .range([height, 0]);

        svg.append("g")
            .call(d3.axisLeft(y));

        var color = d3.scaleOrdinal(d3.schemeCategory10);

        dataSets.forEach((hostData, index) => {
            var line = d3.line()
                .x(d => x(new Date(d.time)))
                .y(d => y(d[valueKey1]));

            svg.append("path")
                .datum(hostData.data)
                .attr("fill", "none")
                .attr("stroke", color(index * 2))
                .attr("stroke-width", 1.5)
                .attr("d", line);

            svg.append("text")
                .attr("x", width - 150)
                .attr("y", ((index + 1) * 20) + 10)
                .attr("fill", color(index * 2))
                .text(`${hostData.host} (${valueKey1.replace('_', ' ')})`);

        });

        datasets2.forEach((hostData, index) => {
            var line = d3.line()
                .x(d => x(new Date(d.time)))
                .y(d => y(d[valueKey2]));

            svg.append("path")
                .datum(hostData.data)
                .attr("fill", "none")
                .attr("stroke", color(index * 3))
                .attr("stroke-width", 1.5)
                .attr("d", line);

            svg.append("text")
                .attr("x", width - 150)
                .attr("y", ((index + 3) * 20) + 10)
                .attr("fill", color(index * 3))
                .text(`${hostData.host} (${valueKey2.replace('_', ' ')})`);

        });
    }

    function init() {
        $.ajax({
            type: 'GET',
            url: 'monitoring/aggregateData/',
            data: {},
            datatype: 'json',
            success: function (response) {
                // Combine CPU usage data from all hosts
                var cpuDataSets = response.coresResultList.map(core => ({
                    host: core.host,
                    data: core.data
                }));
                drawLineGraph(cpuDataSets, '#cpu-chart', 'CPU Usage Across Hosts', 'cpu');

                // Combine Storage usage data from all hosts
                var storageDataSets = response.storageResultList.map(storage => ({
                    host: storage.host,
                    data: storage.data
                }));
                drawLineGraph(storageDataSets, '#storage-chart', 'Storage Usage Across Hosts', 'storage');

                // Combine RAM usage data (Free and Used) from all hosts
                var memoryTotalDataSet = response.memoryTotalResultList.map((mem, index) => ({
                    host: mem.host,
                    data: mem.data
                }))
                var memoryUsedDataSet = response.memoryUsedResultList.map((mem, index) => ({
                    host: mem.host,
                    data: mem.data
                }));
                drawMultiLineGraph(memoryTotalDataSet, memoryUsedDataSet, '#ram-chart', 'RAM Usage Across Hosts', 'memory_total', 'memory_used');

                // Combine Network usage data (In and Out) from all hosts
                var networkDataSets = response.networkInResultList.map((net, index) => ({
                    host: net.host,
                    data: net.data
                })).concat(response.networkOutResultList.map((net, index) => ({
                    host: net.host,
                    data: net.data
                })));
                drawMultiLineGraph(networkDataSets, '#network-chart', 'Network Usage Across Hosts', 'network_in', 'network_out');
            },
            error: function (response) {
                console.log(response);
            }
        });
    }

    init();
});
