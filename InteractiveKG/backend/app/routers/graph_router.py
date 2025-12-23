from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import json
import logging
from ..models.graph_models import (
    NodeModel, RelationshipModel, GraphDataModel,
    NodeCreateRequest, NodeUpdateRequest,
    RelationshipCreateRequest, RelationshipUpdateRequest,
    GraphSearchRequest, GraphSearchResponse
)
from ..models.kgot_models import NodeExplanationRequest, NodeExplanationResponse
from ..services.graph_service import graph_service
from ..services.node_explanation_service import node_explanation_service
from ..services.node_display_name_service import node_display_name_service
from ..services.auto_display_name_processor import auto_display_name_processor
from ..database.connection import db_connection
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/graph", tags=["graph"])
@router.get("/health")
async def health_check():

    return {"status": "healthy", "message": "Graph API is running"}
@router.post("/upload", response_model=GraphDataModel)
async def upload_json_data(file: UploadFile = File(...)):
    try:

        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are allowed")

        content = await file.read()
        json_data = json.loads(content.decode('utf-8'))

        result = await graph_service.import_json_data(json_data)
        logger.info(f"Successfully imported {len(result.nodes)} nodes and {len(result.relationships)} relationships")

        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to upload JSON data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to import data: {str(e)}")
@router.post("/import", response_model=GraphDataModel)
async def import_json_data(json_data: Dict[str, Any]):
    try:

        result = await graph_service.import_json_data(json_data)
        logger.info(f"Successfully imported {len(result.nodes)} nodes and {len(result.relationships)} relationships")

        return result
    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to import JSON data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to import data: {str(e)}")
@router.post("/validate-data")
async def validate_data_only(json_data: Dict[str, Any]):
    try:
        from ..services.data_validation_service import data_validation_service

        validated_data, validation_report = data_validation_service.validate_and_preprocess(json_data)
        return {
            "success": validation_report.is_valid,
            "validation_report": validation_report.to_dict(),
            "preview": {
                "sample_nodes": validated_data.get('nodes', [])[:3],
                "sample_relationships": validated_data.get('relationships', [])[:3]
            }
        }
    except Exception as e:
        logger.error(f"Failed to validate data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate data: {str(e)}")
@router.get("/data", response_model=GraphDataModel)
async def get_all_graph_data():

    try:
        result = await graph_service.get_all_graph_data()
        return result
    except Exception as e:
        logger.error(f"Failed to get graph data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data: {str(e)}")
@router.post("/nodes", response_model=NodeModel)
async def create_node(node_request: NodeCreateRequest):

    try:
        result = await graph_service.create_node(node_request)
        return result
    except Exception as e:
        logger.error(f"Failed to create node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create node: {str(e)}")
@router.get("/nodes/{node_id}", response_model=NodeModel)
async def get_node(node_id: str):

    try:
        result = graph_service.get_node(node_id)
        if not result:
            raise HTTPException(status_code=404, detail="Node not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve node: {str(e)}")
@router.put("/nodes/{node_id}", response_model=NodeModel)
async def update_node(node_id: str, update_request: NodeUpdateRequest):

    try:
        result = graph_service.update_node(node_id, update_request)
        if not result:
            raise HTTPException(status_code=404, detail="Node not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update node: {str(e)}")
@router.delete("/nodes/{node_id}")
async def delete_node(node_id: str):

    try:
        success = graph_service.delete_node(node_id)
        if not success:
            raise HTTPException(status_code=404, detail="Node not found")
        return {"message": "Node deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")
@router.post("/relationships", response_model=RelationshipModel)
async def create_relationship(rel_request: RelationshipCreateRequest):

    try:
        result = graph_service.create_relationship(rel_request)
        return result
    except Exception as e:
        logger.error(f"Failed to create relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create relationship: {str(e)}")
@router.get("/relationships/{rel_id}", response_model=RelationshipModel)
async def get_relationship(rel_id: str):

    try:
        result = graph_service.get_relationship(rel_id)
        if not result:
            raise HTTPException(status_code=404, detail="Relationship not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve relationship: {str(e)}")
@router.put("/relationships/{rel_id}", response_model=RelationshipModel)
async def update_relationship(rel_id: str, update_request: RelationshipUpdateRequest):

    try:
        result = graph_service.update_relationship(rel_id, update_request)
        if not result:
            raise HTTPException(status_code=404, detail="Relationship not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update relationship: {str(e)}")
@router.delete("/relationships/{rel_id}")
async def delete_relationship(rel_id: str):

    try:
        success = graph_service.delete_relationship(rel_id)
        if not success:
            raise HTTPException(status_code=404, detail="Relationship not found")
        return {"message": "Relationship deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete relationship: {str(e)}")
@router.delete("/data")
async def clear_all_data():

    try:
        graph_service.clear_all_data()
        return {"message": "All data cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")
@router.get("/export")
async def export_graph_data():

    try:
        result = await graph_service.get_all_graph_data()
        return JSONResponse(content=result.dict())
    except Exception as e:
        logger.error(f"Failed to export data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")
@router.get("/grouping-analysis")
async def get_node_grouping_analysis():

    try:
        analysis = await graph_service.analyze_node_grouping()
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze node grouping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze node grouping: {str(e)}")
@router.get("/schema-analysis")
async def get_property_schema_analysis():

    try:
        schema = await graph_service.analyze_property_schema()
        return schema
    except Exception as e:
        logger.error(f"Failed to analyze property schema: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze property schema: {str(e)}")
@router.get("/hierarchical-analysis")
async def get_hierarchical_analysis(
    abstraction_level: int = 0,
    mode: str = "unified",
    use_llm: bool = True,
    query_context: str = None
):
    try:
        if abstraction_level < 0 or abstraction_level > 3:
            raise HTTPException(status_code=400, detail="Abstraction level must be between 0 and 3")

        analysis = await graph_service.analyze_hierarchical_abstraction(
            abstraction_level=abstraction_level,
            mode="unified",
            use_llm=True,
            query_context=query_context
        )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze hierarchical structure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze hierarchical structure: {str(e)}")
@router.get("/community-detail")
async def get_community_detail(
    community_id: str,
    abstraction_level: int = 1
):
    try:

        if abstraction_level == 0:
            raise HTTPException(status_code=400, detail="Community details are not available at abstraction level 0 (full view)")
        if abstraction_level < 0 or abstraction_level > 3:
            raise HTTPException(status_code=400, detail="Abstraction level must be between 0 and 3")

        logger.info(f"Fetching hierarchical analysis for community '{community_id}' at level {abstraction_level}")
        analysis = await graph_service.analyze_hierarchical_abstraction(
            abstraction_level=abstraction_level,
            mode="unified",
            use_llm=True,
            query_context=None
        )

        detailed_view = analysis.get("detailed_view", {})
        all_nodes = detailed_view.get("nodes", [])
        all_edges = detailed_view.get("edges", [])
        logger.info(f"Total nodes in detailed_view: {len(all_nodes)}, Total edges: {len(all_edges)}")

        community_nodes = [
            node for node in all_nodes
            if node.get("community_id") == community_id or node.get("community_name") == community_id
        ]
        logger.info(f"Found {len(community_nodes)} nodes for community '{community_id}'")
        if not community_nodes:

            available_communities = set()
            for node in all_nodes:
                if node.get("community_name"):
                    available_communities.add(node.get("community_name"))
            logger.error(f"Community '{community_id}' not found. Available communities: {available_communities}")
            raise HTTPException(status_code=404, detail=f"Community '{community_id}' not found. Available: {list(available_communities)[:5]}")

        community_node_ids = {node["id"] for node in community_nodes}

        community_edges = [
            edge for edge in all_edges
            if edge.get("source") in community_node_ids and edge.get("target") in community_node_ids
        ]

        community_view = analysis.get("community_view", {})
        community_info = None
        for comm in community_view.get("nodes", []):
            if comm.get("id") == community_id or comm.get("name") == community_id:
                community_info = comm
                break
        return {
            "community_id": community_id,
            "community_info": community_info,
            "nodes": community_nodes,
            "edges": community_edges,
            "node_count": len(community_nodes),
            "edge_count": len(community_edges),
            "abstraction_level": abstraction_level
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get community detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get community detail: {str(e)}")
@router.get("/enhanced-analysis")
async def get_enhanced_analysis(
    domain: str = "通用",
    abstraction_level: int = 3
):
    try:
        if abstraction_level < 2 or abstraction_level > 5:
            raise HTTPException(status_code=400, detail="Abstraction level must be between 2 and 5")
        valid_domains = ["医疗", "金融", "学术", "通用"]
        if domain not in valid_domains:
            raise HTTPException(status_code=400, detail=f"Domain must be one of: {valid_domains}")
        result = await graph_service.analyze_enhanced_abstraction(domain, abstraction_level)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform enhanced analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform enhanced analysis: {str(e)}")
@router.post("/load-sample-data")
async def load_sample_data(sample_data: dict):
    try:

        graph_service.clear_all_data()

        result = await graph_service.load_sample_data_to_database(sample_data)
        return {
            "success": True,
            "message": "Sample data loaded successfully",
            "nodes_created": result.get("nodes_created", 0),
            "relationships_created": result.get("relationships_created", 0)
        }
    except Exception as e:
        logger.error(f"Failed to load sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load sample data: {str(e)}")
@router.post("/generate-display-names")
async def generate_display_names():
    try:
        logger.info("开始为所有节点生成语义化展示名称...")

        with db_connection.get_session() as session:
            nodes_query = "MATCH (n) RETURN n.id as id, labels(n) as labels, properties(n) as properties"
            nodes_result = session.run(nodes_query)
            nodes_data = []
            for record in nodes_result:
                node_id = record["id"]
                if node_id is None:
                    continue
                nodes_data.append({
                    'id': str(node_id),
                    'labels': record["labels"] or ['Entity'],
                    'properties': record["properties"] or {}
                })
        if not nodes_data:
            return {"message": "没有找到需要处理的节点", "processed_count": 0}

        display_names = await node_display_name_service.generate_display_names_batch(nodes_data)

        updated_count = 0
        with db_connection.get_session() as session:
            for node_id, display_name in display_names.items():
                try:
                    update_query = """
                    MATCH (n {id: $node_id})
                    SET n.display_name = $display_name
                    RETURN n.id as id
                    """
                    result = session.run(update_query, {
                        "node_id": node_id,
                        "display_name": display_name
                    })
                    if result.single():
                        updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update display_name for node {node_id}: {e}")
                    continue
        logger.info(f"成功为 {updated_count} 个节点生成了语义化展示名称")
        return {
            "message": f"成功为 {updated_count} 个节点生成了语义化展示名称",
            "total_nodes": len(nodes_data),
            "processed_count": updated_count,
            "success_rate": f"{(updated_count / len(nodes_data) * 100):.1f}%" if nodes_data else "0%"
        }
    except Exception as e:
        logger.error(f"Failed to generate display names: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成展示名称失败: {str(e)}")
@router.get("/display-name-status")
async def get_display_name_status():
    try:
        status = auto_display_name_processor.get_status()
        return {
            "status": "success",
            "processor_status": status,
            "message": "自动化处理器状态获取成功"
        }
    except Exception as e:
        logger.error(f"Failed to get display name processor status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
@router.post("/ensure-display-names")
async def ensure_display_names(force_check: bool = False):
    try:
        result = await auto_display_name_processor.ensure_display_names(force_check=force_check)
        return {
            "status": "success",
            "result": result,
            "message": "自动化展示名称处理完成"
        }
    except Exception as e:
        logger.error(f"Failed to ensure display names: {str(e)}")
        raise HTTPException(status_code=500, detail=f"自动化处理失败: {str(e)}")
@router.post("/reset-display-name-processor")
async def reset_display_name_processor():
    try:
        auto_display_name_processor.reset_processor()
        return {
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Failed to reset processor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置处理器失败: {str(e)}")
@router.post("/process-data-change")
async def process_data_change(node_ids: List[str] = None):
    try:
        result = await auto_display_name_processor.process_data_change_event(node_ids)
        return {
            "status": "success",
            "result": result,
            "message": "数据变化事件处理完成"
        }
    except Exception as e:
        logger.error(f"Failed to process data change event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据变化事件处理失败: {str(e)}")
@router.post("/validate-reasoning")
async def validate_reasoning(
    reasoning_query: str,
    domain: str = "通用"
):
    try:
        if not reasoning_query.strip():
            raise HTTPException(status_code=400, detail="Reasoning query cannot be empty")
        valid_domains = ["医疗", "金融", "学术", "通用"]
        if domain not in valid_domains:
            raise HTTPException(status_code=400, detail=f"Domain must be one of: {valid_domains}")
        result = graph_service.validate_reasoning(reasoning_query, domain)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate reasoning: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate reasoning: {str(e)}")
@router.post("/explain-node", response_model=NodeExplanationResponse)
async def explain_node(request: NodeExplanationRequest):
    try:
        logger.info(f"开始解释节点: {request.node_id}, 类型: {request.explanation_type}")
        result = await node_explanation_service.explain_node(
            node_id=request.node_id,
            node_properties=request.node_properties,
            connected_nodes=request.connected_nodes,
            explanation_type=request.explanation_type,
            abstraction_level=request.abstraction_level,
            abstraction_mode=request.abstraction_mode
        )
        logger.info(f"节点解释完成: {request.node_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to explain node {request.node_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to explain node: {str(e)}")