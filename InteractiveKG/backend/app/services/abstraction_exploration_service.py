import logging
from typing import Dict, List, Any, Optional, Tuple
from ..services.hierarchical_abstraction_service import HierarchicalAbstractionService
from ..services.graph_service import GraphService
from ..models.chatbot_models import AbstractionExplorationRequest, AbstractionExplorationResponse
logger = logging.getLogger(__name__)
class AbstractionExplorationService:
    def __init__(self):
        self.graph_service = GraphService()
        self.abstraction_service = HierarchicalAbstractionService()


        self.level_descriptions = {
            0: "Full view - every original node and relationship, coloured by label group",
            1: "Concrete level - fine-grained grouping by concrete features",
            2: "Functional level - medium-grained grouping by functional role",
            3: "Conceptual level - high-level grouping by abstract concepts"
        }


        self.mode_descriptions = {
            "semantic": "Semantic abstraction - group by node properties and semantic similarity",
            "structural": "Structural abstraction - group by graph topology and connection patterns",
            "community": "Community abstraction - detect tightly connected node groups via community detection"
        }

    async def explore_abstraction(self, request: AbstractionExplorationRequest) -> AbstractionExplorationResponse:

        try:
            logger.info(f"Starting abstraction exploration: level={request.abstraction_level}, mode={request.abstraction_mode}")


            graph_data_model = self.graph_service.get_all_graph_data()

            if hasattr(graph_data_model, 'model_dump'):
                graph_data = graph_data_model.model_dump()
            elif hasattr(graph_data_model, 'dict'):
                graph_data = graph_data_model.dict()
            elif hasattr(graph_data_model, 'nodes') and hasattr(graph_data_model, 'relationships'):

                graph_data = {
                    "nodes": [node.dict() if hasattr(node, 'dict') else node for node in graph_data_model.nodes],
                    "relationships": [rel.dict() if hasattr(rel, 'dict') else rel for rel in graph_data_model.relationships]
                }
            else:

                graph_data = graph_data_model if isinstance(graph_data_model, dict) else {
                    "nodes": [],
                    "relationships": []
                }

            if request.action == "explore":
                return await self._explore_single_setting(request, graph_data_model, graph_data)
            elif request.action == "compare":
                return await self._compare_settings(request, graph_data_model, graph_data)
            elif request.action == "select":
                return await self._select_optimal_setting(request, graph_data_model, graph_data)
            else:
                raise ValueError(f"Unknown exploration action: {request.action}")

        except Exception as e:
            logger.error(f"Abstraction exploration failed: {e}")
            return AbstractionExplorationResponse(
                session_id=request.session_id,
                abstraction_level=request.abstraction_level,
                abstraction_mode=request.abstraction_mode,
                exploration_data={},
                success=False,
                error=str(e)
            )

    async def _explore_single_setting(self, request: AbstractionExplorationRequest, graph_data_model, graph_data: Dict[str, Any]) -> AbstractionExplorationResponse:

        try:

            abstraction_result = await self.abstraction_service.analyze_hierarchical_structure(
                graph_data_model,
                request.abstraction_level,
                request.abstraction_mode
            )


            insights = self._generate_insights(
                request.abstraction_level,
                request.abstraction_mode,
                abstraction_result,
                graph_data
            )


            recommendations = self._generate_recommendations(
                request.abstraction_level,
                request.abstraction_mode,
                abstraction_result
            )

            exploration_data = {
                "abstraction_result": abstraction_result,
                "original_nodes_count": len(graph_data.get("nodes", [])),
                "original_relationships_count": len(graph_data.get("relationships", [])),
                "abstracted_groups_count": self._count_abstracted_groups(abstraction_result),
                "level_description": self.level_descriptions.get(request.abstraction_level, ""),
                "mode_description": self.mode_descriptions.get(request.abstraction_mode, ""),
                "complexity_reduction": self._calculate_complexity_reduction(graph_data, abstraction_result)
            }

            return AbstractionExplorationResponse(
                session_id=request.session_id,
                abstraction_level=request.abstraction_level,
                abstraction_mode=request.abstraction_mode,
                exploration_data=exploration_data,
                insights=insights,
                recommendations=recommendations,
                success=True
            )

        except Exception as e:
            logger.error(f"Single-setting exploration failed: {e}")
            raise

    async def _compare_settings(self, request: AbstractionExplorationRequest, graph_data_model, graph_data: Dict[str, Any]) -> AbstractionExplorationResponse:

        try:
            comparison_data = {}


            level_comparisons = []
            for level in range(1, 6):
                result = await self.abstraction_service.analyze_hierarchical_structure(
                    graph_data_model, level, request.abstraction_mode
                )
                level_comparisons.append({
                    "level": level,
                    "groups_count": self._count_abstracted_groups(result),
                    "description": self.level_descriptions.get(level, "")
                })

            mode_comparisons = []
            for mode in ["semantic", "structural", "community"]:
                result = await self.abstraction_service.analyze_hierarchical_structure(
                    graph_data_model, request.abstraction_level, mode
                )
                mode_comparisons.append({
                    "mode": mode,
                    "groups_count": self._count_abstracted_groups(result),
                    "description": self.mode_descriptions.get(mode, "")
                })

            comparison_data = {
                "level_comparisons": level_comparisons,
                "mode_comparisons": mode_comparisons,
                "current_setting": {
                    "level": request.abstraction_level,
                    "mode": request.abstraction_mode
                }
            }

            insights = [
                f"How group counts change per abstraction level in {request.abstraction_mode} mode:",
                f"Level 1: {level_comparisons[0]['groups_count']} groups → level 5: {level_comparisons[4]['groups_count']} groups",
                f"Grouping results per mode at level {request.abstraction_level}:",
                f"semantic: {mode_comparisons[0]['groups_count']} groups, structural: {mode_comparisons[1]['groups_count']} groups, community: {mode_comparisons[2]['groups_count']} groups"
            ]

            recommendations = [
                "Try different abstraction levels to observe how the data structure changes",
                "Compare abstraction modes and pick the setting that best fits the analysis task",
                "Lower levels suit detailed analysis; higher levels suit a big-picture view"
            ]

            return AbstractionExplorationResponse(
                session_id=request.session_id,
                abstraction_level=request.abstraction_level,
                abstraction_mode=request.abstraction_mode,
                exploration_data=comparison_data,
                insights=insights,
                recommendations=recommendations,
                success=True
            )

        except Exception as e:
            logger.error(f"Setting comparison failed: {e}")
            raise

    async def _select_optimal_setting(self, request: AbstractionExplorationRequest, graph_data_model, graph_data: Dict[str, Any]) -> AbstractionExplorationResponse:

        try:

            scenario_analysis = self._analyze_scenario_requirements(graph_data)


            optimal_level, optimal_mode = self._recommend_optimal_setting(scenario_analysis)


            optimal_result = await self.abstraction_service.analyze_hierarchical_structure(
                graph_data_model, optimal_level, optimal_mode
            )

            selection_data = {
                "recommended_level": optimal_level,
                "recommended_mode": optimal_mode,
                "scenario_analysis": scenario_analysis,
                "optimal_result": optimal_result,
                "selection_reasoning": self._explain_selection_reasoning(
                    optimal_level, optimal_mode, scenario_analysis
                )
            }

            insights = [
                f"Based on the current data, abstraction level {optimal_level} with {optimal_mode} mode is recommended",
                f"This setting balances detail retention with structural clarity",
                f"Well suited to data-quality analysis and issue identification"
            ]

            recommendations = [
                f"Use the recommended abstraction setting: level {optimal_level} + {optimal_mode} mode",
                "Perform data editing and cleanup under this setting",
                "Lower the abstraction level for more detail; raise it for an overall view"
            ]

            return AbstractionExplorationResponse(
                session_id=request.session_id,
                abstraction_level=optimal_level,
                abstraction_mode=optimal_mode,
                exploration_data=selection_data,
                insights=insights,
                recommendations=recommendations,
                success=True
            )

        except Exception as e:
            logger.error(f"Optimal setting selection failed: {e}")
            raise

    def _generate_insights(self, level: int, mode: str, abstraction_result: Dict[str, Any], graph_data: Dict[str, Any]) -> List[str]:

        insights = []

        original_nodes = len(graph_data.get("nodes", []))
        abstracted_groups = self._count_abstracted_groups(abstraction_result)

        insights.append(f"Abstraction level {level} organizes {original_nodes} original nodes into {abstracted_groups} logical groups")
        insights.append(f"Characteristics of {mode} mode: {self.mode_descriptions.get(mode, '')}")

        if level <= 2:
            insights.append("Low abstraction level: shows more detail")
        elif level >= 4:
            insights.append("High abstraction level: shows a more macroscopic view")
        else:
            insights.append("Medium abstraction level: balances detail and overview")

        return insights

    def _generate_recommendations(self, level: int, mode: str, abstraction_result: Dict[str, Any]) -> List[str]:

        recommendations = []

        if level == 1:
            recommendations.append("Try a higher abstraction level for a more macroscopic view")
        elif level == 5:
            recommendations.append("Highest abstraction level; try a lower level to see more detail")
        else:
            recommendations.append("The current level suits medium-scale community structures")

        recommendations.append(f"Try other abstraction modes and compare grouping results")
        recommendations.append("Choose the abstraction setting that best fits the analysis task")

        return recommendations

    def _count_abstracted_groups(self, abstraction_result: Dict[str, Any]) -> int:

        try:
            hierarchy = abstraction_result.get("hierarchy", {})
            if not hierarchy:
                return 0


            total_groups = 0
            for level_data in hierarchy.values():
                if isinstance(level_data, dict):
                    for group_data in level_data.values():
                        if isinstance(group_data, dict):
                            total_groups += len(group_data)

            return total_groups
        except Exception:
            return 0

    def _calculate_complexity_reduction(self, graph_data: Dict[str, Any], abstraction_result: Dict[str, Any]) -> float:

        try:
            original_count = len(graph_data.get("nodes", []))
            abstracted_count = self._count_abstracted_groups(abstraction_result)

            if original_count == 0:
                return 0.0

            return (original_count - abstracted_count) / original_count
        except Exception:
            return 0.0

    def _analyze_scenario_requirements(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:

        nodes_count = len(graph_data.get("nodes", []))
        relationships_count = len(graph_data.get("relationships", []))

        return {
            "nodes_count": nodes_count,
            "relationships_count": relationships_count,
            "complexity": "high" if nodes_count > 50 else "medium" if nodes_count > 20 else "low",
            "density": relationships_count / max(nodes_count, 1)
        }

    def _recommend_optimal_setting(self, scenario_analysis: Dict[str, Any]) -> Tuple[int, str]:

        complexity = scenario_analysis.get("complexity", "medium")

        if complexity == "high":
            return 4, "community"
        elif complexity == "low":
            return 2, "semantic"
        else:
            return 3, "structural"

    def _explain_selection_reasoning(self, level: int, mode: str, scenario_analysis: Dict[str, Any]) -> str:

        complexity = scenario_analysis.get("complexity", "medium")
        nodes_count = scenario_analysis.get("nodes_count", 0)

        reasoning = f"Given the {complexity} complexity of the current data ({nodes_count} nodes), "
        reasoning += f"abstraction level {level} is recommended to balance detail and clarity, "
        reasoning += f"using {mode} mode to best organize the data structure."

        return reasoning

abstraction_exploration_service = AbstractionExplorationService()