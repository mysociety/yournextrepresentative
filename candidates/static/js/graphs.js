d3.csv('/leaderboard/contributions.csv', function(error, completeData) {

    if (error) {
        console.log("error", error);
    }

    var data = completeData.filter(function (d) {
        /* return d.contributions > 0; */
        return d.rank < 40;
    });

    var maxContributions = d3.max(data, function (d) {
        return parseInt(d.contributions);
    });

    console.log("maxContributions is:", maxContributions);

    var svg = d3.select('svg'),
    /* This isn't very robust - if it's "1000px", say, that's fine, but
       would work for "100%" */
    w = parseInt(svg.style('width')),
    h = parseInt(svg.style('height')),
    padding = 50,
    barPadding = 1,
    yScale = d3.scale.linear()
                     .domain([0, maxContributions])
                     .range([h - 2 * padding, padding])
                     .nice();
    xScale = d3.scale.ordinal()
                      .domain(data.map(function (d) { return d.username; }))
                      .rangeBands([padding, w - 2 * padding], 0.05);
    var yAxis = d3.svg.axis()
                      .scale(yScale)
                      .orient("left");
    var xAxis = d3.svg.axis()
                      .scale(xScale);

    svg.selectAll("rect")
        .data(data).enter()
        .append("rect")
        .attr("x", function(d, i) {
            return xScale(d.username);
        })
        .attr("y", function(d) {
            return yScale(d.contributions);
        })
        .attr("width", w / data.length)
        .attr("height", function(d) {
            return (h - 2 * padding) - yScale(d.contributions);
        })
        .attr("fill", "teal");

    svg.append("g").attr("class", "axis")
                   .attr('transform', 'translate(' + padding + ', 0)')
                   .call(yAxis);

    svg.append("g").attr("class", "axis")
                   .attr('transform', 'translate(0, ' + (h - padding * 2) + ')')
                   .call(xAxis)
                   .selectAll("text")
                   .attr('y', -4)
                   .attr('x', -9)
                   .attr('transform', 'rotate(270)')
                   .style('text-anchor', 'end');
});
