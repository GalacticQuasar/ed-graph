import argparse
import json

import networkx as nx
from pyvis.network import Network

CATEGORY_COLORS = {
    "General": "#2196F3",
    "Question": "#4CAF50",
    "Social": "#9C27B0",
    "Lectures": "#FF9800",
    "Assignments": "#F44336",
    "Problem Sets": "#00BCD4",
}

DEFAULT_COLOR = "#9E9E9E"

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


def load_graph(json_path: str) -> nx.DiGraph:
    with open(json_path) as f:
        data = json.load(f)
    return nx.node_link_graph(data, directed=True)


def make_label(node_id: int, attrs: dict) -> str:
    title = attrs.get("title", "")
    max_len = 40
    if len(title) > max_len:
        title = title[: max_len - 1] + "..."
    return f"#{node_id}\n{title}"


ED_THREAD_URL = "https://edstem.org/us/courses/{course_id}/discussion/{thread_number}"

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
        select_menu=False,
        filter_menu=False,
        bgcolor="#222222",
        font_color="white"
    )

    net.set_options(
        """
    {
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -3000,
                "centralGravity": 0.3,
                "springLength": 100,
                "springConstant": 0.04
            }
        },
        "edges": {
            "arrows": {
                "to": { "enabled": true, "scaleFactor": 0.5 }
            },
            "smooth": {
                "type": "continuous"
            }
        },
        "nodes": {
            "font": {
                "size": 12
            }
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
        url = ED_THREAD_URL.format(course_id=course_id, thread_number=node_id) if course_id else ""

        net.add_node(
            node_id,
            label=make_label(node_id, attrs),
            title=f"#{node_id}: {attrs.get('title', '')}\nCategory: {category}\nType: {attrs.get('type', '')}",
            color=color,
            size=max(10, 3 * G.degree(node_id)),
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
