"""
Knowledge Graph Navigator – Path A (Semantic Meaning).

Queries the Neo4j etymological graph that is seeded by
Etymological_Seeder.  When Neo4j is unavailable the navigator
degrades gracefully and returns empty context maps so that the
rest of the pipeline can continue.
"""

import logging

logger = logging.getLogger(__name__)


class KnowledgeGraphNavigator:
    def __init__(self, uri: str, user: str, password: str):
        self._available = False
        try:
            from neo4j import GraphDatabase  # type: ignore
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self._available = True
        except Exception as exc:
            logger.warning("Neo4j unavailable – KnowledgeGraphNavigator degraded: %s", exc)

    def close(self):
        if self._available:
            self.driver.close()

    def get_semantic_context(self, terms: list) -> dict:
        """
        Path A: map tokens to the Etymological Graph.
        Returns the 'Core Concept Map' for the Reasoning Bridge.
        Falls back to an empty mapping when Neo4j is not reachable.
        """
        if not self._available:
            return {term: [] for term in terms}

        context_map = {}
        try:
            with self.driver.session() as session:
                for term in terms:
                    query = """
                    MATCH (n:EtymologicalRoot {name: $term})
                    OPTIONAL MATCH (n)-[:DEFINES|RELATED_TO]-(related)
                    RETURN n.name as root, collect(related.name) as relations
                    """
                    result = session.run(query, term=term.lower())
                    record = result.single()
                    if record:
                        context_map[record["root"]] = record["relations"]
        except Exception as exc:
            logger.warning("Error querying knowledge graph: %s", exc)

        return context_map
