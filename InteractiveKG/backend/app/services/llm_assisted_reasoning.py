from typing import Dict, List, Any, Optional, Tuple
import json
import asyncio
from collections import defaultdict
import networkx as nx
from ..models.graph_models import GraphDataModel, NodeModel, RelationshipModel
class LLMAssistedReasoningService:
    def __init__(self):
        self.reasoning_strategies = {
            "医疗": {
                "推理模式": ["因果推理", "症状-疾病关联", "药物相互作用"],
                "验证规则": ["生物学合理性", "临床证据支持", "药理学一致性"],
                "可信度阈值": 0.8
            },
            "金融": {
                "推理模式": ["风险传播", "资金流向", "关联交易"],
                "验证规则": ["监管合规性", "风险逻辑一致性", "时间序列合理性"],
                "可信度阈值": 0.9
            },
            "学术": {
                "推理模式": ["引用关系", "知识演化", "合作网络"],
                "验证规则": ["学术逻辑性", "时间一致性", "领域相关性"],
                "可信度阈值": 0.7
            }
        }

    def validate_reasoning_process(self, graph_data: GraphDataModel,
                                 reasoning_query: str,
                                 domain: str = "通用") -> Dict[str, Any]:

        reasoning_paths = self._decompose_reasoning_paths(graph_data, reasoning_query)


        path_validations = self._validate_multiple_paths(reasoning_paths, domain)


        consistency_check = self._check_domain_consistency(reasoning_paths, domain)


        credibility_score = self._calculate_reasoning_credibility(
            path_validations, consistency_check, domain
        )


        error_analysis = self._analyze_reasoning_errors(
            reasoning_paths, path_validations, consistency_check
        )

        return {
            "推理验证方法": "multi_path_validation",
            "查询": reasoning_query,
            "领域": domain,
            "推理路径": reasoning_paths,
            "路径验证结果": path_validations,
            "一致性检查": consistency_check,
            "可信度评分": credibility_score,
            "错误分析": error_analysis,
            "修正建议": self._generate_correction_suggestions(error_analysis),
            "验证总结": self._generate_validation_summary(credibility_score, error_analysis)
        }

    def _decompose_reasoning_paths(self, graph_data: GraphDataModel,
                                 query: str) -> List[Dict[str, Any]]:

        G = self._build_graph(graph_data)


        key_entities = self._extract_key_entities(query, graph_data)

        reasoning_paths = []


        for i, entity1 in enumerate(key_entities):
            for entity2 in key_entities[i+1:]:
                try:

                    paths = list(nx.all_simple_paths(G, entity1, entity2, cutoff=4))

                    for path in paths[:5]:
                        path_info = {
                            "起点": entity1,
                            "终点": entity2,
                            "路径": path,
                            "长度": len(path) - 1,
                            "关系序列": self._extract_relation_sequence(path, graph_data),
                            "语义描述": self._generate_path_description(path, graph_data)
                        }
                        reasoning_paths.append(path_info)

                except nx.NetworkXNoPath:
                    continue

        return reasoning_paths

    def _validate_multiple_paths(self, reasoning_paths: List[Dict[str, Any]],
                               domain: str) -> Dict[str, Any]:

        validations = {}
        domain_config = self.reasoning_strategies.get(domain, self.reasoning_strategies["学术"])

        for i, path in enumerate(reasoning_paths):
            path_id = f"path_{i}"


            length_validity = self._validate_path_length(path, domain)


            relation_validity = self._validate_relation_sequence(path, domain_config)


            semantic_validity = self._validate_semantic_coherence(path, domain_config)

            validations[path_id] = {
                "路径信息": path,
                "长度合理性": length_validity,
                "关系逻辑性": relation_validity,
                "语义连贯性": semantic_validity,
                "综合有效性": (length_validity + relation_validity + semantic_validity) / 3
            }

        return validations

    def _check_domain_consistency(self, reasoning_paths: List[Dict[str, Any]],
                                domain: str) -> Dict[str, Any]:

        consistency_results = {
            "领域规则符合度": 0.0,
            "专业术语正确性": 0.0,
            "时间逻辑一致性": 0.0,
            "因果关系合理性": 0.0,
            "详细检查结果": []
        }

        domain_config = self.reasoning_strategies.get(domain, {})
        validation_rules = domain_config.get("验证规则", [])

        for rule in validation_rules:
            rule_score = self._apply_domain_rule(reasoning_paths, rule, domain)
            consistency_results["详细检查结果"].append({
                "规则": rule,
                "符合度": rule_score,
                "说明": self._get_rule_explanation(rule, rule_score)
            })


        if consistency_results["详细检查结果"]:
            avg_score = sum(r["符合度"] for r in consistency_results["详细检查结果"]) / len(consistency_results["详细检查结果"])
            consistency_results["总体一致性评分"] = avg_score

        return consistency_results

    def _calculate_reasoning_credibility(self, path_validations: Dict[str, Any],
                                       consistency_check: Dict[str, Any],
                                       domain: str) -> Dict[str, Any]:



        if path_validations:
            path_scores = [v["综合有效性"] for v in path_validations.values()]
            avg_path_score = sum(path_scores) / len(path_scores)
        else:
            avg_path_score = 0.0


        consistency_score = consistency_check.get("总体一致性评分", 0.0)


        domain_config = self.reasoning_strategies.get(domain, {"可信度阈值": 0.7})
        threshold = domain_config["可信度阈值"]


        overall_credibility = (avg_path_score * 0.6 + consistency_score * 0.4)

        credibility_level = "高" if overall_credibility >= threshold else "中" if overall_credibility >= 0.5 else "低"

        return {
            "路径验证平均分": avg_path_score,
            "一致性检查分数": consistency_score,
            "综合可信度": overall_credibility,
            "可信度等级": credibility_level,
            "领域阈值": threshold,
            "是否可信": overall_credibility >= threshold
        }

    def _analyze_reasoning_errors(self, reasoning_paths: List[Dict[str, Any]],
                                path_validations: Dict[str, Any],
                                consistency_check: Dict[str, Any]) -> Dict[str, Any]:


        errors = {
            "路径错误": [],
            "逻辑错误": [],
            "一致性错误": [],
            "严重程度": "低"
        }


        for path_id, validation in path_validations.items():
            if validation["综合有效性"] < 0.5:
                errors["路径错误"].append({
                    "路径ID": path_id,
                    "问题": "路径有效性低",
                    "详情": validation,
                    "严重程度": "中" if validation["综合有效性"] < 0.3 else "低"
                })


        for check_result in consistency_check.get("详细检查结果", []):
            if check_result["符合度"] < 0.6:
                errors["一致性错误"].append({
                    "规则": check_result["规则"],
                    "符合度": check_result["符合度"],
                    "说明": check_result["说明"],
                    "严重程度": "高" if check_result["符合度"] < 0.3 else "中"
                })


        if any(e.get("严重程度") == "高" for e in errors["一致性错误"]):
            errors["严重程度"] = "高"
        elif any(e.get("严重程度") == "中" for e in errors["路径错误"] + errors["一致性错误"]):
            errors["严重程度"] = "中"

        return errors

    def _generate_correction_suggestions(self, error_analysis: Dict[str, Any]) -> List[str]:

        suggestions = []

        if error_analysis["路径错误"]:
            suggestions.append("检查推理路径是否完整和连贯")

        if error_analysis["一致性错误"]:
            suggestions.append("检查是否存在与已知事实矛盾的推理结论")

        if error_analysis["严重程度"] == "高":
            suggestions.append("建议进行人工审查和修正")

        return suggestions

    def _generate_validation_summary(self, credibility_score: Dict[str, Any],
                                   error_analysis: Dict[str, Any]) -> str:


        credibility = credibility_score["综合可信度"]
        is_credible = credibility_score["是否可信"]
        error_severity = error_analysis["严重程度"]

        if is_credible and error_severity == "低":
            return f"✅ 推理过程验证通过，可信度为 {credibility:.2f}，可以信任此推理结果"
        elif credibility > 0.5 and error_severity == "中":
            return f"⚠️ 推理过程基本可信，但存在一些问题，可信度为 {credibility:.2f}，建议谨慎使用"
        else:
            return f"❌ 推理过程存在严重问题，可信度仅为 {credibility:.2f}，不建议使用此推理结果"


    def _build_graph(self, graph_data: GraphDataModel) -> nx.Graph:

        G = nx.Graph()
        for node in graph_data.nodes:
            G.add_node(node.id, **node.properties)
        for rel in graph_data.relationships:
            G.add_edge(rel.start_node_id, rel.end_node_id, type=rel.type, **rel.properties)
        return G

    def _extract_key_entities(self, query: str, graph_data: GraphDataModel) -> List[str]:


        return [node.id for node in graph_data.nodes[:5]]

    def _extract_relation_sequence(self, path: List[str], graph_data: GraphDataModel) -> List[str]:

        relations = []
        for i in range(len(path) - 1):
            for rel in graph_data.relationships:
                if (rel.start_node_id == path[i] and rel.end_node_id == path[i+1]) or \
                   (rel.start_node_id == path[i+1] and rel.end_node_id == path[i]):
                    relations.append(rel.type)
                    break
        return relations

    def _generate_path_description(self, path: List[str], graph_data: GraphDataModel) -> str:

        node_names = []
        for node_id in path:
            for node in graph_data.nodes:
                if node.id == node_id:
                    name = node.properties.get("name", node.properties.get("displayName", node_id))
                    node_names.append(name)
                    break
        return " → ".join(node_names)

    def _validate_path_length(self, path: Dict[str, Any], domain: str) -> float:

        length = path["长度"]

        if domain == "医疗":
            return 1.0 if length <= 3 else max(0.0, 1.0 - (length - 3) * 0.2)
        elif domain == "金融":
            return 1.0 if length <= 4 else max(0.0, 1.0 - (length - 4) * 0.15)
        else:
            return 1.0 if length <= 5 else max(0.0, 1.0 - (length - 5) * 0.1)

    def _validate_relation_sequence(self, path: Dict[str, Any], domain_config: Dict[str, Any]) -> float:


        relations = path["关系序列"]
        if not relations:
            return 0.0

        unique_relations = len(set(relations))
        total_relations = len(relations)


        diversity_score = min(unique_relations / total_relations, 1.0)
        return diversity_score

    def _validate_semantic_coherence(self, path: Dict[str, Any], domain_config: Dict[str, Any]) -> float:


        description = path["语义描述"]
        if not description:
            return 0.0


        words = description.split()
        if len(words) < 2:
            return 0.3
        elif len(words) > 10:
            return 0.7
        else:
            return 0.9

    def _apply_domain_rule(self, reasoning_paths: List[Dict[str, Any]],
                          rule: str, domain: str) -> float:


        rule_scores = {
            "生物学合理性": 0.8,
            "临床证据支持": 0.7,
            "药理学一致性": 0.9,
            "监管合规性": 0.85,
            "风险逻辑一致性": 0.75,
            "时间序列合理性": 0.8,
            "学术逻辑性": 0.9,
            "时间一致性": 0.85,
            "领域相关性": 0.8
        }
        return rule_scores.get(rule, 0.7)

    def _get_rule_explanation(self, rule: str, score: float) -> str:

        if score >= 0.8:
            return f"{rule}检查通过，符合领域标准"
        elif score >= 0.6:
            return f"{rule}基本符合，但有改进空间"
        else:
            return f"{rule}不符合标准，需要重新审查"