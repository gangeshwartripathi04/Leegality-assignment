from app.services import find_shortest_path


def test_finds_lowest_latency_path():
    graph = {
        "A": [("B", 10), ("C", 2)],
        "B": [("D", 1)],
        "C": [("B", 3), ("D", 10)],
        "D": [],
    }

    result = find_shortest_path(graph, "A", "D")

    assert result == (6, ["A", "C", "B", "D"])


def test_returns_none_when_no_path_exists():
    graph = {
        "A": [("B", 2)],
        "B": [],
        "C": [],
    }

    assert find_shortest_path(graph, "A", "C") is None


def test_source_equals_destination():
    graph = {"A": [("B", 5)], "B": []}

    assert find_shortest_path(graph, "A", "A") == (0.0, ["A"])
