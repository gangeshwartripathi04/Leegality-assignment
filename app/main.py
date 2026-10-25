from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from .database import Base, engine, get_db
from .models import Edge, Node, RouteHistory
from .schemas import (
    EdgeCreate,
    EdgeResponse,
    NodeCreate,
    NodeResponse,
    RouteHistoryResponse,
    RouteRequest,
    RouteResponse,
)
from .services import find_shortest_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Leegality Route Optimizer",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/nodes", response_model=NodeResponse, status_code=201)
def create_node(payload: NodeCreate, db: Session = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(400, "Name cannot be empty")

    if db.scalar(select(Node).where(Node.name == name)):
        raise HTTPException(400, "Node already exists")

    node = Node(name=name)
    db.add(node)

    try:
        db.commit()
        db.refresh(node)
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Node already exists")

    return node


@app.get("/nodes", response_model=list[NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    return list(db.scalars(select(Node).order_by(Node.id)).all())


@app.post("/edges", response_model=EdgeResponse, status_code=201)
def create_edge(payload: EdgeCreate, db: Session = Depends(get_db)):
    source_name = payload.source.strip()
    destination_name = payload.destination.strip()

    if not source_name or not destination_name:
        raise HTTPException(400, "Source and destination are required")

    source = db.scalar(select(Node).where(Node.name == source_name))
    destination = db.scalar(select(Node).where(Node.name == destination_name))

    if not source or not destination:
        raise HTTPException(400, "Source or destination node not found")

    if source.id == destination.id:
        raise HTTPException(400, "Self-edges are not supported")

    edge = Edge(
        source_id=source.id,
        destination_id=destination.id,
        latency=payload.latency,
    )
    db.add(edge)

    try:
        db.commit()
        db.refresh(edge)
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Invalid or duplicate edge")

    return EdgeResponse(
        id=edge.id,
        source=source.name,
        destination=destination.name,
        latency=edge.latency,
    )


@app.get("/edges", response_model=list[EdgeResponse])
def list_edges(db: Session = Depends(get_db)):
    source_node = aliased(Node)
    destination_node = aliased(Node)

    rows = db.execute(
        select(Edge, source_node.name, destination_node.name)
        .join(source_node, Edge.source_id == source_node.id)
        .join(destination_node, Edge.destination_id == destination_node.id)
        .order_by(Edge.id)
    ).all()

    return [
        EdgeResponse(
            id=edge.id,
            source=source,
            destination=destination,
            latency=edge.latency,
        )
        for edge, source, destination in rows
    ]


@app.post("/routes/shortest", response_model=RouteResponse)
def shortest_route(payload: RouteRequest, db: Session = Depends(get_db)):
    source_name = payload.source.strip()
    destination_name = payload.destination.strip()

    source = db.scalar(select(Node).where(Node.name == source_name))
    destination = db.scalar(select(Node).where(Node.name == destination_name))

    if not source or not destination:
        raise HTTPException(
            status_code=400,
            detail="Invalid or non-existent nodes",
        )

    source_node = aliased(Node)
    destination_node = aliased(Node)

    rows = db.execute(
        select(
            source_node.name,
            destination_node.name,
            Edge.latency,
        )
        .join(source_node, Edge.source_id == source_node.id)
        .join(destination_node, Edge.destination_id == destination_node.id)
    ).all()

    graph = {node.name: [] for node in db.scalars(select(Node)).all()}

    for start, end, latency in rows:
        graph[start].append((end, latency))

    result = find_shortest_path(graph, source_name, destination_name)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No path exists between {source_name} and {destination_name}",
        )

    total_latency, path = result

    history = RouteHistory(
        source_id=source.id,
        destination_id=destination.id,
        total_latency=total_latency,
        path=path,
    )
    db.add(history)
    db.commit()

    return RouteResponse(total_latency=total_latency, path=path)


@app.get("/routes/history", response_model=list[RouteHistoryResponse])
def route_history(
    source: str | None = None,
    destination: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
):
    source_node = aliased(Node)
    destination_node = aliased(Node)

    query = (
        select(
            RouteHistory,
            source_node.name,
            destination_node.name,
        )
        .join(source_node, RouteHistory.source_id == source_node.id)
        .join(destination_node, RouteHistory.destination_id == destination_node.id)
    )

    if source:
        query = query.where(source_node.name == source.strip())

    if destination:
        query = query.where(destination_node.name == destination.strip())

    if date_from:
        if date_from.tzinfo is None:
            date_from = date_from.replace(tzinfo=timezone.utc)
        query = query.where(RouteHistory.created_at >= date_from)

    if date_to:
        if date_to.tzinfo is None:
            date_to = date_to.replace(tzinfo=timezone.utc)
        query = query.where(RouteHistory.created_at <= date_to)

    rows = db.execute(
        query.order_by(RouteHistory.created_at.desc()).limit(limit)
    ).all()

    return [
        RouteHistoryResponse(
            id=record.id,
            source=source_name,
            destination=destination_name,
            total_latency=record.total_latency,
            path=record.path,
            created_at=record.created_at,
        )
        for record, source_name, destination_name in rows
    ]
