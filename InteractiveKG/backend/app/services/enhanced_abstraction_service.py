from typing import Dict, List, Any, Set, Tuple, Optional
import numpy as np
import networkx as nx
from collections import defaultdict, Counter
from sklearn.cluster import DBSCAN, SpectralClustering
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import json
from ..models.graph_models import GraphDataModel, NodeModel, RelationshipModel
class EnhancedAbstractionService:
    def __init__(self):
        self.domain_configs = {
            "医疗": {
                "关键节点类型": ["Disease", "Drug", "Protein", "Gene", "Symptom"],
                "复杂度权重": {"结构": 0.3, "语义": 0.4, "时间": 0.3},
                "抽象策略": "生物学层次"
            },
            "金融": {
                "关键节点类型": ["Account", "Transaction", "Entity", "Risk"],
                "复杂度权重": {"结构": 0.5, "语义": 0.2, "时间": 0.3},
                "抽象策略": "风险传播"
            },
            "学术": {
                "关键节点类型": ["Publication", "Author", "Institution", "Topic"],
                "复杂度权重": {"结构": 0.4, "语义": 0.4, "时间": 0.2},
                "抽象策略": "知识演化"
            }
        }

    def analyze_domain_specific_hierarchy(self, graph_data: GraphDataModel,
                                        domain: str = "通用",
                                        abstraction_level: int = 3) -> Dict[str, Any]:
        if not graph_data.nodes:
            return self._empty_enhanced_analysis()


        detected_domain = self._detect_domain(graph_data)
        active_domain = domain if domain != "通用" else detected_domain
        config = self.domain_configs.get(active_domain, self._default_config())


        complexity_analysis = self._comprehensive_complexity_analysis(graph_data, config)


        domain_hierarchy = self._build_domain_aware_hierarchy(graph_data, config, abstraction_level)


        llm_limitation_analysis = self._analyze_llm_limitations(graph_data, complexity_analysis)


        interaction_necessity_score = self._calculate_interaction_necessity(
            complexity_analysis, llm_limitation_analysis
        )

        return {
            "enhanced_method": "domain_aware_hierarchical_abstraction",
            "detected_domain": detected_domain,
            "active_domain": active_domain,
            "abstraction_levels": abstraction_level,
            "domain_hierarchy": domain_hierarchy,
            "complexity_analysis": complexity_analysis,
            "llm_limitation_analysis": llm_limitation_analysis,
            "interaction_necessity_score": interaction_necessity_score,
            "color_mapping": self._generate_domain_colors(domain_hierarchy, active_domain),
            "research_insights": self._generate_research_insights(
                complexity_analysis, llm_limitation_analysis, interaction_necessity_score
            )
        }

    def _detect_domain(self, graph_data: GraphDataModel) -> str:

        node_types = set()
        for node in graph_data.nodes:
            node_types.update(node.labels)


        domain_keywords = {
            "医疗": {"Disease", "Drug", "Protein", "Gene", "Symptom", "Patient", "Treatment"},
            "金融": {"Account", "Transaction", "Risk", "Investment", "Bank", "Credit"},
            "学术": {"Publication", "Author", "Institution", "Research", "Paper", "Journal"}
        }

        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = len(node_types.intersection(keywords)) / len(keywords)
            domain_scores[domain] = score

        if max(domain_scores.values()) > 0.3:
            return max(domain_scores, key=domain_scores.get)
        return "通用"

    def _comprehensive_complexity_analysis(self, graph_data: GraphDataModel,
                                         config: Dict[str, Any]) -> Dict[str, Any]:

        G = self._build_networkx_graph(graph_data)


        structural_metrics = {
            "节点数量": len(graph_data.nodes),
            "边数量": len(graph_data.relationships),
            "平均度": np.mean([d for n, d in G.degree()]) if G.nodes() else 0,
            "聚类系数": nx.average_clustering(G) if G.nodes() else 0,
            "直径": self._safe_diameter(G),
            "模块度": self._calculate_modularity(G)
        }


        semantic_metrics = {
            "节点类型多样性": len(set(label for node in graph_data.nodes for label in node.labels)),
            "属性复杂度": np.mean([len(node.properties) for node in graph_data.nodes]),
            "关系类型多样性": len(set(rel.type for rel in graph_data.relationships)),
            "语义密度": self._calculate_semantic_density(graph_data)
        }


        cognitive_metrics = {
            "信息熵": self._calculate_information_entropy(graph_data),
            "推理路径长度": self._calculate_reasoning_path_complexity(G),
            "多跳关系复杂度": self._calculate_multi_hop_complexity(G),
            "隐式关系发现难度": self._calculate_implicit_relation_difficulty(graph_data)
        }

        return {
            "结构复杂度": structural_metrics,
            "语义复杂度": semantic_metrics,
            "认知复杂度": cognitive_metrics,
            "综合复杂度评分": self._calculate_comprehensive_score(
                structural_metrics, semantic_metrics, cognitive_metrics, config
            )
        }

    def _build_domain_aware_hierarchy(self, graph_data: GraphDataModel,
                                    config: Dict[str, Any],
                                    levels: int) -> Dict[str, Any]:

        hierarchy = {}


        core_groups = self._identify_domain_core_groups(graph_data, config)
        hierarchy["level_0"] = {"domain_core_groups": core_groups}


        if levels > 1:
            functional_modules = self._identify_functional_modules(graph_data, core_groups)
            hierarchy["level_1"] = {"functional_modules": functional_modules}


        if levels > 2:
            specialized_groups = self._identify_specialized_groups(graph_data, functional_modules)
            hierarchy["level_2"] = {"specialized_groups": specialized_groups}

        return hierarchy

    def _analyze_llm_limitations(self, graph_data: GraphDataModel,
                               complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:



        scale_limitations = {
            "节点数量超限": len(graph_data.nodes) > 100,
            "关系复杂度超限": len(graph_data.relationships) > 200,
            "多跳推理困难": complexity_analysis["认知复杂度"]["多跳关系复杂度"] > 0.7
        }


        reasoning_limitations = {
            "隐式关系发现": complexity_analysis["认知复杂度"]["隐式关系发现难度"] > 0.6,
            "动态网络分析": True,
            "概率推理": True,
            "因果关系识别": complexity_analysis["认知复杂度"]["推理路径长度"] > 0.8
        }


        domain_limitations = {
            "专业术语理解": self._assess_terminology_complexity(graph_data),
            "领域规则应用": self._assess_domain_rule_complexity(graph_data),
            "实时更新需求": True
        }

        return {
            "数据规模局限性": scale_limitations,
            "推理能力局限性": reasoning_limitations,
            "专业知识局限性": domain_limitations,
            "总体局限性评分": self._calculate_limitation_score(
                scale_limitations, reasoning_limitations, domain_limitations
            )
        }

    def _calculate_interaction_necessity(self, complexity_analysis: Dict[str, Any],
                                       llm_limitation_analysis: Dict[str, Any]) -> float:



        complexity_factor = min(complexity_analysis["综合复杂度评分"] / 10.0, 1.0)


        limitation_factor = llm_limitation_analysis["总体局限性评分"]


        domain_factor = 0.8


        necessity_score = (
            complexity_factor * 0.4 +
            limitation_factor * 0.4 +
            domain_factor * 0.2
        ) * 100

        return min(necessity_score, 100.0)

    def _generate_research_insights(self, complexity_analysis: Dict[str, Any],
                                  llm_limitation_analysis: Dict[str, Any],
                                  interaction_necessity_score: float) -> Dict[str, Any]:


        insights = {
            "LLM局限性证据": [],
            "交互式可视化优势": [],
            "研究贡献点": [],
            "实际应用价值": []
        }


        if complexity_analysis["综合复杂度评分"] > 7:
            insights["LLM局限性证据"].append("数据复杂度超出LLM单次处理能力")

        if llm_limitation_analysis.get("推理能力局限性", {}).get("多跳推理困难", False):
            insights["LLM局限性证据"].append("多跳推理路径超出LLM推理深度限制")


        if interaction_necessity_score > 80:
            insights["交互式可视化优势"].append("支持动态探索和渐进式理解")
            insights["交互式可视化优势"].append("提供多层级抽象视图")


        insights["研究贡献点"].append("证明了复杂专业领域数据需要交互式工具")
        insights["研究贡献点"].append("提供了LLM能力边界的量化评估方法")

        return insights


    def _build_networkx_graph(self, graph_data: GraphDataModel) -> nx.Graph:

        G = nx.Graph()
        for node in graph_data.nodes:
            G.add_node(node.id, labels=node.labels, properties=node.properties)
        for rel in graph_data.relationships:
            G.add_edge(rel.start_node_id, rel.end_node_id, type=rel.type, properties=rel.properties)
        return G

    def _safe_diameter(self, G: nx.Graph) -> float:

        if not G.nodes() or not nx.is_connected(G):
            return 0.0
        try:
            return nx.diameter(G)
        except:
            return 0.0

    def _calculate_modularity(self, G: nx.Graph) -> float:

        if not G.edges():
            return 0.0
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G)
            return community_louvain.modularity(partition, G)
        except:
            return 0.0

    def _calculate_semantic_density(self, graph_data: GraphDataModel) -> float:

        if not graph_data.nodes:
            return 0.0

        total_semantic_connections = 0
        for node in graph_data.nodes:

            semantic_weight = len(node.labels) + len(node.properties)
            total_semantic_connections += semantic_weight

        return total_semantic_connections / len(graph_data.nodes)

    def _default_config(self) -> Dict[str, Any]:

        return {
            "关键节点类型": [],
            "复杂度权重": {"结构": 0.4, "语义": 0.3, "时间": 0.3},
            "抽象策略": "通用层次"
        }

    def _empty_enhanced_analysis(self) -> Dict[str, Any]:

        return {
            "enhanced_method": "none",
            "detected_domain": "未知",
            "active_domain": "通用",
            "abstraction_levels": 0,
            "domain_hierarchy": {},
            "complexity_analysis": {},
            "llm_limitation_analysis": {},
            "interaction_necessity_score": 0.0,
            "color_mapping": {},
            "research_insights": {}
        }
    def _calculate_comprehensive_score(self, structural_metrics: Dict[str, Any],
                                     semantic_metrics: Dict[str, Any],
                                     cognitive_metrics: Dict[str, Any],
                                     config: Dict[str, Any]) -> float:

        weights = config.get("复杂度权重", {"结构": 0.4, "语义": 0.3, "时间": 0.3})

        structural_score = min(
            (structural_metrics["节点数量"] / 50 +
             structural_metrics["边数量"] / 100 +
             structural_metrics["平均度"] / 10 +
             structural_metrics["聚类系数"] * 5 +
             structural_metrics["直径"] / 10 +
             structural_metrics["模块度"] * 5) / 6, 10.0
        )

        semantic_score = min(
            (semantic_metrics["节点类型多样性"] / 5 +
             semantic_metrics["属性复杂度"] / 5 +
             semantic_metrics["关系类型多样性"] / 5 +
             semantic_metrics["语义密度"] / 10) / 4 * 10, 10.0
        )

        cognitive_score = min(
            (cognitive_metrics["信息熵"] +
             cognitive_metrics["推理路径长度"] * 10 +
             cognitive_metrics["多跳关系复杂度"] * 10 +
             cognitive_metrics["隐式关系发现难度"] * 10) / 4, 10.0
        )

        comprehensive_score = (
            structural_score * weights["结构"] +
            semantic_score * weights["语义"] +
            cognitive_score * weights["时间"]
        )
        return min(comprehensive_score, 10.0)
    def _calculate_information_entropy(self, graph_data: GraphDataModel) -> float:

        if not graph_data.nodes:
            return 0.0

        type_counts = Counter()
        for node in graph_data.nodes:
            if node.labels:
                type_counts[node.labels[0]] += 1
            else:
                type_counts["Unknown"] += 1
        total = sum(type_counts.values())
        entropy = 0.0
        for count in type_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
        return entropy / 5.0
    def _calculate_reasoning_path_complexity(self, G: nx.Graph) -> float:

        if not G.nodes() or len(G.nodes()) < 2:
            return 0.0
        try:

            avg_path_length = nx.average_shortest_path_length(G)
            return min(avg_path_length / 10.0, 1.0)
        except:
            return 0.5
    def _calculate_multi_hop_complexity(self, G: nx.Graph) -> float:

        if not G.nodes():
            return 0.0

        total_nodes = len(G.nodes())
        multi_hop_connections = 0
        for node in list(G.nodes())[:10]:
            try:
                two_hop = set(nx.single_source_shortest_path_length(G, node, cutoff=2).keys())
                three_hop = set(nx.single_source_shortest_path_length(G, node, cutoff=3).keys())
                multi_hop_connections += len(three_hop) - len(two_hop)
            except:
                continue
        return min(multi_hop_connections / (total_nodes * 10), 1.0)
    def _calculate_implicit_relation_difficulty(self, graph_data: GraphDataModel) -> float:

        if not graph_data.nodes:
            return 0.0

        total_possible_relations = len(graph_data.nodes) * (len(graph_data.nodes) - 1) / 2
        actual_relations = len(graph_data.relationships)
        if total_possible_relations == 0:
            return 0.0
        sparsity = 1 - (actual_relations / total_possible_relations)
        return min(sparsity, 1.0)
    def _identify_domain_core_groups(self, graph_data: GraphDataModel,
                                   config: Dict[str, Any]) -> Dict[str, List[str]]:

        core_groups = defaultdict(list)
        key_types = set(config.get("关键节点类型", []))
        for node in graph_data.nodes:
            node_type = node.labels[0] if node.labels else "Unknown"
            if key_types and node_type in key_types:

                core_groups[f"核心_{node_type}"].append(node.id)
            else:

                core_groups[f"辅助_{node_type}"].append(node.id)
        return dict(core_groups)
    def _identify_functional_modules(self, graph_data: GraphDataModel,
                                   core_groups: Dict[str, List[str]]) -> Dict[str, List[str]]:


        functional_modules = defaultdict(list)
        for node in graph_data.nodes:

            attr_count = len(node.properties)
            if attr_count >= 5:
                module_name = "高信息密度模块"
            elif attr_count >= 2:
                module_name = "中信息密度模块"
            else:
                module_name = "低信息密度模块"
            functional_modules[module_name].append(node.id)
        return dict(functional_modules)
    def _identify_specialized_groups(self, graph_data: GraphDataModel,
                                   functional_modules: Dict[str, List[str]]) -> Dict[str, List[str]]:

        specialized_groups = defaultdict(list)
        for node in graph_data.nodes:

            if "name" in node.properties:
                specialized_groups["命名实体"].append(node.id)
            elif "id" in node.properties:
                specialized_groups["标识实体"].append(node.id)
            else:
                specialized_groups["匿名实体"].append(node.id)
        return dict(specialized_groups)
    def _assess_terminology_complexity(self, graph_data: GraphDataModel) -> float:

        if not graph_data.nodes:
            return 0.0

        total_terms = 0
        complex_terms = 0
        for node in graph_data.nodes:
            for key, value in node.properties.items():
                total_terms += 1

                if len(str(key)) > 10 or len(str(value)) > 20:
                    complex_terms += 1
        return complex_terms / max(total_terms, 1)
    def _assess_domain_rule_complexity(self, graph_data: GraphDataModel) -> float:


        if not graph_data.relationships:
            return 0.0
        relation_types = set(rel.type for rel in graph_data.relationships)
        return min(len(relation_types) / 10.0, 1.0)
    def _calculate_limitation_score(self, scale_limitations: Dict[str, bool],
                                  reasoning_limitations: Dict[str, bool],
                                  domain_limitations: Dict[str, Any]) -> float:


        scale_score = sum(scale_limitations.values()) / len(scale_limitations)

        reasoning_score = sum(reasoning_limitations.values()) / len(reasoning_limitations)

        domain_score = 0.8

        overall_score = (scale_score * 0.3 + reasoning_score * 0.4 + domain_score * 0.3)
        return min(overall_score, 1.0)
    def _generate_domain_colors(self, domain_hierarchy: Dict[str, Any],
                              active_domain: str) -> Dict[str, str]:

        color_schemes = {
            "医疗": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
            "金融": ["#6C5CE7", "#A29BFE", "#FD79A8", "#FDCB6E", "#E17055"],
            "学术": ["#0984E3", "#00B894", "#E84393", "#FDCB6E", "#6C5CE7"],
            "通用": ["#3498DB", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6"]
        }
        colors = color_schemes.get(active_domain, color_schemes["通用"])
        color_mapping = {}

        color_index = 0
        for level_key, level_data in domain_hierarchy.items():
            if isinstance(level_data, dict):
                for group_key, group_data in level_data.items():
                    if isinstance(group_data, dict):
                        for group_name in group_data.keys():
                            color_mapping[group_name] = colors[color_index % len(colors)]
                            color_index += 1
        return color_mapping