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
                logger.info(f"处理数据变化事件，节点范围: {'指定节点' if node_ids else '全部节点'}")

                if node_ids:

                    missing_nodes = await self._detect_missing_display_names_for_nodes(node_ids)
                else:

                    missing_nodes = await self._detect_missing_display_names()

                new_missing_nodes = [
                    node for node in missing_nodes
                    if node['id'] not in self._processed_nodes
                ]
                if not new_missing_nodes:
                    logger.info("没有需要处理的新节点")
                    return {
                        "action": "no_new_nodes",
                        "total_checked": len(missing_nodes),
                        "already_processed": len(missing_nodes) - len(new_missing_nodes),
                        "new_processed": 0
                    }
                logger.info(f"发现 {len(new_missing_nodes)} 个新节点需要生成display_name")

                display_names = await self._generate_display_names_with_priority(new_missing_nodes)

                updated_count = await self._update_display_names_in_db(display_names)

                for node in new_missing_nodes:
                    self._processed_nodes.add(node['id'])
                logger.info(f"数据变化事件处理完成: 更新了 {updated_count} 个节点的display_name")
                return {
                    "action": "processed",
                    "total_checked": len(missing_nodes),
                    "already_processed": len(missing_nodes) - len(new_missing_nodes),
                    "new_processed": updated_count,
                    "generated_names": len(display_names)
                }
            except Exception as e:
                logger.error(f"数据变化事件处理失败: {e}")
                return {
                    "action": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

    async def process_new_nodes(self, node_ids: List[str]) -> Dict[str, Any]:
        if not node_ids:
            return {"action": "no_nodes", "processed_count": 0}

        try:
            logger.info(f"为 {len(node_ids)} 个新节点生成display_name...")


            nodes_data = await self._get_nodes_by_ids(node_ids)


            missing_nodes = [
                node for node in nodes_data
                if not node.get('properties', {}).get('display_name')
            ]

            if not missing_nodes:
                return {"action": "no_missing", "processed_count": 0}

            display_names = await self._generate_display_names_with_priority(missing_nodes)

            updated_count = await self._update_display_names_in_db(display_names)

            logger.info(f"为新节点生成display_name完成: {updated_count} 个节点")

            return {
                "action": "processed",
                "requested_count": len(node_ids),
                "missing_count": len(missing_nodes),
                "processed_count": updated_count
            }

        except Exception as e:
            logger.error(f"处理新节点display_name失败: {e}")
            return {"action": "error", "error": str(e)}

    def clear_processed_cache(self):

        self._processed_nodes.clear()
        logger.info("已清空处理缓存")

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
            logger.error(f"检测缺失display_name失败: {e}")
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
            logger.error(f"检测指定节点缺失display_name失败: {e}")
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
            logger.error(f"获取节点数据失败: {e}")
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
                            logger.debug(f"成功更新节点 {node_uid} 的display_name: {display_name}")
                    except Exception as e:
                        logger.error(f"更新节点 {node_uid} 的display_name失败: {e}")
                        continue
        except Exception as e:
            logger.error(f"批量更新display_name失败: {e}")
        return updated_count

    async def _count_total_nodes(self) -> int:

        try:
            with db_connection.get_session() as session:
                result = session.run("MATCH (n) RETURN count(n) as total")
                record = result.single()
                return record["total"] if record else 0
        except Exception as e:
            logger.error(f"统计节点总数失败: {e}")
            return 0

    def reset_processor(self):

        self._processed_nodes.clear()
        self._initialization_complete = False
        logger.info("处理器状态已重置")
    async def _generate_display_names_with_priority(self, nodes: List[Dict[str, Any]]) -> Dict[str, str]:
        display_names = {}
        nodes_for_llm = []
        logger.info(f"开始处理 {len(nodes)} 个节点的display_name生成（优先级策略）")

        for node in nodes:
            node_id = node['id']
            properties = node.get('properties', {})
            name_value = properties.get('name', '').strip() if properties.get('name') else ''
            if name_value:

                display_names[node_id] = name_value
                logger.debug(f"节点 {node_id} 使用name属性作为display_name: {name_value}")
            else:

                nodes_for_llm.append(node)

        if nodes_for_llm:
            logger.info(f"使用name属性: {len(display_names)} 个节点，需要LLM生成: {len(nodes_for_llm)} 个节点")
            try:
                llm_generated = await node_display_name_service.generate_display_names_batch(nodes_for_llm)
                display_names.update(llm_generated)
                logger.info(f"LLM生成完成: {len(llm_generated)} 个display_name")
            except Exception as e:
                logger.error(f"LLM生成display_name失败: {e}")

                for node in nodes_for_llm:
                    node_id = node['id']
                    if node_id not in display_names:

                        labels = node.get('labels', ['Entity'])
                        display_names[node_id] = labels[0] if labels else 'Unknown'
        else:
            logger.info(f"所有 {len(nodes)} 个节点都使用了name属性，无需LLM生成")
        logger.info(f"优先级策略处理完成: 总共生成 {len(display_names)} 个display_name")
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