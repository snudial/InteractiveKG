import time
import logging
from typing import List, Dict, Any, Optional
from ..models.kgot_models import (
    NodeExplanationRequest, NodeExplanationResponse,
    ConnectedNodeInfo, ExplanationType
)
from ..config.llm_config import get_llm_config
from ..services.llm_service import LLMService
logger = logging.getLogger(__name__)
class NodeExplanationService:


    def __init__(self):
        self.llm_config = get_llm_config()
        self.llm_service = LLMService(self.llm_config) if self.llm_config else None
        self.explanation_cache = {}
        self.last_request_time = 0
        self.min_request_interval = 1.0

    async def explain_node(
        self,
        node_id: str,
        node_properties: Dict[str, Any],
        connected_nodes: List[ConnectedNodeInfo],
        explanation_type: ExplanationType,
        abstraction_level: Optional[int] = 3,
        abstraction_mode: Optional[str] = "semantic"
    ) -> NodeExplanationResponse:
        start_time = time.time()

        try:

            cache_key = self._generate_cache_key(
                node_id, explanation_type, abstraction_level, abstraction_mode
            )

            if cache_key in self.explanation_cache:
                cached_result = self.explanation_cache[cache_key]
                cached_result.cached = True
                cached_result.execution_time = time.time() - start_time
                logger.info(f"Returning node explanation from cache: {node_id}")
                return cached_result


            node_name = self._get_node_display_name(node_properties)


            connected_desc = self._build_connected_nodes_description(connected_nodes)


            if explanation_type == ExplanationType.SEMANTIC:
                prompt = self._build_semantic_explanation_prompt(
                    node_name, node_properties, connected_desc, abstraction_level, abstraction_mode
                )
            else:
                prompt = self._build_reasoning_explanation_prompt(
                    node_name, node_properties, connected_desc, abstraction_level, abstraction_mode
                )


            explanation = await self._call_llm_for_explanation(prompt)


            result = NodeExplanationResponse(
                success=True,
                explanation=explanation,
                explanation_type=explanation_type,
                node_id=node_id,
                execution_time=time.time() - start_time,
                cached=False
            )


            self.explanation_cache[cache_key] = result

            logger.info(f"Node explanation generated: {node_id}, type: {explanation_type}")
            return result

        except Exception as e:
            logger.error(f"Node explanation failed: {node_id}, error: {str(e)}")
            return NodeExplanationResponse(
                success=False,
                explanation="",
                explanation_type=explanation_type,
                node_id=node_id,
                execution_time=time.time() - start_time,
                error=f"Explanation generation failed: {str(e)}",
                cached=False
            )

    def _generate_cache_key(
        self,
        node_id: str,
        explanation_type: ExplanationType,
        abstraction_level: int,
        abstraction_mode: str
    ) -> str:

        return f"{node_id}_{explanation_type.value}_{abstraction_level}_{abstraction_mode}"

    def _get_node_display_name(self, node_properties: Dict[str, Any]) -> str:

        return (
            node_properties.get('displayName') or
            node_properties.get('name') or
            node_properties.get('title') or
            node_properties.get('id', 'Unknown Node')
        )

    def _build_connected_nodes_description(self, connected_nodes: List[ConnectedNodeInfo]) -> str:

        if not connected_nodes:
            return "No directly connected nodes"

        descriptions = []
        for node in connected_nodes[:5]:
            node_name = node.name or node.id
            descriptions.append(f"{node_name}({node.type}) connected via relationship {node.relationship_type}")

        if len(connected_nodes) > 5:
            descriptions.append(f"and {len(connected_nodes) - 5} more nodes")

        return ", ".join(descriptions)

    def _build_semantic_explanation_prompt(
        self,
        node_name: str,
        node_properties: Dict[str, Any],
        connected_desc: str,
        abstraction_level: int,
        abstraction_mode: str
    ) -> str:

        node_type = node_properties.get('type', 'Unknown Type')
        prompt = f"""Node Info:
- Name: {node_name}
- Type: {node_type}
- Abstraction Level: {abstraction_level}
- Abstraction Mode: {abstraction_mode}
Connections: {connected_desc}
Please explain briefly and clearly:
"""
        return prompt

    def _build_reasoning_explanation_prompt(
        self,
        node_name: str,
        node_properties: Dict[str, Any],
        connected_desc: str,
        abstraction_level: int,
        abstraction_mode: str
    ) -> str:

        node_type = node_properties.get('type', 'Unknown Type')
        prompt = f"""Node Info:
- Name: {node_name}
- Type: {node_type}
- Abstraction Level: {abstraction_level}
- Abstraction Mode: {abstraction_mode}
Connections: {connected_desc}
Explain the reasoning process:
Answer in English. Explain the AI's reasoning process to help users understand why this structure was generated."""
        return prompt

    async def _call_llm_for_explanation(self, prompt: str) -> str:

        import asyncio

        if not self.llm_service or not self.llm_service.client:
            return "LLM service not configured; cannot generate explanation. Please check API key."

        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: waiting {wait_time:.2f}s before next request")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()
        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:

                payload = {
                    "model": "gpt-4o-mini-2024-07-18",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a knowledge graph expert who explains semantic relationships between nodes and AI reasoning processes. Answer in concise, clear English."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3
                }
                headers = {
                    "Authorization": f"Bearer {self.llm_service.config.api_key}",
                    "Content-Type": "application/json"
                }
                response = await self.llm_service.client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.llm_service.config.timeout
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get('choices') and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        return content.strip()
                    else:
                        return "LLM did not return a valid response. Please try again later."

                elif response.status_code == 429:

                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        wait_time = int(retry_after)
                    else:

                        wait_time = base_delay * (2 ** attempt)

                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_text = response.text
                        logger.error(f"OpenAI API rate limit error after {max_retries} attempts: {error_text}")
                        return f"API rate limit exceeded. Please wait a moment and try again. (Error: {error_text[:100]})"

                elif response.status_code == 401:

                    logger.error(f"OpenAI API authentication error: {response.text}")
                    return "API authentication failed. Please check your API key configuration."

                elif response.status_code == 500 or response.status_code == 502 or response.status_code == 503:

                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        logger.warning(f"OpenAI API server error ({response.status_code}). Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"OpenAI API server error after {max_retries} attempts: {response.status_code} - {response.text}")
                        return f"OpenAI API server error. Please try again later. (Status: {response.status_code})"

                else:

                    error_text = response.text
                    logger.error(f"OpenAI API error: {response.status_code} - {error_text}")
                    return f"API call failed (status: {response.status_code}). Please try again later. (Error: {error_text[:100]})"
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(f"Request timeout. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error("Request timeout after all retries")
                    return "Request timeout. Please try again later."

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(f"LLM call failed: {str(e)}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"LLM call failed after {max_retries} attempts: {str(e)}")
                    return f"Explanation generation failed: {str(e)}. Please try again later or check LLM configuration."

        return "Failed to generate explanation after multiple attempts. Please try again later."

node_explanation_service = NodeExplanationService()