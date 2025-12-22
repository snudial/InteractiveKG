import asyncio
import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import aiohttp
from urllib.parse import quote
logger = logging.getLogger(__name__)
@dataclass
class ExternalKnowledge:

    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    source: str
    confidence: float
    raw_content: str
@dataclass
class KnowledgeAcquisitionResult:

    success: bool
    knowledge: Optional[ExternalKnowledge]
    error: Optional[str] = None
    search_query: str = ""
    sources_count: int = 0
class ExternalKnowledgeService:


    def __init__(self):
        self.max_search_results = 3
        self.timeout = 10
        self._llm = None

    def _init_llm(self):

        if not self._llm:
            try:
                from ..config.llm_config import get_llm_config, is_llm_enabled
                if is_llm_enabled():
                    from kgot_simple import SimpleLLM
                    config = get_llm_config()

                    forced_model = 'gpt-4o-mini-2024-07-18'
                    self._llm = SimpleLLM(
                        api_key=config.api_key,
                        base_url='https://api.openai.com/v1',
                        model=forced_model,
                        temperature=0.0
                    )
                    logger.info(f"External knowledge service LLM initialized successfully, forced model: {forced_model}")
                else:
                    logger.warning("LLM not enabled, external knowledge acquisition will be limited")
            except Exception as e:
                logger.error(f"LLM initialization failed: {e}")
                self._llm = None

    async def acquire_knowledge_for_problem(self, problem: str, current_kg_context: str = "") -> KnowledgeAcquisitionResult:
        为特定问题获取外部知识

        Args:
            problem: 待解决的问题
            current_kg_context: 当前知识图谱上下文

        Returns:
            KnowledgeAcquisitionResult: 知识获取结果
        try:
            logger.info(f"开始为问题获取外部知识: {problem}")


            search_queries = await self._generate_search_queries(problem, current_kg_context)


            search_results = []
            for query in search_queries[:2]:
                results = await self._search_external_sources(query)
                search_results.extend(results)

            if not search_results:
                return KnowledgeAcquisitionResult(
                    success=False,
                    knowledge=None,
                    error="未找到相关外部信息",
                    search_query="; ".join(search_queries)
                )


            knowledge = await self._extract_structured_knowledge(problem, search_results)

            return KnowledgeAcquisitionResult(
                success=True,
                knowledge=knowledge,
                search_query="; ".join(search_queries),
                sources_count=len(search_results)
            )

        except Exception as e:
            logger.error(f"External knowledge acquisition failed: {e}")
            return KnowledgeAcquisitionResult(
                success=False,
                knowledge=None,
                error=str(e),
                search_query=problem
            )

    async def _generate_search_queries(self, problem: str, current_context: str) -> List[str]:

        try:
            self._init_llm()

            if not self._llm:

                return self._generate_rule_based_queries(problem)

            messages = [
                {
                    "role": "system",
Requirements:
                },
                {
                    "role": "user",
Current knowledge graph context: {current_context[:500]}
                }
            ]

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._llm.chat, messages)


            queries = [q.strip() for q in response.split('\n') if q.strip()]
            return queries[:3]

        except Exception as e:
            logger.error(f"Search query generation failed: {e}")
            return self._generate_rule_based_queries(problem)

    def _generate_rule_based_queries(self, problem: str) -> List[str]:


        keywords = re.findall(r'\b\w+\b', problem.lower())
        keywords = [k for k in keywords if len(k) > 2 and k not in ['what', 'how', 'why', 'where', 'when']]

        queries = []
        if len(keywords) >= 2:
            queries.append(' '.join(keywords[:3]))
            queries.append(' '.join(keywords[1:4]))
        else:
            queries.append(problem)

        return queries[:2]

    async def _search_external_sources(self, query: str) -> List[Dict[str, Any]]:

        try:






            logger.info(f"搜索外部源: {query}")


            mock_results = [
                {
                    "title": f"关于{query}的信息",
                    "content": f"这是关于{query}的详细信息。包含相关的实体、概念和关系。",
                    "source": "外部知识库",
                    "url": f"https://example.com/search?q={quote(query)}",
                    "confidence": 0.8
                }
            ]

            return mock_results

        except Exception as e:
            logger.error(f"外部搜索失败: {e}")
            return []

    async def _extract_structured_knowledge(self, problem: str, search_results: List[Dict[str, Any]]) -> ExternalKnowledge:

        try:
            self._init_llm()


            combined_content = "\n\n".join([
                f"Source: {result['source']}\nTitle: {result['title']}\nContent: {result['content']}"
                for result in search_results
            ])

            if not self._llm:

                return self._extract_rule_based_knowledge(problem, combined_content)

            messages = [
                {
                    "role": "system",
Output format:
{
  "entities": [
    {"name": "Entity name", "type": "Entity type", "properties": {"attribute": "value"}}
  ],
  "relationships": [
    {"source": "Source entity", "target": "Target entity", "type": "Relationship type", "properties": {"attribute": "value"}}
  ]
}
Requirements:
                },
                {
                    "role": "user",
External information:
{combined_content[:2000]}
                }
            ]

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._llm.chat, messages)


            try:
                knowledge_data = json.loads(response)
                return ExternalKnowledge(
                    entities=knowledge_data.get('entities', []),
                    relationships=knowledge_data.get('relationships', []),
                    source="External knowledge acquisition",
                    confidence=0.7,
                    raw_content=combined_content
                )
            except json.JSONDecodeError:
                logger.warning("LLM returned invalid JSON, using rule-based method")
                return self._extract_rule_based_knowledge(problem, combined_content)

        except Exception as e:
            logger.error(f"Structured knowledge extraction failed: {e}")
            return self._extract_rule_based_knowledge(problem, combined_content)

    def _extract_rule_based_knowledge(self, problem: str, content: str) -> ExternalKnowledge:


        entities = []
        relationships = []

        keywords = re.findall(r'\b[A-Za-z\u4e00-\u9fff]+\b', problem)
        for keyword in keywords[:5]:
            if len(keyword) > 1:
                entities.append({
                    "name": keyword,
                    "type": "concept",
                    "properties": {"source": "problem extraction"}
                })

        return ExternalKnowledge(
            entities=entities,
            relationships=relationships,
            source="rule extraction",
            confidence=0.5,
            raw_content=content
        )

external_knowledge_service = ExternalKnowledgeService()