from neo4j import GraphDatabase
import os
from typing import Optional
import logging
logger = logging.getLogger(__name__)
class Neo4jConnection:


    def __init__(self):
        self.driver: Optional[GraphDatabase.driver] = None
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password123")

    def connect(self):

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )

            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    logger.info("Successfully connected to Neo4j database")
                    return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j database: {str(e)}")
            return False
        return False

    def close(self):

        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def get_session(self):

        if not self.driver:
            if not self.connect():
                raise Exception("Failed to establish database connection")
        return self.driver.session()

    def execute_query(self, query: str, parameters: dict = None):

        with self.get_session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Query execution failed: {str(e)}")
                raise

    def execute_write_query(self, query: str, parameters: dict = None):

        with self.get_session() as session:
            try:
                def write_tx(tx):
                    result = tx.run(query, parameters or {})
                    return [record.data() for record in result]
                return session.write_transaction(write_tx)
            except Exception as e:
                logger.error(f"Write query execution failed: {str(e)}")
                raise

db_connection = Neo4jConnection()