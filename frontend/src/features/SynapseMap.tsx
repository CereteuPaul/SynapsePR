import { useRef, useEffect } from "react";
import * as d3 from "d3";

type RoadmapItem = {
  file_path: string;
  review_priority: number;
};

type Props = {
  roadmap?: RoadmapItem[];
};

export default function SynapseMap({ roadmap }: Props) {
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const data = (roadmap || [])
      .slice(0, 12)
      .map((r, i) => ({ id: r.file_path, group: i % 3 }));
    const width = 380;
    const height = 160;

    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    const linkForce = d3
      .forceLink()
      .id((d: any) => d.id)
      .distance(40);
    const simulation = d3
      .forceSimulation(data as any)
      .force("charge", d3.forceManyBody().strength(-50))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("link", linkForce);

    // add zoom
    const container = svg.append("g");

    const node = container
      .append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(data)
      .enter()
      .append("g");

    node
      .append("circle")
      .attr("r", 18)
      .attr("fill", "#06b6d4")
      .attr("opacity", 0.14);

    node
      .append("text")
      .text((d: any) => d.id.split("/").slice(-1)[0])
      .attr("font-size", 10)
      .attr("fill", "#cbd5e1")
      .attr("text-anchor", "middle")
      .attr("dy", 4);

    // tooltip
    const parent = ref.current?.parentElement;
    let tooltip: any = null;
    if (parent) {
      tooltip = d3
        .select(parent)
        .append("div")
        .style("position", "absolute")
        .style("pointer-events", "none")
        .style("padding", "6px 8px")
        .style("background", "rgba(2,6,23,0.9)")
        .style("color", "#e2e8f0")
        .style("border-radius", "6px")
        .style("font-size", "12px")
        .style("display", "none");
    }

    node
      .on("mouseover", function (_event: any, d: any) {
        d3.select(this).select("circle").attr("opacity", 0.28);
        if (tooltip) {
          tooltip
            .style("display", "block")
            .html("<strong>" + d.id + "</strong>");
        }
      })
      .on("mousemove", function (event: any) {
        if (tooltip) {
          tooltip
            .style("left", event.offsetX + 16 + "px")
            .style("top", event.offsetY + 8 + "px");
        }
      })
      .on("mouseout", function () {
        d3.select(this).select("circle").attr("opacity", 0.14);
        if (tooltip) tooltip.style("display", "none");
      })
      .call(
        d3
          .drag()
          .on("start", (event: any, d: any) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event: any, d: any) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event: any, d: any) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }) as any,
      );

    svg.call(
      (d3.zoom() as any).on("zoom", (event: any) =>
        container.attr("transform", event.transform),
      ),
    );

    simulation.on("tick", () => {
      node.attr("transform", (d: any) => "translate(" + d.x + "," + d.y + ")");
    });

    return () => {
      simulation.stop();
    };
  }, [roadmap]);

  return (
    <div style={{ margin: "12px 0" }}>
      <div style={{ fontSize: 12, color: "#cbd5e1", marginBottom: 8 }}>
        Synapse Map
      </div>
      <svg
        ref={ref}
        width={380}
        height={160}
        style={{ background: "transparent", borderRadius: 8 }}
      />
    </div>
  );
}
