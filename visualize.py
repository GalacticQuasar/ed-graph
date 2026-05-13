import argparse
import json

import networkx as nx
from pyvis.network import Network

ED_THREAD_URL = "https://edstem.org/us/courses/{course_id}/discussion/threads/{thread_number}"

CATEGORY_COLORS = {
    "General": "#4A90D9",
    "Question": "#50C878",
    "Social": "#B565A7",
    "Lectures": "#F5A623",
    "Assignments": "#E74C3C",
    "Problem Sets": "#00BCD4",
}

DEFAULT_COLOR = "#8899A6"

PALETTE = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4",
    "#469990", "#dcbeff", "#9A6324", "#fffac8", "#800000",
    "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9",
]


def category_color(category: str, all_categories: list[str]) -> str:
    if category in CATEGORY_COLORS:
        return CATEGORY_COLORS[category]
    try:
        idx = all_categories.index(category)
        return PALETTE[idx % len(PALETTE)]
    except ValueError:
        return DEFAULT_COLOR


TYPE_SHAPES = {
    "question": "dot",
    "note": "box",
    "announcement": "star",
    "poll": "triangle",
}


def load_graph(json_path: str) -> nx.DiGraph:
    with open(json_path) as f:
        data = json.load(f)
    return nx.node_link_graph(data, directed=True)


def make_label(node_id: int, attrs: dict) -> str:
    title = attrs.get("title", "")
    max_len = 35
    if len(title) > max_len:
        title = title[: max_len - 1] + "\u2026"
    return f"#{node_id} {title}"


def make_tooltip(node_id: int, attrs: dict, degree: int, url: str) -> str:
    title = attrs.get("title", "")
    category = attrs.get("category", "")
    thread_type = attrs.get("type", "")
    lines = [
        f"<b>#{node_id}: {title}</b>",
        f"Category: {category}",
        f"Type: {thread_type}",
        f"Connections: {degree}",
    ]
    if url:
        lines.append(f'<a href="{url}" target="_blank">Open on Ed \u2197</a>')
    return "<br>".join(lines)


CLICK_JS_TEMPLATE = """
<script>
network.on("click", function(params) {{
    if (params.nodes.length === 1) {{
        var nodeId = params.nodes[0];
        var url = "https://edstem.org/us/courses/{course_id}/discussion/threads/" + nodeId;
        window.open(url, "_blank");
    }}
}});
</script>
"""


def build_pyvis_network(G: nx.DiGraph, output_path: str):
    course_id = G.graph.get("course_id", "")

    net = Network(
        height="98vh",
        width="100%",
        directed=True,
        notebook=False,
        neighborhood_highlight=True,
        select_menu=False,
        filter_menu=False,
        bgcolor="#1a1a2e",
        font_color="#e0e0e0",
        cdn_resources="remote",
    )

    net.set_options(
        """
    {
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -5000,
                "centralGravity": 0.2,
                "springLength": 150,
                "springConstant": 0.04,
                "damping": 0.09
            },
            "minVelocity": 0.75
        },
        "edges": {
            "arrows": {
                "to": { "enabled": true, "scaleFactor": 0.6 }
            },
            "smooth": {
                "type": "continuous",
                "roundness": 0.5
            },
            "color": {
                "opacity": 0.6,
                "inherit": "from"
            },
            "width": 1.5
        },
        "nodes": {
            "font": {
                "size": 14,
                "face": "Inter, system-ui, -apple-system, sans-serif"
            },
            "borderWidth": 1,
            "borderWidthSelected": 3,
            "shadow": {
                "enabled": true
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
        }
    }
    """
    )

    all_categories = sorted(
        {G.nodes[n].get("category", "") for n in G.nodes()}
    )

    for node_id in G.nodes():
        attrs = G.nodes[node_id]
        category = attrs.get("category", "")
        color = category_color(category, all_categories)
        thread_type = attrs.get("type", "")
        shape = TYPE_SHAPES.get(thread_type, "dot")
        degree = G.degree(node_id)

        url = ED_THREAD_URL.format(course_id=course_id, thread_number=node_id) if course_id else ""

        net.add_node(
            node_id,
            label=make_label(node_id, attrs),
            title=make_tooltip(node_id, attrs, degree, url),
            color=color,
            shape=shape,
            size=max(10, 4 * degree),
            group=category or "Other",
        )

    for src, dst in G.edges():
        net.add_edge(src, dst)

    net.save_graph(output_path)

    if course_id:
        click_js = CLICK_JS_TEMPLATE.format(course_id=course_id)
        with open(output_path, "a") as f:
            f.write(click_js)

    print(f"Saved visualization to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Visualize Ed Discussion reference graph")
    parser.add_argument("--input", default="ed_data.json", help="Path to JSON graph data")
    parser.add_argument("--output", default="ed_graph.html", help="Output HTML file path")
    parser.add_argument("--min-degree", type=int, default=0, help="Only show nodes with at least this degree (0 = show all)")
    args = parser.parse_args()

    G = load_graph(args.input)

    if args.min_degree > 0:
        keep = [n for n in G.nodes() if G.degree(n) >= args.min_degree]
        G = G.subgraph(keep).copy()
        print(f"Filtered to nodes with degree >= {args.min_degree}")

    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    build_pyvis_network(G, args.output)


if __name__ == "__main__":
    main()
