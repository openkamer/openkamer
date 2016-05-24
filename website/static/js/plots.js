
var create_plot = function(json_filepath, title) {
    // Set the dimensions of the canvas / graph
    plot_width = parseInt(d3.select("body").select("#plot").style('width'), 10);
    var margin = {top: 60, right: 30, bottom: 50, left: 60};
    var width = plot_width - margin.left - margin.right;
    var height = Math.min(plot_width/2.0 - margin.top - margin.bottom, 300);
    var plot_height = height + margin.top + margin.bottom;

    // Parse the date / time
    var parseDate = d3.time.format("%Y-%m-%d").parse;
    var bisectDate = d3.bisector(function(d) { return d.datetime; }).left;

    // Set the ranges
    var x = d3.time.scale().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);

    // Define the axes
    var xAxis = d3.svg.axis().scale(x)
        .orient("bottom").ticks(7);

    var yAxis = d3.svg.axis().scale(y)
        .orient("left").ticks(8);

    // Define the line
    var valueline = d3.svg.line()
        .x(function(d) { return x(d.datetime); })
        .y(function(d) { return y(d.y); });

    // Adds the svg canvas
    var svg = d3.select("body").select("#plot")
        .append("svg")
            .attr("id", title)
            .attr("width", plot_width)
            .attr("height", plot_height)
        .append("g")
            .attr("transform",
                  "translate(" + margin.left + "," + margin.top + ")");


    // Get the data
    d3.json(json_filepath, function(json) {
        var data = json.points;
        data.forEach(function(d) {
            d.datetime = parseDate(d.datetime);
        });

        // Scale the range of the data
        x.domain(d3.extent(data, function(d) { return d.datetime; }));
        y.domain([0, d3.max(data, function(d) { return d.y + 1; })]);

        // Add the valueline path.
        svg.append("path")
            .attr("class", "line")
            .attr("d", valueline(data));

        // Append marker
        svg.selectAll(".marker")
            .data(data)
            .enter().append("circle")
            .attr("class", "marker")
            .attr("r", 3)
            .attr("cx", function(d) { return x(d.datetime); })
            .attr("cy", function(d) { return y(d.y); });

        // focus is based on http://www.d3noob.org/2014/07/my-favourite-tooltip-method-for-line.html
        var focus = svg.append("g")
            .style("display", "none");

        // append the rectangle to capture mouse
        svg.append("rect")
            .attr("width", plot_width)
            .attr("height", plot_height)
            .style("fill", "none")
            .style("pointer-events", "all")
            .on("mouseover", function() { focus.style("display", null); })
            .on("mouseout", function() { focus.style("display", "none"); })
            .on("mousemove", mousemove);

        // append the circle at the intersection
        focus.append("circle")
            .attr("class", "y")
            .style("fill", "steelblue")
            .style("stroke-width", 3)
            .style("stroke", "white")
            .attr("r", 5);

        // place the value at the intersection
        focus.append("text")
            .attr("class", "y1")
            .style("stroke", "black")
            .style("stroke-width", "3.5px")
            .style("opacity", 0.8)
            .attr("dx", 8)
            .attr("dy", "-.3em");

        focus.append("text")
            .attr("class", "y2")
            .style("fill", "white")
            .attr("dx", 8)
            .attr("dy", "-.3em");

        // place the date at the intersection
        focus.append("text")
            .attr("class", "y3")
            .style("stroke", "black")
            .style("stroke-width", "3.5px")
            .style("opacity", 0.8)
            .attr("dx", 8)
            .attr("dy", "1em");

        focus.append("text")
            .attr("class", "y4")
            .style("fill", "white")
            .attr("dx", 8)
            .attr("dy", "1em");

        function mousemove() {
            var x0 = x.invert(d3.mouse(this)[0]);
            var i = bisectDate(data, x0, 1);
            if (i > 0 && i < data.length) {
                var d0 = data[i - 1];
                var d1 = data[i];
                var d = x0 - d0.datetime > d1.datetime - x0 ? d1 : d0;
            } else { // mouse is outside the plot area, i is not valid
                var d = data[data.length-1];
            }

            focus.select("circle.y")
                .attr("transform",
                      "translate(" + x(d.datetime) + "," +
                                     y(d.y) + ")");

            var formatDate = d3.time.format("%d %b");

            var tooltip_x = x(d.datetime) - 100;
            var tooltip_y = y(d.y) - 30;
            var translate_str = "translate(" + tooltip_x + "," + tooltip_y + ")";

            focus.select("text.y1")
                .attr("transform", translate_str)
                .text(Math.round(d.y) + ' ' + json.unit);

            focus.select("text.y2")
                .attr("transform", translate_str)
                .text(Math.round(d.y) + ' ' + json.unit);

            focus.select("text.y3")
                .attr("transform", translate_str)
                .text(formatDate(d.datetime));

            focus.select("text.y4")
                .attr("transform", translate_str)
                .text(formatDate(d.datetime));
        }

//        d3.select(window).on('resize', resize);
//
//        function resize() {
//            // update width
////            var svg = svg;
////            var x = x;
//            plot_width = parseInt(d3.select("body").select("#plot").style('width'), 10);
//            width = plot_width - margin.left - margin.right;
//            x.range([0, width]);
//            d3.select("body").select("#plot").select("svg")
//            .attr("width", width)
//        }

        // Add the X Axis
        svg.append("g")
            .attr("class", "x axis")
            .style("fill", "steelblue")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        svg.append("text")      // text label for the x axis
            .attr("x", width / 2 )
            .attr("y",  height + margin.bottom )
            .style("text-anchor", "middle")
            .style("fill", "white")
            .text(json['xlabel']);

        // Add the Y Axis
        svg.append("g")
            .attr("class", "y axis")
            .style("fill", "steelblue")
            .call(yAxis);

        svg.append("text")      // text label for the x axis
            .attr("transform", "rotate(-90)")
            .attr("x", 0 - height / 2 )
            .attr("y", - margin.left )
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .style("fill", "white")
            .text(json['ylabel']);

        svg.append("text")
            .attr("x", width / 2 )
            .attr("y", "-1em")
            .style("text-anchor", "middle")
            .style("fill", "white")
            .style("font-size", "1.5em")
            .text(json['title']);
    });
};

create_plot("/static/media/test.json", "documents");
