import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const GraphVisualization = ({ data }) => {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Add resize handler
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };

    window.addEventListener('resize', updateDimensions);
    updateDimensions();

    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (!data || !svgRef.current || !dimensions.width || !dimensions.height) return;

    // Clear any existing SVG content
    d3.select(svgRef.current).selectAll("*").remove();

    // Process nodes to expand thoughts into separate nodes
    const expandedNodes = [];
    const expandedEdges = [];
    
    data.nodes.forEach(node => {
      if (node.thoughts && node.thoughts.length > 0) {
        node.thoughts.forEach((thought, index) => {
          const newNode = {
            key: `${node.key}_thought_${index}`,
            label: thought.question,
            tag: node.tag,
            cluster: node.cluster,
            x: node.x,
            y: node.y,
            sizenode: node.sizenode,
            thoughts: [thought]
          };
          expandedNodes.push(newNode);

          // Create edges between thoughts
          if (index > 0) {
            expandedEdges.push([
              `${node.key}_thought_${index-1}`,
              `${node.key}_thought_${index}`,
              "Next step"
            ]);
          }
        });
      }
    });

    // Process original edges to connect with expanded nodes
    data.edges.forEach(edge => {
      const sourceNode = data.nodes.find(n => n.key === edge[0]);
      const targetNode = data.nodes.find(n => n.key === edge[1]);
      
      const sourceLastThoughtIndex = sourceNode.thoughts.length - 1;
      const targetFirstThoughtIndex = 0;
      
      expandedEdges.push([
        `${edge[0]}_thought_${sourceLastThoughtIndex}`,
        `${edge[1]}_thought_${targetFirstThoughtIndex}`,
        edge[2]
      ]);
    });

    // Set up SVG dimensions
    const width = dimensions.width;
    const height = dimensions.height;
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Create a group for the zoom
    const g = svg.append('g');

    // Add zoom capabilities
    const zoom = d3.zoom()
      .scaleExtent([0.1, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Process edges for D3
    const d3Edges = expandedEdges.map(edge => ({
      source: edge[0],
      target: edge[1],
      label: edge[2]
    }));

    // Create force simulation with expanded nodes
    const simulation = d3.forceSimulation(expandedNodes)
      .force("link", d3.forceLink(d3Edges)
        .id(d => d.key)
        .distance(200))
      .force("charge", d3.forceManyBody().strength(-1000))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // Add arrow marker definition
    svg.append("defs").selectAll("marker")
      .data(["end"])
      .enter().append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 30)
      .attr("refY", 0)
      .attr("markerWidth", 8)
      .attr("markerHeight", 8)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#999");

    // Draw edges with arrows
    const links = g.selectAll(".link")
      .data(d3Edges)
      .enter()
      .append("g")
      .attr("class", "link-group");

    links.append("line")
      .attr("class", "link")
      .style("stroke", "#999")
      .style("stroke-width", 2)
      .attr("marker-end", "url(#arrow)");

    // Add edge labels
    links.append("text")
      .attr("class", "edge-label")
      .attr("dy", -8)
      .attr("text-anchor", "middle")
      .text(d => d.label);

    // Create node groups
    const nodes = g.selectAll(".node")
      .data(expandedNodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // Add circles to nodes
    nodes.append("circle")
      .attr("r", d => d.sizenode || 40)
      .style("fill", d => {
        const cluster = data.clusters.find(c => c.key === d.cluster);
        return cluster ? cluster.color : "#ccc";
      });

    // Add node content
    nodes.each(function(d) {
      const node = d3.select(this);
      const thought = d.thoughts[0];
      
      // Add question text
      node.append("text")
        .attr("dy", -15)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .style("font-weight", "bold")
        .text(thought.question);

      // Add current answer if exists
      if (thought.current) {
        node.append("text")
          .attr("dy", 15)
          .attr("text-anchor", "middle")
          .style("font-size", "12px")
          .text(thought.current);
      }

      // Add phase number
      node.append("text")
        .attr("dy", 35)
        .attr("text-anchor", "middle")
        .style("font-size", "10px")
        .style("fill", "#666")
        .text(`Phase ${thought.phase}`);
    });

    // Add hover effect
    nodes.append("title")
      .text(d => {
        const thought = d.thoughts[0];
        return `${d.label}\nQuestion: ${thought.question}\nCurrent: ${thought.current}\nPhase: ${thought.phase}`;
      });

    // Update positions on tick
    simulation.on("tick", () => {
      links.select("line")
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      links.select("text")
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2);

      nodes.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

  }, [data, dimensions]);

  return (
    <div className="graph-container" ref={containerRef}>
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default GraphVisualization; 