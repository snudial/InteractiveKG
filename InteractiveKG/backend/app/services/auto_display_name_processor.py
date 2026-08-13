import logging
import asyncio
from typing import Dict, List, Any, Set
from datetime import datetime
from ..database.connection import db_connection
from .node_display_name_service import node_display_name_service
logger = logging.getLogger(__name__)
class AutoDisplayNameProcessor:

    def __init__(self):
        self._processing_lock = asyncio.Lock()
        self._initialization_complete = False
        self._processed_nodes: Set[str] = set()

    async def ensure_display_names(self, force_check: bool = False) -> Dict[str, Any]:
        async with self._processing_lock:
            try:
                logger.info("Starting automatic detection and generation of display_name attributes...")

                missing_nodes = await self._detect_missing_display_names()
                if not missing_nodes:
                    logger.info("All nodes already have display_name attribute")
                    self._initialization_complete = True
                    return {
                        "action": "no_action_needed",
                        "total_nodes": await self._count_total_nodes(),
                        "missing_count": 0,
                        "processed_count": 0
                    }
                logger.info(f"Found {len(missing_nodes)} nodes missing display_name attribute")

                display_names = await node_display_name_service.generate_display_names_batch(missing_nodes)

                updated_count = await self._update_display_names_in_db(display_names)

                for node in missing_nodes:
                    self._processed_nodes.add(node['id'])
                self._initialization_complete = True
                logger.info(f"Event-driven processing completed: Updated display_name for {updated_count} nodes")
                return {
                    "action": "processed",
                    "total_nodes": await self._count_total_nodes(),
                    "missing_count": len(missing_nodes),
                    "processed_count": updated_count,
                    "success_rate": f"{(updated_count / len(missing_nodes) * 100):.1f}%" if missing_nodes else "0%"
                }
            except Exception as e:
                logger.error(f"Event-driven display_name processing failed: {e}")
                return {
                    "action": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    async def process_data_change_event(self, node_ids: List[str] = None) -> Dict[str, Any]:
        async with self._processing_lock:
            try:
                logger.info(f"Handling data-change event, scope: {'specified nodes' if node_ids else 'all nodes'}")

                if node_ids:

                    missing_nodes = await self._detect_missing_display_names_for_nodes(node_ids)
                else:

                    missing_nodes = await self._detect_missing_display_names()

                new_missing_nodes = [
                    node for node in missing_nodes
                    if node['id'] not in self._processed_nodes
                ]
                if not new_missing_nodes:
                    logger.info("No new nodes to process")
                    return {
                        "action": "no_new_nodes",
                        "total_checked": len(missing_nodes),
                        "already_processed": len(missing_nodes) - len(new_missing_nodes),
                        "new_processed": 0
                    }
                logger.info(f"Found {len(new_missing_nodes)} new nodes needing a display_name")

                display_names = await self._generate_display_names_with_priority(new_missing_nodes)

                updated_count = await self._update_display_names_in_db(display_names)

                for node in new_missing_nodes:
                    self._processed_nodes.add(node['id'])
                logger.info(f"Data-change event handled: updated display_name on {updated_count} nodes")
                return {
                    "action": "processed",
                    "total_checked": len(missing_nodes),
                    "already_processed": len(missing_nodes) - len(new_missing_nodes),
                    "new_processed": updated_count,
                    "generated_names": len(display_names)
                }
            except Exception as e:
                logger.error(f"Failed to handle data-change event: {e}")
                return {
                    "action": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

    async def process_new_nodes(self, node_ids: List[str]) -> Dict[str, Any]:
        if not node_ids:
            return {"action": "no_nodes", "processed_count": 0}

        try:
            logger.info(f"Generating display_name for {len(node_ids)} new nodes...")


            nodes_data = await self._get_nodes_by_ids(node_ids)


            missing_nodes = [
                node for node in nodes_data
                if not node.get('properties', {}).get('display_name')
            ]

            if not missing_nodes:
                return {"action": "no_missing", "processed_count": 0}

            display_names = await self._generate_display_names_with_priority(missing_nodes)

            updated_count = await self._update_display_names_in_db(display_names)

            logger.info(f"display_name generation for new nodes finished: {updated_count} nodes")

            return {
                "action": "processed",
                "requested_count": len(node_ids),
                "missing_count": len(missing_nodes),
                "processed_count": updated_count
            }

        except Exception as e:
            logger.error(f"Failed to process display_name for new nodes: {e}")
            return {"action": "error", "error": str(e)}

    def clear_processed_cache(self):

        self._processed_nodes.clear()
        logger.info("Processing cache cleared")

    async def _detect_missing_display_names(self) -> List[Dict[str, Any]]:

        try:
            with db_connection.get_session() as session:
                query = """
                MATCH (n)
                WHERE n.display_name IS NULL OR n.display_name = ''
                RETURN n._internal_uid as internal_uid, labels(n) as labels, properties(n) as properties
                """
                result = session.run(query)
                missing_nodes = []
                for record in result:
                    internal_uid = record["internal_uid"]
                    if internal_uid:
                        missing_nodes.append({
                            'id': internal_uid,
                            'labels': record["labels"] or ['Entity'],
                            'properties': record["properties"] or {}
                        })
                return missing_nodes
        except Exception as e:
            logger.error(f"Failed to detect missing display_name values: {e}")
            return []
    async def _detect_missing_display_names_for_nodes(self, node_ids: List[str]) -> List[Dict[str, Any]]:

        try:
            with db_connection.get_session() as session:
                query = """
                MATCH (n)
                WHERE n._internal_uid IN $node_uids
                AND (n.display_name IS NULL OR n.display_name = '')
                RETURN n._internal_uid as internal_uid, labels(n) as labels, properties(n) as properties
                """
                result = session.run(query, node_uids=node_ids)
                missing_nodes = []
                for record in result:
                    internal_uid = record["internal_uid"]
                    if internal_uid:
                        missing_nodes.append({
                            'id': internal_uid,
                            'labels': record["labels"] or ['Entity'],
                            'properties': record["properties"] or {}
                        })
                return missing_nodes
        except Exception as e:
            logger.error(f"Failed to detect missing display_name on the specified nodes: {e}")
            return []
    async def _get_nodes_by_ids(self, node_ids: List[str]) -> List[Dict[str, Any]]:

        try:
            with db_connection.get_session() as session:
                query = """
                MATCH (n)
                WHERE n._internal_uid IN $node_ids OR n.id IN $node_ids
                RETURN n._internal_uid as internal_uid, n.id as custom_id,
                       labels(n) as labels, properties(n) as properties
                """
                result = session.run(query, {"node_ids": node_ids})
                nodes_data = []
                for record in result:
                    internal_uid = record["internal_uid"]
                    custom_id = record["custom_id"]

                    node_id = internal_uid or custom_id
                    if node_id is not None:
                        nodes_data.append({
                            'id': str(node_id),
                            'labels': record["labels"] or ['Entity'],
                            'properties': record["properties"] or {}
                        })
                return nodes_data
        except Exception as e:
            logger.error(f"Failed to fetch node data: {e}")
            return []

    async def _update_display_names_in_db(self, display_names: Dict[str, str]) -> int:

        updated_count = 0
        try:
            with db_connection.get_session() as session:
                for node_uid, display_name in display_names.items():
                    try:
                        update_query = """
                        MATCH (n)
                        WHERE n._internal_uid = $uid
                        SET n.display_name = $display_name
                        RETURN n._internal_uid as uid
                        """
                        result = session.run(update_query, {
                            "uid": node_uid,
                            "display_name": display_name
                        })
                        if result.single():
                            updated_count += 1
                            logger.debug(f"Updated display_name of node {node_uid}: {display_name}")
                    except Exception as e:
                        logger.error(f"Failed to update display_name of node {node_uid}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Bulk display_name update failed: {e}")
        return updated_count

    async def _count_total_nodes(self) -> int:

        try:
            with db_connection.get_session() as session:
                result = session.run("MATCH (n) RETURN count(n) as total")
                record = result.single()
                return record["total"] if record else 0
        except Exception as e:
            logger.error(f"Failed to count nodes: {e}")
            return 0

    def reset_processor(self):

        self._processed_nodes.clear()
        self._initialization_complete = False
        logger.info("Processor state reset")
    async def _generate_display_names_with_priority(self, nodes: List[Dict[str, Any]]) -> Dict[str, str]:
        display_names = {}
        nodes_for_llm = []
        logger.info(f"Generating display_name for {len(nodes)} nodes (priority strategy)")

        for node in nodes:
            node_id = node['id']
            properties = node.get('properties', {})
            name_value = properties.get('name', '').strip() if properties.get('name') else ''
            if name_value:

                display_names[node_id] = name_value
                logger.debug(f"Node {node_id} uses its name property as display_name: {name_value}")
            else:

                nodes_for_llm.append(node)

        if nodes_for_llm:
            logger.info(f"Using the name property for {len(display_names)} nodes; {len(nodes_for_llm)} nodes need LLM generation")
            try:
                llm_generated = await node_display_name_service.generate_display_names_batch(nodes_for_llm)
                display_names.update(llm_generated)
                logger.info(f"LLM generation finished: {len(llm_generated)} display_name values")
            except Exception as e:
                logger.error(f"LLM display_name generation failed: {e}")

                for node in nodes_for_llm:
                    node_id = node['id']
                    if node_id not in display_names:

                        labels = node.get('labels', ['Entity'])
                        display_names[node_id] = labels[0] if labels else 'Unknown'
        else:
            logger.info(f"All {len(nodes)} nodes used their name property; no LLM generation needed")
        logger.info(f"Priority strategy finished: generated {len(display_names)} display_name values in total")
        return display_names
    def get_status(self) -> Dict[str, Any]:

        return {
            "initialization_complete": self._initialization_complete,
            "processed_nodes_count": len(self._processed_nodes),
            "mode": "event_driven",
            "priority_strategy": "name_first_then_llm",
            "last_update": datetime.now().isoformat()
        }

auto_display_name_processor = AutoDisplayNameProcessor()