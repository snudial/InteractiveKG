from typing import Dict, List, Any, Set, Tuple, Optional
import logging
import igraph as ig
import leidenalg as la
from collections import defaultdict
from ..models.graph_models import GraphDataModel, NodeModel, RelationshipModel
from .llm_service import LLMService, LLMConfig, LLMProvider
logger = logging.getLogger(__name__)
class HierarchicalAbstractionService:
    def __init__(self, llm_config: Optional[LLMConfig] = None, use_llm: bool = True):
        self.color_palette = [
            "#EF4444", "#F97316", "#F59E0B", "#EAB308", "#84CC16",
            "#22C55E", "#10B981", "#14B8A6", "#06B6D4", "#0EA5E9",
            "#3B82F6", "#6366F1", "#8B5CF6", "#A855F7", "#D946EF",
            "#EC4899", "#F43F5E", "#DC2626", "#EA580C", "#D97706",
            "#CA8A04", "#65A30D", "#16A34A", "#059669", "#0891B2",
            "#0284C7", "#2563EB", "#4F46E5", "#7C3AED", "#9333EA",
            "#C026D3", "#DB2777"
        ]

        self.use_llm = True
        self.llm_service = None




        self.resolution_mapping = {
            0: None,
            1: 2.0,
            2: 1.0,
            3: 0.5
        }

        if not llm_config:

            from ..config.llm_config import get_llm_config
            llm_config = get_llm_config()
        if llm_config:

            forced_config = LLMConfig(
                provider=LLMProvider.OPENAI_GPT4O_MINI,
                model_name='gpt-4o-mini-2024-07-18',
                api_key=llm_config.api_key,
                timeout=llm_config.timeout,
                max_retries=llm_config.max_retries
            )
            self.llm_service = LLMService(forced_config)
            logger.info(f"Initialized LLM service with provider: {LLMProvider.OPENAI_GPT4O_MINI}")
        else:
            logger.error("无法获取LLM配置，层级抽象功能将不可用")

    async def analyze_hierarchical_structure(self, graph_data: GraphDataModel,
                                           abstraction_level: int = 2,
                                           mode: str = "unified",
                                           query_context: str = None) -> Dict[str, Any]:
        if not graph_data.nodes:
            return self._empty_analysis()

        if abstraction_level == 0:
            return self._create_full_view_result(graph_data)

        if abstraction_level < 0 or abstraction_level > 3:
            logger.warning(f"Invalid abstraction level {abstraction_level}, using level 2")
            abstraction_level = 2
        try:
            logger.info(f"Applying Leiden algorithm-based analysis, level {abstraction_level}")

            leiden_result = await self._leiden_community_detection(graph_data, abstraction_level)
            if leiden_result:

                semantic_result = await self._generate_semantic_group_names(
                    leiden_result, graph_data, query_context
                )
                if semantic_result:
                    logger.info(f"Leiden analysis successful with {semantic_result.get('group_count', 0)} groups")
                    return {
                        "abstraction_method": "leiden_community_detection",
                        "abstraction_levels": abstraction_level,
                        "hierarchy": semantic_result["hierarchy"],
                        "community_view": semantic_result.get("community_view", {}),
                        "detailed_view": semantic_result.get("detailed_view", {}),
                        "color_mapping": self._generate_hierarchical_colors(semantic_result["hierarchy"]),
                        "analysis_metadata": {
                            "total_nodes": len(graph_data.nodes),
                            "total_relationships": len(graph_data.relationships),
                            "cognitive_level": f"Level {abstraction_level}",
                            "abstraction_strategy": semantic_result.get("abstraction_strategy", ""),
                            "theoretical_basis": "Leiden algorithm community detection with LLM semantic naming",
                            "group_count": semantic_result.get("group_count", 0),
                            "confidence": semantic_result.get("confidence", 0.9),
                            "source": "leiden_community_detection",
                            "resolution": self.resolution_mapping.get(abstraction_level, 1.0),
                            "view_mode": "two_stage"
                        }
                    }
            logger.warning("Leiden analysis failed, falling back to static methods")
        except Exception as e:
            logger.error(f"Leiden analysis failed: {str(e)}, falling back to static methods")

        logger.info("Using simplified static analysis")
        return self._fallback_static_analysis(graph_data, abstraction_level)
    def _build_igraph_graph(self, graph_data: GraphDataModel) -> ig.Graph:

        g = ig.Graph()

        node_id_to_index = {}
        node_attributes = []

        for i, node in enumerate(graph_data.nodes):
            node_id = node.id
            if node_id is None:

                node_name = node.properties.get('name', 'unknown') if node.properties else 'unknown'
                node_id = f"node_{hash(str(node_name))}"
            node_id_to_index[node_id] = i
            node_attributes.append({
                'id': node_id,
                'labels': node.labels,
                'properties': node.properties
            })

        g.add_vertices(len(node_attributes))

        for i, attrs in enumerate(node_attributes):
            g.vs[i]['id'] = attrs['id']
            g.vs[i]['labels'] = attrs['labels']
            g.vs[i]['properties'] = attrs['properties']

        edges = []
        for rel in graph_data.relationships:
            start_id = rel.start_node_id
            end_id = rel.end_node_id
            if start_id in node_id_to_index and end_id in node_id_to_index:
                start_idx = node_id_to_index[start_id]
                end_idx = node_id_to_index[end_id]
                edges.append((start_idx, end_idx))
        if edges:
            g.add_edges(edges)
        return g
    async def _leiden_community_detection(self, graph_data: GraphDataModel, abstraction_level: int) -> Dict[str, Any]:
        try:

            g = self._build_igraph_graph(graph_data)
            if g.vcount() == 0:
                logger.warning("Graph has no vertices")
                return None

            resolution = self.resolution_mapping.get(abstraction_level, 1.0)

            if g.ecount() == 0:

                partition = la.ModularityVertexPartition(g)

                membership = list(range(g.vcount()))
            else:

                partition = la.find_partition(g, la.RBConfigurationVertexPartition, resolution_parameter=resolution)
                membership = partition.membership

            communities = defaultdict(list)
            for vertex_idx, community_id in enumerate(membership):
                node_id = g.vs[vertex_idx]['id']
                communities[community_id].append(node_id)

            node_to_community = {}
            community_names = {}
            for i, (community_id, node_ids) in enumerate(communities.items()):
                community_name = f"Community_{i}"
                community_names[community_id] = community_name
                for node_id in node_ids:
                    node_to_community[node_id] = {
                        "community_id": community_name,
                        "community_name": community_name
                    }

            inter_community_edges = self._compute_inter_community_edges(
                graph_data, node_to_community, community_names
            )

            community_view = self._build_community_view(
                communities, community_names, inter_community_edges
            )

            detailed_view = self._build_detailed_view(
                graph_data, node_to_community
            )

            label_groups = {}
            for community_id, node_ids in communities.items():
                group_name = community_names[community_id]
                label_groups[group_name] = node_ids
            logger.info(f"Leiden algorithm detected {len(label_groups)} communities")
            return {
                "hierarchy": {
                    "level_0": {
                        "label_groups": label_groups
                    }
                },
                "community_view": community_view,
                "detailed_view": detailed_view,
                "group_count": len(label_groups),
                "resolution": resolution,
                "algorithm": "leiden",
                "node_to_community": node_to_community
            }
        except Exception as e:
            logger.error(f"Leiden community detection failed: {e}")
            return None
    def _compute_inter_community_edges(self, graph_data: GraphDataModel,
                                     node_to_community: Dict[str, Dict[str, str]],
                                     community_names: Dict[int, str]) -> List[Dict[str, Any]]:
        inter_edges = defaultdict(lambda: {"weight": 0.0, "edge_count": 0, "edge_details": []})
        for relationship in graph_data.relationships:
            source_id = relationship.start_node_id
            target_id = relationship.end_node_id

            source_community = node_to_community.get(source_id)
            target_community = node_to_community.get(target_id)
            if source_community and target_community:
                source_comm_id = source_community["community_id"]
                target_comm_id = target_community["community_id"]

                if source_comm_id != target_comm_id:

                    edge_key = tuple(sorted([source_comm_id, target_comm_id]))

                    edge_weight = 1.0
                    if hasattr(relationship, 'properties') and relationship.properties:
                        edge_weight = float(relationship.properties.get('weight', 1.0))
                    inter_edges[edge_key]["weight"] += edge_weight
                    inter_edges[edge_key]["edge_count"] += 1
                    inter_edges[edge_key]["edge_details"].append({
                        "source": source_id,
                        "target": target_id,
                        "type": relationship.type,
                        "weight": edge_weight
                    })

        result = []
        for (comm1, comm2), edge_data in inter_edges.items():
            result.append({
                "source": comm1,
                "target": comm2,
                "weight": edge_data["weight"],
                "edge_count": edge_data["edge_count"],
                "edge_details": edge_data["edge_details"]
            })
        return result
    def _build_community_view(self, communities: Dict[int, List[str]],
                            community_names: Dict[int, str],
                            inter_community_edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        nodes = []
        for community_id, node_ids in communities.items():
            community_name = community_names[community_id]
            nodes.append({
                "id": community_name,
                "name": community_name,
                "description": f"Community containing {len(node_ids)} nodes",
                "node_count": len(node_ids),
                "member_node_ids": node_ids,
                "type": "community"
            })

        edges = []
        for edge in inter_community_edges:
            source_name = community_names.get(edge["source"], str(edge["source"]))
            target_name = community_names.get(edge["target"], str(edge["target"]))
            edges.append({
                "source": source_name,
                "target": target_name,
                "weight": edge["weight"],
                "edge_count": edge["edge_count"],
                "edge_details": edge.get("edge_details", [])
            })
        return {
            "nodes": nodes,
            "edges": edges
        }
    def _build_detailed_view(self, graph_data: GraphDataModel,
                           node_to_community: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        nodes = []
        for node in graph_data.nodes:

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
                node_dict["community_id"] = "unknown"
                node_dict["community_name"] = "Unknown Community"
            nodes.append(node_dict)

        edges = []
        for relationship in graph_data.relationships:
            edges.append({
                "source": relationship.start_node_id,
                "target": relationship.end_node_id,
                "type": relationship.type,
                "properties": relationship.properties
            })
        return {
            "nodes": nodes,
            "edges": edges
        }
    async def _generate_semantic_group_names(self, leiden_result: Dict[str, Any],
                                           graph_data: GraphDataModel,
                                           query_context: str = None) -> Dict[str, Any]:
        if not self.llm_service:
            logger.warning("LLM service not available, using default group names")
            return leiden_result
        try:
            label_groups = leiden_result["hierarchy"]["level_0"]["label_groups"]

            group_descriptions = {}
            for group_name, node_ids in label_groups.items():
                group_info = self._build_group_description(node_ids, graph_data)
                group_descriptions[group_name] = group_info

            prompt = self._build_semantic_naming_prompt(group_descriptions, query_context)

            response = await self.llm_service._call_llm(prompt)
            if response:
                semantic_names = self._parse_semantic_names_response(response)
                if semantic_names:

                    new_label_groups = {}
                    old_to_new_mapping = {}
                    name_counter = {}
                    for old_name, node_ids in label_groups.items():
                        semantic_info = semantic_names.get(old_name, {})
                        base_name = semantic_info.get('name', old_name)
                        new_description = semantic_info.get('description', f"Community containing {len(node_ids)} nodes")

                        if base_name in name_counter:

                            name_counter[base_name] += 1
                            new_name = f"{base_name} {name_counter[base_name]}"
                        else:

                            name_counter[base_name] = 1
                            new_name = base_name
                        new_label_groups[new_name] = node_ids
                        old_to_new_mapping[old_name] = {
                            'name': new_name,
                            'description': new_description
                        }

                    updated_result = leiden_result.copy()
                    updated_result["hierarchy"]["level_0"]["label_groups"] = new_label_groups
                    updated_result["abstraction_strategy"] = "Leiden community detection with LLM semantic naming"
                    updated_result["confidence"] = 0.9

                    if "community_view" in updated_result:
                        for node in updated_result["community_view"]["nodes"]:
                            old_id = node["id"]
                            if old_id in old_to_new_mapping:
                                semantic_info = old_to_new_mapping[old_id]
                                node["name"] = semantic_info["name"]
                                node["description"] = semantic_info["description"]
                                node["id"] = semantic_info["name"]


                        for edge in updated_result["community_view"]["edges"]:

                            for old_name, new_info in old_to_new_mapping.items():
                                if edge["source"] == old_name:
                                    edge["source"] = new_info["name"]
                                if edge["target"] == old_name:
                                    edge["target"] = new_info["name"]

                    if "detailed_view" in updated_result:
                        for node in updated_result["detailed_view"]["nodes"]:
                            old_community_id = node.get("community_id")
                            if old_community_id in old_to_new_mapping:
                                semantic_info = old_to_new_mapping[old_community_id]
                                node["community_id"] = semantic_info["name"]
                                node["community_name"] = semantic_info["name"]
                    logger.info(f"Successfully generated semantic names for {len(semantic_names)} groups")
                    return updated_result
            logger.warning("Failed to generate semantic names, using default names")
            return leiden_result
        except Exception as e:
            logger.error(f"Semantic name generation failed: {e}")
            return leiden_result
    def _build_group_description(self, node_ids: List[str], graph_data: GraphDataModel) -> Dict[str, Any]:
        node_map = {node.id: node for node in graph_data.nodes}

        labels = []
        properties = []
        names = []
        for node_id in node_ids:
            if node_id in node_map:
                node = node_map[node_id]
                labels.extend(node.labels)
                if node.properties:
                    properties.append(node.properties)
                    if 'name' in node.properties:
                        names.append(node.properties['name'])

        label_counts = {}
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1

        common_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        return {
            "node_count": len(node_ids),
            "common_labels": [label for label, _ in common_labels],
            "sample_names": names[:5],
            "total_properties": len(properties)
        }
    def _build_semantic_naming_prompt(self, group_descriptions: Dict[str, Dict], query_context: str = None) -> str:
        context_info = f"Query context: {query_context}" if query_context else "No specific query context provided"
        group_info_text = ""
        for group_name, info in group_descriptions.items():
            group_info_text += f"""
{group_name}:
- Node count: {info['node_count']}
- Common labels: {', '.join(info['common_labels'])}
- Sample names: {', '.join(info['sample_names'])}
"""
        prompt = f"""{context_info}
Group Information:
{group_info_text}
Requirements:
Please respond in JSON format:
{{
    "Community_0": {{
        "name": "Semantic Name 1",
        "description": "Brief description of what this community represents"
    }},
    "Community_1": {{
        "name": "Semantic Name 2",
        "description": "Brief description of what this community represents"
    }},
    ...
}}
"""
        return prompt
    def _parse_semantic_names_response(self, response: str) -> Dict[str, Dict[str, str]]:
        try:
            import json

            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            semantic_names = json.loads(response)
            if isinstance(semantic_names, dict):
                logger.info(f"Successfully parsed {len(semantic_names)} semantic names")
                return semantic_names
            else:
                logger.warning("LLM response is not a valid dictionary")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing semantic names: {e}")
            return {}
    def _fallback_static_analysis(self, graph_data: GraphDataModel, abstraction_level: int) -> Dict[str, Any]:
        基于节点标签进行简单分组

        if abstraction_level == 0:
            return self._create_full_view_result(graph_data)

        label_groups = defaultdict(list)
        for node in graph_data.nodes:
            primary_label = node.labels[0] if node.labels else "Unknown"
            label_groups[primary_label].append(node.id)

        target_groups = min(len(label_groups), abstraction_level + 2)

        if len(label_groups) > target_groups:

            sorted_groups = sorted(label_groups.items(), key=lambda x: len(x[1]), reverse=True)

            current_groups = {}
            merged_nodes = []
            for i, (label, nodes) in enumerate(sorted_groups):
                if i < target_groups - 1:
                    current_groups[label] = nodes
                else:
                    merged_nodes.extend(nodes)
            if merged_nodes:
                current_groups["Other"] = merged_nodes
        else:
            current_groups = dict(label_groups)
        return {
            "abstraction_method": "static_label_fallback",
            "abstraction_levels": abstraction_level,
            "hierarchy": {"level_0": {"label_groups": current_groups}},
            "color_mapping": self._generate_hierarchical_colors({"level_0": {"label_groups": current_groups}}),
            "analysis_metadata": {
                "total_nodes": len(graph_data.nodes),
                "total_relationships": len(graph_data.relationships),
                "cognitive_level": f"Level {abstraction_level}",
                "group_count": len(current_groups),
                "source": "static_label_fallback"
            }
        }

    def _generate_hierarchical_colors(self, hierarchy: Dict[str, Any]) -> Dict[str, str]:

        color_mapping = {}
        color_index = 0

        if "level_0" in hierarchy and "label_groups" in hierarchy["level_0"]:
            for group_name in hierarchy["level_0"]["label_groups"].keys():
                color_mapping[group_name] = self.color_palette[color_index % len(self.color_palette)]
                color_index += 1
                logger.info(f"🎨 Assigned color {self.color_palette[color_index - 1]} to community: {group_name}")

        if "community_overlay" in hierarchy:
            for community_id in hierarchy["community_overlay"].keys():
                color_mapping[f"Community_{community_id}"] = self.color_palette[color_index % len(self.color_palette)]
                color_index += 1

        if "structural_clusters" in hierarchy:
            for cluster_id in hierarchy["structural_clusters"].keys():
                color_mapping[f"Cluster_{cluster_id}"] = self.color_palette[color_index % len(self.color_palette)]
                color_index += 1
        logger.info(f"🎨 Generated color mapping with {len(color_mapping)} entries: {list(color_mapping.keys())}")
        return color_mapping
    def _create_full_view_result(self, graph_data: GraphDataModel) -> Dict[str, Any]:

        label_groups = {}
        all_node_ids = []
        for node in graph_data.nodes:
            all_node_ids.append(node.id)

            primary_label = node.labels[0] if node.labels else "Unknown"
            if primary_label not in label_groups:
                label_groups[primary_label] = []
            label_groups[primary_label].append(node.id)

        color_mapping = self._generate_label_colors(list(label_groups.keys()))

        group_stats = {label: len(nodes) for label, nodes in label_groups.items()}
        return {
            "abstraction_method": "label_based_grouping",
            "abstraction_levels": 0,
            "hierarchy": {
                "level_0": {
                    "label_groups": label_groups
                }
            },
            "color_mapping": color_mapping,
            "analysis_metadata": {
                "total_nodes": len(graph_data.nodes),
                "total_relationships": len(graph_data.relationships),
                "cognitive_level": "Full View - Label Grouped",
                "abstraction_strategy": "Group and color nodes by labels, displaying all original nodes and relationships",
                "theoretical_basis": "Label grouping mode: Visual grouping based on node types while maintaining complete graph structure",
                "group_count": len(label_groups),
                "group_distribution": group_stats,
                "confidence": 1.0,
                "visible_nodes": all_node_ids,
                "source": "full_view_label_grouping"
            }
        }
    def _generate_label_colors(self, labels: List[str]) -> Dict[str, str]:
        color_palette = [
            "#10B981",
            "#3B82F6",
            "#F59E0B",
            "#EF4444",
            "#8B5CF6",
            "#06B6D4",
            "#F97316",
            "#84CC16",
            "#EC4899",
            "#6366F1",
            "#14B8A6",
            "#F59E0B",
        ]
        color_mapping = {}
        for i, label in enumerate(labels):
            color_mapping[label] = color_palette[i % len(color_palette)]
        return color_mapping
    def _empty_analysis(self) -> Dict[str, Any]:

        return {
            "abstraction_method": "empty",
            "abstraction_levels": 1,
            "hierarchy": {"level_0": {"label_groups": {}}},
            "color_mapping": {},
            "analysis_metadata": {
                "total_nodes": 0,
                "total_relationships": 0,
                "source": "empty_graph"
            }
        }