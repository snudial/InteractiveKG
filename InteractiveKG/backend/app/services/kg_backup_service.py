import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..database.connection import db_connection
from .data_transformation_service import data_transformer
logger = logging.getLogger(__name__)
@dataclass
class BackupMetadata:

    backup_id: str
    timestamp: datetime
    node_count: int
    relationship_count: int
    description: str
@dataclass
class KGBackup:

    metadata: BackupMetadata
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
class KGBackupService:


    def __init__(self):
        self.db = db_connection
        self._current_backup: Optional[KGBackup] = None

    async def create_backup(self, description: str = "automatic backup") -> str:
        try:
            backup_id = f"backup_{int(time.time())}"
            logger.info(f"Creating knowledge graph backup: {backup_id}")

            nodes_query = """
            MATCH (n)
            RETURN n.id as id, labels(n) as labels, properties(n) as properties
            """
            nodes = self.db.execute_query(nodes_query)

            relationships_query = """
            MATCH (a)-[r]->(b)
            RETURN a.id as source, b.id as target, type(r) as relationship,
                   properties(r) as properties, id(r) as rel_id
            """
            relationships = self.db.execute_query(relationships_query)


            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=datetime.now(),
                node_count=len(nodes),
                relationship_count=len(relationships),
                description=description
            )


            backup = KGBackup(
                metadata=metadata,
                nodes=nodes,
                relationships=relationships
            )


            self._current_backup = backup

            logger.info(f"Backup created: {backup_id}, nodes: {len(nodes)}, relationships: {len(relationships)}")
            return backup_id

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise Exception(f"Backup creation failed: {e}")

    async def clear_database(self) -> bool:
        try:
            logger.info("Clearing the knowledge graph database")


            clear_query = "MATCH (n) DETACH DELETE n"
            self.db.execute_query(clear_query)


            count_query = "MATCH (n) RETURN count(n) as count"
            result = self.db.execute_query(count_query)
            node_count = result[0]['count'] if result else 0

            if node_count == 0:
                logger.info("Database cleared")
                return True
            else:
                logger.error(f"Database clear failed; {node_count} nodes remain")
                return False

        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False

    async def insert_new_data(self, nodes: List[Dict[str, Any]],
                            relationships: List[Dict[str, Any]]) -> bool:
        try:
            logger.info(f"Inserting new data: {len(nodes)} nodes, {len(relationships)} relationships")


            for node in nodes:
                try:
                    node_id = node.get('id')
                    properties = node.get('properties', {})
                    labels = node.get('labels', ['Entity'])

                    if not node_id:
                        node_id = f"node_{hash(str(properties.get('name', 'unknown')))}"

                    properties['id'] = node_id

                    label_str = ':'.join(labels)

                    prop_items = []
                    for key, value in properties.items():
                        if isinstance(value, str):
                            prop_items.append(f"{key}: '{value}'")
                        else:
                            prop_items.append(f"{key}: {value}")
                    prop_str = ', '.join(prop_items) if prop_items else ''

                    if prop_str:
                        create_query = f"CREATE (n:{label_str} {{{prop_str}}})"
                    else:
                        create_query = f"CREATE (n:{label_str} {{id: '{node_id}'}})"
                    self.db.execute_query(create_query)

                except Exception as e:
                    logger.error(f"Failed to insert node {node.get('id', 'unknown')}: {e}")
                    continue


            for rel in relationships:
                try:

                    source_id = rel.get('start_node_id') or rel.get('source')
                    target_id = rel.get('end_node_id') or rel.get('target')
                    rel_type = rel.get('type') or rel.get('relationship', 'RELATED')
                    properties = rel.get('properties', {})

                    if not source_id or not target_id:
                        logger.warning(f"Skipping invalid relationship: source={source_id}, target={target_id}")
                        continue


                    rel_id = rel.get('id')
                    if not rel_id:
                        rel_id = data_transformer.generate_relationship_id(rel)

                    properties['id'] = rel_id

                    prop_items = []
                    for key, value in properties.items():
                        if isinstance(value, str):
                            prop_items.append(f"{key}: '{value}'")
                        else:
                            prop_items.append(f"{key}: {value}")
                    prop_str = ', '.join(prop_items) if prop_items else f"id: '{rel_id}'"

                    create_query = f"""
                    MATCH (a {{id: '{source_id}'}}), (b {{id: '{target_id}'}})
                    CREATE (a)-[r:{rel_type} {{{prop_str}}}]->(b)
                    """
                    self.db.execute_query(create_query)

                except Exception as e:
                    logger.error(f"Failed to insert relationship {rel.get('source', 'unknown')}->{rel.get('target', 'unknown')}: {e}")
                    continue

            logger.info("New data inserted")
            return True

        except Exception as e:
            logger.error(f"Failed to insert new data: {e}")
            return False

    async def restore_from_backup(self, backup_id: Optional[str] = None) -> bool:

        try:
            if not self._current_backup:
                logger.error("No backup data available")
                return False

            backup = self._current_backup
            logger.info(f"Restoring data from backup: {backup.metadata.backup_id}")


            if not await self.clear_database():
                logger.error("Failed to clear database; cannot restore")
                return False


            success = await self.insert_new_data(backup.nodes, backup.relationships)

            if success:
                logger.info(f"Data restored: {len(backup.nodes)} nodes, {len(backup.relationships)} relationships")
            else:
                logger.error("Data restore failed")

            return success

        except Exception as e:
            logger.error(f"Failed to restore data: {e}")
            return False

    async def safe_update_with_new_data(self, new_nodes: List[Dict[str, Any]],
                                      new_relationships: List[Dict[str, Any]],
                                      description: str = "intelligent-solving update") -> Dict[str, Any]:
        try:
            logger.info("Starting a safe knowledge graph update")

            validated_data = data_transformer.validate_and_fix_data({
                'nodes': new_nodes,
                'relationships': new_relationships
            })
            new_nodes = validated_data['nodes']
            new_relationships = validated_data['relationships']

            backup_id = await self.create_backup(description)


            if not await self.clear_database():
                raise Exception("Failed to clear database")


            if not await self.insert_new_data(new_nodes, new_relationships):

                logger.error("Failed to insert new data; attempting backup restore")
                await self.restore_from_backup(backup_id)
                raise Exception("Failed to insert new data; original data restored")

            result = {
                'success': True,
                'backup_id': backup_id,
                'nodes_inserted': len(new_nodes),
                'relationships_inserted': len(new_relationships),
                'message': 'Knowledge graph safely updated'
            }

            logger.info(f"Safe update finished: {result}")
            return result

        except Exception as e:
            logger.error(f"Safe update failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Knowledge graph safe update failed'
            }

    def get_current_backup_info(self) -> Optional[Dict[str, Any]]:

        if not self._current_backup:
            return None

        metadata = self._current_backup.metadata
        return {
            'backup_id': metadata.backup_id,
            'timestamp': metadata.timestamp.isoformat(),
            'node_count': metadata.node_count,
            'relationship_count': metadata.relationship_count,
            'description': metadata.description
        }

kg_backup_service = KGBackupService()