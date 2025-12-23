import logging
from typing import Dict, List, Any, Optional, Union
import hashlib
import json
import uuid
from ..models.graph_models import NodeModel, RelationshipModel, GraphDataModel
logger = logging.getLogger(__name__)
class DataTransformationService:
    @staticmethod
    def generate_internal_uid() -> str:

        return str(uuid.uuid4())
    @staticmethod
    def generate_node_id(node_data: Dict[str, Any]) -> str:

        if node_data.get('id'):
            return str(node_data['id'])

        name = node_data.get('properties', {}).get('name', 'unknown')
        node_type = node_data.get('type', 'Entity')
        labels = node_data.get('labels', [node_type])

        identifier = f"{name}_{labels[0] if labels else 'Entity'}"
        return str(abs(hash(identifier)) % 1000000)

    @staticmethod
    def generate_relationship_id(rel_data: Dict[str, Any]) -> str:

        if rel_data.get('id'):
            return str(rel_data['id'])


        source = rel_data.get('source') or rel_data.get('start_node_id', 'unknown')
        target = rel_data.get('target') or rel_data.get('end_node_id', 'unknown')
        rel_type = rel_data.get('type', 'RELATED')

        identifier = f"{source}_{rel_type}_{target}"
        return str(abs(hash(identifier)) % 1000000)

    @classmethod
    def kgot_to_standard(cls, kgot_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:

        {
          "entities": [{"id": "...", "type": "...", "properties": {...}}],
          "relationships": [{"source": "...", "target": "...", "type": "...", "properties": {...}}]
        }
        try:
            nodes = []
            relationships = []


            entities = kgot_data.get('entities', [])
            for entity in entities:

                internal_uid = cls.generate_internal_uid()
                node = {
                    'id': cls.generate_node_id(entity),
                    'labels': [entity.get('type', 'Entity')],
                    'properties': entity.get('properties', {})
                }

                if 'name' not in node['properties'] and entity.get('id'):
                    node['properties']['name'] = str(entity['id'])

                node['properties']['_internal_uid'] = internal_uid
                nodes.append(node)


            relations = kgot_data.get('relationships', [])
            for rel in relations:
                relationship = {
                    'id': cls.generate_relationship_id(rel),
                    'type': rel.get('type', 'RELATED'),
                    'start_node_id': str(rel.get('source', '')),
                    'end_node_id': str(rel.get('target', '')),
                    'properties': rel.get('properties', {})
                }
                relationships.append(relationship)

            return {
                'nodes': nodes,
                'relationships': relationships
            }

        except Exception as e:
            logger.error(f"KGOT数据转换失败: {e}")
            return {'nodes': [], 'relationships': []}

    @classmethod
    def standard_to_neo4j(cls, standard_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        确保所有字段都符合Neo4j的要求
        try:
            nodes = []
            relationships = []


            for node in standard_data.get('nodes', []):

                internal_uid = cls.generate_internal_uid()
                neo4j_node = {
                    'id': node.get('id') or cls.generate_node_id(node),
                    'labels': node.get('labels', ['Entity']),
                    'properties': dict(node.get('properties', {}))
                }

                neo4j_node['properties']['id'] = neo4j_node['id']

                neo4j_node['properties']['_internal_uid'] = internal_uid
                nodes.append(neo4j_node)


            for rel in standard_data.get('relationships', []):
                neo4j_rel = {
                    'id': rel.get('id') or cls.generate_relationship_id(rel),
                    'type': rel.get('type', 'RELATED'),
                    'start_node_id': str(rel.get('start_node_id', '')),
                    'end_node_id': str(rel.get('end_node_id', '')),
                    'properties': dict(rel.get('properties', {}))
                }
                relationships.append(neo4j_rel)

            return {
                'nodes': nodes,
                'relationships': relationships
            }

        except Exception as e:
            logger.error(f"Neo4j格式转换失败: {e}")
            return {'nodes': [], 'relationships': []}

    @classmethod
    def neo4j_to_frontend(cls, neo4j_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        确保所有必需字段都存在
        try:
            nodes = []
            relationships = []


            for node in neo4j_data.get('nodes', []):
                frontend_node = {
                    'id': str(node.get('id', cls.generate_node_id(node))),
                    'labels': node.get('labels', ['Entity']),
                    'properties': dict(node.get('properties', {}))
                }
                nodes.append(frontend_node)


            for rel in neo4j_data.get('relationships', []):
                frontend_rel = {
                    'id': str(rel.get('id', cls.generate_relationship_id(rel))),
                    'type': rel.get('type', 'RELATED'),
                    'start_node_id': str(rel.get('start_node_id', '')),
                    'end_node_id': str(rel.get('end_node_id', '')),
                    'properties': dict(rel.get('properties', {}))
                }
                relationships.append(frontend_rel)

            return {
                'nodes': nodes,
                'relationships': relationships
            }

        except Exception as e:
            logger.error(f"前端格式转换失败: {e}")
            return {'nodes': [], 'relationships': []}

    @classmethod
    def to_pydantic_models(cls, data: Dict[str, List[Dict[str, Any]]]) -> GraphDataModel:
        try:
            nodes = [NodeModel(**node) for node in data.get('nodes', [])]
            relationships = [RelationshipModel(**rel) for rel in data.get('relationships', [])]

            return GraphDataModel(nodes=nodes, relationships=relationships)

        except Exception as e:
            logger.error(f"Pydantic模型转换失败: {e}")
            return GraphDataModel(nodes=[], relationships=[])

    @classmethod
    def from_pydantic_models(cls, graph_model: GraphDataModel) -> Dict[str, List[Dict[str, Any]]]:
        try:
            return {
                'nodes': [node.dict() for node in graph_model.nodes],
                'relationships': [rel.dict() for rel in graph_model.relationships]
            }
        except Exception as e:
            logger.error(f"Pydantic模型解析失败: {e}")
            return {'nodes': [], 'relationships': []}

    @classmethod
    def validate_and_fix_data(cls, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        try:
            fixed_nodes = []
            fixed_relationships = []


            for node in data.get('nodes', []):
                fixed_node = {
                    'id': str(node.get('id') or cls.generate_node_id(node)),
                    'labels': node.get('labels') or ['Entity'],
                    'properties': node.get('properties') or {}
                }

                if 'name' not in fixed_node['properties']:
                    fixed_node['properties']['name'] = fixed_node['id']

                if '_internal_uid' not in fixed_node['properties']:
                    fixed_node['properties']['_internal_uid'] = cls.generate_internal_uid()
                fixed_nodes.append(fixed_node)


            node_ids = {node['id'] for node in fixed_nodes}

            for rel in data.get('relationships', []):
                start_id = str(rel.get('start_node_id') or rel.get('source', ''))
                end_id = str(rel.get('end_node_id') or rel.get('target', ''))


                if not start_id or not end_id:
                    continue

                fixed_rel = {
                    'id': str(rel.get('id') or cls.generate_relationship_id(rel)),
                    'type': rel.get('type', 'RELATED'),
                    'start_node_id': start_id,
                    'end_node_id': end_id,
                    'properties': rel.get('properties') or {}
                }

                fixed_relationships.append(fixed_rel)

            return {
                'nodes': fixed_nodes,
                'relationships': fixed_relationships
            }

        except Exception as e:
            logger.error(f"数据验证修复失败: {e}")
            return {'nodes': [], 'relationships': []}

data_transformer = DataTransformationService()