$(document).ready(function () {
    function drawLineGraph(dataSets, element, title, valueKey) {
        var parentElement = d3.select(element).node().parentNode;
        var margin = { top: 20, right: 30, bottom: 30, left: 40 },
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

        // Define a color scale to differentiate between hosts
        var color = d3.scaleOrdinal(d3.schemeCategory10);

        // Draw a line for each host
        dataSets.forEach((hostData, index) => {
            var line = d3.line()
                .x(function (d) { return x(new Date(d.time)); })
                .y(function (d) { return y(d[valueKey]); });

            svg.append("path")
                .datum(hostData.data)
                .attr("fill", "none")
                .attr("stroke", color(index))
                .attr("stroke-width", 1.5)
                .attr("d", line);

            svg.append("text")
                .attr("x", width - 100)
                .attr("y", (index * 20) + 10)
                .attr("fill", color(index))
                .text(hostData.host);
        });

        svg.append("text")
            .attr("x", (width / 2))
            .attr("y", 0 - (margin.top / 2))
            .attr("text-anchor", "middle")
            .style("font-size", "16px")
            .style("text-decoration", "underline")
            .text(title);
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
                var ramDataSets = [
                    { data: response.memoryFreeResultList.flatMap(mem => mem.data), host: 'Free RAM', label: 'memory_free' },
                    { data: response.memoryUsedResultList.flatMap(mem => mem.data), host: 'Used RAM', label: 'memory_used' }
                ];
                drawLineGraph(ramDataSets, '#ram-chart', 'RAM Usage Across Hosts', 'memory_free');

                // Combine Network usage data (In and Out) from all hosts
                var networkDataSets = [
                    { data: response.networkInResultList.flatMap(net => net.data), host: 'Network In', label: 'network_in' },
                    { data: response.networkOutResultList.flatMap(net => net.data), host: 'Network Out', label: 'network_out' }
                ];
                drawLineGraph(networkDataSets, '#network-chart', 'Network Usage Across Hosts', 'network_in');
            },
            error: function (response) {
                console.log(response);
            }
        });
    }

    init();
});
