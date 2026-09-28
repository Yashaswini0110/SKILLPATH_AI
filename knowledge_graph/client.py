"""Neo4j driver wrapper."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from neo4j import Driver, GraphDatabase, Session


class GraphClient:
    def __init__(self, uri: str, user: str, password: str) -> None:
        self.uri = uri
        self._driver: Driver = GraphDatabase.driver(
            uri, auth=(user, password), connection_timeout=3
        )

    def verify(self) -> bool:
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def run(self, query: str, **params: Any) -> list[dict[str, Any]]:
        with self.session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]

    def close(self) -> None:
        self._driver.close()
