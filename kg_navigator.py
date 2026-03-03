import logging
from neo4j import GraphDatabase


class KnowledgeGraphNavigator:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            logging.error("Failed to initialize Neo4j driver: %s", e)
            raise

    def close(self):
        self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_semantic_context(self, terms: list):
        """
        Path A: Map tokens to the Etymological Graph.
        Returns the 'Core Concept Map' for the Reasoning Bridge.
        """
        context_map = {}
        with self.driver.session() as session:
            for term in terms:
                # Optimized Cypher using the execute_read pattern for safety
                query = """
                MATCH (n:EtymologicalRoot {name: $term})
                OPTIONAL MATCH (n)-[:DEFINES|RELATED_TO]-(related)
                RETURN n.name as root, collect(related.name) as relations
                """
                result = session.run(query, term=term.lower())
                record = result.single()
                if record:
                    context_map[record["root"]] = record["relations"]
        return context_map
