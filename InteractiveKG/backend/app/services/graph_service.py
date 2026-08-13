from typing import List, Dict, Any, Optional
import json
import uuid
import asyncio
import logging
import re
from collections import Counter
from ..database.connection import db_connection
from ..models.graph_models import (
    NodeModel, RelationshipModel, GraphDataModel,
    NodeCreateRequest, NodeUpdateRequest,
    RelationshipCreateRequest, RelationshipUpdateRequest,
    GraphSearchRequest, GraphSearchResponse
)
from .hierarchical_abstraction_service import HierarchicalAbstractionService
from .id_resolvers import NodeIDResolver, RelationshipIDResolver
from .enhanced_abstraction_service import EnhancedAbstractionService
from ..config.llm_config import get_llm_config, is_llm_enabled
from .llm_assisted_reasoning import LLMAssistedReasoningService
from .data_transformation_service import data_transformer
from .auto_display_name_processor import auto_display_name_processor
from .duplicate_cleanup_service import DuplicateCleanupService
from .data_validation_service import data_validation_service, DataValidationReport
logger = logging.getLogger(__name__)
class GraphService:

    def __init__(self):
        self.db = db_connection

        self.node_id_resolver = NodeIDResolver(self.db)
        self.relationship_id_resolver = RelationshipIDResolver(self.db)

        self._llm_config = None
        self._llm_enabled = None
        self._hierarchical_service = None
        self.enhanced_service = EnhancedAbstractionService()
        self.reasoning_service = LLMAssistedReasoningService()
        self.cleanup_service = DuplicateCleanupService(self.db)
    def _get_llm_config(self):

        if self._llm_config is None:
            self._llm_config = get_llm_config()
            self._llm_enabled = is_llm_enabled()
        return self._llm_config
    @property
    def llm_config(self):
        return self._get_llm_config()
    @property
    def llm_enabled(self):
        if self._llm_enabled is None:
            self._get_llm_config()
        return self._llm_enabled
    @property
    def hierarchical_service(self):

        if self._hierarchical_service is None:
            self._hierarchical_service = HierarchicalAbstractionService(
                llm_config=self.llm_config,
                use_llm=False
            )
        return self._hierarchical_service

    def _sanitize_label(self, label: str) -> str:
        import re

        sanitized = re.sub(r'[^\w\s-]', '', label, flags=re.UNICODE)

        sanitized = re.sub(r'[\s-]+', '_', sanitized)

        if sanitized and sanitized[0].isdigit():
            sanitized = 'N_' + sanitized

        if not sanitized:
            sanitized = 'Entity'
        return sanitized
    async def create_node(self, node_request: NodeCreateRequest) -> NodeModel:


        escaped_labels = []
        for label in (node_request.labels or ["Node"]):

            sanitized_label = self._sanitize_label(label)

            if " " in sanitized_label or "-" in sanitized_label:
                escaped_labels.append(f"`{sanitized_label}`")
            else:
                escaped_labels.append(sanitized_label)
        labels_str = ":".join(escaped_labels)

        internal_uid = self.node_id_resolver.generate_internal_uid()

        props_dict = node_request.properties.copy()
        props_dict["_internal_uid"] = internal_uid
        query = f"""
        CREATE (n:{labels_str} $props)
        RETURN id(n) as neo4j_id, labels(n) as labels, properties(n) as properties
        """
        with self.db.get_session() as session:
            result = session.run(query, {"props": props_dict})
            record = result.single()
            if record:
                neo4j_id = record["neo4j_id"]
                properties = record["properties"] or {}

                created_node = NodeModel(
                    id=internal_uid,
                    labels=record["labels"],
                    properties=properties
                )

                asyncio.create_task(auto_display_name_processor.process_data_change_event([internal_uid]))
                logger.info(f"Created node with internal UID: {internal_uid}, Neo4j ID: {neo4j_id}")
                return created_node
        raise Exception("Failed to create node")

    def get_node(self, node_id: str) -> Optional[NodeModel]:


        identifiers = self.node_id_resolver.get_node_identifiers(node_id)
        if not identifiers:
            return None
        neo4j_id = identifiers["neo4j_id"]
        with self.db.get_session() as session:
            query = """
            MATCH (n) WHERE id(n) = $neo4j_id
            RETURN id(n) as neo4j_id, labels(n) as labels, properties(n) as properties
            """
            result = session.run(query, {"neo4j_id": neo4j_id})
            record = result.single()
            if record:
                properties = record["properties"] or {}

                internal_uid = identifiers["internal_uid"]
                if not internal_uid:
                    internal_uid = self.node_id_resolver.ensure_internal_uid(neo4j_id)
                    properties["_internal_uid"] = internal_uid

                final_id = internal_uid or identifiers["custom_id"] or str(neo4j_id)
                return NodeModel(
                    id=final_id,
                    labels=record["labels"],
                    properties=properties
                )
        return None

    def update_node(self, node_id: str, update_request: NodeUpdateRequest) -> Optional[NodeModel]:


        neo4j_id = self.node_id_resolver.resolve_to_neo4j_id(node_id)
        if neo4j_id is None:
            logger.warning(f"Could not find node for identifier: {node_id}")
            return None

        existing_node = self.get_node(node_id)
        if not existing_node:
            return None

        original_labels = existing_node.labels or []

        updated_node = existing_node

        if update_request.properties:

            existing_properties = existing_node.properties or {}
            system_properties = {k: v for k, v in existing_properties.items() if k.startswith('_')}



            final_properties = {
                **system_properties,
                **update_request.properties
            }



            query = """
            MATCH (n) WHERE id(n) = $neo4j_id
            SET n = $props
            RETURN id(n) as neo4j_id, labels(n) as labels, properties(n) as properties
            """
            result = self.db.execute_write_query(query, {
                "neo4j_id": neo4j_id,
                "props": final_properties
            })
            if result:
                record = result[0]
                properties = record["properties"] or {}

                internal_uid = properties.get('_internal_uid')
                if not internal_uid:
                    internal_uid = self.node_id_resolver.ensure_internal_uid(record["neo4j_id"])
                    properties['_internal_uid'] = internal_uid
                updated_node = NodeModel(
                    id=internal_uid,
                    labels=record["labels"] or ['Entity'],
                    properties=properties
                )

                if 'display_name' in update_request.properties:
                    logger.info(f"User manually set display_name of node {node_id} to: {update_request.properties['display_name']}")
                else:

                    asyncio.create_task(auto_display_name_processor.process_data_change_event([internal_uid]))

        if update_request.labels:

            existing_labels = original_labels



            if update_request.properties:

                props_to_use = updated_node.properties or {}
            else:

                props_to_use = updated_node.properties or {}


            system_props = {k: v for k, v in props_to_use.items() if k.startswith('_')}
            user_props = {k: v for k, v in props_to_use.items() if not k.startswith('_')}
            final_props = {**system_props, **user_props}


            escaped_new_labels = [f"`{label}`" for label in update_request.labels]
            new_labels_str = ':'.join(escaped_new_labels)




            if existing_labels:


                remove_parts = []
                for old_label in existing_labels:


                    escaped_old_label = old_label.replace('`', '``')

                    if ' ' in old_label or '-' in old_label or not old_label.replace('_', '').isalnum():
                        remove_parts.append(f"n:`{escaped_old_label}`")
                    else:
                        remove_parts.append(f"n:{escaped_old_label}")

                remove_clause = "REMOVE " + ", ".join(remove_parts)
                query = f"""
                MATCH (n) WHERE id(n) = $neo4j_id
                {remove_clause}
                SET n:{new_labels_str}
                SET n = $props
                RETURN id(n) as neo4j_id, labels(n) as labels, properties(n) as properties
                """
            else:
                query = f"""
                MATCH (n) WHERE id(n) = $neo4j_id
                SET n:{new_labels_str}
                SET n = $props
                RETURN id(n) as neo4j_id, labels(n) as labels, properties(n) as properties
                """
            result = self.db.execute_write_query(query, {
                "neo4j_id": neo4j_id,
                "props": final_props
            })
            if result:
                record = result[0]
                properties = record["properties"] or {}

                internal_uid = properties.get('_internal_uid')
                if not internal_uid:
                    internal_uid = self.node_id_resolver.ensure_internal_uid(record["neo4j_id"])
                    properties['_internal_uid'] = internal_uid
                updated_node = NodeModel(
                    id=internal_uid,
                    labels=record["labels"] or ['Entity'],
                    properties=properties
                )
        return updated_node

    def delete_node(self, node_id: str) -> bool:

        neo4j_id = self.node_id_resolver.resolve_to_neo4j_id(node_id)
        if neo4j_id is None:
            logger.warning(f"Could not find node for identifier: {node_id}")
            return False
        try:
            with self.db.get_session() as session:
                check_query = """
                MATCH (n) WHERE id(n) = $neo4j_id
                RETURN labels(n) as labels
                """
                result = session.run(check_query, neo4j_id=neo4j_id)
                record = result.single()

                if record and 'Community' in record['labels']:

                    logger.info(f"Deleting Community node {node_id} and all its member nodes")

                    member_query = """
                    MATCH (m)-[:MEMBER_OF]->(c)
                    WHERE id(c) = $neo4j_id
                    RETURN id(m) as member_id, labels(m) as member_labels
                    """
                    member_result = session.run(member_query, neo4j_id=neo4j_id)

                    deleted_members = 0
                    member_ids_to_delete = []

                    for member_record in member_result:
                        member_neo4j_id = member_record['member_id']
                        member_labels = member_record['member_labels']

                        uid_query = """
                        MATCH (m) WHERE id(m) = $member_id
                        RETURN coalesce(m._internal_uid, m.id, toString(id(m))) as uid
                        """
                        uid_result = session.run(uid_query, member_id=member_neo4j_id)
                        uid_record = uid_result.single()
                        if uid_record and uid_record['uid']:
                            member_ids_to_delete.append(uid_record['uid'])
                            logger.debug(f"Will delete member node: {uid_record['uid']} (labels: {member_labels})")



                    for member_id_to_delete in member_ids_to_delete:
                        if self.delete_node(member_id_to_delete):
                            deleted_members += 1

                    logger.info(f"Deleted {deleted_members} member nodes from community {node_id}")


                delete_query = """
                MATCH (n) WHERE id(n) = $neo4j_id
                DETACH DELETE n
                RETURN count(n) as deleted_count
                """
                result = session.run(delete_query, neo4j_id=neo4j_id)
                record = result.single()
                success = record and record['deleted_count'] > 0
                if success:
                    logger.info(f"Successfully deleted node with identifier: {node_id} (Neo4j ID: {neo4j_id})")
                return success
        except Exception as e:
            logger.error(f"Failed to delete node {node_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def create_relationship(self, rel_request: RelationshipCreateRequest) -> RelationshipModel:


        start_neo4j_id = self.node_id_resolver.resolve_to_neo4j_id(rel_request.start_node_id)
        end_neo4j_id = self.node_id_resolver.resolve_to_neo4j_id(rel_request.end_node_id)
        if start_neo4j_id is None:
            raise Exception(f"Start node not found: {rel_request.start_node_id}")
        if end_neo4j_id is None:
            raise Exception(f"End node not found: {rel_request.end_node_id}")

        rel_internal_uid = self.node_id_resolver.generate_internal_uid()

        props_dict = rel_request.properties.copy()
        props_dict['_internal_uid'] = rel_internal_uid
        query = f"""
        MATCH (start) WHERE id(start) = $start_neo4j_id
        MATCH (end) WHERE id(end) = $end_neo4j_id
        CREATE (start)-[r:{rel_request.type} $props]->(end)
        RETURN id(r) as rel_id, type(r) as type,
               id(start) as start_neo4j_id, id(end) as end_neo4j_id,
               start._internal_uid as start_uid, end._internal_uid as end_uid,
               r._internal_uid as rel_uid, properties(r) as properties
        """
        with self.db.get_session() as session:
            result = session.run(query, {
                "start_neo4j_id": start_neo4j_id,
                "end_neo4j_id": end_neo4j_id,
                "props": props_dict
            })
            record = result.single()
            if record:

                start_id = record["start_uid"] or str(record["start_neo4j_id"])
                end_id = record["end_uid"] or str(record["end_neo4j_id"])
                rel_uid = record["rel_uid"] or str(record["rel_id"])
                logger.info(f"Created relationship with UID {rel_uid} between {start_id} and {end_id}")
                return RelationshipModel(
                    id=rel_uid,
                    type=record["type"],
                    start_node_id=start_id,
                    end_node_id=end_id,
                    properties=record["properties"]
                )
        raise Exception("Failed to create relationship")
    def get_relationship(self, rel_id: str) -> Optional[RelationshipModel]:

        try:
            with self.db.get_session() as session:

                if self.node_id_resolver.is_uuid_format(rel_id):
                    query = """
                    MATCH (start)-[r]->(end)
                    WHERE r._internal_uid = $rel_uid
                    RETURN r._internal_uid as rel_uid, type(r) as rel_type,
                           start._internal_uid as start_uid, end._internal_uid as end_uid,
                           id(start) as start_neo4j_id, id(end) as end_neo4j_id,
                           properties(r) as properties
                    """
                    result = session.run(query, {"rel_uid": rel_id})
                    record = result.single()
                    if record:

                        start_id = record["start_uid"] or str(record["start_neo4j_id"])
                        end_id = record["end_uid"] or str(record["end_neo4j_id"])
                        return RelationshipModel(
                            id=record["rel_uid"],
                            type=record["rel_type"],
                            start_node_id=start_id,
                            end_node_id=end_id,
                            properties=record["properties"]
                        )

                neo4j_rel_id = int(rel_id)
                query = """
                MATCH (start)-[r]->(end)
                WHERE id(r) = $neo4j_rel_id
                RETURN r._internal_uid as rel_uid, id(r) as rel_id, type(r) as rel_type,
                       start._internal_uid as start_uid, end._internal_uid as end_uid,
                       id(start) as start_neo4j_id, id(end) as end_neo4j_id,
                       properties(r) as properties
                """
                result = session.run(query, {"neo4j_rel_id": neo4j_rel_id})
                record = result.single()
                if record:

                    rel_uid = record["rel_uid"] or str(record["rel_id"])
                    start_id = record["start_uid"] or str(record["start_neo4j_id"])
                    end_id = record["end_uid"] or str(record["end_neo4j_id"])
                    return RelationshipModel(
                        id=rel_uid,
                        type=record["rel_type"],
                        start_node_id=start_id,
                        end_node_id=end_id,
                        properties=record["properties"]
                    )
        except (ValueError, TypeError):
            logger.warning(f"Invalid relationship ID format: {rel_id}")
        return None
    def update_relationship(self, rel_id: str, update_request: RelationshipUpdateRequest) -> Optional[RelationshipModel]:


        existing_rel = self.get_relationship(rel_id)
        if not existing_rel:
            return None

        if update_request.properties:

            if self.node_id_resolver.is_uuid_format(rel_id):
                query = """
                MATCH (start)-[r]->(end)
                WHERE r._internal_uid = $rel_uid
                SET r += $props
                RETURN r._internal_uid as rel_uid, type(r) as rel_type,
                       start._internal_uid as start_uid, end._internal_uid as end_uid,
                       id(start) as start_neo4j_id, id(end) as end_neo4j_id,
                       properties(r) as properties
                """
                result = self.db.execute_write_query(query, {
                    "rel_uid": rel_id,
                    "props": update_request.properties
                })
            else:

                try:
                    neo4j_rel_id = int(rel_id)
                    query = """
                    MATCH (start)-[r]->(end)
                    WHERE id(r) = $neo4j_rel_id
                    SET r += $props
                    RETURN r._internal_uid as rel_uid, id(r) as rel_id, type(r) as rel_type,
                           start._internal_uid as start_uid, end._internal_uid as end_uid,
                           id(start) as start_neo4j_id, id(end) as end_neo4j_id,
                           properties(r) as properties
                    """
                    result = self.db.execute_write_query(query, {
                        "neo4j_rel_id": neo4j_rel_id,
                        "props": update_request.properties
                    })
                except (ValueError, TypeError):
                    logger.warning(f"Invalid relationship ID format: {rel_id}")
                    return None
            if result:
                record = result[0]

                rel_uid = record.get("rel_uid") or str(record.get("rel_id"))
                start_id = record["start_uid"] or str(record["start_neo4j_id"])
                end_id = record["end_uid"] or str(record["end_neo4j_id"])
                return RelationshipModel(
                    id=rel_uid,
                    type=record["rel_type"],
                    start_node_id=start_id,
                    end_node_id=end_id,
                    properties=record["properties"]
                )
        return existing_rel
    def delete_relationship(self, rel_id: str) -> bool:

        try:

            if self.node_id_resolver.is_uuid_format(rel_id):
                query = """
                MATCH ()-[r]-()
                WHERE r._internal_uid = $rel_uid
                DELETE r
                RETURN count(r) as deleted_count
                """
                result = self.db.execute_write_query(query, {"rel_uid": rel_id})
            else:

                neo4j_rel_id = self.relationship_id_resolver.resolve_to_neo4j_id(rel_id)
                if neo4j_rel_id is None:
                    logger.warning(f"Could not find relationship for identifier: {rel_id}")
                    return False
                query = """
                MATCH ()-[r]-()
                WHERE id(r) = $neo4j_rel_id
                DELETE r
                RETURN count(r) as deleted_count
                """
                result = self.db.execute_write_query(query, {"neo4j_rel_id": neo4j_rel_id})
            success = result and result[0]["deleted_count"] > 0
            if success:
                logger.info(f"Successfully deleted relationship with identifier: {rel_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete relationship {rel_id}: {str(e)}")
            return False

    async def get_all_graph_data(self) -> GraphDataModel:


        if not auto_display_name_processor._initialization_complete:
            await auto_display_name_processor.ensure_display_names()
        nodes = []
        relationships = []
        with self.db.get_session() as session:

            nodes_query = "MATCH (n) RETURN id(n) as neo4j_id, labels(n) as labels, properties(n) as properties"
            nodes_result = session.run(nodes_query)
            for record in nodes_result:
                properties = record["properties"] or {}
                neo4j_id = record["neo4j_id"]

                internal_uid = properties.get('_internal_uid')
                if not internal_uid:
                    internal_uid = self.node_id_resolver.ensure_internal_uid(neo4j_id)
                    properties['_internal_uid'] = internal_uid

                node_id = internal_uid

                if 'display_name' not in properties or not properties['display_name']:

                    if 'name' in properties and properties['name']:
                        properties['display_name'] = properties['name']
                    elif 'id' in properties and properties['id']:
                        properties['display_name'] = str(properties['id'])
                    else:
                        properties['display_name'] = f"Node_{node_id[:8]}"
                nodes.append(NodeModel(
                    id=node_id,
                    labels=record["labels"] or ['Entity'],
                    properties=properties
                ))

            rels_query = """
            MATCH (start)-[r]->(end)
            RETURN id(r) as rel_neo4j_id, r._internal_uid as rel_uid, type(r) as rel_type,
                   id(start) as start_neo4j_id, id(end) as end_neo4j_id,
                   start._internal_uid as start_uid, end._internal_uid as end_uid,
                   properties(start) as start_props, properties(end) as end_props,
                   properties(r) as properties
            """
            rels_result = session.run(rels_query)
            for record in rels_result:
                rel_properties = record["properties"] or {}

                rel_uid = record["rel_uid"]
                if not rel_uid:


                    rel_uid = str(record["rel_neo4j_id"])

                start_uid = record["start_uid"]
                end_uid = record["end_uid"]

                if not start_uid:
                    start_uid = self.node_id_resolver.ensure_internal_uid(record["start_neo4j_id"])
                if not end_uid:
                    end_uid = self.node_id_resolver.ensure_internal_uid(record["end_neo4j_id"])
                relationships.append(RelationshipModel(
                    id=rel_uid,
                    type=record["rel_type"] or 'RELATED',
                    start_node_id=start_uid,
                    end_node_id=end_uid,
                    properties=rel_properties
                ))
        return GraphDataModel(nodes=nodes, relationships=relationships)

    def _analyze_json_format(self, json_data: Dict[str, Any]) -> Dict[str, str]:

        format_mapping = {
            'nodes_key': 'nodes',
            'relationships_key': 'relationships',
            'node_labels_key': 'labels',
            'node_type_key': None,
            'rel_start_key': 'start_node_id',
            'rel_end_key': 'end_node_id',
            'rel_type_key': 'type'
        }

        if 'relationships' in json_data:
            format_mapping['relationships_key'] = 'relationships'
        elif 'edges' in json_data:
            format_mapping['relationships_key'] = 'edges'
        elif 'links' in json_data:
            format_mapping['relationships_key'] = 'links'

        nodes_data = json_data.get(format_mapping['nodes_key'], [])
        if nodes_data:
            sample_node = nodes_data[0]

            if 'labels' in sample_node:
                format_mapping['node_labels_key'] = 'labels'
            elif 'type' in sample_node:
                format_mapping['node_type_key'] = 'type'
            elif 'category' in sample_node:
                format_mapping['node_type_key'] = 'category'
            elif 'class' in sample_node:
                format_mapping['node_type_key'] = 'class'

        relationships_data = json_data.get(format_mapping['relationships_key'], [])
        if relationships_data:
            sample_rel = relationships_data[0]

            if 'start_node_id' in sample_rel:
                format_mapping['rel_start_key'] = 'start_node_id'
                format_mapping['rel_end_key'] = 'end_node_id'
            elif 'source' in sample_rel:
                format_mapping['rel_start_key'] = 'source'
                format_mapping['rel_end_key'] = 'target'
            elif 'from' in sample_rel:
                format_mapping['rel_start_key'] = 'from'
                format_mapping['rel_end_key'] = 'to'
            elif 'src' in sample_rel:
                format_mapping['rel_start_key'] = 'src'
                format_mapping['rel_end_key'] = 'dst'

            if 'type' in sample_rel:
                format_mapping['rel_type_key'] = 'type'
            elif 'label' in sample_rel:
                format_mapping['rel_type_key'] = 'label'
            elif 'relation' in sample_rel:
                format_mapping['rel_type_key'] = 'relation'
            elif 'relationship' in sample_rel:
                format_mapping['rel_type_key'] = 'relationship'
        return format_mapping
    async def import_json_data(self, json_data: Dict[str, Any]) -> GraphDataModel:

        has_abstraction_levels = 'abstraction_levels' in json_data
        abstraction_levels_data = json_data.get('abstraction_levels', {}) if has_abstraction_levels else None

        if 'original_graph' in json_data:
            logger.info("Sample-data format detected; extracting original_graph...")
            graph_data = json_data['original_graph']
        else:
            graph_data = json_data

        logger.info("Validating and preprocessing uploaded data...")
        validated_data, validation_report = data_validation_service.validate_and_preprocess(graph_data)

        logger.info(f"Data validation finished: {validation_report.statistics}")
        if validation_report.errors:
            logger.error(f"Validation errors: {validation_report.errors}")
            raise ValueError(f"Data validation failed: {'; '.join(validation_report.errors)}")
        if validation_report.warnings:
            logger.warning(f"Validation warnings: {validation_report.warnings}")
        if validation_report.fixes_applied:
            logger.info(f"Fixes applied: {len(validation_report.fixes_applied)}")

        self.clear_all_data()

        nodes_data = validated_data.get('nodes', [])
        relationships_data = validated_data.get('relationships', [])

        created_nodes = []
        id_mapping = {}
        logger.info(f"Creating {len(nodes_data)} nodes...")
        for i, node_data in enumerate(nodes_data):

            labels = node_data.get('labels', ['Entity'])
            properties = node_data.get('properties', {})
            original_id = node_data.get('id', f'node_{i}')
            node_request = NodeCreateRequest(
                labels=labels,
                properties=properties
            )
            created_node = await self.create_node(node_request)
            created_nodes.append(created_node)

            id_mapping[original_id] = created_node.id

            if "name" in properties:
                name_key = f"{properties['name'].lower()}_id"
                id_mapping[name_key] = created_node.id
        logger.info(f"Created {len(created_nodes)} nodes")

        created_relationships = []
        logger.info(f"Creating {len(relationships_data)} relationships...")
        for rel_data in relationships_data:

            start_id = rel_data.get('start_node_id')
            end_id = rel_data.get('end_node_id')
            rel_type = rel_data.get('type', 'RELATED')
            properties = rel_data.get('properties', {})

            mapped_start_id = id_mapping.get(start_id, start_id)
            mapped_end_id = id_mapping.get(end_id, end_id)
            try:
                rel_request = RelationshipCreateRequest(
                    type=rel_type,
                    start_node_id=mapped_start_id,
                    end_node_id=mapped_end_id,
                    properties=properties
                )
                created_rel = self.create_relationship(rel_request)
                created_relationships.append(created_rel)
            except Exception as e:
                logger.error(f"Failed to create relationship ({start_id} -> {end_id}): {str(e)}")
                continue
        logger.info(f"Created {len(created_relationships)} relationships")

        if created_nodes:
            node_ids = [node.id for node in created_nodes]
            asyncio.create_task(auto_display_name_processor.process_data_change_event(node_ids))
            logger.info(f"Bulk import finished; display_name generation triggered for {len(node_ids)} nodes")

        if abstraction_levels_data:
            logger.info("Importing predefined abstraction-level data...")
            await self._import_abstraction_levels(abstraction_levels_data, id_mapping)
            logger.info("Predefined abstraction-level data imported")
        return GraphDataModel(nodes=created_nodes, relationships=created_relationships)
    async def _import_abstraction_levels(self, abstraction_levels: Dict[str, Any], id_mapping: Dict[str, str]):
        with self.db.get_session() as session:
            for level_key, level_data in abstraction_levels.items():
                if level_key == 'level_0':

                    continue
                level_num = int(level_key.split('_')[1])
                communities = level_data.get('communities', [])
                relationships = level_data.get('relationships', [])
                logger.info(f"Importing {level_key}: {len(communities)} communities, {len(relationships)} relationships")

                for community in communities:
                    community_id = community['id']
                    community_label = community.get('label', community_id)
                    community_props = community.get('properties', {})
                    member_ids = community.get('member_ids', [])

                    community_name = community.get('name', community_label)
                    community_description = community.get('description', community_props.get('description', ''))
                    community_type = community.get('type', community_props.get('type', 'community'))

                    mapped_member_ids = [id_mapping.get(mid, mid) for mid in member_ids]

                    create_community_query = """
                    CREATE (c:Community {
                        id: $community_id,
                        name: $community_name,
                        label: $community_label,
                        abstraction_level: $level,
                        size: $size,
                        description: $description,
                        type: $type,
                        node_count: $node_count,
                        member_node_ids: $member_node_ids
                    })
                    """
                    session.run(create_community_query,
                               community_id=community_id,
                               community_name=community_name,
                               community_label=community_label,
                               level=level_num,
                               size=community.get('size', len(member_ids)),
                               description=community_description,
                               type=community_type,
                               node_count=len(mapped_member_ids),
                               member_node_ids=mapped_member_ids)
                logger.info(f"Created {len(communities)} Community nodes for {level_key}")

                for community in communities:
                    community_id = community['id']
                    member_ids = community.get('member_ids', [])
                    for member_id in member_ids:

                        neo4j_member_id = id_mapping.get(member_id, member_id)
                        logger.debug(f"Creating MEMBER_OF: {member_id} -> {neo4j_member_id} -> {community_id}")

                        member_query = """
                        MATCH (m) WHERE m._internal_uid = $member_id OR m.id = $member_id
                        MATCH (c:Community {id: $community_id, abstraction_level: $level})
                        MERGE (m)-[r:MEMBER_OF]->(c)
                        SET r.abstraction_level = $level
                        RETURN coalesce(m._internal_uid, m.id) as member_id, c.id as community_id
                        """
                        result = session.run(member_query,
                                   member_id=neo4j_member_id,
                                   community_id=community_id,
                                   level=level_num)
                        record = result.single()
                        if record:
                            logger.debug(f"Successfully created MEMBER_OF: {record['member_id']} -> {record['community_id']}")
                        else:
                            logger.warning(f"Failed to create MEMBER_OF for member_id={neo4j_member_id}, community_id={community_id}")

                for rel in relationships:
                    source_id = rel['source']
                    target_id = rel['target']
                    rel_type = rel.get('type', 'RELATED_TO')
                    weight = rel.get('weight', 1)
                    rel_query = """
                    MATCH (source:Community {id: $source_id, abstraction_level: $level})
                    MATCH (target:Community {id: $target_id, abstraction_level: $level})
                    CREATE (source)-[r:COMMUNITY_EDGE {
                        type: $rel_type,
                        weight: $weight,
                        abstraction_level: $level
                    }]->(target)
                    """
                    session.run(rel_query,
                               source_id=source_id,
                               target_id=target_id,
                               rel_type=rel_type,
                               weight=weight,
                               level=level_num)
                logger.info(f"{level_key} imported")
    async def _get_predefined_abstraction(self, abstraction_level: int) -> Optional[Dict[str, Any]]:
        if abstraction_level == 0:

            return None
        with self.db.get_session() as session:
            return await self._get_predefined_hierarchical_data_with_session(session, abstraction_level)
    def _expand_community_members_recursive(self, session, member_ids: List[str]) -> List[str]:
        original_nodes = []
        for member_id in member_ids:
            check_query = """
            MATCH (n)
            WHERE (n._internal_uid = $id OR n.id = $id)
            RETURN n, labels(n) as labels
            """
            result = session.run(check_query, id=member_id)
            record = result.single()
            if not record:
                logger.warning(f"Member {member_id} not found in database")
                continue
            node_labels = record['labels']
            if 'Community' in node_labels:
                expand_query = """
                MATCH (m)-[:MEMBER_OF]->(c)
                WHERE (c._internal_uid = $id OR c.id = $id)
                RETURN collect(coalesce(m._internal_uid, m.id)) as sub_members
                """
                expand_result = session.run(expand_query, id=member_id)
                expand_record = expand_result.single()
                if expand_record and expand_record['sub_members']:

                    sub_original = self._expand_community_members_recursive(session, expand_record['sub_members'])
                    original_nodes.extend(sub_original)
            else:

                original_nodes.append(member_id)
        return original_nodes
    async def _get_predefined_hierarchical_data_with_session(self, session, abstraction_level: int) -> Optional[Dict[str, Any]]:
        check_query = """
        MATCH (c:Community {abstraction_level: $level})
        RETURN count(c) as count
        """
        result = session.run(check_query, level=abstraction_level)
        record = result.single()
        if not record or record['count'] == 0:
            return None

        communities_query = """
            MATCH (c:Community {abstraction_level: $level})
            OPTIONAL MATCH (m)-[:MEMBER_OF]->(c)
            RETURN c, collect(coalesce(m._internal_uid, m.id)) as member_ids
            ORDER BY c.id
            """
        communities_result = session.run(communities_query, level=abstraction_level)

        edges_query = """
            MATCH (source:Community {abstraction_level: $level})-[r:COMMUNITY_EDGE]->(target:Community {abstraction_level: $level})
            RETURN source.id as source_id, source.label as source_label,
                   target.id as target_id, target.label as target_label,
                   r.type as type, r.weight as weight
            """
        edges_result = session.run(edges_query, level=abstraction_level)

        community_nodes = []
        label_groups = {}
        node_to_community = {}
        for record in communities_result:
            community = record['c']
            member_ids = record['member_ids']
            community_id = community['id']

            community_name = community.get('name', community.get('label', community_id))
            community_type = community.get('type', 'community')

            if abstraction_level >= 2:
                original_node_ids = self._expand_community_members_recursive(session, member_ids)
                original_node_count = len(original_node_ids)
                community_description = community.get('description', f'Community containing {original_node_count} original nodes')
            else:
                original_node_count = len(member_ids)
                community_description = community.get('description', f'Community containing {original_node_count} nodes')
            community_nodes.append({
                    "id": community_id,
                    "name": community_name,
                    "label": community_name,
                    "labels": ["Community"],
                    "size": community.get('size', original_node_count),
                    "description": community_description,
                    "type": community_type,
                    "node_count": original_node_count,
                    "member_node_ids": member_ids,
                    "properties": {
                        "name": community_name,
                        "displayName": community_name,
                        "description": community_description,
                        "type": community_type,
                        "size": community.get('size', original_node_count),
                        "node_count": original_node_count,
                        "member_node_ids": member_ids,
                        "abstraction_level": abstraction_level
                    }
                })

            label_groups[community_name] = member_ids

            if abstraction_level >= 2:
                original_node_ids = self._expand_community_members_recursive(session, member_ids)
                for original_node_id in original_node_ids:
                    node_to_community[original_node_id] = {
                        "community_id": community_id,
                        "community_name": community_name
                    }
            else:
                for member_id in member_ids:
                    node_to_community[member_id] = {
                        "community_id": community_id,
                        "community_name": community_name
                    }

        community_edges = []
        for record in edges_result:
                community_edges.append({
                    "source": record['source_id'],
                    "target": record['target_id'],
                    "type": record['type'],
                    "weight": record.get('weight', 1),
                    "edge_count": record.get('weight', 1)
                })

        graph_data = await self.get_all_graph_data()

        detailed_nodes = []
        for node in graph_data.nodes:
            if 'Community' in node.labels:
                continue
            display_label = node.properties.get('display_name') or node.properties.get('name') or (node.labels[0] if node.labels else 'Unknown')
            node_dict = {
                "id": node.id,
                "label": display_label,
                "labels": node.labels,
                "properties": node.properties
            }

            community_info = node_to_community.get(node.id)
            if community_info:
                node_dict["community_id"] = community_info["community_id"]
                node_dict["community_name"] = community_info["community_name"]
            else:
                logger.warning(f"Node {node.id} ({display_label}) not found in any community")
                node_dict["community_id"] = "unknown"
                node_dict["community_name"] = "Unknown Community"
            detailed_nodes.append(node_dict)
        detailed_edges = []
        for rel in graph_data.relationships:
            detailed_edges.append({
                "source": rel.start_node_id,
                "target": rel.end_node_id,
                "type": rel.type,
                "properties": rel.properties
            })

        return {
                "abstraction_method": "predefined_user_study",
                "abstraction_levels": abstraction_level,
                "hierarchy": {
                    "level_0": {
                        "label_groups": label_groups
                    }
                },
                "community_view": {
                    "nodes": community_nodes,
                    "edges": community_edges
                },
                "detailed_view": {
                    "nodes": detailed_nodes,
                    "edges": detailed_edges
                },
                "color_mapping": self._generate_color_mapping_for_communities(label_groups),
                "analysis_metadata": {
                    "total_nodes": len(graph_data.nodes),
                    "total_relationships": len(graph_data.relationships),
                    "cognitive_level": f"Level {abstraction_level}",
                    "group_count": len(community_nodes),
                    "source": "predefined_user_study",
                    "view_mode": "two_stage"
                }
            }
    def _generate_color_mapping_for_communities(self, label_groups: Dict[str, list]) -> Dict[str, Any]:

        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
            "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52B788"
        ]
        color_mapping = {}
        for i, group_name in enumerate(label_groups.keys()):
            color_mapping[group_name] = colors[i % len(colors)]
        return {
            "level_0": color_mapping
        }
    def clear_all_data(self):

        query = "MATCH (n) DETACH DELETE n"
        with self.db.get_session() as session:
            session.run(query)
    async def load_sample_data_to_database(self, sample_data: dict) -> dict:
        nodes_created = 0
        relationships_created = 0
        try:
            with self.db.get_session() as session:

                if "nodes" in sample_data:
                    for node_data in sample_data["nodes"]:
                        try:

                            node_id = node_data.get("id")
                            labels = node_data.get("labels", ["Node"])
                            properties = node_data.get("properties", {})
                            if not node_id:
                                continue

                            escaped_labels = []
                            for label in labels:
                                if " " in label or "-" in label:
                                    escaped_labels.append(f"`{label}`")
                                else:
                                    escaped_labels.append(label)
                            labels_str = ":".join(escaped_labels)

                            query = f"CREATE (n:{labels_str}) SET n = $properties, n.id = $node_id"
                            session.run(query, properties=properties, node_id=node_id)
                            nodes_created += 1
                        except Exception as e:
                            logger.error(f"Failed to create node {node_data.get('id', 'unknown')}: {str(e)}")
                            continue

                if "relationships" in sample_data:
                    for rel_data in sample_data["relationships"]:
                        try:

                            rel_id = rel_data.get("id")
                            rel_type = rel_data.get("type", "RELATED_TO")
                            start_node_id = rel_data.get("start_node_id")
                            end_node_id = rel_data.get("end_node_id")
                            properties = rel_data.get("properties", {})
                            if not all([start_node_id, end_node_id]):
                                continue

                            query = f"""
                            MATCH (start {{id: $start_id}})
                            MATCH (end {{id: $end_id}})
                            CREATE (start)-[r:`{rel_type}`]->(end)
                            SET r = $properties
                            """
                            if rel_id:
                                query = f"""
                                MATCH (start {{id: $start_id}})
                                MATCH (end {{id: $end_id}})
                                CREATE (start)-[r:`{rel_type}`]->(end)
                                SET r = $properties, r.id = $rel_id
                                """
                                session.run(query,
                                           start_id=start_node_id,
                                           end_id=end_node_id,
                                           properties=properties,
                                           rel_id=rel_id)
                            else:
                                query = f"""
                                MATCH (start {{id: $start_id}})
                                MATCH (end {{id: $end_id}})
                                CREATE (start)-[r:`{rel_type}`]->(end)
                                SET r = $properties
                                """
                                session.run(query,
                                           start_id=start_node_id,
                                           end_id=end_node_id,
                                           properties=properties)
                            relationships_created += 1
                        except Exception as e:
                            logger.error(f"Failed to create relationship {rel_data.get('id', 'unknown')}: {str(e)}")
                            continue
            logger.info(f"Sample data loaded: {nodes_created} nodes, {relationships_created} relationships")
            return {
                "nodes_created": nodes_created,
                "relationships_created": relationships_created
            }
        except Exception as e:
            logger.error(f"Failed to load sample data to database: {str(e)}")
            raise
    async def analyze_node_grouping(self) -> Dict[str, Any]:

        graph_data = await self.get_all_graph_data()
        if not graph_data.nodes:
            return {
                "grouping_attribute": None,
                "groups": {},
                "color_mapping": {},
                "default_color": "#6B7280"
            }

        property_analysis = {}

        property_analysis["_node_type"] = []
        for node in graph_data.nodes:

            if node.labels:
                property_analysis["_node_type"].append(node.labels[0])
            else:
                property_analysis["_node_type"].append("Unknown")
            for key, value in node.properties.items():
                if key == "id":
                    continue
                if key not in property_analysis:
                    property_analysis[key] = []

                str_value = str(value)
                property_analysis[key].append(str_value)

        best_attribute = None
        best_score = 0
        for attr_name, values in property_analysis.items():

            value_counts = Counter(values)
            unique_count = len(value_counts)
            total_count = len(values)

            if unique_count > 15:
                continue

            if unique_count == total_count and attr_name != "_node_type":
                continue


            if unique_count >= 2:

                group_score = max(0, 10 - abs(unique_count - 5))

                min_count = min(value_counts.values())
                max_count = max(value_counts.values())
                distribution_score = min_count / max_count if max_count > 0 else 0

                type_bonus = 3 if attr_name == "_node_type" else 0
                total_score = group_score + distribution_score * 5 + type_bonus
                if total_score > best_score:
                    best_score = total_score
                    best_attribute = attr_name

        if best_attribute is None and "_node_type" in property_analysis:
            best_attribute = "_node_type"

        color_palette = [
            "#EF4444", "#F97316", "#F59E0B", "#EAB308", "#84CC16",
            "#22C55E", "#10B981", "#14B8A6", "#06B6D4", "#0EA5E9",
            "#3B82F6", "#6366F1", "#8B5CF6", "#A855F7", "#D946EF",
            "#EC4899", "#F43F5E"
        ]
        groups = {}
        color_mapping = {}
        if best_attribute:

            for node in graph_data.nodes:
                if best_attribute == "_node_type":

                    attr_value = node.labels[0] if node.labels else "Unknown"
                else:

                    attr_value = str(node.properties.get(best_attribute, "Unknown"))
                if attr_value not in groups:
                    groups[attr_value] = []
                groups[attr_value].append(node.id)

            group_names = sorted(groups.keys())
            for i, group_name in enumerate(group_names):
                color_mapping[group_name] = color_palette[i % len(color_palette)]
        return {
            "grouping_attribute": best_attribute,
            "groups": groups,
            "color_mapping": color_mapping,
            "default_color": "#6B7280"
        }
    async def analyze_hierarchical_abstraction(self,
                                             abstraction_level: int = 3,
                                             mode: str = "semantic",
                                             use_llm: bool = False,
                                             query_context: str = None) -> Dict[str, Any]:

        predefined_result = await self._get_predefined_abstraction(abstraction_level)
        if predefined_result:
            logger.info(f"Using predefined abstraction-level data (level {abstraction_level})")
            return predefined_result

        logger.info(f"No predefined data found; computing dynamically with the Leiden algorithm (level {abstraction_level})")
        graph_data = await self.get_all_graph_data()

        if use_llm and self.llm_enabled:
            llm_service = HierarchicalAbstractionService(
                llm_config=self.llm_config,
                use_llm=True
            )
            return await llm_service.analyze_hierarchical_structure(
                graph_data, abstraction_level, mode, query_context
            )
        else:

            return await self.hierarchical_service.analyze_hierarchical_structure(
                graph_data, abstraction_level, mode, query_context
            )
    async def analyze_enhanced_abstraction(self, domain: str = "general", abstraction_level: int = 3) -> Dict[str, Any]:
        try:
            graph_data = await self.get_all_graph_data()
            return self.enhanced_service.analyze_domain_specific_hierarchy(
                graph_data, domain, abstraction_level
            )
        except Exception as e:
            print(f"Error in enhanced abstraction analysis: {e}")
            return {
                "error": str(e),
                "enhanced_method": "domain_aware_hierarchical_abstraction",
                "detected_domain": "unknown",
                "active_domain": domain,
                "abstraction_levels": abstraction_level,
                "domain_hierarchy": {},
                "complexity_analysis": {},
                "llm_limitation_analysis": {},
                "interaction_necessity_score": 0.0,
                "color_mapping": {},
                "research_insights": {}
            }
    def validate_reasoning(self, reasoning_query: str, domain: str = "general") -> Dict[str, Any]:
        try:
            graph_data = self.get_all_graph_data()
            return self.reasoning_service.validate_reasoning_process(
                graph_data, reasoning_query, domain
            )
        except Exception as e:
            print(f"Error in reasoning validation: {e}")
            return {
                "error": str(e),
                "validation_method": "multi_path_validation",
                "query": reasoning_query,
                "domain": domain,
                "reasoning_paths": [],
                "path_validations": {},
                "consistency_check": {},
                "credibility_score": {"overall_credibility": 0.0, "is_credible": False},
                "error_analysis": {"severity": "unknown"},
                "correction_suggestions": [],
                "validation_summary": "Validation failed with an error"
            }
    async def analyze_property_schema(self) -> Dict[str, Any]:

        graph_data = await self.get_all_graph_data()

        node_properties = {}
        node_labels = set()
        for node in graph_data.nodes:

            for label in node.labels:
                node_labels.add(label)

            for key, value in node.properties.items():
                if key == "id":
                    continue
                if key not in node_properties:
                    node_properties[key] = {
                        "type": type(value).__name__,
                        "examples": set(),
                        "frequency": 0
                    }
                node_properties[key]["frequency"] += 1

                if len(node_properties[key]["examples"]) < 5:
                    node_properties[key]["examples"].add(str(value))

        relationship_properties = {}
        relationship_types = set()
        for rel in graph_data.relationships:

            relationship_types.add(rel.type)

            for key, value in rel.properties.items():
                if key == "id":
                    continue
                if key not in relationship_properties:
                    relationship_properties[key] = {
                        "type": type(value).__name__,
                        "examples": set(),
                        "frequency": 0
                    }
                relationship_properties[key]["frequency"] += 1

                if len(relationship_properties[key]["examples"]) < 5:
                    relationship_properties[key]["examples"].add(str(value))

        for prop_info in node_properties.values():
            prop_info["examples"] = list(prop_info["examples"])
        for prop_info in relationship_properties.values():
            prop_info["examples"] = list(prop_info["examples"])
        return {
            "node_schema": {
                "labels": sorted(list(node_labels)),
                "properties": node_properties
            },
            "relationship_schema": {
                "types": sorted(list(relationship_types)),
                "properties": relationship_properties
            },
            "total_nodes": len(graph_data.nodes),
            "total_relationships": len(graph_data.relationships)
        }

graph_service = GraphService()