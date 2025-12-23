import logging
import uuid
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
logger = logging.getLogger(__name__)
class DataValidationReport:


    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.fixes_applied: List[str] = []
        self.statistics = {
            'total_nodes': 0,
            'total_relationships': 0,
            'nodes_fixed': 0,
            'relationships_fixed': 0,
            'ids_generated': 0,
            'labels_added': 0,
            'properties_added': 0,
            'display_names_generated': 0,
            'invalid_relationships_removed': 0
        }

    def add_error(self, message: str):

        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):

        self.warnings.append(message)

    def add_fix(self, message: str):

        self.fixes_applied.append(message)

    def to_dict(self) -> Dict[str, Any]:

        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'fixes_applied': self.fixes_applied,
            'statistics': self.statistics,
            'timestamp': datetime.now().isoformat()
        }
class DataValidationService:

    @staticmethod
    def generate_unique_id(prefix: str = "node") -> str:

        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def generate_internal_uid() -> str:

        return str(uuid.uuid4())

    def validate_and_preprocess(self, json_data: Any) -> Tuple[Dict[str, Any], DataValidationReport]:
        report = DataValidationReport()

        try:

            validated_structure = self._validate_basic_structure(json_data, report)
            if not validated_structure:
                return json_data, report


            format_mapping = self._analyze_and_normalize_format(validated_structure, report)


            nodes_data = validated_structure.get(format_mapping['nodes_key'], [])
            processed_nodes = self._process_nodes(nodes_data, format_mapping, report)


            relationships_data = validated_structure.get(format_mapping['relationships_key'], [])
            processed_relationships = self._process_relationships(
                relationships_data,
                processed_nodes,
                format_mapping,
                report
            )


            processed_data = {
                'nodes': processed_nodes,
                'relationships': processed_relationships
            }


            report.statistics['total_nodes'] = len(processed_nodes)
            report.statistics['total_relationships'] = len(processed_relationships)

            logger.info(f"数据验证完成: {report.statistics}")

            return processed_data, report

        except Exception as e:
            logger.error(f"数据验证预处理失败: {str(e)}")
            report.add_error(f"数据处理异常: {str(e)}")
            return json_data, report

    def _validate_basic_structure(self, json_data: Any, report: DataValidationReport) -> Optional[Dict[str, Any]]:


        if isinstance(json_data, list):
            logger.info("检测到 Neo4j 导出格式（数组格式），开始转换...")
            converted_data = self._convert_neo4j_export_format(json_data, report)
            if converted_data:
                return converted_data
            else:
                return None

        if not isinstance(json_data, dict):
            return None

        has_nodes = any(key in json_data for key in ['nodes', 'vertices', 'entities'])
        if has_nodes:
            return json_data

        nested_keys = ['graph', 'data', 'kg', 'knowledge_graph', 'network']
        for nested_key in nested_keys:
            if nested_key in json_data and isinstance(json_data[nested_key], dict):
                nested_data = json_data[nested_key]
                has_nested_nodes = any(key in nested_data for key in ['nodes', 'vertices', 'entities'])
                if has_nested_nodes:
                    logger.info(f"检测到嵌套结构: {nested_key}")
                    return nested_data

        report.add_error("数据必须包含节点数组（nodes/vertices/entities），支持顶层或嵌套在 graph/data/kg 对象中，或使用 Neo4j 导出格式")
        return None

        has_relationships = any(key in json_data for key in ['relationships', 'edges', 'links', 'relations'])
        if not has_relationships:

            json_data['relationships'] = []
        return json_data
    def _convert_neo4j_export_format(self, neo4j_data: List[Dict], report: DataValidationReport) -> Optional[Dict[str, Any]]:
        try:
            nodes_dict = {}
            relationships_list = []
            for record in neo4j_data:
                if not isinstance(record, dict):
                    continue

                if 'n' in record and isinstance(record['n'], dict):
                    n_node = record['n']
                    node_id = str(n_node.get('identity', n_node.get('elementId', '')))
                    if node_id and node_id not in nodes_dict:
                        nodes_dict[node_id] = {
                            'id': node_id,
                            'labels': n_node.get('labels', []),
                            'properties': n_node.get('properties', {})
                        }

                if 'm' in record and isinstance(record['m'], dict):
                    m_node = record['m']
                    node_id = str(m_node.get('identity', m_node.get('elementId', '')))
                    if node_id and node_id not in nodes_dict:
                        nodes_dict[node_id] = {
                            'id': node_id,
                            'labels': m_node.get('labels', []),
                            'properties': m_node.get('properties', {})
                        }

                if 'r' in record and isinstance(record['r'], dict):
                    r_rel = record['r']
                    start_id = str(r_rel.get('start', ''))
                    end_id = str(r_rel.get('end', ''))
                    rel_type = r_rel.get('type', 'RELATED_TO')
                    if start_id and end_id:
                        relationships_list.append({
                            'start_node_id': start_id,
                            'end_node_id': end_id,
                            'type': rel_type,
                            'properties': r_rel.get('properties', {})
                        })

            nodes_list = list(nodes_dict.values())
            logger.info(f"Neo4j 格式转换完成: {len(nodes_list)} 个节点, {len(relationships_list)} 个关系")
            return {
                'nodes': nodes_list,
                'relationships': relationships_list
            }
        except Exception as e:
            logger.error(f"Neo4j 格式转换失败: {str(e)}")
            return None

    def _analyze_and_normalize_format(self, json_data: Dict[str, Any], report: DataValidationReport) -> Dict[str, str]:


        format_mapping = {
            'nodes_key': 'nodes',
            'relationships_key': 'relationships',
            'node_labels_key': 'labels',
            'node_type_key': None,
            'rel_start_key': 'start_node_id',
            'rel_end_key': 'end_node_id',
            'rel_type_key': 'type'
        }


        for key in ['nodes', 'vertices', 'entities']:
            if key in json_data:
                format_mapping['nodes_key'] = key
                break


        for key in ['relationships', 'edges', 'links', 'relations']:
            if key in json_data:
                format_mapping['relationships_key'] = key
                break


        nodes_data = json_data.get(format_mapping['nodes_key'], [])
        if nodes_data and len(nodes_data) > 0:
            sample_node = nodes_data[0]

            if 'labels' in sample_node:
                format_mapping['node_labels_key'] = 'labels'
            elif 'label' in sample_node:
                format_mapping['node_type_key'] = 'label'
            elif 'type' in sample_node:
                format_mapping['node_type_key'] = 'type'
            elif 'category' in sample_node:
                format_mapping['node_type_key'] = 'category'
            elif 'class' in sample_node:
                format_mapping['node_type_key'] = 'class'


        relationships_data = json_data.get(format_mapping['relationships_key'], [])
        if relationships_data and len(relationships_data) > 0:
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

        logger.info(f"格式分析完成: {format_mapping}")
        return format_mapping

    def _process_nodes(self, nodes_data: List[Dict[str, Any]], format_mapping: Dict[str, str], report: DataValidationReport) -> List[Dict[str, Any]]:


        processed_nodes = []
        node_id_set = set()

        for i, node_data in enumerate(nodes_data):
            try:
                processed_node = self._process_single_node(node_data, i, format_mapping, report, node_id_set)
                if processed_node:
                    processed_nodes.append(processed_node)

            except Exception as e:
                logger.error(f"处理节点 {i} 时出错: {str(e)}")
                report.add_warning(f"节点 {i} 处理失败，已跳过: {str(e)}")

        return processed_nodes

    def _process_single_node(self, node_data: Dict[str, Any], index: int, format_mapping: Dict[str, str],
                            report: DataValidationReport, node_id_set: set) -> Optional[Dict[str, Any]]:



        original_id = node_data.get('id')
        if not original_id:

            node_id = self.generate_unique_id('node')
            report.add_fix(f"节点 {index} 缺少ID，已生成: {node_id}")
            report.statistics['ids_generated'] += 1
        else:
            node_id = str(original_id)


        if node_id in node_id_set:

            new_id = f"{node_id}_{uuid.uuid4().hex[:6]}"
            report.add_warning(f"节点ID重复: {node_id}，已重命名为: {new_id}")
            node_id = new_id

        node_id_set.add(node_id)


        labels = self._extract_node_labels(node_data, format_mapping, report)
        if not labels:
            labels = ['Entity']
            report.add_fix(f"节点 {node_id} 缺少类型标签，已设置为: Entity")
            report.statistics['labels_added'] += 1


        properties = node_data.get('properties', {})
        if not isinstance(properties, dict):
            properties = {}
            report.add_warning(f"节点 {node_id} 的properties不是字典格式，已重置")


        properties_added = self._ensure_required_properties(node_id, properties, node_data, labels, report)
        if properties_added:
            report.statistics['properties_added'] += properties_added


        processed_node = {
            'id': node_id,
            'labels': labels,
            'properties': properties
        }

        report.statistics['nodes_fixed'] += 1
        return processed_node
    def _extract_node_labels(self, node_data: Dict[str, Any], format_mapping: Dict[str, str], report: DataValidationReport) -> List[str]:

        labels = []

        if format_mapping['node_labels_key'] and format_mapping['node_labels_key'] in node_data:
            labels_value = node_data[format_mapping['node_labels_key']]
            if isinstance(labels_value, list):
                labels = [str(label) for label in labels_value if label]
            elif isinstance(labels_value, str) and labels_value:
                labels = [labels_value]

        elif format_mapping['node_type_key'] and format_mapping['node_type_key'] in node_data:
            type_value = node_data[format_mapping['node_type_key']]
            if isinstance(type_value, list):
                labels = [str(t) for t in type_value if t]
            elif isinstance(type_value, str) and type_value:
                labels = [type_value]
        return labels
    def _ensure_required_properties(self, node_id: str, properties: Dict[str, Any],
                                   node_data: Dict[str, Any], labels: List[str],
                                   report: DataValidationReport) -> int:

        properties_added = 0

        if '_internal_uid' not in properties:
            properties['_internal_uid'] = self.generate_internal_uid()
            properties_added += 1

        if 'name' not in properties or not properties['name']:

            name = self._extract_name_from_node(node_data, properties)
            if not name:

                name = f"{labels[0]}_{node_id.split('_')[-1]}" if labels else node_id
            properties['name'] = name
            properties_added += 1
            report.add_fix(f"节点 {node_id} 缺少name属性，已设置为: {name}")


        return properties_added
    def _extract_name_from_node(self, node_data: Dict[str, Any], properties: Dict[str, Any]) -> Optional[str]:


        name_candidates = [
            properties.get('displayName'),
            properties.get('display_name'),
            properties.get('title'),
            properties.get('label'),
            properties.get('name'),
            node_data.get('name'),
            node_data.get('label'),
            node_data.get('displayName'),
            node_data.get('title')
        ]
        for candidate in name_candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return None
    def _process_relationships(self, relationships_data: List[Dict[str, Any]],
                              processed_nodes: List[Dict[str, Any]],
                              format_mapping: Dict[str, str],
                              report: DataValidationReport) -> List[Dict[str, Any]]:

        processed_relationships = []

        valid_node_ids = {node['id'] for node in processed_nodes}
        for i, rel_data in enumerate(relationships_data):
            try:
                processed_rel = self._process_single_relationship(
                    rel_data, i, valid_node_ids, format_mapping, report
                )
                if processed_rel:
                    processed_relationships.append(processed_rel)
            except Exception as e:
                logger.error(f"处理关系 {i} 时出错: {str(e)}")
                report.add_warning(f"关系 {i} 处理失败，已跳过: {str(e)}")
        return processed_relationships
    def _process_single_relationship(self, rel_data: Dict[str, Any], index: int,
                                    valid_node_ids: set, format_mapping: Dict[str, str],
                                    report: DataValidationReport) -> Optional[Dict[str, Any]]:


        start_id = rel_data.get(format_mapping['rel_start_key'])
        if not start_id:
            report.statistics['invalid_relationships_removed'] += 1
            return None
        start_id = str(start_id)

        end_id = rel_data.get(format_mapping['rel_end_key'])
        if not end_id:
            report.statistics['invalid_relationships_removed'] += 1
            return None
        end_id = str(end_id)

        if start_id not in valid_node_ids:
            report.statistics['invalid_relationships_removed'] += 1
            return None
        if end_id not in valid_node_ids:
            report.statistics['invalid_relationships_removed'] += 1
            return None

        rel_type = rel_data.get(format_mapping['rel_type_key'])
        if not rel_type:
            rel_type = 'RELATED'
            report.add_fix(f"关系 {index} 缺少类型，已设置为: RELATED")
        rel_type = str(rel_type)

        properties = rel_data.get('properties', {})
        if not isinstance(properties, dict):
            properties = {}
            report.add_warning(f"关系 {index} 的properties不是字典格式，已重置")

        if '_internal_uid' not in properties:
            properties['_internal_uid'] = self.generate_internal_uid()
            report.add_fix(f"关系 {index} 添加了内部UID")

        rel_id = rel_data.get('id')
        if not rel_id:
            rel_id = self.generate_unique_id('rel')
        else:
            rel_id = str(rel_id)

        processed_rel = {
            'id': rel_id,
            'type': rel_type,
            'start_node_id': start_id,
            'end_node_id': end_id,
            'properties': properties
        }
        report.statistics['relationships_fixed'] += 1
        return processed_rel

data_validation_service = DataValidationService()