from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any
import json
import logging
import os
from pathlib import Path
from ..models.chatbot_models import (
    ChatbotRequest, ChatbotResponse, ScenarioLoadRequest, ScenarioLoadResponse,
    UserTestProgressRequest, UserTestProgressResponse, IntegrationActionRequest,
    IntegrationActionResponse, TestScenario, TestPhase, AbstractionExplorationRequest,
    AbstractionExplorationResponse
)
from ..services.chatbot_service import chatbot_service
from ..services.scenario_service import scenario_service
from ..services.abstraction_exploration_service import abstraction_exploration_service
from ..services.graph_service import GraphService
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])
@router.post("/create-session")
async def create_session():

    try:
        session_id = chatbot_service.create_session()
        return {
            "session_id": session_id,
            "current_phase": TestPhase.CASE1_INTRO,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")
@router.post("/chat", response_model=ChatbotResponse)
async def chat(request: ChatbotRequest):

    try:
        response = await chatbot_service.process_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")
@router.get("/session/{session_id}")
async def get_session_info(session_id: str):

    try:
        session = chatbot_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        advance_button = chatbot_service.get_phase_advance_button(session)

        data_source_selection_buttons = chatbot_service.get_data_source_selection_buttons(session)
        return {
            "session_id": session.session_id,
            "current_phase": session.current_phase,
            "current_scenario": session.current_scenario,
            "progress_percentage": chatbot_service.get_progress_percentage(session),
            "phase_description": chatbot_service.phase_descriptions.get(session.current_phase, ""),
            "messages_count": len(session.messages),
            "case1_completed": session.case1_completed,
            "case2_completed": session.case2_completed,
            "advance_button": advance_button,
            "data_source_selection_buttons": data_source_selection_buttons
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话信息失败: {str(e)}")
@router.post("/load-scenario", response_model=ScenarioLoadResponse)
async def load_scenario(request: ScenarioLoadRequest):

    try:

        session = chatbot_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")


        result = scenario_service.load_scenario_to_database(request.scenario)

        if result["success"]:

            session.current_scenario = request.scenario
            session.scenario_data_loaded = True

            return ScenarioLoadResponse(
                session_id=request.session_id,
                scenario=request.scenario,
                data_loaded=True,
                nodes_count=result["nodes_count"],
                relationships_count=result["relationships_count"],
                success=True
            )
        else:
            return ScenarioLoadResponse(
                session_id=request.session_id,
                scenario=request.scenario,
                data_loaded=False,
                nodes_count=0,
                relationships_count=0,
                success=False,
                error=result.get("error", "未知错误")
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载场景失败: {str(e)}")
@router.post("/progress", response_model=UserTestProgressResponse)
async def update_progress(request: UserTestProgressRequest):

    try:
        session = chatbot_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        if request.action == "next_phase":
            success = chatbot_service.advance_phase(request.session_id, request.phase)
        elif request.action == "previous_phase":

            success = True
        elif request.action == "reset":
            session.current_phase = TestPhase.CASE1_INTRO
            session.current_scenario = None
            session.scenario_data_loaded = False
            session.case1_completed = False
            session.case2_completed = False
            session.selected_domain = None
            success = True
        elif request.action == "complete_case":
            if session.current_phase in [TestPhase.CASE1_INTRO, TestPhase.CASE1_LLM_RESPONSE,
                                         TestPhase.CASE1_EXPLORE_GRAPH, TestPhase.CASE1_IDENTIFY_ERRORS,
                                         TestPhase.CASE1_EDIT_CORRECT, TestPhase.CASE1_REQUERY_COMPARE]:
                session.case1_completed = True
            elif session.current_phase in [TestPhase.CASE2_INTRO, TestPhase.CASE2_LLM_RESPONSE,
                                           TestPhase.CASE2_EXPLORE_GRAPH, TestPhase.CASE2_IDENTIFY_ERRORS,
                                           TestPhase.CASE2_EDIT_CORRECT, TestPhase.CASE2_REQUERY_COMPARE]:
                session.case2_completed = True
            success = True
        else:
            success = False

        if success:
            progress = chatbot_service.get_progress_percentage(session)
            phase_desc = chatbot_service.phase_descriptions.get(session.current_phase, "")

            return UserTestProgressResponse(
                session_id=request.session_id,
                current_phase=session.current_phase,
                progress_percentage=progress,
                phase_description=phase_desc,
                next_instructions=f"当前阶段：{phase_desc}",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail="无效的进度更新操作")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新进度失败: {str(e)}")
@router.get("/scenario/{scenario}/info")
async def get_scenario_info(scenario: TestScenario):

    try:
        info = scenario_service.get_scenario_info(scenario)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取场景信息失败: {str(e)}")
@router.get("/scenario/{scenario}/target-question")
async def get_target_question(scenario: TestScenario):

    try:
        question = scenario_service.get_target_question(scenario)
        return {"target_question": question}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取目标问题失败: {str(e)}")
@router.post("/integration-action", response_model=IntegrationActionResponse)
async def execute_integration_action(request: IntegrationActionRequest):

    try:
        session = chatbot_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        result = {}
        executed = False

        if request.action_type == "highlight_nodes":

            node_ids = request.parameters.get("node_ids", [])
            result = {"highlighted_nodes": node_ids}
            executed = True

        elif request.action_type == "open_property_panel":

            node_id = request.parameters.get("node_id")
            result = {"panel_opened": True, "node_id": node_id}
            executed = True

        elif request.action_type == "trigger_search":

            query = request.parameters.get("query", "")
            result = {"search_triggered": True, "query": query}
            executed = True

        elif request.action_type == "load_data":

            scenario = request.parameters.get("scenario")
            if scenario:
                load_result = scenario_service.load_scenario_to_database(TestScenario(scenario))
                result = load_result
                executed = load_result["success"]

        return IntegrationActionResponse(
            session_id=request.session_id,
            action_type=request.action_type,
            executed=executed,
            result=result,
            success=executed
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行集成动作失败: {str(e)}")
@router.post("/scenario/{scenario}/correct-data")
async def apply_data_correction(scenario: TestScenario, node_id: str, updates: Dict[str, Any]):

    try:
        success = scenario_service.apply_data_correction(scenario, node_id, updates)
        return {
            "success": success,
            "node_id": node_id,
            "message": "数据修正成功" if success else "数据修正失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用数据修正失败: {str(e)}")
@router.delete("/hallucination/node/{node_id}")
async def remove_hallucination_node(node_id: str):

    try:
        success = scenario_service.remove_hallucination_node(node_id)
        return {
            "success": success,
            "node_id": node_id,
            "message": "幻觉节点删除成功" if success else "幻觉节点删除失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除幻觉节点失败: {str(e)}")
@router.delete("/hallucination/relationship")
async def remove_hallucination_relationship(
    start_node_id: str,
    end_node_id: str,
    rel_type: str
):

    try:
        success = scenario_service.remove_hallucination_relationship(
            start_node_id, end_node_id, rel_type
        )
        return {
            "success": success,
            "relationship": f"{start_node_id}->{end_node_id} ({rel_type})",
            "message": "幻觉关系删除成功" if success else "幻觉关系删除失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除幻觉关系失败: {str(e)}")
@router.get("/scenario/{scenario}/cleanup-status")
async def get_cleanup_status(scenario: TestScenario):

    try:
        status = scenario_service.validate_cleanup_completion(scenario)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取清理状态失败: {str(e)}")
@router.post("/abstraction-exploration", response_model=AbstractionExplorationResponse)
async def explore_abstraction(request: AbstractionExplorationRequest):

    try:
        response = await abstraction_exploration_service.explore_abstraction(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抽象探索失败: {str(e)}")
@router.get("/abstraction-exploration/levels")
async def get_abstraction_levels():

    try:
        return {
            "levels": {
                0: "完整视图 - 显示所有原始节点和关系，按标签分组着色",
                1: "具体层次 - 基于具体特征进行细粒度分组",
                2: "功能层次 - 按功能角色进行中等粒度分组",
                3: "概念层次 - 基于抽象概念进行高层次分组"
            },
            "modes": {
                "semantic": "语义抽象 - 基于节点属性和语义相似性进行分组",
                "structural": "结构抽象 - 基于图的拓扑结构和连接模式进行分组",
                "community": "社区抽象 - 基于社区检测算法识别紧密连接的节点群"
            },
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取抽象级别信息失败: {str(e)}")
@router.post("/advance-phase")
async def advance_phase(request: Dict[str, Any]):

    try:
        session_id = request.get("session_id")
        target_phase_str = request.get("target_phase")
        if not session_id:
            raise HTTPException(status_code=400, detail="缺少session_id参数")

        target_phase = None
        if target_phase_str:
            try:
                target_phase = TestPhase(target_phase_str)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的目标阶段: {target_phase_str}")

        success = chatbot_service.advance_phase(session_id, target_phase)
        if success:

            session = chatbot_service.get_session(session_id)

            advance_button = chatbot_service.get_phase_advance_button(session)

            data_source_selection_buttons = chatbot_service.get_data_source_selection_buttons(session)
            return {
                "success": True,
                "current_phase": session.current_phase if session else None,
                "advance_button": advance_button,
                "data_source_selection_buttons": data_source_selection_buttons or [],
                "message": "阶段推进成功"
            }
        else:
            return {
                "success": False,
                "message": "阶段推进失败"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"阶段推进失败: {str(e)}")
@router.post("/upload-custom-data")
async def upload_custom_data(
    file: UploadFile = File(...),
    session_id: str = None
):

    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")

        session = chatbot_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.current_phase not in [TestPhase.CASE1_INTRO, TestPhase.CASE2_INTRO]:
            raise HTTPException(
                status_code=400,
                detail=f"Custom data upload only allowed in CASE1_INTRO or CASE2_INTRO phase, current phase: {session.current_phase}"
            )

        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are allowed")

        content = await file.read()
        json_data = json.loads(content.decode('utf-8'))

        graph_service = GraphService()

        graph_service.clear_all_data()
        logger.info("Cleared existing graph data before importing custom data")

        result = await graph_service.import_json_data(json_data)
        logger.info(f"Successfully imported custom data: {len(result.nodes)} nodes, {len(result.relationships)} relationships")

        if session.current_phase == TestPhase.CASE1_INTRO:
            chatbot_service.advance_phase(session_id, TestPhase.CASE1_LLM_RESPONSE)
        elif session.current_phase == TestPhase.CASE2_INTRO:
            chatbot_service.advance_phase(session_id, TestPhase.CASE2_LLM_RESPONSE)
        return {
            "success": True,
            "message": "Custom data uploaded successfully",
            "nodes_count": len(result.nodes),
            "relationships_count": len(result.relationships),
            "data": {
                "nodes": [node.model_dump() for node in result.nodes],
                "relationships": [rel.model_dump() for rel in result.relationships]
            }
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload custom data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload custom data: {str(e)}")
@router.get("/sample-data/{filename}")
async def get_sample_data(filename: str):
    try:

        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")


        backend_dir = Path(__file__).parent.parent.parent
        sample_data_dir = backend_dir / "sample_data"
        file_path = sample_data_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Sample data file not found: {filename}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded sample data file: {filename}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load sample data file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load sample data: {str(e)}")