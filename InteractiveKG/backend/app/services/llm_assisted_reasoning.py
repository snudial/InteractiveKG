from typing import Dict, List, Any
import networkx as nx
from ..models.graph_models import GraphDataModel


class LLMAssistedReasoningService:
    def __init__(self):
        self.reasoning_strategies = {
            "medical": {
                "reasoning_patterns": ["causal reasoning", "symptom-disease association", "drug interaction"],
                "validation_rules": ["biological plausibility", "clinical evidence support", "pharmacological consistency"],
                "credibility_threshold": 0.8
            },
            "finance": {
                "reasoning_patterns": ["risk propagation", "fund flow", "related-party transactions"],
                "validation_rules": ["regulatory compliance", "risk logic consistency", "time series plausibility"],
                "credibility_threshold": 0.9
            },
            "academic": {
                "reasoning_patterns": ["citation relations", "knowledge evolution", "collaboration network"],
                "validation_rules": ["academic soundness", "temporal consistency", "domain relevance"],
                "credibility_threshold": 0.7
            }
        }

    def validate_reasoning_process(self, graph_data: GraphDataModel,
                                 reasoning_query: str,
                                 domain: str = "general") -> Dict[str, Any]:

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
            "validation_method": "multi_path_validation",
            "query": reasoning_query,
            "domain": domain,
            "reasoning_paths": reasoning_paths,
            "path_validations": path_validations,
            "consistency_check": consistency_check,
            "credibility_score": credibility_score,
            "error_analysis": error_analysis,
            "correction_suggestions": self._generate_correction_suggestions(error_analysis),
            "validation_summary": self._generate_validation_summary(credibility_score, error_analysis)
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
                            "start": entity1,
                            "end": entity2,
                            "path": path,
                            "length": len(path) - 1,
                            "relation_sequence": self._extract_relation_sequence(path, graph_data),
                            "description": self._generate_path_description(path, graph_data)
                        }
                        reasoning_paths.append(path_info)

                except nx.NetworkXNoPath:
                    continue

        return reasoning_paths

    def _validate_multiple_paths(self, reasoning_paths: List[Dict[str, Any]],
                               domain: str) -> Dict[str, Any]:

        validations = {}
        domain_config = self.reasoning_strategies.get(domain, self.reasoning_strategies["academic"])

        for i, path in enumerate(reasoning_paths):
            path_id = f"path_{i}"

            length_validity = self._validate_path_length(path, domain)

            relation_validity = self._validate_relation_sequence(path, domain_config)

            semantic_validity = self._validate_semantic_coherence(path, domain_config)

            validations[path_id] = {
                "path_info": path,
                "length_validity": length_validity,
                "relation_validity": relation_validity,
                "semantic_validity": semantic_validity,
                "overall_validity": (length_validity + relation_validity + semantic_validity) / 3
            }

        return validations

    def _check_domain_consistency(self, reasoning_paths: List[Dict[str, Any]],
                                domain: str) -> Dict[str, Any]:

        consistency_results = {
            "domain_rule_compliance": 0.0,
            "terminology_correctness": 0.0,
            "temporal_consistency": 0.0,
            "causal_plausibility": 0.0,
            "detailed_checks": []
        }

        domain_config = self.reasoning_strategies.get(domain, {})
        validation_rules = domain_config.get("validation_rules", [])

        for rule in validation_rules:
            rule_score = self._apply_domain_rule(reasoning_paths, rule, domain)
            consistency_results["detailed_checks"].append({
                "rule": rule,
                "compliance": rule_score,
                "explanation": self._get_rule_explanation(rule, rule_score)
            })

        if consistency_results["detailed_checks"]:
            avg_score = sum(r["compliance"] for r in consistency_results["detailed_checks"]) / len(consistency_results["detailed_checks"])
            consistency_results["overall_consistency_score"] = avg_score

        return consistency_results

    def _calculate_reasoning_credibility(self, path_validations: Dict[str, Any],
                                       consistency_check: Dict[str, Any],
                                       domain: str) -> Dict[str, Any]:

        if path_validations:
            path_scores = [v["overall_validity"] for v in path_validations.values()]
            avg_path_score = sum(path_scores) / len(path_scores)
        else:
            avg_path_score = 0.0

        consistency_score = consistency_check.get("overall_consistency_score", 0.0)

        domain_config = self.reasoning_strategies.get(domain, {"credibility_threshold": 0.7})
        threshold = domain_config["credibility_threshold"]

        overall_credibility = (avg_path_score * 0.6 + consistency_score * 0.4)

        credibility_level = "high" if overall_credibility >= threshold else "medium" if overall_credibility >= 0.5 else "low"

        return {
            "avg_path_score": avg_path_score,
            "consistency_score": consistency_score,
            "overall_credibility": overall_credibility,
            "credibility_level": credibility_level,
            "domain_threshold": threshold,
            "is_credible": overall_credibility >= threshold
        }

    def _analyze_reasoning_errors(self, reasoning_paths: List[Dict[str, Any]],
                                path_validations: Dict[str, Any],
                                consistency_check: Dict[str, Any]) -> Dict[str, Any]:

        errors = {
            "path_errors": [],
            "logic_errors": [],
            "consistency_errors": [],
            "severity": "low"
        }

        for path_id, validation in path_validations.items():
            if validation["overall_validity"] < 0.5:
                errors["path_errors"].append({
                    "path_id": path_id,
                    "issue": "low path validity",
                    "details": validation,
                    "severity": "medium" if validation["overall_validity"] < 0.3 else "low"
                })

        for check_result in consistency_check.get("detailed_checks", []):
            if check_result["compliance"] < 0.6:
                errors["consistency_errors"].append({
                    "rule": check_result["rule"],
                    "compliance": check_result["compliance"],
                    "explanation": check_result["explanation"],
                    "severity": "high" if check_result["compliance"] < 0.3 else "medium"
                })

        if any(e.get("severity") == "high" for e in errors["consistency_errors"]):
            errors["severity"] = "high"
        elif any(e.get("severity") == "medium" for e in errors["path_errors"] + errors["consistency_errors"]):
            errors["severity"] = "medium"

        return errors

    def _generate_correction_suggestions(self, error_analysis: Dict[str, Any]) -> List[str]:

        suggestions = []

        if error_analysis["path_errors"]:
            suggestions.append("Check whether the reasoning paths are complete and coherent")

        if error_analysis["consistency_errors"]:
            suggestions.append("Check for reasoning conclusions that contradict known facts")

        if error_analysis["severity"] == "high":
            suggestions.append("Manual review and correction is recommended")

        return suggestions

    def _generate_validation_summary(self, credibility_score: Dict[str, Any],
                                   error_analysis: Dict[str, Any]) -> str:

        credibility = credibility_score["overall_credibility"]
        is_credible = credibility_score["is_credible"]
        error_severity = error_analysis["severity"]

        if is_credible and error_severity == "low":
            return f"✅ Reasoning validated; credibility {credibility:.2f} — the result can be trusted"
        elif credibility > 0.5 and error_severity == "medium":
            return f"⚠️ Reasoning is broadly credible but has some issues; credibility {credibility:.2f} — use with caution"
        else:
            return f"❌ Reasoning has serious problems; credibility only {credibility:.2f} — do not rely on this result"

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

        length = path["length"]

        if domain == "medical":
            return 1.0 if length <= 3 else max(0.0, 1.0 - (length - 3) * 0.2)
        elif domain == "finance":
            return 1.0 if length <= 4 else max(0.0, 1.0 - (length - 4) * 0.15)
        else:
            return 1.0 if length <= 5 else max(0.0, 1.0 - (length - 5) * 0.1)

    def _validate_relation_sequence(self, path: Dict[str, Any], domain_config: Dict[str, Any]) -> float:

        relations = path["relation_sequence"]
        if not relations:
            return 0.0

        unique_relations = len(set(relations))
        total_relations = len(relations)

        diversity_score = min(unique_relations / total_relations, 1.0)
        return diversity_score

    def _validate_semantic_coherence(self, path: Dict[str, Any], domain_config: Dict[str, Any]) -> float:

        description = path["description"]
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
            "biological plausibility": 0.8,
            "clinical evidence support": 0.7,
            "pharmacological consistency": 0.9,
            "regulatory compliance": 0.85,
            "risk logic consistency": 0.75,
            "time series plausibility": 0.8,
            "academic soundness": 0.9,
            "temporal consistency": 0.85,
            "domain relevance": 0.8
        }
        return rule_scores.get(rule, 0.7)

    def _get_rule_explanation(self, rule: str, score: float) -> str:

        if score >= 0.8:
            return f"{rule}: check passed, meets domain standards"
        elif score >= 0.6:
            return f"{rule}: broadly compliant, with room for improvement"
        else:
            return f"{rule}: below standard, needs re-review"
