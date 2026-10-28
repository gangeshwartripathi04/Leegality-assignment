# Leegality Route Optimizer

A Python backend application for optimizing network routes based on connection latency.

The application represents servers as nodes and network connections as directed edges. Each edge has a latency cost. Given a source and destination server, the application calculates the route with the minimum total latency and records successful route queries for later analysis.

The project uses FastAPI, PostgreSQL, SQLAlchemy, and Docker Compose.

## Features

- Create and list network nodes.
- Create and list directed network connections.
- Validate node names, connections, and positive latency values.
- Calculate minimum-latency routes using Dijkstra's algorithm.
- Return the selected route and total latency.
- Return an error when no route exists.
- Store successful route queries in PostgreSQL.
- Filter route history by source, destination, date range, and result limit.
- Run the API and database using Docker Compose.

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| API framework | FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Algorithm | Dijkstra's shortest-path algorithm |
| Priority queue | Python heapq |
| Containerization | Docker and Docker Compose |
| Testing | pytest |

## Project Structure

```text
Leegality-assignment/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── services.py
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── data/
│   └── network.json
├── scripts/
│   └── load_network.py
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites

Install the following:

- Docker Desktop
- Git
- curl

Python is not required on the host to run the application through Docker.

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd Leegality-assignment
```

Replace `<repository-url>` with the repository URL.

### 2. Configure environment variables

Create a local `.env` file:

```bash
cat > .env <<'ENV'
DB_PASSWORD=local_dev_password_change_me
ENV
```

Use a strong password for non-local environments. Do not commit `.env` or production credentials to Git.

### 3. Build and start the application

```bash
docker compose up --build -d
```

Check container status:

```bash
docker compose ps
```

View API logs:

```bash
docker compose logs -f api
```

The API is available at:

- API base URL: http://localhost:8000
- Interactive API documentation: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

On startup, the current application initializes missing database tables automatically.

## Database Design

### Nodes

Stores the servers participating in the network.

| Column | Description |
|---|---|
| id | Primary key |
| name | Unique server name |

### Edges

Stores directed connections between servers.

| Column | Description |
|---|---|
| id | Primary key |
| source_id | Foreign key referencing the source node |
| destination_id | Foreign key referencing the destination node |
| latency | Positive connection latency |

An edge from ServerA to ServerB does not automatically create a reverse edge from ServerB to ServerA.

Duplicate directed edges are rejected.

### Route History

Stores successfully calculated routes.

| Column | Description |
|---|---|
| id | Primary key |
| source_id | Source node reference |
| destination_id | Destination node reference |
| total_latency | Minimum calculated latency |
| path | Ordered route represented as a JSON array |
| created_at | Query timestamp |

Each successful shortest-route request creates a separate history record.

## API Reference

### 1. Health Check

**GET `/health`**

Checks whether the API is responding.

```bash
curl http://localhost:8000/health
```

Example response:

```json
{
  "status": "ok"
}
```

### 2. Create a Node

**POST `/nodes`**

Request:

```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"name":"ServerA"}'
```

Example response:

```json
{
  "id": 1,
  "name": "ServerA"
}
```

Successful creation returns `201 Created`.

### 3. List Nodes

**GET `/nodes`**

```bash
curl http://localhost:8000/nodes
```

Returns the registered network nodes.

### 4. Create an Edge

**POST `/edges`**

Both endpoint nodes must exist before the connection can be created.

```bash
curl -X POST http://localhost:8000/edges \
  -H "Content-Type: application/json" \
  -d '{
    "source":"ServerA",
    "destination":"ServerB",
    "latency":12.5
  }'
```

Example response:

```json
{
  "id": 1,
  "source": "ServerA",
  "destination": "ServerB",
  "latency": 12.5
}
```

Latency must be greater than zero.

### 5. List Edges

**GET `/edges`**

```bash
curl http://localhost:8000/edges
```

Returns the registered network connections.

### 6. Find the Shortest Route

**POST `/routes/shortest`**

Request:

```bash
curl -X POST http://localhost:8000/routes/shortest \
  -H "Content-Type: application/json" \
  -d '{
    "source":"ServerA",
    "destination":"ServerD"
  }'
```

Example response:

```json
{
  "total_latency": 23.4,
  "path": ["ServerA", "ServerB", "ServerD"]
}
```

The endpoint returns the path with the lowest total latency.

If no path exists, the API returns `404 Not Found`.

### 7. Query Route History

**GET `/routes/history`**

Returns previously calculated routes.

```bash
curl "http://localhost:8000/routes/history?limit=10"
```

Supported query parameters:

| Parameter | Description |
|---|---|
| source | Filter by source server name |
| destination | Filter by destination server name |
| limit | Maximum number of results |
| date_from | Include records at or after this timestamp |
| date_to | Include records at or before this timestamp |

Example:

```bash
curl "http://localhost:8000/routes/history?source=ServerA&destination=ServerD&limit=10"
```

Date filters accept ISO 8601 timestamps. Timestamps without a timezone are interpreted as UTC by the current implementation.

## How the Shortest-Path Algorithm Works

The application uses Dijkstra's algorithm to find the route with minimum total latency.

### Algorithm steps

1. Load the network connections from PostgreSQL.
2. Represent the network as an adjacency list in Python.
3. Initialize the source distance to zero and all other distances to infinity.
4. Use a min-heap to process the node with the lowest known distance.
5. Update neighboring nodes when a shorter route is discovered.
6. Reconstruct the route using predecessor information.
7. Save the successful result in route history.

### Example network

```text
A --10--> B --1--> D
 \         ^
  \2       |3
   v       |
    C -----
    |
    +--10--> D
```

Possible routes from A to D:

- A -> B -> D = 11
- A -> C -> D = 12
- A -> C -> B -> D = 6

The algorithm returns:

```json
{
  "total_latency": 6.0,
  "path": ["A", "C", "B", "D"]
}
```

For a graph with V vertices and E edges, the typical time complexity of Dijkstra's algorithm with an adjacency list and binary heap is O((V + E) log V).

## Load the Sample Network

The repository includes a sample network dataset in `data/network.json` and a loader in `scripts/load_network.py`.

Start the application first, then execute:

```bash
python3 scripts/load_network.py
```

The loader sends HTTP requests through curl to create nodes and edges in the running API.

The loader is intended for an empty dataset. Running it again without clearing or resetting the database will encounter duplicate-node errors.

After loading the network, try:

```bash
curl -X POST http://localhost:8000/routes/shortest \
  -H "Content-Type: application/json" \
  -d '{
    "source":"Mumbai-Gateway",
    "destination":"Singapore-Gateway"
  }'
```

The result will contain the minimum latency and the selected path for the sample network.

## Testing

Run the test suite inside the API container:

```bash
docker compose exec api pytest -q
```

The shortest-path unit tests cover:

- Selecting the lowest-latency route.
- Handling unreachable destinations.
- Handling identical source and destination nodes.

The current tests primarily cover the algorithm. Additional API integration tests should verify HTTP status codes, database persistence, filtering, and invalid requests.

## Docker Commands

Start the application:

```bash
docker compose up --build -d
```

View running containers:

```bash
docker compose ps
```

Follow API logs:

```bash
docker compose logs -f api
```

Stop containers without deleting database data:

```bash
docker compose down
```

Stop containers and delete the database volume:

```bash
docker compose down -v
```

**Warning:** `docker compose down -v` deletes the persisted PostgreSQL data. Use it only when you intentionally want to reset the database.

## Current Limitations and Future Improvements

- Introduce Alembic migrations instead of relying on automatic table creation.
- Add comprehensive API integration tests with a dedicated test database.
- Add structured logging and consistent error responses.
- Add optional node and edge deletion endpoints.
- Improve graph loading efficiency for large networks.
- Add pagination and additional indexes if route history becomes large.
- Consider a cache only if profiling demonstrates a need.

## Design Decisions

- PostgreSQL provides relational integrity for nodes and edges.
- Python handles shortest-path calculation because the graph algorithm is independent of HTTP and database concerns.
- FastAPI separates request validation from business logic.
- Docker Compose makes local development reproducible without requiring a host-installed PostgreSQL server.
- Route history supports auditing and analyzing previously calculated routes.

## License

This project was developed as a Python backend exercise. Add an appropriate license if the project is intended for public distribution.
