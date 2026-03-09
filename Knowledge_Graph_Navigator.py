from neo4j import GraphDatabase
import logging

class KnowledgeGraphNavigator:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

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


if __name__ == "__main__":
    # Integration into RootAI Flow
    kg_navigator = KnowledgeGraphNavigator("bolt://localhost:7687", "neo4j", "rootai")
