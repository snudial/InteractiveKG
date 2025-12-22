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
            0: "完整视图 - 显示所有原始节点和关系，按标签分组着色",
            1: "具体层次 - 基于具体特征进行细粒度分组",
            2: "功能层次 - 按功能角色进行中等粒度分组",
            3: "概念层次 - 基于抽象概念进行高层次分组"
        }


        self.mode_descriptions = {
            "semantic": "语义抽象 - 基于节点属性和语义相似性进行分组",
            "structural": "结构抽象 - 基于图的拓扑结构和连接模式进行分组",
            "community": "社区抽象 - 基于社区检测算法识别紧密连接的节点群"
        }

    async def explore_abstraction(self, request: AbstractionExplorationRequest) -> AbstractionExplorationResponse:

        try:
            logger.info(f"开始抽象探索: level={request.abstraction_level}, mode={request.abstraction_mode}")


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
                raise ValueError(f"未知的探索动作: {request.action}")

        except Exception as e:
            logger.error(f"抽象探索失败: {e}")
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
            logger.error(f"单设置探索失败: {e}")
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
                f"在{request.abstraction_mode}模式下，不同抽象级别的分组数量变化：",
                f"级别1: {level_comparisons[0]['groups_count']}组 → 级别5: {level_comparisons[4]['groups_count']}组",
                f"在级别{request.abstraction_level}下，不同模式的分组效果：",
                f"语义模式: {mode_comparisons[0]['groups_count']}组，结构模式: {mode_comparisons[1]['groups_count']}组，社区模式: {mode_comparisons[2]['groups_count']}组"
            ]

            recommendations = [
                "建议尝试不同的抽象级别，观察数据结构的变化",
                "比较不同抽象模式，选择最适合当前分析任务的设置",
                "较低级别适合详细分析，较高级别适合整体把握"
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
            logger.error(f"设置比较失败: {e}")
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
                f"基于当前数据特征，推荐使用抽象级别{optimal_level}和{optimal_mode}模式",
                f"这个设置能够平衡细节保留和结构清晰度",
                f"适合进行数据质量分析和问题识别"
            ]

            recommendations = [
                f"使用推荐的抽象设置：级别{optimal_level} + {optimal_mode}模式",
                "在此设置下进行数据编辑和清理操作",
                "如需要更多细节，可以降低抽象级别；如需要整体视图，可以提高抽象级别"
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
            logger.error(f"最优设置选择失败: {e}")
            raise

    def _generate_insights(self, level: int, mode: str, abstraction_result: Dict[str, Any], graph_data: Dict[str, Any]) -> List[str]:

        insights = []

        original_nodes = len(graph_data.get("nodes", []))
        abstracted_groups = self._count_abstracted_groups(abstraction_result)

        insights.append(f"抽象级别{level}将{original_nodes}个原始节点组织成{abstracted_groups}个逻辑组")
        insights.append(f"{mode}模式的特点：{self.mode_descriptions.get(mode, '')}")

        if level <= 2:
            insights.append("低抽象级别：显示更多细节")
        elif level >= 4:
            insights.append("高抽象级别：显示更宏观的视图")
        else:
            insights.append("中等抽象级别：平衡细节和概览")

        return insights

    def _generate_recommendations(self, level: int, mode: str, abstraction_result: Dict[str, Any]) -> List[str]:

        recommendations = []

        if level == 1:
            recommendations.append("建议尝试更高的抽象级别以获得更宏观的视图")
        elif level == 5:
            recommendations.append("最高抽象级别，建议尝试较低的级别以查看更多细节")
        else:
            recommendations.append("当前级别适合查看中等规模的社区结构")

        recommendations.append(f"尝试其他抽象模式，比较不同的分组效果")
        recommendations.append("选择最适合当前分析任务的抽象设置")

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

        reasoning = f"基于当前数据的{complexity}复杂度（{nodes_count}个节点），"
        reasoning += f"推荐使用抽象级别{level}来平衡细节和清晰度，"
        reasoning += f"使用{mode}模式来最好地组织数据结构。"

        return reasoning

abstraction_exploration_service = AbstractionExplorationService()