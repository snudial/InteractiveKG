Designed to handle large-scale data that exceeds traditional LLM processing capabilities.
from typing import Dict, List, Any, Set, Tuple, Optional
import math
import networkx as nx
from collections import defaultdict, Counter
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from ..models.graph_models import GraphDataModel, NodeModel, RelationshipModel
from .llm_service import LLMService, LLMConfig, LLMProvider
import logging
logger = logging.getLogger(__name__)
class HierarchicalAbstractionService:
    Advanced hierarchical abstraction service for complex knowledge graphs.
    Implements multiple abstraction algorithms:
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
                                           abstraction_level: int = 3,
                                           mode: str = "unified",
                                           query_context: str = None) -> Dict[str, Any]:
            query_context: Optional context for intelligent analysis
        Returns:
            Dictionary containing hierarchical analysis results
        if not graph_data.nodes:
            return self._empty_analysis()

        if abstraction_level == 0:
            return self._create_full_view_result(graph_data)

        if not self.use_llm or not self.llm_service:
            raise ValueError(
                "LLM service is not available. Hierarchical abstraction requires LLM functionality. "
                "Please ensure LLM is properly configured and enabled. Only GPT-4o-mini model is supported."
            )
        try:
            logger.info(f"Applying unified cognitive hierarchy analysis, level {abstraction_level}")
            llm_result = await self._unified_cognitive_abstraction(
                graph_data, abstraction_level, query_context
            )
            if llm_result and llm_result.get("confidence", 0) > 0.7:
                logger.info(f"Unified analysis successful with confidence {llm_result.get('confidence')}")
                return {
                    "abstraction_method": "unified_cognitive_hierarchy",
                    "abstraction_levels": abstraction_level,
                    "hierarchy": llm_result["hierarchy"],
                    "color_mapping": self._generate_hierarchical_colors(llm_result["hierarchy"]),
                    "analysis_metadata": {
                        "total_nodes": len(graph_data.nodes),
                        "total_relationships": len(graph_data.relationships),
                        "cognitive_level": llm_result.get("cognitive_level", "unknown"),
                        "abstraction_strategy": llm_result.get("abstraction_strategy", ""),
                        "theoretical_basis": llm_result.get("theoretical_basis", ""),
                        "group_count": llm_result.get("group_count", 0),
                        "confidence": llm_result.get("confidence", 0),
                        "source": "unified_cognitive_hierarchy"
                    }
                }
            else:
                confidence = llm_result.get("confidence", 0) if llm_result else 0
                raise ValueError(
                    f"LLM-based abstraction analysis failed with low confidence ({confidence}). "
                    "Unable to generate reliable hierarchical abstraction. "
                    "Please check the graph data quality or try a different abstraction level."
                )
        except Exception as e:
            logger.error(f"Unified cognitive hierarchy analysis failed: {str(e)}")
            raise ValueError(
                f"Hierarchical abstraction failed: {str(e)}. "
                "Only LLM-based unified cognitive hierarchy method is supported. "
                "Please ensure GPT-4o-mini model is properly configured."
            )

    def _build_networkx_graph(self, graph_data: GraphDataModel) -> nx.Graph:

        G = nx.Graph()

        for node in graph_data.nodes:

            node_id = node.id
            if node_id is None:

                node_name = node.properties.get('name', 'unknown') if node.properties else 'unknown'
                node_id = f"node_{hash(str(node_name))}"
            G.add_node(node_id,
                      labels=node.labels,
                      properties=node.properties)

        for rel in graph_data.relationships:

            start_id = rel.start_node_id
            end_id = rel.end_node_id
            if start_id is None or end_id is None:
                continue
            G.add_edge(start_id, end_id,
                      type=rel.type,
                      properties=rel.properties)
        return G



        Apply dynamic community detection with abstraction-level-aware grouping.
        Uses Louvain algorithm with post-processing for target group counts.

        if G.number_of_edges() == 0:
            return self._fallback_community_detection(G, abstraction_level)
        try:
            import community as community_louvain
        except ImportError:

            return self._fallback_community_detection(G, abstraction_level)
        hierarchy = {}

        if G.number_of_edges() == 0:

            components = list(nx.connected_components(G))
            communities = {i: list(component) for i, component in enumerate(components)}
            modularity_score = 0.0
        else:

            partition = community_louvain.best_partition(G)

            communities = defaultdict(list)
            for node, community_id in partition.items():
                communities[community_id].append(node)
            communities = dict(communities)

            try:
                modularity_score = community_louvain.modularity(partition, G)
            except:
                modularity_score = 0.0

        final_communities = self._apply_dynamic_community_grouping(
            communities, G, abstraction_level
        )
        hierarchy["level_0"] = {
            "communities": final_communities,
            "modularity": modularity_score
        }
        return hierarchy
    def _apply_dynamic_community_grouping(self, communities: Dict[int, List[str]],
                                        G: nx.Graph, abstraction_level: int) -> Dict[int, List[str]]:
        Apply dynamic community grouping based on abstraction level.
        Level 1: Keep original communities (may be 10-15)
        Level 2-3: Merge smaller communities (target 7-9)
        Level 4-5: Aggressive merging (target 3-5)
        if abstraction_level == 1:
            return communities

        if abstraction_level <= 3:
            target_count = max(7, min(9, len(communities)))
        else:
            target_count = max(3, min(5, len(communities)))
        if len(communities) <= target_count:
            return communities

        community_scores = []
        for comm_id, nodes in communities.items():

            size_score = len(nodes)

            internal_edges = 0
            for node1 in nodes:
                for node2 in nodes:
                    if node1 != node2 and G.has_edge(node1, node2):
                        internal_edges += 1
            connectivity_score = internal_edges / max(1, len(nodes) * (len(nodes) - 1))
            total_score = size_score * 0.7 + connectivity_score * 0.3
            community_scores.append((comm_id, nodes, total_score))

        community_scores.sort(key=lambda x: x[2], reverse=True)

        final_communities = {}
        for i, (comm_id, nodes, score) in enumerate(community_scores):
            if i < target_count - 1:
                final_communities[comm_id] = nodes
            else:

                if 'merged' not in final_communities:
                    final_communities['merged'] = []
                final_communities['merged'].extend(nodes)
        return final_communities
    def _structural_similarity_hierarchy(self, graph_data: GraphDataModel, abstraction_level: int) -> Dict[str, Any]:
        Create dynamic hierarchy based on structural similarity with abstraction-level-aware clustering.
        Uses degree centrality, clustering coefficient, and betweenness centrality.
        G = self._build_networkx_graph(graph_data)

        degree_centrality = nx.degree_centrality(G)
        clustering_coeff = nx.clustering(G)
        try:
            betweenness_centrality = nx.betweenness_centrality(G)
        except:
            betweenness_centrality = {node: 0 for node in G.nodes()}

        feature_matrix = []
        node_ids = list(G.nodes())
        for node in node_ids:
            feature_vector = [
                degree_centrality.get(node, 0),
                clustering_coeff.get(node, 0),
                betweenness_centrality.get(node, 0)
            ]
            feature_matrix.append(feature_vector)

        target_clusters = self._calculate_target_cluster_count(len(node_ids), abstraction_level)

        if len(feature_matrix) > 1:
            clustering = AgglomerativeClustering(
                n_clusters=min(len(node_ids), target_clusters),
                linkage='ward'
            )
            cluster_labels = clustering.fit_predict(feature_matrix)

            cluster_labels = [int(label) for label in cluster_labels]
        else:
            cluster_labels = [0] * len(node_ids)

        hierarchy = {}
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            clusters[int(label)].append(node_ids[i])
        hierarchy["level_0"] = {"clusters": dict(clusters)}
        return hierarchy
    def _calculate_target_cluster_count(self, total_nodes: int, abstraction_level: int) -> int:

        if abstraction_level == 1:

            return min(15, max(8, total_nodes // 3))
        elif abstraction_level <= 3:

            return min(9, max(7, total_nodes // 5))
        else:

            return min(5, max(3, total_nodes // 8))

    def _semantic_property_hierarchy(self, graph_data: GraphDataModel, levels: int) -> Dict[str, Any]:
        Create dynamic hierarchy based on semantic properties and node types.
        Implements progressive grouping based on abstraction level.
        hierarchy = {}

        label_groups = defaultdict(list)
        for node in graph_data.nodes:
            primary_label = node.labels[0] if node.labels else "Unknown"
            label_groups[primary_label].append(node.id)

        final_groups = self._apply_dynamic_semantic_grouping(
            dict(label_groups), graph_data, levels
        )
        hierarchy["level_0"] = {"label_groups": final_groups}
        return hierarchy

    def _apply_dynamic_semantic_grouping(self, label_groups: Dict[str, List[str]],
                                        graph_data: GraphDataModel, abstraction_level: int) -> Dict[str, List[str]]:
        Apply dynamic grouping based on abstraction level.
        Level 1: Keep all original groups (13-15 groups)
        Level 2-3: Merge similar groups (7-9 groups)
        Level 4-5: Aggressive merging (3-5 groups)
        if abstraction_level == 1:

            return label_groups

        merge_rules = {

            'biological': ['Protein', 'Gene', 'Enzyme', 'Molecule', 'Compound'],

            'medical': ['Disease', 'Symptom', 'Treatment', 'Drug', 'Therapy'],

            'anatomical': ['Tissue', 'Organ', 'Cell', 'Anatomy'],

            'research': ['Publication', 'Study', 'Research', 'Paper', 'Article'],

            'other': ['Unknown', 'Misc', 'General']
        }

        if abstraction_level <= 3:

            target_groups = max(7, min(9, len(label_groups)))
            return self._merge_semantic_groups(label_groups, merge_rules, target_groups, 'medium')
        else:

            target_groups = max(3, min(5, len(label_groups)))
            return self._merge_semantic_groups(label_groups, merge_rules, target_groups, 'high')
    def _merge_semantic_groups(self, label_groups: Dict[str, List[str]],
                             merge_rules: Dict[str, List[str]],
                             target_groups: int, merge_level: str) -> Dict[str, List[str]]:

        merged_groups = {}
        used_labels = set()

        for category, labels in merge_rules.items():
            category_nodes = []
            category_labels = []
            for label in labels:
                if label in label_groups and label not in used_labels:
                    category_nodes.extend(label_groups[label])
                    category_labels.append(label)
                    used_labels.add(label)
            if category_nodes:

                if len(category_labels) == 1:
                    group_name = category_labels[0]
                else:
                    group_name = f"{category.title()}_Group"
                merged_groups[group_name] = category_nodes

        for label, nodes in label_groups.items():
            if label not in used_labels:
                merged_groups[label] = nodes

        if len(merged_groups) > target_groups and merge_level == 'high':
            merged_groups = self._aggressive_merge(merged_groups, target_groups)
        return merged_groups
    def _aggressive_merge(self, groups: Dict[str, List[str]], target_count: int) -> Dict[str, List[str]]:

        if len(groups) <= target_count:
            return groups

        sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]))
        final_groups = {}
        main_groups = sorted_groups[-target_count:]
        small_groups = sorted_groups[:-target_count]

        for name, nodes in main_groups:
            final_groups[name] = nodes

        if small_groups:
            other_nodes = []
            for name, nodes in small_groups:
                other_nodes.extend(nodes)
            final_groups["Other_Group"] = other_nodes
        return final_groups
    def _group_by_property_patterns(self, nodes: List[NodeModel]) -> Dict[str, List[str]]:

        property_patterns = defaultdict(list)
        for node in nodes:

            prop_keys = sorted(node.properties.keys())
            pattern_key = "|".join(prop_keys)
            property_patterns[pattern_key].append(node.id)
        return dict(property_patterns)

    def _hybrid_abstraction(self, graph_data: GraphDataModel,
                          community_hierarchy: Dict,
                          structural_hierarchy: Dict,
                          semantic_hierarchy: Dict) -> Dict[str, Any]:
        Combine multiple hierarchical approaches for optimal abstraction.

        base_hierarchy = semantic_hierarchy.copy()


        if "level_0" in community_hierarchy:
            communities = community_hierarchy["level_0"]["communities"]
            base_hierarchy["community_overlay"] = communities


        if "level_0" in structural_hierarchy:
            clusters = structural_hierarchy["level_0"]["clusters"]
            base_hierarchy["structural_clusters"] = clusters

        return base_hierarchy

    def _generate_hierarchical_colors(self, hierarchy: Dict[str, Any]) -> Dict[str, str]:

        color_mapping = {}
        color_index = 0

        if "level_0" in hierarchy and "label_groups" in hierarchy["level_0"]:
            for group_name in hierarchy["level_0"]["label_groups"].keys():
                color_mapping[group_name] = self.color_palette[color_index % len(self.color_palette)]
                color_index += 1

        if "community_overlay" in hierarchy:
            for community_id in hierarchy["community_overlay"].keys():
                color_mapping[f"Community_{community_id}"] = self.color_palette[color_index % len(self.color_palette)]
                color_index += 1

        if "structural_clusters" in hierarchy:
            for cluster_id in hierarchy["structural_clusters"].keys():
                color_mapping[f"Cluster_{cluster_id}"] = self.color_palette[color_index % len(self.color_palette)]
                color_index += 1
        return color_mapping
    def _convert_llm_result_to_hierarchy(self, llm_result: Dict[str, Any], mode: str) -> Dict[str, Any]:

        hierarchy = {}

        if mode == "semantic":

            label_groups = {}
            for group_name, group_data in llm_result["groups"].items():
                label_groups[group_name] = group_data["nodes"]
            hierarchy["level_0"] = {"label_groups": label_groups}
        elif mode == "community":

            community_overlay = {}
            for i, (group_name, group_data) in enumerate(llm_result["groups"].items()):
                community_overlay[i] = group_data["nodes"]
            hierarchy["community_overlay"] = community_overlay
        elif mode == "structural":

            structural_clusters = {}
            for i, (group_name, group_data) in enumerate(llm_result["groups"].items()):
                structural_clusters[i] = group_data["nodes"]
            hierarchy["structural_clusters"] = structural_clusters
        return hierarchy
    def _calculate_hierarchy_statistics(self, hierarchy: Dict[str, Any]) -> Dict[str, Any]:

        stats = {
            "total_levels": len([k for k in hierarchy.keys() if k.startswith("level_")]),
            "groups_per_level": {}
        }

        for level_key, level_data in hierarchy.items():
            if level_key.startswith("level_"):
                if "label_groups" in level_data:
                    stats["groups_per_level"][level_key] = len(level_data["label_groups"])
                elif "communities" in level_data:
                    stats["groups_per_level"][level_key] = len(level_data["communities"])
                elif "clusters" in level_data:
                    stats["groups_per_level"][level_key] = len(level_data["clusters"])

        return stats

    def _calculate_complexity_score(self, graph_data: GraphDataModel, hierarchy: Dict[str, Any]) -> float:
        Calculate complexity score to demonstrate need for interactive visualization.
        Higher scores indicate data that exceeds traditional LLM processing capabilities.
        node_count = len(graph_data.nodes)
        edge_count = len(graph_data.relationships)


        structural_complexity = (node_count * edge_count) / 1000


        unique_labels = set()
        for node in graph_data.nodes:
            unique_labels.update(node.labels)
        label_diversity = len(unique_labels)


        total_properties = sum(len(node.properties) for node in graph_data.nodes)
        property_complexity = total_properties / max(node_count, 1)


        hierarchy_levels = len([k for k in hierarchy.keys() if k.startswith("level_")])
        hierarchy_complexity = hierarchy_levels * 2


        complexity_score = (
            structural_complexity * 0.4 +
            label_diversity * 0.2 +
            property_complexity * 0.2 +
            hierarchy_complexity * 0.2
        )

        return min(complexity_score, 100.0)

    def _empty_analysis(self) -> Dict[str, Any]:

        return {
            "abstraction_method": "none",
            "abstraction_levels": 0,
            "hierarchy": {},
            "color_mapping": {},
            "statistics": {},
            "complexity_score": 0.0
        }

    def _fallback_community_detection(self, G: nx.Graph, levels: int) -> Dict[str, Any]:

        components = list(nx.connected_components(G))
        hierarchy = {
            "level_0": {
                "communities": {i: list(component) for i, component in enumerate(components)},
                "modularity": 0.0
            }
        }
        return hierarchy

    def _create_community_graph(self, G: nx.Graph, communities: Dict) -> nx.Graph:

        new_graph = nx.Graph()


        for comm_id in communities.keys():
            new_graph.add_node(f"community_{comm_id}")


        for edge in G.edges():
            node1, node2 = edge
            comm1 = None
            comm2 = None

            for comm_id, nodes in communities.items():
                if node1 in nodes:
                    comm1 = f"community_{comm_id}"
                if node2 in nodes:
                    comm2 = f"community_{comm_id}"

            if comm1 and comm2 and comm1 != comm2:
                new_graph.add_edge(comm1, comm2)

        return new_graph
    async def _unified_cognitive_abstraction(self, graph_data: GraphDataModel,
                                            abstraction_level: int,
                                            query_context: str = None) -> Dict[str, Any]:
        统一的认知层次抽象分析
        基于认知层次理论，提供一致的、可预测的抽象结果
        Args:
        try:

            if abstraction_level == 0:
                return self._create_full_view_result(graph_data)

            target_groups = self._calculate_cognitive_groups(len(graph_data.nodes), abstraction_level)

            graph_description = self._build_graph_description(graph_data)

            prompt = self._build_unified_cognitive_prompt(
                graph_description, abstraction_level, target_groups, query_context
            )

            if self.llm_service:
                response = await self.llm_service._call_llm(prompt)
                if response:
                    return self._parse_cognitive_response(response, graph_data, target_groups)
            return None
        except Exception as e:
            logger.error(f"统一认知抽象分析失败: {e}")
            return self._fallback_static_analysis(graph_data, abstraction_level)
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
                "abstraction_level": 0,
                "source": "full_view_label_grouping"
            }
        }
    def _generate_label_colors(self, labels: List[str]) -> Dict[str, str]:
        为不同的标签生成不同的颜色

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
            "#F472B6",
            "#A855F7",
            "#22D3EE",
            "#FDE047",
            "#FB7185",
            "#4ADE80",
            "#60A5FA",
            "#FBBF24",
            "#F87171"
        ]
        color_mapping = {}
        for i, label in enumerate(labels):

            color_mapping[label] = color_palette[i % len(color_palette)]
        return color_mapping
    def _build_graph_description(self, graph_data: GraphDataModel) -> str:

        description_parts = []

        description_parts.append(f"图数据概览:")
        description_parts.append(f"- 节点总数: {len(graph_data.nodes)}")
        description_parts.append(f"- 关系总数: {len(graph_data.relationships)}")

        description_parts.append(f"\n节点详细信息:")
        for i, node in enumerate(graph_data.nodes, 1):
            node_info = f"{i}. 节点ID: {node.id}"
            if node.labels:
                node_info += f", 标签: {', '.join(node.labels)}"
            if node.properties:
                key_props = []
                for key, value in node.properties.items():
                    if key in ['name', 'description', 'value', 'type']:
                        key_props.append(f"{key}: {value}")
                if key_props:
                    node_info += f", 属性: {', '.join(key_props)}"
            description_parts.append(node_info)

        description_parts.append(f"\n关系详细信息:")
        for i, rel in enumerate(graph_data.relationships, 1):
            rel_info = f"{i}. {rel.start_node_id} --[{rel.type}]--> {rel.end_node_id}"
            if rel.properties:
                key_props = []
                for key, value in rel.properties.items():
                    key_props.append(f"{key}: {value}")
                if key_props:
                    rel_info += f" (属性: {', '.join(key_props)})"
            description_parts.append(rel_info)
        return "\n".join(description_parts)
    def _calculate_cognitive_groups(self, total_nodes: int, abstraction_level: int) -> int:
        基于认知层次理论计算目标分组数量
        认知层次理论：人类处理信息的认知容量有限，不同抽象级别对应不同的分组粒度
        - Level 0 (完整视图): 显示所有原始节点，不进行分组 (1组)
        - Level 1 (具体层): 关注具体细节，分组数量较多 (8-12组)
        - Level 2 (功能层): 按功能分组，中等数量 (6-8组)
        - Level 3 (概念层): 按概念分组，适中数量 (4-6组)
        - Level 4 (抽象层): 高度抽象，较少分组 (3-4组)
        - Level 5 (整体层): 最高抽象，最少分组 (2-3组)

        if abstraction_level == 0:
            return 1

        base_groups = {
            1: (8, 12),
            2: (6, 8),
            3: (4, 6),
            4: (3, 4),
            5: (2, 3)
        }
        min_groups, max_groups = base_groups.get(abstraction_level, (3, 6))

        if total_nodes <= 5:
            return min(total_nodes, max_groups)
        elif total_nodes <= 15:
            return min(max_groups, max(min_groups, total_nodes // 3))
        else:
            return min(max_groups, max(min_groups, int(total_nodes ** 0.5)))
    def _build_unified_cognitive_prompt(self, graph_description: str,
                                      abstraction_level: int,
                                      target_groups: int,
                                      query_context: str = None) -> str:


        cognitive_levels = {
            0: {
                "name": "Full View",
                "description": "Display the complete original knowledge graph without any abstraction processing",
                "strategy": "Maintain all original nodes and relationships, do not apply any grouping or simplification algorithms"
            },
            1: {
                "name": "Concrete Level",
                "description": "Focus on specific details and individual elements, maintain fine-grained grouping",
                "strategy": "Group according to specific attributes and direct functions of nodes, maintain detailed distinction"
            },
            2: {
                "name": "Functional Level",
                "description": "Group by function and role, focus on practical uses of elements",
                "strategy": "Group nodes with similar functions or roles together, emphasize practicality"
            },
            3: {
                "name": "Conceptual Level",
                "description": "Group by concepts and semantic similarity, focus on abstract concepts",
                "strategy": "Group based on semantic similarity and conceptual relationships, emphasize logical relationships of concepts"
            },
            4: {
                "name": "Abstract Level",
                "description": "Highly abstract grouping, focus on core categories and main concepts",
                "strategy": "Merge related concepts into larger abstract categories, emphasize overall structure"
            },
            5: {
                "name": "Holistic Level",
                "description": "Highest level abstraction, focus on overall structure and core elements",
                "strategy": "Only retain the most core conceptual groups, emphasize holism and simplicity"
            }
        }
        current_level = cognitive_levels[abstraction_level]
【Cognitive Hierarchy Theory Foundation】
Human cognition follows hierarchical principles when processing information, with different abstraction levels corresponding to different cognitive granularities and grouping strategies.
【Current Cognitive Level】
- Level Name: {current_level["name"]}
- Level Description: {current_level["description"]}
- Grouping Strategy: {current_level["strategy"]}
- Target Group Count: {target_groups} groups
【Strict Constraints】
1. **Group Count Constraint**: Must strictly produce exactly {target_groups} groups, no more, no less
2. **Cognitive Consistency**: Grouping method must conform to current cognitive level characteristics
3. **Completeness**: All nodes must be assigned to some group
4. **Balance**: Group node counts should be relatively balanced, avoiding extreme imbalance
【Query Context】
{query_context or "No specific query context, using general grouping strategy"}
【Graph Data Information】
{graph_description}
【Output Requirements】
Please strictly follow the JSON format below, ensuring exactly {target_groups} groups are produced:
{{
    "cognitive_level": "{current_level["name"]}",
    "abstraction_strategy": "Specific grouping strategy description",
    "theoretical_basis": "Cognitive hierarchy theory basis explanation",
    "group_count": {target_groups},
    "hierarchy": {{
        "level_0": {{
            "label_groups": {{
                "Group1": ["node_id1", "node_id2", ...],
                "Group2": ["node_id3", "node_id4", ...],
                ...
            }}
        }}
    }},
    "group_explanations": {{
        "Group1": "Cognitive meaning and grouping basis of this group",
        "Group2": "Cognitive meaning and grouping basis of this group",
        ...
    }},
    "confidence": 0.95
}}
        return prompt
    def _parse_cognitive_response(self, response: str, graph_data: GraphDataModel, target_groups: int) -> Dict[str, Any]:

        try:
            import json

            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            parsed = json.loads(response)

            required_fields = ['cognitive_level', 'abstraction_strategy', 'hierarchy', 'group_count', 'confidence']
            for field in required_fields:
                if field not in parsed:
                    logger.warning(f"认知响应缺少必要字段: {field}")
                    return None

            actual_groups = len(parsed['hierarchy']['level_0']['label_groups'])
            if actual_groups != target_groups:
                logger.warning(f"分组数量不匹配: 期望{target_groups}，实际{actual_groups}")

                parsed = self._adjust_group_count(parsed, graph_data, target_groups)

            all_node_ids = {node.id for node in graph_data.nodes}
            hierarchy = parsed['hierarchy']
            if 'level_0' in hierarchy and 'label_groups' in hierarchy['level_0']:
                for group_name, node_ids in hierarchy['level_0']['label_groups'].items():
                    valid_node_ids = [nid for nid in node_ids if nid in all_node_ids]
                    hierarchy['level_0']['label_groups'][group_name] = valid_node_ids

            grouped_nodes = set()
            for node_ids in hierarchy['level_0']['label_groups'].values():
                grouped_nodes.update(node_ids)
            ungrouped_nodes = all_node_ids - grouped_nodes
            if ungrouped_nodes:

                min_group = min(hierarchy['level_0']['label_groups'].items(), key=lambda x: len(x[1]))
                hierarchy['level_0']['label_groups'][min_group[0]].extend(list(ungrouped_nodes))
                logger.info(f"将{len(ungrouped_nodes)}个未分组节点添加到组'{min_group[0]}'")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"解析认知响应JSON失败: {e}")
            return None
        except Exception as e:
            logger.error(f"处理认知响应失败: {e}")
            return None
    def _adjust_group_count(self, parsed: Dict[str, Any], graph_data: GraphDataModel, target_groups: int) -> Dict[str, Any]:

        try:
            current_groups = parsed['hierarchy']['level_0']['label_groups']
            current_count = len(current_groups)
            if current_count > target_groups:

                while len(current_groups) > target_groups:

                    sorted_groups = sorted(current_groups.items(), key=lambda x: len(x[1]))
                    smallest_group = sorted_groups[0]
                    second_smallest = sorted_groups[1]

                    current_groups[second_smallest[0]].extend(smallest_group[1])
                    del current_groups[smallest_group[0]]
            elif current_count < target_groups:

                while len(current_groups) < target_groups:

                    largest_group = max(current_groups.items(), key=lambda x: len(x[1]))
                    if len(largest_group[1]) < 2:
                        break

                    nodes = largest_group[1]
                    mid = len(nodes) // 2
                    new_group_name = f"{largest_group[0]}_分组{len(current_groups)}"
                    current_groups[largest_group[0]] = nodes[:mid]
                    current_groups[new_group_name] = nodes[mid:]
            parsed['group_count'] = len(current_groups)
            return parsed
        except Exception as e:
            logger.error(f"调整分组数量失败: {e}")
            return parsed
    def _return_original_data(self, graph_data: GraphDataModel) -> Dict[str, Any]:


        all_node_ids = [node.id for node in graph_data.nodes]
        return {
            "abstraction_method": "original_data",
            "abstraction_levels": 0,
            "hierarchy": {"level_0": {"label_groups": {"Original Data": all_node_ids}}},
            "color_mapping": {"Original Data": self.color_palette[0]},
            "analysis_metadata": {
                "total_nodes": len(graph_data.nodes),
                "total_relationships": len(graph_data.relationships),
                "cognitive_level": "Level 0 - Original Data",
                "group_count": 1,
                "source": "original_data_no_abstraction"
            }
        }
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
    def _generate_hierarchical_colors(self, hierarchy: Dict[str, Any]) -> Dict[str, str]:

        color_mapping = {}
        color_index = 0
        if "level_0" in hierarchy and "label_groups" in hierarchy["level_0"]:
            for group_name in hierarchy["level_0"]["label_groups"].keys():
                if color_index < len(self.color_palette):
                    color_mapping[group_name] = self.color_palette[color_index]
                    color_index += 1
                else:

                    color_mapping[group_name] = self.color_palette[color_index % len(self.color_palette)]
                    color_index += 1
        return color_mapping

    def _build_intelligent_abstraction_prompt(self, graph_description: str,
                                            abstraction_level: int,
                                            mode: str,
                                            query_context: str = None) -> str:

        return self._build_unified_cognitive_prompt(
            graph_description,
            abstraction_level,
            self._calculate_cognitive_groups(len(graph_description.split('\n')), abstraction_level),
            query_context
        )
    def _parse_intelligent_response(self, response: str, graph_data: GraphDataModel) -> Dict[str, Any]:

        target_groups = self._calculate_cognitive_groups(len(graph_data.nodes), 3)
        return self._parse_cognitive_response(response, graph_data, target_groups)