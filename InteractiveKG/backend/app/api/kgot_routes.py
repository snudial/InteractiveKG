from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import re
from ..database.connection import db_connection
from ..services.external_kgot_service import (
    external_kgot_service as enhanced_kgot_service,
    KGOTSolveResult,
    KGOTRetrieveResult,
)
from ..services.kg_backup_service import kg_backup_service
from ..services.graph_service import GraphService
from ..config.cleanup_config import cleanup_config
router = APIRouter(prefix="/api/kgot", tags=["Enhanced KGOT"])
logger = logging.getLogger(__name__)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_identifier(value: str, what: str) -> str:
    """Validate a label/type/property name before interpolating it into Cypher."""
    if not _IDENTIFIER_RE.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {what}: {value!r}")
    return value


def _clear_knowledge_graph() -> None:
    """Delete every node and relationship."""
    db_connection.execute_write_query("MATCH (n) DETACH DELETE n")


def _add_node(node_id: str, label: str, node_type: str, properties: Dict[str, Any]) -> None:
    """MERGE a node by id with the given type label and properties."""
    node_type = _safe_identifier(node_type, "node type")
    set_parts = ["n.label = $label"]
    params: Dict[str, Any] = {"node_id": node_id, "label": label}
    for key, value in properties.items():
        _safe_identifier(key, "property name")
        set_parts.append(f"n.{key} = ${key}")
        params[key] = value
    cypher = f"MERGE (n:{node_type} {{id: $node_id}}) SET " + ", ".join(set_parts)
    db_connection.execute_write_query(cypher, params)


def _add_relationship(source_id: str, target_id: str, relationship_type: str,
                      properties: Dict[str, Any]) -> None:
    """MERGE a relationship between two nodes matched by id."""
    relationship_type = _safe_identifier(relationship_type, "relationship type")
    params: Dict[str, Any] = {"source_id": source_id, "target_id": target_id}
    cypher = (
        f"MATCH (a {{id: $source_id}}), (b {{id: $target_id}}) "
        f"MERGE (a)-[r:{relationship_type}]->(b)"
    )
    if properties:
        set_parts = []
        for key, value in properties.items():
            _safe_identifier(key, "property name")
            set_parts.append(f"r.{key} = ${key}")
            params[key] = value
        cypher += " SET " + ", ".join(set_parts)
    db_connection.execute_write_query(cypher, params)

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
                    logger.info(f"Post-solve auto-cleanup succeeded: removed {cleanup_result.get('successfully_deleted', 0)} duplicate relationships")
                elif cleanup_result:
                    logger.warning(f"Post-solve auto-cleanup partially succeeded: {cleanup_result}")
            except Exception as cleanup_error:
                if cleanup_config.should_continue_on_error():
                    logger.warning(f"Post-solve auto-cleanup failed (main functionality unaffected): {str(cleanup_error)}")
                else:
                    logger.error(f"Post-solve auto-cleanup failed: {str(cleanup_error)}")
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
        raise HTTPException(status_code=500, detail=f"Enhanced problem solving failed: {str(e)}")
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
        raise HTTPException(status_code=500, detail=f"Pure internal retrieval failed: {str(e)}")
@router.get("/status")
async def get_enhanced_kgot_status():
    """Report the enhanced KGOT service status."""
    try:

        is_available = enhanced_kgot_service.llm_enabled

        return {
            "available": is_available,
            "llm_enabled": enhanced_kgot_service.llm_enabled,
            "features": {
                "enhanced_problem_solving": is_available,
                "pure_internal_retrieval": is_available
            },
            "message": "Enhanced KGOT service is healthy" if is_available else "LLM not enabled; KGOT functionality unavailable"
        }

    except Exception as e:
        return {
            "available": False,
            "llm_enabled": False,
            "features": {
                "enhanced_problem_solving": False,
                "pure_internal_retrieval": False
            },
            "message": f"Enhanced KGOT service error: {str(e)}"
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
            "message": "Backup info fetched" if backup_info else "No backup data yet"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch backup info"
        }
@router.post("/backup/restore")
async def restore_from_backup():

    try:
        success = await kg_backup_service.restore_from_backup()
        if success:
            return {
                "success": True,
                "message": "Knowledge graph data restored"
            }
        else:
            return {
                "success": False,
                "message": "Knowledge graph restore failed; check the backup data"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Restore operation failed"
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
            raise HTTPException(status_code=404, detail=f"Dataset file not found: {dataset_file}")

        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        _clear_knowledge_graph()

        nodes_loaded = 0
        error_nodes_count = 0
        for node in dataset.get('nodes', []):
            _add_node(
                node_id=node['id'],
                label=node['label'],
                node_type=node['type'],
                properties=node.get('properties', {})
            )
            nodes_loaded += 1
            if node.get('properties', {}).get('error_flag'):
                error_nodes_count += 1

        for rel in dataset.get('relationships', []):
            _add_relationship(
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
            message=f"Loaded error dataset '{dataset['dataset_info']['name']}' with {error_nodes_count} error nodes"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load error dataset: {str(e)}")