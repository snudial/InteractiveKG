from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from ..services.kgot_integration import enhanced_kgot_service, KGOTSolveResult, KGOTRetrieveResult
from ..services.kg_backup_service import kg_backup_service
from ..services.graph_service import GraphService
from ..config.cleanup_config import cleanup_config
router = APIRouter(prefix="/api/kgot", tags=["Enhanced KGOT"])
logger = logging.getLogger(__name__)

class EnhancedProblemSolveRequest(BaseModel):
    problem: str
    learn_from_solution: bool = True
    abstraction_level: Optional[int] = None
    abstraction_mode: str = "semantic"
class PureInternalRetrieveRequest(BaseModel):
    query: str
    abstraction_level: Optional[int] = None
    abstraction_mode: str = "semantic"
    view_mode: Optional[str] = "detailed"
class LoadErrorDataRequest(BaseModel):
    dataset_id: str

class EnhancedProblemSolveResponse(BaseModel):
    answer: str
    execution_time: float
    iterations: int
    kg_updates: int
    success: bool
    error: Optional[str] = None
    reasoning_steps: Optional[List[str]] = None
    should_refresh_graph: bool = True
class PureInternalRetrieveResponse(BaseModel):
    answer: str
    execution_time: float
    context_nodes: int
    success: bool
    error: Optional[str] = None
    retrieved_context: str = ""
class LoadErrorDataResponse(BaseModel):
    success: bool
    dataset_id: str
    nodes_loaded: int
    error_nodes_count: int
    message: str
    error: Optional[str] = None
@router.post("/enhanced-solve", response_model=EnhancedProblemSolveResponse)
async def enhanced_problem_solving(request: EnhancedProblemSolveRequest):
    try:
        result = await enhanced_kgot_service.enhanced_problem_solving(
            problem=request.problem,
            learn_from_solution=request.learn_from_solution,
            abstraction_level=request.abstraction_level,
            abstraction_mode=request.abstraction_mode
        )

        cleanup_result = None
        if result.success and result.kg_updates > 0 and cleanup_config.should_cleanup_after_kgot_solve():
            try:
                graph_service = GraphService()
                cleanup_result = graph_service.cleanup_service.auto_cleanup_after_kgot()
                if cleanup_result and cleanup_result.get('cleanup_success'):
                    logger.info(f"KGOT求解后自动清理成功: 删除了 {cleanup_result.get('successfully_deleted', 0)} 个重复关系")
                elif cleanup_result:
                    logger.warning(f"KGOT求解后自动清理部分成功: {cleanup_result}")
            except Exception as cleanup_error:
                if cleanup_config.should_continue_on_error():
                    logger.warning(f"KGOT求解后自动清理失败，但不影响主要功能: {str(cleanup_error)}")
                else:
                    logger.error(f"KGOT求解后自动清理失败: {str(cleanup_error)}")
                    raise cleanup_error
        return EnhancedProblemSolveResponse(
            answer=result.answer,
            execution_time=result.execution_time,
            iterations=result.iterations,
            kg_updates=result.kg_updates,
            success=result.success,
            error=result.error,
            reasoning_steps=result.reasoning_steps,
            should_refresh_graph=result.kg_updates > 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"增强问题求解失败: {str(e)}")
@router.post("/pure-internal-retrieve", response_model=PureInternalRetrieveResponse)
async def pure_internal_retrieval(request: PureInternalRetrieveRequest):
    try:
        result = await enhanced_kgot_service.pure_internal_retrieval(
            query=request.query,
            abstraction_level=request.abstraction_level,
            abstraction_mode=request.abstraction_mode,
            view_mode=request.view_mode
        )

        return PureInternalRetrieveResponse(
            answer=result.answer,
            execution_time=result.execution_time,
            context_nodes=result.context_nodes,
            success=result.success,
            error=result.error,
            retrieved_context=result.retrieved_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"纯内部检索失败: {str(e)}")
@router.get("/status")
async def get_enhanced_kgot_status():
    获取增强KGOT服务状态
    try:

        is_available = enhanced_kgot_service.llm_enabled

        return {
            "available": is_available,
            "llm_enabled": enhanced_kgot_service.llm_enabled,
            "features": {
                "enhanced_problem_solving": is_available,
                "pure_internal_retrieval": is_available
            },
            "message": "增强KGOT服务正常" if is_available else "LLM未启用，KGOT功能不可用"
        }

    except Exception as e:
        return {
            "available": False,
            "llm_enabled": False,
            "features": {
                "enhanced_problem_solving": False,
                "pure_internal_retrieval": False
            },
            "message": f"增强KGOT服务异常: {str(e)}"
        }

@router.post("/solve", response_model=EnhancedProblemSolveResponse)
async def solve_problem_compatibility(request: EnhancedProblemSolveRequest):

    return await enhanced_problem_solving(request)
@router.post("/retrieve", response_model=PureInternalRetrieveResponse)
async def retrieve_knowledge_compatibility(request: PureInternalRetrieveRequest):

    return await pure_internal_retrieval(request)

@router.get("/backup/info")
async def get_backup_info():

    try:
        backup_info = kg_backup_service.get_current_backup_info()
        return {
            "success": True,
            "backup_info": backup_info,
            "message": "备份信息获取成功" if backup_info else "暂无备份数据"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "获取备份信息失败"
        }
@router.post("/backup/restore")
async def restore_from_backup():

    try:
        success = await kg_backup_service.restore_from_backup()
        if success:
            return {
                "success": True,
                "message": "知识图谱数据恢复成功"
            }
        else:
            return {
                "success": False,
                "message": "知识图谱数据恢复失败，请检查备份数据"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "恢复操作异常"
        }
@router.post("/load-error-data", response_model=LoadErrorDataResponse)
async def load_error_dataset(request: LoadErrorDataRequest):

    try:
        import json
        import os
        from pathlib import Path

        dataset_file = f"{request.dataset_id}_dataset.json"
        dataset_path = Path(__file__).parent.parent.parent.parent / dataset_file
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"数据集文件不存在: {dataset_file}")

        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        await enhanced_kgot_service.clear_knowledge_graph()

        nodes_loaded = 0
        error_nodes_count = 0
        for node in dataset.get('nodes', []):
            await enhanced_kgot_service.add_node(
                node_id=node['id'],
                label=node['label'],
                node_type=node['type'],
                properties=node.get('properties', {})
            )
            nodes_loaded += 1
            if node.get('properties', {}).get('error_flag'):
                error_nodes_count += 1

        for rel in dataset.get('relationships', []):
            await enhanced_kgot_service.add_relationship(
                source_id=rel['source'],
                target_id=rel['target'],
                relationship_type=rel['type'],
                properties=rel.get('properties', {})
            )
        return LoadErrorDataResponse(
            success=True,
            dataset_id=request.dataset_id,
            nodes_loaded=nodes_loaded,
            error_nodes_count=error_nodes_count,
            message=f"成功加载错误数据集 '{dataset['dataset_info']['name']}'，包含 {error_nodes_count} 个错误节点"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载错误数据集失败: {str(e)}")