$(document).ready(function () {
  let chartState = {
    svg: null,
    x: null,
    y: null,
    width: null,
    height: null,
    margin: { top: 30, right: 30, bottom: 70, left: 60 },
    currentData: null,
    vm_count_data: null,
    section_count_data: null
  };

  $('.report-item').on('click', function () {
    $(this).find('.chevron').toggleClass('rotated');
  });

  // Handle Form submission
  $('#filterForm').on('submit', function (e) {
    e.preventDefault();     // prevent the default action

    // Create a form element
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = 'extract_general_stat';

    // Append all input fields from #filterForm
    // Append all input fields from #summaryfilterForm
    $(this).find('input, select').each(function () {
      var input = document.createElement('input');
      input.type = 'hidden';
      input.name = this.name;
      input.value = this.value;
      form.appendChild(input);
    });

    // Append CSRF token
    var csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = $('input[name=csrfmiddlewaretoken]').val();
    form.appendChild(csrfInput);

    // Append form to body and submit
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
  });

  // Handle Form submission
  $('#filterForm2').on('submit', function (e) {
    e.preventDefault();     // prevent the default action

    // Create a form element
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = 'extract_detail_stat';

    // Append all input fields from #detailedFilterForm
    $(this).find('input, select').each(function () {
      var input = document.createElement('input');
      input.type = 'hidden';
      input.name = this.name;
      input.value = this.value;
      form.appendChild(input);
    });

    // Append CSRF token
    var csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = $('input[name=csrfmiddlewaretoken]').val();
    form.appendChild(csrfInput);

    // Append form to body and submit
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
  });

  $('#general_ticketing_reports_form').on('submit', function (e) {
    e.preventDefault(); // Prevent the default form submission

    // Gather form data
    var formData = $(this).serialize();
    var startDate = $('#ticketingdateStart').val();
    var endDate = $('#ticketingdateEnd').val();

    console.log(startDate, endDate)
    if (validateDates(startDate, endDate)) {
      console.log('correct date format')
      $.ajax({
        type: 'POST',
        url: $(this).attr('action'),
        data: formData,
        dataType: 'json', // Expect a JSON response
        success: function (response) {
          // Handle successful response
          // Generate tables and card for ticket report summary
          console.log("Form submitted successfully:", response);
          $('#generated-report-section').removeClass('d-none');
          $('#average_core_request').html(response.average_stats.avg_cores)
          $('#average_ram_request').html(response.average_stats.avg_ram)
          $('#average_accepted_turnover_list').html(response.average_accepted_turnover)
          $('#average_lifecycle_request_list').html(response.average_turn_over_days_to_due_date)

          request_use_case_table_init(response.total_times_requested)
          class_course_request_table_init(response.vm_count_stat, response.sections_course_stat)

        },
        error: function (xhr, status, error) {
          // Handle error response
          console.error("Form submission failed:", status, error);
          // Optionally, show an error message to the user
        }
      });
      $('#error_alert_ticketing').addClass('d-none');
    } else {
      console.log('wrong date format')
      $('#error_alert_ticketing').removeClass('d-none');
    }

    // Make the AJAX request

  });

  function validateDates(startDate, endDate) {
    if (!startDate || !endDate) {
      return false;
    }

    if (new Date(startDate) > new Date(endDate)) {
      return false;
    }

    return true;
  }


  function request_use_case_table_init(data) {
    var margin = { top: 30, right: 30, bottom: 70, left: 60 },
      width = 500 - margin.left - margin.right,
      height = 400 - margin.top - margin.bottom;

    // Append the SVG object to the body of the page
    var svg = d3.select("#request_use_case_table")
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform",
        "translate(" + margin.left + "," + margin.top + ")");

    var request_use_case_data = Object.entries(data).map(([key, value]) => ({ use_case: key, total: value }));

    var x = d3.scaleBand()
      .range([0, width])
      .domain(request_use_case_data.map(function (d) { return d.use_case; })) // Use the use_case property
      .padding(0.2);
    svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "translate(0,0)rotate(0)")
      .style("text-anchor", "center");

    // Add Y axis
    var y = d3.scaleLinear()
      .domain([0, d3.max(request_use_case_data, function (d) { return d.total; })]) // Use d3.max to set Y domain dynamically
      .range([height, 0]);
    svg.append("g")
      .call(d3.axisLeft(y));

    // Bars
    svg.selectAll("mybar")
      .data(request_use_case_data)
      .enter()
      .append("rect")
      .attr("x", function (d) { return x(d.use_case); }) // Use the use_case property
      .attr("y", function (d) { return y(d.total); }) // Use the total property
      .attr("width", x.bandwidth())
      .attr("height", function (d) { return height - y(d.total); }) // Use the total property
      .attr("fill", "#69b3a2");
  }

  function class_course_request_table_init(vm_count_stat, sections_course_stat) {
    // Clear any existing chart
    d3.select('#class_course_requests_table svg').remove();

    // Convert data
    chartState.vm_count_data = Object.entries(vm_count_stat)
      .map(([key, value]) => ({ course_code: key, total: value }));

    chartState.section_count_data = Object.entries(sections_course_stat)
      .map(([key, value]) => ({ course_code: key, total: value }));

    // Set current data
    chartState.currentData = chartState.vm_count_data;

    // Setup dimensions
    const width = 500 - chartState.margin.left - chartState.margin.right;
    const height = 400 - chartState.margin.top - chartState.margin.bottom;
    chartState.width = width;
    chartState.height = height;

    // Create SVG
    const svg = d3.select('#class_course_requests_table')
      .append("svg")
      .attr("width", width + chartState.margin.left + chartState.margin.right)
      .attr("height", height + chartState.margin.top + chartState.margin.bottom)
      .append("g")
      .attr("transform", `translate(${chartState.margin.left},${chartState.margin.top})`);

    chartState.svg = svg;

    // Create scales
    chartState.x = d3.scaleBand()
      .range([0, width])
      .domain(chartState.currentData.map(d => d.course_code))
      .padding(0.2);

    chartState.y = d3.scaleLinear()
      .domain([0, d3.max(chartState.currentData, d => d.total)])
      .range([height, 0]);

    // Create axes
    svg.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(chartState.x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end");

    svg.append("g")
      .attr("class", "y-axis")
      .call(d3.axisLeft(chartState.y));

    // Add toggle button
    const toggleContainer = $('#class_course_filter_list')

    toggleContainer.append(
      $('<li>')
        .attr("class", "dropdown-item")
        .text("Show total VM Count")
        .on("click", () => updateChart(chartState.vm_count_data))
    );

    toggleContainer.append(
      $('<li>')
        .attr("class", "dropdown-item")
        .text("Show total Section Count")
        .on("click", () => updateChart(chartState.section_count_data))
    );

    // Initial render
    updateChart(chartState.currentData);
  }

  function updateChart(newData) {
    if (!chartState.svg) return;

    // Update current data reference
    chartState.currentData = newData;

    // Update scales
    chartState.x.domain(newData.map(d => d.course_code));
    chartState.y.domain([0, d3.max(newData, d => d.total)]);

    // Update axes with transition
    chartState.svg.select(".x-axis")
      .transition()
      .duration(750)
      .call(d3.axisBottom(chartState.x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end");

    chartState.svg.select(".y-axis")
      .transition()
      .duration(750)
      .call(d3.axisLeft(chartState.y));

    // Update bars
    const bars = chartState.svg.selectAll("rect")
      .data(newData, d => d.course_code);

    // Remove old bars
    bars.exit()
      .transition()
      .duration(750)
      .attr("y", chartState.height)
      .attr("height", 0)
      .remove();

    // Add new bars
    const newBars = bars.enter()
      .append("rect")
      .attr("x", d => chartState.x(d.course_code))
      .attr("y", chartState.height)
      .attr("width", chartState.x.bandwidth())
      .attr("height", 0)
      .attr("fill", "#69b3a2");

    // Update all bars
    bars.merge(newBars)
      .transition()
      .duration(750)
      .attr("x", d => chartState.x(d.course_code))
      .attr("y", d => chartState.y(d.total))
      .attr("width", chartState.x.bandwidth())
      .attr("height", d => chartState.height - chartState.y(d.total));

    // Add tooltips
    chartState.svg.selectAll("rect")
      .on("mouseover", function (event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("fill", "#3498db");

        // Add tooltip
        chartState.svg.append("text")
          .attr("class", "tooltip")
          .attr("x", chartState.x(d.course_code) + chartState.x.bandwidth() / 2)
          .attr("y", chartState.y(d.total) - 5)
          .attr("text-anchor", "middle")
          .text(`${d.total}`)
          .style("font-size", "12px");
      })
      .on("mouseout", function () {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("fill", "#69b3a2");

        // Remove tooltip
        chartState.svg.selectAll(".tooltip").remove();
      });
  }
});