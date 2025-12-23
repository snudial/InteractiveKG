import json
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import httpx
import logging
from ..models.graph_models import GraphDataModel, NodeModel
logger = logging.getLogger(__name__)
class LLMProvider(Enum):
    OPENAI_GPT4O_MINI = "openai_gpt4o_mini"
    DISABLED = "disabled"

@dataclass
class LLMConfig:
    provider: LLMProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    timeout: int = 30
    max_retries: int = 2
class LLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.cache: Dict[str, Any] = {}
        self.client = None
        self._initialize_client()

    def _initialize_client(self):

        if self.config.provider == LLMProvider.OPENAI_GPT4O_MINI:

            if self.config.model_name and "gpt-4o-mini" not in self.config.model_name:
                logger.warning(f"强制覆盖模型 '{self.config.model_name}' 为 'gpt-4o-mini-2024-07-18'")
                self.config.model_name = "gpt-4o-mini-2024-07-18"
            self.client = httpx.AsyncClient(
                base_url="https://api.openai.com/v1",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=self.config.timeout
            )
        else:

            raise ValueError(f"不支持的LLM提供商: {self.config.provider}. 只允许使用 GPT-4o-mini")

    def _generate_cache_key(self, data: str, abstraction_level: int, mode: str) -> str:

        content = f"{data}_{abstraction_level}_{mode}"
        return hashlib.md5(content.encode()).hexdigest()

    async def analyze_graph_structure(self,
                                    graph_data: GraphDataModel,
                                    abstraction_level: int,
                                    mode: str = "semantic") -> Optional[Dict[str, Any]]:
        if self.config.provider == LLMProvider.DISABLED:
            return None


        data_summary = self._create_data_summary(graph_data)
        cache_key = self._generate_cache_key(data_summary, abstraction_level, mode)


        if cache_key in self.cache:
            logger.info(f"Using cached LLM response for {mode} analysis")
            return self.cache[cache_key]

        try:

            prompt = self._create_analysis_prompt(graph_data, abstraction_level, mode)


            response = await self._call_llm(prompt)

            if response:

                parsed_result = self._parse_llm_response(response, graph_data)

                if parsed_result:

                    self.cache[cache_key] = parsed_result
                    logger.info(f"Successfully cached LLM analysis for {mode} mode")
                    return parsed_result

        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")

        return None

    def _create_data_summary(self, graph_data: GraphDataModel) -> str:

        node_types = {}
        for node in graph_data.nodes:
            node_type = node.labels[0] if node.labels else "Unknown"
            node_types[node_type] = node_types.get(node_type, 0) + 1

        rel_types = {}
        for rel in graph_data.relationships:
            rel_types[rel.type] = rel_types.get(rel.type, 0) + 1

        return f"nodes:{len(graph_data.nodes)}_types:{sorted(node_types.items())}_rels:{len(graph_data.relationships)}_rel_types:{sorted(rel_types.items())}"

    def _create_analysis_prompt(self, graph_data: GraphDataModel, abstraction_level: int, mode: str) -> str:


        node_analysis = self._analyze_nodes(graph_data)
        relationship_analysis = self._analyze_relationships(graph_data)


        target_groups = self._calculate_target_groups(len(graph_data.nodes), abstraction_level)

        prompt = f"""**Graph Overview:**
- Total nodes: {len(graph_data.nodes)}
- Total relationships: {len(graph_data.relationships)}
- Target abstraction level: {abstraction_level} (1=detailed, 5=highly abstract)
- Analysis mode: {mode}
- Target number of groups: {target_groups}
**Node Analysis:**
{node_analysis}
**Relationship Analysis:**
{relationship_analysis}
**Task:** Based on the {mode} analysis mode and abstraction level {abstraction_level}, suggest {target_groups} intelligent groups that:
**Response Format (JSON only):**
{{
    "groups": {{
        "group_name_1": {{
            "nodes": ["node_id_1", "node_id_2", ...],
            "description": "Brief description of this group",
            "rationale": "Why these nodes belong together"
        }},
        "group_name_2": {{
            "nodes": ["node_id_3", "node_id_4", ...],
            "description": "Brief description of this group",
            "rationale": "Why these nodes belong together"
        }}
    }},
    "abstraction_strategy": "Brief explanation of the overall grouping strategy",
    "confidence": 0.85
}}
"""
        return prompt
    def _analyze_nodes(self, graph_data: GraphDataModel) -> str:

        node_types = {}
        sample_properties = {}
        for node in graph_data.nodes:
            node_type = node.labels[0] if node.labels else "Unknown"
            node_types[node_type] = node_types.get(node_type, 0) + 1

            if node_type not in sample_properties and node.properties:
                sample_properties[node_type] = list(node.properties.keys())[:3]
        analysis = []
        for node_type, count in sorted(node_types.items()):
            props = sample_properties.get(node_type, [])
            props_str = f" (properties: {', '.join(props)})" if props else ""
            analysis.append(f"- {node_type}: {count} nodes{props_str}")
        return "\n".join(analysis)
    def _analyze_relationships(self, graph_data: GraphDataModel) -> str:

        rel_types = {}
        rel_patterns = {}
        for rel in graph_data.relationships:
            rel_types[rel.type] = rel_types.get(rel.type, 0) + 1

            source_node = next((n for n in graph_data.nodes if n.id == rel.start_node_id), None)
            target_node = next((n for n in graph_data.nodes if n.id == rel.end_node_id), None)
            if source_node and target_node:
                source_type = source_node.labels[0] if source_node.labels else "Unknown"
                target_type = target_node.labels[0] if target_node.labels else "Unknown"
                pattern = f"{source_type} -> {target_type}"
                rel_patterns[pattern] = rel_patterns.get(pattern, 0) + 1
        analysis = []
        for rel_type, count in sorted(rel_types.items()):
            analysis.append(f"- {rel_type}: {count} relationships")
        if rel_patterns:
            analysis.append("\nCommon patterns:")
            for pattern, count in sorted(rel_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                analysis.append(f"- {pattern}: {count} times")
        return "\n".join(analysis)
    def _calculate_target_groups(self, total_nodes: int, abstraction_level: int) -> int:

        if abstraction_level == 1:
            return min(15, max(8, total_nodes // 3))
        elif abstraction_level <= 3:
            return min(9, max(5, total_nodes // 6))
        else:
            return min(5, max(3, total_nodes // 10))
    async def _call_llm(self, prompt: str) -> Optional[str]:

        if not self.client:
            return None
        try:
            if self.config.provider == LLMProvider.OPENAI_GPT4O_MINI:
                return await self._call_openai(prompt)
            elif self.config.provider == LLMProvider.OLLAMA_LOCAL:
                return await self._call_ollama(prompt)
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            return None
    async def _call_openai(self, prompt: str) -> Optional[str]:


        forced_model = "gpt-4o-mini-2024-07-18"
        payload = {
            "model": forced_model,
            "messages": [
                {"role": "system", "content": "You are an expert graph analyst. Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _parse_llm_response(self, response: str, graph_data: GraphDataModel) -> Optional[Dict[str, Any]]:

        try:

            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            parsed = json.loads(response)

            if "groups" not in parsed:
                logger.error("LLM response missing 'groups' field")
                return None

            all_node_ids = {node.id for node in graph_data.nodes}
            validated_groups = {}
            for group_name, group_data in parsed["groups"].items():
                if "nodes" not in group_data:
                    continue

                valid_nodes = [nid for nid in group_data["nodes"] if nid in all_node_ids]
                if valid_nodes:
                    validated_groups[group_name] = {
                        "nodes": valid_nodes,
                        "description": group_data.get("description", ""),
                        "rationale": group_data.get("rationale", "")
                    }
            if not validated_groups:
                logger.error("No valid groups found in LLM response")
                return None
            return {
                "groups": validated_groups,
                "abstraction_strategy": parsed.get("abstraction_strategy", ""),
                "confidence": parsed.get("confidence", 0.5),
                "source": "llm_analysis"
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error validating LLM response: {str(e)}")
            return None
    async def close(self):

        if self.client:
            await self.client.aclose()