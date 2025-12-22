import logging
import asyncio
from typing import Dict, List, Any, Optional
from ..config.llm_config import get_llm_config, is_llm_enabled
from .llm_service import LLMService
logger = logging.getLogger(__name__)
class NodeDisplayNameService:


    def __init__(self):
        self.llm_config = get_llm_config()
        self.llm_service = LLMService(self.llm_config) if self.llm_config else None
        self.enabled = is_llm_enabled()

    async def generate_display_name(self, node_properties: Dict[str, Any], node_labels: List[str] = None) -> str:
        if not self.enabled or not self.llm_service:

            return self._generate_fallback_name(node_properties, node_labels)
        try:

            prompt = self._build_display_name_prompt(node_properties, node_labels)

            response = await self.llm_service._call_llm(prompt)

            display_name = self._clean_display_name(response)

            if display_name:
                logger.debug(f"Generated display name: '{display_name}' for properties: {node_properties}")
                return display_name
            else:
                logger.warning(f"LLM generated empty display name, using fallback for properties: {node_properties}")
                return self._generate_fallback_name(node_properties, node_labels)

        except Exception as e:
            logger.error(f"Failed to generate display name via LLM: {e}")
            return self._generate_fallback_name(node_properties, node_labels)

    async def generate_display_names_batch(self, nodes: List[Dict[str, Any]]) -> Dict[str, str]:
        if not nodes:
            return {}

        display_names = {}


        semaphore = asyncio.Semaphore(5)

        async def process_node(node):
            async with semaphore:
                node_id = node.get('id')
                properties = {k: v for k, v in node.get('properties', {}).items() if k != 'id'}
                labels = node.get('labels', [])

                display_name = await self.generate_display_name(properties, labels)
                return node_id, display_name


        tasks = [process_node(node) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)


        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing node: {result}")
                continue

            node_id, display_name = result
            if node_id:
                display_names[node_id] = display_name

        logger.info(f"Generated display names for {len(display_names)} nodes")
        return display_names

    def _build_display_name_prompt(self, properties: Dict[str, Any], labels: List[str] = None) -> str:


        filtered_properties = {k: v for k, v in properties.items()
                             if k != 'id' and v is not None and str(v).strip()}
        prompt = "Generate a concise semantic display name (1-5 words) for this node.\n"
        if labels:
            prompt += f"\nLabels: {', '.join(labels)}"
        if filtered_properties:
            prompt += "\nProperties:"
            for key, value in filtered_properties.items():
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                prompt += f"\n  {key}: {value_str}"
        else:
            prompt += "\nProperties: No specific properties"
        prompt += "\nRequirements:\nPlease return the display name directly, without any explanation or additional text.\nExamples:"
        return prompt

    def _clean_display_name(self, raw_name: str) -> str:
        if not raw_name:
            return ""

        cleaned = raw_name.strip()

        import re

        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        cleaned = cleaned.strip()

        try:
            import json
            if cleaned.startswith('{') and cleaned.endswith('}'):
                parsed = json.loads(cleaned)

                for key in ['display_name', 'name', 'title']:
                    if key in parsed:
                        cleaned = str(parsed[key]).strip()
                        break
        except (json.JSONDecodeError, KeyError):

            pass

        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]

        cleaned = ' '.join(cleaned.split())

        max_chars = 30
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars].strip()


        if not cleaned or cleaned.lower() in ['node', 'unknown', 'unnamed node']:
            return ""

        if self._is_meaningless_value(cleaned):
            return ""
        return cleaned

    def _is_meaningless_value(self, value: str) -> bool:
        if not value:
            return True
        value = value.strip()

        if value.isdigit():
            return True

        if '-' in value and len(value) > 20:
            parts = value.split('-')
            if len(parts) >= 4 and all(len(p) > 0 for p in parts):
                return True

        if len(value) > 20 and value.replace('-', '').replace('_', '').isalnum() and ' ' not in value:
            return True
        return False
    def _generate_fallback_name(self, properties: Dict[str, Any], labels: List[str] = None) -> str:
        name_keys = ['name', 'title', 'label', 'description', 'field', 'type', 'category']
        for key in name_keys:
            if key in properties and properties[key]:
                value = str(properties[key]).strip()
                if value and not self._is_meaningless_value(value):

                    if len(value) > 15:
                        value = value[:15] + "..."
                    return value

        if labels:

            meaningful_labels = [label for label in labels
                               if label not in ['Node', 'Entity']]
            if meaningful_labels:
                return meaningful_labels[0]

        for key, value in properties.items():
            if key != 'id' and value:
                value_str = str(value).strip()
                if value_str and not self._is_meaningless_value(value_str):
                    if len(value_str) <= 20:
                        return value_str
                    else:
                        return value_str[:15] + "..."


        return "Entity"

node_display_name_service = NodeDisplayNameService()