$(document).ready(function () {
    function drawLineGraph(data, element, title, valueKey) {
        var margin = { top: 20, right: 30, bottom: 30, left: 40 },
            width = 460 - margin.left - margin.right,
            height = 400 - margin.top - margin.bottom;

        var svg = d3.select(element)
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var x = d3.scaleTime()
            .domain(d3.extent(data, function (d) { return new Date(d.time); }))
            .range([0, width]);

        svg.append("g")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(x));

        var y = d3.scaleLinear()
            .domain([0, d3.max(data, function (d) { return d[valueKey]; })])
            .range([height, 0]);

        svg.append("g")
            .call(d3.axisLeft(y));

        svg.append("path")
            .datum(data)
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            .attr("stroke-width", 1.5)
            .attr("d", d3.line()
                .x(function (d) { return x(new Date(d.time)); })
                .y(function (d) { return y(d[valueKey]); })
            );

        svg.append("text")
            .attr("x", (width / 2))
            .attr("y", 0 - (margin.top / 2))
            .attr("text-anchor", "middle")
            .style("font-size", "16px")
            .style("text-decoration", "underline")
            .text(title);
    }
    function drawMultiLineGraph(data1, data2, element, title, valueKey1, valueKey2) {
        var margin = { top: 20, right: 30, bottom: 30, left: 40 },
            width = 460 - margin.left - margin.right,
            height = 400 - margin.top - margin.bottom;

        var svg = d3.select(element)
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var x = d3.scaleTime()
            .domain(d3.extent(data1.concat(data2), function (d) { return new Date(d.time); }))
            .range([0, width]);

        svg.append("g")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(x));

        var y = d3.scaleLinear()
            .domain([0, d3.max(data1.concat(data2), function (d) { return d[valueKey1] || d[valueKey2]; })])
            .range([height, 0]);

        svg.append("g")
            .call(d3.axisLeft(y));

        var line1 = d3.line()
            .x(function (d) { return x(new Date(d.time)); })
            .y(function (d) { return y(d[valueKey1]); });

        var line2 = d3.line()
            .x(function (d) { return x(new Date(d.time)); })
            .y(function (d) { return y(d[valueKey2]); });

        svg.append("path")
            .datum(data1)
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            .attr("stroke-width", 1.5)
            .attr("d", line1);

        svg.append("path")
            .datum(data2)
            .attr("fill", "none")
            .attr("stroke", "red")
            .attr("stroke-width", 1.5)
            .attr("d", line2);

        svg.append("text")
            .attr("x", (width / 2))
            .attr("y", 0 - (margin.top / 2))
            .attr("text-anchor", "middle")
            .style("font-size", "16px")
            .style("text-decoration", "underline")
            .text(title);

        var legend = svg.append("g")
            .attr("transform", "translate(" + (width - 100) + ", 0)");

        legend.append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", 10)
            .attr("height", 10)
            .attr("fill", "steelblue");

        legend.append("text")
            .attr("x", 20)
            .attr("y", 10)
            .text("Free RAM");

        legend.append("rect")
            .attr("x", 0)
            .attr("y", 20)
            .attr("width", 10)
            .attr("height", 10)
            .attr("fill", "red");

        legend.append("text")
            .attr("x", 20)
            .attr("y", 30)
            .text("Used RAM");
    }
    function init() {
        $.ajax({
            type: 'GET',
            url: 'monitoring/aggregateData/',
            data: {},
            datatype: 'json',
            success: function (response) {
                drawLineGraph(response.coresResultList, '#cpu-chart', 'CPU Usage', 'cpu');
                drawLineGraph(response.storageResultList, '#storage-chart', 'Storage Usage', 'storage');
                drawMultiLineGraph(response.memoryFreeResultList, response.memoryUsedResultList, '#ram-chart', 'RAM Usage', 'memory_free', 'memory_used');
                drawMultiLineGraph(response.networkInResultList, response.networkOutResultList, '#network-chart', 'Network Usage', 'network_in', 'network_out');
            },
            error: function (response) {
                console.log(response);
            }
        });
    }

    init();
});
