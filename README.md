# Ed Graph

Visualize cross-references between Ed Discussion threads as an interactive graph.

Many Ed Discussion threads reference each other. This tool fetches all threads in a course, extracts `#NUMBER` references from posts and replies, and renders an interactive graph where edges point from the referencing thread to the referenced thread.

## Setup

Requires Python 3.10+ with [uv](https://docs.astral.sh/uv/) (recommended).

```bash
uv pip install edapi networkx pyvis
```

Set your Ed API token in a `.env` file:

```
ED_API_TOKEN=your_token_here
```

Get a token from https://edstem.org/us/settings/api-tokens.

## Usage

### 1. Fetch thread data

```bash
python fetch.py                      # interactive course selection
python fetch.py --course-id 12345    # skip the prompt
```

This produces two files:
- `ed_data.json` — graph data in networkx node-link format (includes `course_id` for Ed linking in visualization)
- `ed_data.graphml` — graph data for Gephi and other tools

### 2. Visualize

```bash
python visualize.py
python visualize.py --input ed_data.json --output ed_graph.html
python visualize.py --min-degree 1   # only show connected nodes
```

Open `ed_graph.html` in a browser.

### Interactive features

- **Hover** a node to see title, category, type, and connection count (with a link to open on Ed)
- **Click** a node to open the thread on Ed in a new tab
- **Drag** nodes to rearrange the layout
- **Filter** nodes by category using the dropdown menu
- **Select** a node to highlight its neighborhood (dim all unrelated nodes)
- **Keyboard** navigation: arrow keys to pan, +/- to zoom

### Visual encoding

| Attribute | Mapping |
|-----------|---------|
| Node color | Category (General, Question, Social, Lectures, Assignments, Problem Sets, etc.) |
| Node shape | Thread type (dot = question, box = note, star = announcement, triangle = poll) |
| Node size | Degree (number of connections) |
| Edge color | Inherited from source node |
| Edge direction | Arrow points from referencing thread → referenced thread |

## How it works

- `fetch.py` paginates through all threads via `list_threads()`, then fetches full content for each (including answers and nested comments)
- Extracts `#NUMBER` references from every `document` field (thread body, answers, and all nested comments)
- Filters references to only valid thread numbers within the course
- Builds a directed graph and saves as JSON + GraphML
- `visualize.py` loads the JSON, builds a pyvis network, and saves an interactive HTML file
