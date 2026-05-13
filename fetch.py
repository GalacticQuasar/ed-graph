import argparse
import json
import re
import time

import networkx as nx
from edapi import EdAPI

REFERENCE_PATTERN = re.compile(r"#(\d+)")
BATCH_SIZE = 100
REQUEST_DELAY = 0.2


def extract_references(document: str) -> list[int]:
    return [int(m) for m in REFERENCE_PATTERN.findall(document)]


def extract_all_references(thread: dict) -> set[int]:
    refs = set()

    refs.update(extract_references(thread.get("document", "")))

    for answer in thread.get("answers", []):
        refs.update(extract_references(answer.get("document", "")))
        for comment in answer.get("comments", []):
            refs.update(_refs_from_comments(comment))

    for comment in thread.get("comments", []):
        refs.update(_refs_from_comments(comment))

    return refs


def _refs_from_comments(comment: dict) -> set[int]:
    refs = set(extract_references(comment.get("document", "")))
    for reply in comment.get("comments", []):
        refs.update(_refs_from_comments(reply))
    return refs


def choose_course(ed: EdAPI, course_id: int | None = None) -> int:
    if course_id is not None:
        return course_id

    user_info = ed.get_user_info()
    user = user_info["user"]
    print(f"Hello {user['name']}!")

    courses = sorted(
        user_info["courses"], key=lambda e: e["course"]["created_at"], reverse=True
    )

    for i, entry in enumerate(courses):
        course = entry["course"]
        print(f"  {i}: {course['name']} ({course['code']})")

    choice = int(input("Choose a class: "))
    return courses[choice]["course"]["id"]


def fetch_all_threads(ed: EdAPI, course_id: int) -> list[dict]:
    all_threads = []
    offset = 0

    while True:
        threads = ed.list_threads(course_id, limit=BATCH_SIZE, offset=offset)
        if not threads:
            break
        all_threads.extend(threads)
        offset += len(threads)
        if len(threads) < BATCH_SIZE:
            break

    return all_threads


def fetch_thread_detail(
    ed: EdAPI, course_id: int, thread_number: int
) -> dict | None:
    try:
        return ed.get_course_thread(course_id, thread_number)
    except Exception as e:
        print(f"  Warning: failed to fetch thread #{thread_number}: {e}")
        return None


def build_graph(ed: EdAPI, course_id: int) -> nx.DiGraph:
    print("Fetching thread list...")
    thread_list = fetch_all_threads(ed, course_id)
    print(f"Found {len(thread_list)} threads")

    valid_numbers = {t["number"] for t in thread_list}
    number_to_id = {t["number"]: t["id"] for t in thread_list}

    G = nx.DiGraph()

    for t in thread_list:
        G.add_node(
            t["number"],
            id=t["id"],
            title=t["title"],
            category=t["category"],
            subcategory=t.get("subcategory", ""),
            subsubcategory=t.get("subsubcategory", ""),
            type=t["type"],
        )

    print("Fetching thread details and extracting references...")
    for i, t in enumerate(thread_list):
        number = t["number"]
        if (i + 1) % 20 == 0 or (i + 1) == len(thread_list):
            print(f"  Processing {i + 1}/{len(thread_list)}...")

        detail = fetch_thread_detail(ed, course_id, number)
        if detail is None:
            continue

        refs = extract_all_references(detail)
        course_refs = refs & valid_numbers
        course_refs.discard(number)

        for ref in course_refs:
            G.add_edge(number, ref)

        if REQUEST_DELAY > 0:
            time.sleep(REQUEST_DELAY)

    return G


def save_graph(G: nx.DiGraph, json_path: str, graphml_path: str):
    data = nx.node_link_data(G)

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved JSON to {json_path}")

    nx.write_graphml(G, graphml_path)
    print(f"Saved GraphML to {graphml_path}")


def main():
    parser = argparse.ArgumentParser(description="Fetch Ed Discussion threads and build reference graph")
    parser.add_argument("--course-id", type=int, help="Course ID (skips interactive prompt)")
    args = parser.parse_args()

    ed = EdAPI()
    ed.login()

    course_id = choose_course(ed, args.course_id)

    G = build_graph(ed, course_id)

    print(f"\nGraph summary:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    save_graph(G, "ed_data.json", "ed_data.graphml")


if __name__ == "__main__":
    main()