import logging
import time
import asyncio
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from ..database.connection import db_connection, Neo4jConnection
logger = logging.getLogger(__name__)
class DuplicateCleanupService:

    def __init__(self, db: Neo4jConnection = None):
        self.db = db or db_connection

    def detect_duplicate_relationships(self) -> Dict[Tuple[str, str, str], List[Dict]]:
        try:
            query = """
            MATCH (start)-[r]->(end)
            RETURN r._internal_uid as rel_uid, id(r) as rel_neo4j_id, type(r) as rel_type,
                   start._internal_uid as start_uid, end._internal_uid as end_uid,
                   id(start) as start_neo4j_id, id(end) as end_neo4j_id,
                   properties(r) as properties
            """
            with self.db.get_session() as session:
                result = session.run(query)
                relationships = []
                for record in result:

                    rel_id = record['rel_uid'] or str(record['rel_neo4j_id'])
                    start_id = record['start_uid'] or str(record['start_neo4j_id'])
                    end_id = record['end_uid'] or str(record['end_neo4j_id'])
                    relationships.append({
                        'id': rel_id,
                        'type': record['rel_type'],
                        'start_node_id': start_id,
                        'end_node_id': end_id,
                        'properties': record['properties'] or {}
                    })

            relationship_groups = defaultdict(list)
            for rel in relationships:
                key = (rel['start_node_id'], rel['end_node_id'], rel['type'])
                relationship_groups[key].append(rel)

            duplicate_groups = {k: v for k, v in relationship_groups.items() if len(v) > 1}
            return duplicate_groups
        except Exception as e:
            logger.error(f"Error while detecting duplicate relationships: {str(e)}")
            return {}

    def cleanup_duplicate_relationships(self, duplicate_groups: Dict[Tuple[str, str, str], List[Dict]],
                                      timeout_seconds: int = 30) -> Tuple[int, int]:
        start_time = time.time()
        deleted_count = 0
        failed_count = 0

        try:
            for (start_id, end_id, rel_type), group in duplicate_groups.items():

                if time.time() - start_time > timeout_seconds:
                    logger.warning(f"Duplicate relationship cleanup timed out after processing {deleted_count} relationships")
                    break


                to_keep = group[0]
                to_delete = group[1:]

                logger.info(f"Cleaning relationship group: {start_id} -> {end_id} ({rel_type}), "
                           f"keeping {to_keep['id']}, deleting {len(to_delete)} duplicates")

                for rel in to_delete:
                    try:
                        success = self._delete_relationship_by_id(rel['id'])
                        if success:
                            deleted_count += 1
                            logger.debug(f"Deleted duplicate relationship: {rel['id']}")
                        else:
                            failed_count += 1
                            logger.warning(f"Failed to delete relationship: {rel['id']}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Exception while deleting relationship {rel['id']}: {str(e)}")

            logger.info(f"Duplicate relationship cleanup finished: {deleted_count} deleted, {failed_count} failed")
            return deleted_count, failed_count

        except Exception as e:
            logger.error(f"Error while cleaning duplicate relationships: {str(e)}")
            return deleted_count, failed_count

    def _delete_relationship_by_id(self, rel_id: str) -> bool:

        try:

            if '-' in rel_id and len(rel_id) == 36:
                query = """
                MATCH ()-[r]-()
                WHERE r._internal_uid = $rel_uid
                DELETE r
                RETURN count(r) as deleted_count
                """
                result = self.db.execute_write_query(query, {"rel_uid": rel_id})
            else:
                neo4j_rel_id = int(rel_id)
                query = """
                MATCH ()-[r]-()
                WHERE id(r) = $neo4j_rel_id
                DELETE r
                RETURN count(r) as deleted_count
                """
                result = self.db.execute_write_query(query, {"neo4j_rel_id": neo4j_rel_id})
            return result and result[0]["deleted_count"] > 0
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid relationship ID format: {rel_id}, error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error while deleting relationship: {str(e)}")
            return False

    def auto_cleanup_after_kgot(self, custom_config: Optional[Dict] = None) -> Optional[Dict]:
        start_time = time.time()
        try:

            if not cleanup_config.is_auto_cleanup_enabled():
                logger.info("Auto-cleanup is disabled; skipping")
                return None

            params = cleanup_config.get_cleanup_parameters()
            if custom_config:
                params.update(custom_config)
            log_config = cleanup_config.get_logging_config()
            if log_config["log_details"]:
                logger.info("Running post-KGOT duplicate relationship detection...")

            duplicate_groups = self.detect_duplicate_relationships()
            if not duplicate_groups:
                if log_config["log_details"]:
                    logger.info("No duplicate relationships detected; skipping cleanup")
                return None
            total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
            if total_duplicates < params["min_duplicates_threshold"]:
                if log_config["log_details"]:
                    logger.info(f"Duplicate count ({total_duplicates}) is below the threshold ({params['min_duplicates_threshold']}); skipping cleanup")
                return None
            if log_config["log_details"]:
                logger.info(f"Detected {len(duplicate_groups)} duplicate relationship groups, {total_duplicates} duplicates in total")

            deleted_count, failed_count = 0, 0
            for retry in range(params.get("max_retries", 1) + 1):
                try:
                    deleted_count, failed_count = self.cleanup_duplicate_relationships(
                        duplicate_groups,
                        timeout_seconds=params["timeout_seconds"]
                    )
                    break
                except Exception as e:
                    if retry < params.get("max_retries", 1):
                        logger.warning(f"Cleanup retry {retry + 1}/{params.get('max_retries', 1)}: {str(e)}")
                        time.sleep(1)
                    else:
                        raise e

            remaining_duplicates = self.detect_duplicate_relationships()
            cleanup_result = {
                'detected_duplicate_groups': len(duplicate_groups),
                'total_duplicates_found': total_duplicates,
                'successfully_deleted': deleted_count,
                'failed_to_delete': failed_count,
                'remaining_duplicates': len(remaining_duplicates),
                'cleanup_success': len(remaining_duplicates) == 0,
                'execution_time': time.time() - start_time
            }
            if log_config["log_statistics"]:
                if cleanup_result['cleanup_success']:
                    logger.info(f"Automatic duplicate cleanup finished: deleted {deleted_count} duplicate relationships")
                else:
                    logger.warning(f"Auto-cleanup finished but {len(remaining_duplicates)} duplicate groups remain")
            return cleanup_result
        except Exception as e:
            error_msg = f"Error during automatic duplicate relationship cleanup: {str(e)}"
            logger.error(error_msg)
            if not cleanup_config.should_continue_on_error():
                raise Exception(error_msg)
            return {
                'error': str(e),
                'cleanup_success': False
            }

    def get_relationship_statistics(self) -> Dict:
        try:
            query = """
            MATCH ()-[r]->()
            RETURN count(r) as total_relationships,
                   count(DISTINCT type(r)) as unique_types,
                   collect(DISTINCT type(r)) as relationship_types
            """
            with self.db.get_session() as session:
                result = session.run(query)
                record = result.single()

                if record:
                    return {
                        'total_relationships': record['total_relationships'],
                        'unique_types': record['unique_types'],
                        'relationship_types': record['relationship_types']
                    }
                else:
                    return {
                        'total_relationships': 0,
                        'unique_types': 0,
                        'relationship_types': []
                    }

        except Exception as e:
            logger.error(f"Error while fetching relationship statistics: {str(e)}")
            return {
                'error': str(e),
                'total_relationships': 0,
                'unique_types': 0,
                'relationship_types': []
            }