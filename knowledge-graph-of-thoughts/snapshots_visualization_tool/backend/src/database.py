






import os
import re
import neo4j
driver = neo4j.GraphDatabase.driver("bolt://" + os.environ.get("NEO4J_INTERNAL_HOST") + ":7687")
def get_max_id() -> int:
    MATCH (n)
    RETURN n
    ORDER BY toInteger(n.id) DESC
    LIMIT 1
    with driver.session() as session:
        with session.begin_transaction() as tx:
            result = tx.run(get_max_id_query)
            if result.peek() is None:
                return 0
            max_id = result.single()["n"]["id"]

    return int(max_id) + 1
def create_constraint_dynamically(tx, error_message):
    Create the required unique constraint for import based on the error message.

    match = re.search(r"CREATE CONSTRAINT FOR \(n:(\w+)\) REQUIRE n\.(\w+) IS UNIQUE", error_message)
    if match:
        label = match.group(1)
        property_name = match.group(2)
        constraint_query = f"CREATE CONSTRAINT FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE;"
        tx.run(constraint_query)
    else:
        raise Exception("Failed to parse constraint creation query from error message.")
def import_graph_from_json(file_path: str, label: str) -> bool | int:
    This function is used to import a graph from a JSON file using the APOC plugin.
    After importing, it will add a label to all new nodes.
    :param file_path: The path to the JSON file.
    :type file_path: str
    :param label: The label that will be added to all new nodes.
    :type label: str
    :return: True if the graph was imported successfully, False otherwise.
    :rtype: bool
    with driver.session() as session:
        while True:
            try:
                with session.begin_transaction() as tx:

                    CALL apoc.import.json('file://{file_path}', {{importIdName: 'id'}})
                    YIELD nodes
                    RETURN nodes
                    result = tx.run(import_query)
                    record = result.single()
                    if record:

                        MATCH (node)
                        WHERE NONE(label IN labels(node) WHERE label STARTS WITH '___edge_')
                        SET node:___edge_{label}
                        tx.run(update_labels_query)
                        tx.commit()
                        return True
                    else:
                        print("No data returned from import query.")
                        tx.rollback()
                        return False
            except neo4j.exceptions.ClientError as e:
                error_message = str(e)
                if "Missing constraint required for import" in error_message:
                    print("Creating missing constraint.")
                    with session.begin_transaction() as tx:

                        create_constraint_dynamically(tx, error_message)
                        tx.commit()
                    with session.begin_transaction() as tx:

                        MATCH (node)
                        WHERE NONE(label IN labels(node) WHERE label STARTS WITH '___edge_')
                        DETACH DELETE node
                        tx.run(delete_query)
                        tx.commit()
                else:
                    print(f"Error importing graph from JSON: {e}")
                    return False

def dbms_reset_neo4j() -> bool:
    This function is used to reset the Neo4j database by deleting all nodes and relationships.
    with driver.session() as session:
        try:
            with session.begin_transaction() as tx:

                MATCH (n)
                DETACH DELETE n
                tx.run(delete_query)
                tx.commit()
            with session.begin_transaction() as tx:
                SHOW ALL CONSTRAINTS
                YIELD name
                RETURN name
                result = tx.run(schema_delete_query)
                for name in result:
                    DROP CONSTRAINT {name["name"]}
                    tx.run(delete_schema_query)
                tx.commit()

            return True
        except neo4j.exceptions.ClientError as e:
            print(f"Error resetting Neo4j database: {e}")
            return False