"""Resolvers that translate user-facing node/relationship identifiers.

Nodes may be addressed by an internal UUID (`_internal_uid`), a custom `id`
property, or a raw Neo4j element id; these classes normalize the three forms.
"""

from typing import Dict, Any, Optional
import re
import uuid
import logging

logger = logging.getLogger(__name__)


class NodeIDResolver:
    def __init__(self, db_connection):
        self.db = db_connection
    @staticmethod
    def generate_internal_uid() -> str:

        return str(uuid.uuid4())
    @staticmethod
    def is_uuid_format(identifier: str) -> bool:

        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(identifier))
    @staticmethod
    def is_neo4j_id_format(identifier: str) -> bool:

        try:
            int(identifier)
            return True
        except (ValueError, TypeError):
            return False
    def resolve_to_neo4j_id(self, node_identifier: str) -> Optional[int]:
        with self.db.get_session() as session:

            if self.is_uuid_format(node_identifier):
                query = "MATCH (n) WHERE n._internal_uid = $uid RETURN id(n) as neo4j_id"
                result = session.run(query, {"uid": node_identifier})
                record = result.single()
                if record:
                    return record["neo4j_id"]

            query = "MATCH (n) WHERE n.id = $custom_id RETURN id(n) as neo4j_id"
            result = session.run(query, {"custom_id": node_identifier})
            record = result.single()
            if record:
                return record["neo4j_id"]

            if self.is_neo4j_id_format(node_identifier):
                try:
                    neo4j_id = int(node_identifier)

                    query = "MATCH (n) WHERE id(n) = $neo4j_id RETURN id(n) as neo4j_id"
                    result = session.run(query, {"neo4j_id": neo4j_id})
                    record = result.single()
                    if record:
                        return neo4j_id
                except (ValueError, TypeError):
                    pass
            return None
    def resolve_to_internal_uid(self, node_identifier: str) -> Optional[str]:
        with self.db.get_session() as session:

            if self.is_uuid_format(node_identifier):
                query = "MATCH (n) WHERE n._internal_uid = $uid RETURN n._internal_uid as uid"
                result = session.run(query, {"uid": node_identifier})
                record = result.single()
                if record:
                    return record["uid"]

            query = "MATCH (n) WHERE n.id = $custom_id RETURN n._internal_uid as uid"
            result = session.run(query, {"custom_id": node_identifier})
            record = result.single()
            if record and record["uid"]:
                return record["uid"]

            if self.is_neo4j_id_format(node_identifier):
                try:
                    neo4j_id = int(node_identifier)
                    query = "MATCH (n) WHERE id(n) = $neo4j_id RETURN n._internal_uid as uid"
                    result = session.run(query, {"neo4j_id": neo4j_id})
                    record = result.single()
                    if record and record["uid"]:
                        return record["uid"]
                except (ValueError, TypeError):
                    pass
            return None
    def get_node_identifiers(self, node_identifier: str) -> Optional[Dict[str, Any]]:
        with self.db.get_session() as session:

            neo4j_id = self.resolve_to_neo4j_id(node_identifier)
            if neo4j_id is None:
                return None

            query = """
            MATCH (n) WHERE id(n) = $neo4j_id
            RETURN id(n) as neo4j_id, n._internal_uid as internal_uid, n.id as custom_id
            """
            result = session.run(query, {"neo4j_id": neo4j_id})
            record = result.single()
            if record:
                return {
                    "neo4j_id": record["neo4j_id"],
                    "internal_uid": record["internal_uid"],
                    "custom_id": record["custom_id"]
                }
            return None
    def ensure_internal_uid(self, neo4j_id: int) -> str:
        with self.db.get_session() as session:

            query = "MATCH (n) WHERE id(n) = $neo4j_id RETURN n._internal_uid as uid"
            result = session.run(query, {"neo4j_id": neo4j_id})
            record = result.single()
            if record and record["uid"]:
                return record["uid"]

            new_uid = self.generate_internal_uid()
            query = """
            MATCH (n) WHERE id(n) = $neo4j_id
            SET n._internal_uid = $uid
            RETURN n._internal_uid as uid
            """
            result = session.run(query, {"neo4j_id": neo4j_id, "uid": new_uid})
            record = result.single()
            if record:
                logger.info(f"Created internal UID {new_uid} for node {neo4j_id}")
                return record["uid"]
            raise Exception(f"Failed to create internal UID for node {neo4j_id}")
class RelationshipIDResolver:
    def __init__(self, db_connection):
        self.db = db_connection
    @staticmethod
    def is_neo4j_id_format(identifier: str) -> bool:

        try:
            int(identifier)
            return True
        except (ValueError, TypeError):
            return False
    def resolve_to_neo4j_id(self, rel_identifier: str) -> Optional[int]:
        if self.is_neo4j_id_format(rel_identifier):
            try:
                neo4j_id = int(rel_identifier)

                with self.db.get_session() as session:
                    query = "MATCH ()-[r]-() WHERE id(r) = $neo4j_id RETURN id(r) as neo4j_id"
                    result = session.run(query, {"neo4j_id": neo4j_id})
                    record = result.single()
                    if record:
                        return neo4j_id
            except (ValueError, TypeError):
                pass
        return None
