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
- `ed_data.json` — graph data in networkx node-link format
- `ed_data.graphml` — graph data for Gephi and other tools

### 2. Visualize

```bash
python visualize.py
python visualize.py --input ed_data.json --output ed_graph.html
```

Open `ed_graph.html` in a browser. Nodes are colored by category and sized by degree. Hover for details; drag to rearrange.

## How it works

- Fetches all threads via paginated `list_threads()`, then retrieves full content for each thread (including answers and nested comments)
- Extracts `#NUMBER` references from every `document` field
- Filters references to only valid thread numbers within the course
- Builds a directed graph: edges go from the thread containing the reference to the referenced thread
