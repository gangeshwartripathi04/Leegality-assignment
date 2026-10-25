
# app/services.py

import heapq


def find_shortest_path(graph, source, destination):
    """
    graph = {
        "ServerA": [("ServerB", 12.5), ("ServerC", 5.0)]
    }
    Returns (total_latency, path), or None if unreachable.
    """
    distances = {source: 0.0}
    previous = {}
    queue = [(0.0, source)]

    while queue:
        current_distance, current = heapq.heappop(queue)

        if current_distance > distances.get(current, float("inf")):
            continue

        if current == destination:
            path = []
            node = destination

            while node is not None:
                path.append(node)
                node = previous.get(node)

            return current_distance, list(reversed(path))

        for neighbor, latency in graph.get(current, []):
            new_distance = current_distance + latency

            if new_distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_distance
                previous[neighbor] = current
                heapq.heappush(queue, (new_distance, neighbor))

    return None
