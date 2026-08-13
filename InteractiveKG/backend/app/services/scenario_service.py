import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from ..models.chatbot_models import TestScenario
from ..models.graph_models import GraphDataModel, NodeModel, RelationshipModel
from ..services.graph_service import graph_service
logger = logging.getLogger(__name__)
class ScenarioService:
    def __init__(self):
        self.scenario_data: Dict[TestScenario, Dict[str, Any]] = {}
        self.current_scenario: Optional[TestScenario] = None
        self._load_scenario_data()

    def _load_scenario_data(self):

        try:

            project_root = Path(__file__).parent.parent.parent.parent


            act1_file = project_root / "chatbot_scenario_data_act1.json"
            if act1_file.exists():
                with open(act1_file, 'r', encoding='utf-8') as f:
                    self.scenario_data[TestScenario.ACT_I] = json.load(f)
                logger.info("Act I scenario data loaded")
            else:
                logger.warning(f"Act I data file not found: {act1_file}")


            act2_file = project_root / "chatbot_scenario_data_act2.json"
            if act2_file.exists():
                with open(act2_file, 'r', encoding='utf-8') as f:
                    self.scenario_data[TestScenario.ACT_II] = json.load(f)
                logger.info("Act II scenario data loaded")
            else:
                logger.warning(f"Act II data file not found: {act2_file}")

        except Exception as e:
            logger.error(f"Failed to load scenario data: {e}")

    def get_scenario_info(self, scenario: TestScenario) -> Dict[str, Any]:

        data = self.scenario_data.get(scenario, {})
        return {
            "scenario_name": data.get("scenario_name", ""),
            "description": data.get("description", ""),
            "user_role": data.get("user_role", ""),
            "target_question": data.get("target_question", ""),
            "expected_issue": data.get("expected_issue", "")
        }

    def load_scenario_to_database(self, scenario: TestScenario) -> Dict[str, Any]:

        try:
            if scenario not in self.scenario_data:
                raise ValueError(f"Scenario data not found: {scenario}")

            data = self.scenario_data[scenario]


            graph_service.clear_all_data()


            graph_data = {
                "nodes": data.get("nodes", []),
                "relationships": data.get("relationships", [])
            }


            result = graph_service.import_json_data(graph_data)

            self.current_scenario = scenario

            logger.info(f"Scenario {scenario} data loaded: {len(result.nodes)} nodes, {len(result.relationships)} relationships")

            return {
                "scenario": scenario,
                "nodes_count": len(result.nodes),
                "relationships_count": len(result.relationships),
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to load scenario data into the database: {e}")
            return {
                "scenario": scenario,
                "nodes_count": 0,
                "relationships_count": 0,
                "success": False,
                "error": str(e)
            }

    def get_target_question(self, scenario: TestScenario) -> str:

        data = self.scenario_data.get(scenario, {})
        return data.get("target_question", "")

    def get_expected_issue(self, scenario: TestScenario) -> str:

        data = self.scenario_data.get(scenario, {})
        return data.get("expected_issue", "")

    def get_correct_data_updates(self, scenario: TestScenario) -> Dict[str, Any]:

        if scenario != TestScenario.ACT_I:
            return {}

        data = self.scenario_data.get(scenario, {})
        return data.get("correct_data_updates", {})

    def get_hallucination_info(self, scenario: TestScenario) -> Dict[str, Any]:

        if scenario != TestScenario.ACT_II:
            return {}

        data = self.scenario_data.get(scenario, {})
        return {
            "hallucination_nodes": data.get("hallucination_nodes", []),
            "hallucination_relationships": data.get("hallucination_relationships", []),
            "correct_analysis": data.get("correct_analysis_after_cleanup", "")
        }

    def apply_data_correction(self, scenario: TestScenario, node_id: str, updates: Dict[str, Any]) -> bool:

        try:
            if scenario != TestScenario.ACT_I:
                return False


            correct_updates = self.get_correct_data_updates(scenario)
            if node_id not in correct_updates:
                return False


            node = graph_service.get_node_by_id(node_id)
            if not node:
                return False


            updated_properties = {**node.properties, **correct_updates[node_id]["properties"]}

            from ..models.graph_models import NodeUpdateRequest
            update_request = NodeUpdateRequest(properties=updated_properties)

            updated_node = graph_service.update_node(node_id, update_request)

            logger.info(f"Data correction applied to node {node_id}")
            return updated_node is not None

        except Exception as e:
            logger.error(f"Failed to apply data correction: {e}")
            return False

    def remove_hallucination_node(self, node_id: str) -> bool:

        try:
            if self.current_scenario != TestScenario.ACT_II:
                return False


            hallucination_info = self.get_hallucination_info(TestScenario.ACT_II)
            if node_id not in hallucination_info.get("hallucination_nodes", []):
                logger.warning(f"Node {node_id} is not a hallucinated node")
                return False


            success = graph_service.delete_node(node_id)

            if success:
                logger.info(f"Hallucinated node {node_id} deleted")

            return success

        except Exception as e:
            logger.error(f"Failed to delete hallucinated node: {e}")
            return False

    def remove_hallucination_relationship(self, start_node_id: str, end_node_id: str, rel_type: str) -> bool:

        try:
            if self.current_scenario != TestScenario.ACT_II:
                return False


            hallucination_info = self.get_hallucination_info(TestScenario.ACT_II)
            hallucination_rels = hallucination_info.get("hallucination_relationships", [])

            is_hallucination = any(
                rel["start_node_id"] == start_node_id and
                rel["end_node_id"] == end_node_id and
                rel["type"] == rel_type
                for rel in hallucination_rels
            )

            if not is_hallucination:
                logger.warning(f"Relationship {start_node_id}->{end_node_id} ({rel_type}) is not a hallucinated relationship")
                return False


            relationships = graph_service.get_all_graph_data().relationships
            target_rel = None

            for rel in relationships:
                if (rel.start_node_id == start_node_id and
                    rel.end_node_id == end_node_id and
                    rel.type == rel_type):
                    target_rel = rel
                    break

            if target_rel:
                success = graph_service.delete_relationship(target_rel.id)
                if success:
                    logger.info(f"Hallucinated relationship {start_node_id}->{end_node_id} ({rel_type}) deleted")
                return success

            return False

        except Exception as e:
            logger.error(f"Failed to delete hallucinated relationship: {e}")
            return False

    def validate_cleanup_completion(self, scenario: TestScenario) -> Dict[str, Any]:

        try:
            if scenario != TestScenario.ACT_II:
                return {"completed": False, "error": "Only applicable to Act II"}

            hallucination_info = self.get_hallucination_info(scenario)
            current_data = graph_service.get_all_graph_data()


            remaining_hallucination_nodes = []
            for node_id in hallucination_info.get("hallucination_nodes", []):
                if any(node.id == node_id for node in current_data.nodes):
                    remaining_hallucination_nodes.append(node_id)


            remaining_hallucination_rels = []
            for hal_rel in hallucination_info.get("hallucination_relationships", []):
                for rel in current_data.relationships:
                    if (rel.start_node_id == hal_rel["start_node_id"] and
                        rel.end_node_id == hal_rel["end_node_id"] and
                        rel.type == hal_rel["type"]):
                        remaining_hallucination_rels.append(hal_rel)
                        break

            cleanup_completed = (len(remaining_hallucination_nodes) == 0 and
                               len(remaining_hallucination_rels) == 0)

            return {
                "completed": cleanup_completed,
                "remaining_nodes": remaining_hallucination_nodes,
                "remaining_relationships": remaining_hallucination_rels,
                "total_nodes": len(current_data.nodes),
                "total_relationships": len(current_data.relationships)
            }

        except Exception as e:
            logger.error(f"Failed to verify cleanup completion: {e}")
            return {"completed": False, "error": str(e)}

scenario_service = ScenarioService()