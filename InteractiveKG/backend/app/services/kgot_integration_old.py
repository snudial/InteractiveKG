import logging
from typing import Optional
from .external_kgot_service import external_kgot_service, KGOTSolveResult, KGOTRetrieveResult
logger = logging.getLogger(__name__)
class EnhancedKGOTService:


    def __init__(self):
        self.db = db_connection

        self._kg = None
        self._llm = None
        self._solver = None
        self._retriever = None
        self._llm_config = None
        self._llm_enabled = None
    def _get_llm_config(self):

        if self._llm_config is None:

            from dotenv import load_dotenv
            load_dotenv()
            self._llm_config = get_llm_config()
            self._llm_enabled = is_llm_enabled()
            if self._llm_config:
                logger.info(f"LLM配置已加载: {self._llm_config.provider}, 模型: {self._llm_config.model_name}")
            else:
                logger.warning("LLM配置未找到或已禁用")
        return self._llm_config
    def _is_llm_enabled(self):

        self._get_llm_config()
        return self._llm_enabled
    def _init_kgot_components(self, require_llm=True):
        初始化 KGOT 组件
        Args:
            require_llm: 是否要求LLM必须启用

        llm_config = self._get_llm_config()
        llm_enabled = self._is_llm_enabled()
        if require_llm and not llm_enabled:
            raise ValueError("LLM 未启用，无法使用需要LLM的 KGOT 功能")

        try:

            import sys
            import os

            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from kgot_simple import SimpleKG, SimpleLLM, KGLLMSolver, KGLLMRetriever


            self._kg = SimpleKG(
                uri=self.db.uri,
                username=self.db.username,
                password=self.db.password
            )


            forced_model_name = 'gpt-4o-mini-2024-07-18'
            api_key = getattr(llm_config, 'api_key', None)
            base_url = 'https://api.openai.com/v1'

            config_model = getattr(llm_config, 'model_name', None)
            if config_model and config_model != forced_model_name:
                logger.warning(f"KGOT服务强制覆盖模型 '{config_model}' 为 '{forced_model_name}'")

            if llm_config.provider.value != 'openai_gpt4o_mini':
                logger.warning(f"KGOT服务不支持提供商 '{llm_config.provider.value}'，强制使用 OpenAI GPT-4o-mini")
            self._llm = SimpleLLM(
                model=forced_model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=0.0
            )

            self._solver = KGLLMSolver(self._kg, self._llm, max_iterations=3)
            self._retriever = KGLLMRetriever(self._kg, self._llm)

            logger.info("KGOT 组件初始化成功")

        except Exception as e:
            logger.error(f"KGOT 组件初始化失败: {e}")
            raise

    @property
    def kg(self):
        if self._kg is None:
            self._init_kgot_components()
        return self._kg

    @property
    def llm(self):
        if self._llm is None:
            self._init_kgot_components()
        return self._llm

    @property
    def solver(self):
        if self._solver is None:
            self._init_kgot_components()
        return self._solver

    @property
    def retriever(self):
        if self._retriever is None:
            self._init_kgot_components()
        return self._retriever
    @property
    def llm_enabled(self):

        return self._is_llm_enabled()

    async def enhanced_problem_solving(self, problem: str, learn_from_solution: bool = True, abstraction_level: int = None, abstraction_mode: str = "semantic") -> KGOTSolveResult:
        阶段2: 外部知识获取与KG更新循环
        阶段3: 知识充足性检查
        阶段4: 基于充实KG的多轮推理求解（追踪推理过程）
        阶段5: 返回结果
        Args:
            problem: 待求解的问题
            learn_from_solution: 是否从解决方案中学习并更新知识图谱
            abstraction_level: 层级抽象级别，None表示使用原始数据
            abstraction_mode: 抽象模式

        start_time = time.time()
        kg_updates = 0
        current_answer = ""
        max_knowledge_iterations = 3
        max_reasoning_iterations = 3
        knowledge_acquisition_log = []
        reasoning_steps = []
        try:
            logger.info(f"开始主动智能问题求解: {problem}")
            logger.info("假设知识图谱为空状态，开始外部知识获取")

            from .external_knowledge_service import external_knowledge_service

            for knowledge_iteration in range(1, max_knowledge_iterations + 1):
                logger.info(f"知识获取迭代 {knowledge_iteration}/{max_knowledge_iterations}")

                current_kg_context = await self._get_kg_context(problem, abstraction_level, abstraction_mode)

                logger.info("开始外部知识补充")
                knowledge_result = await external_knowledge_service.acquire_knowledge_for_problem(
                    problem, current_kg_context
                )
                knowledge_acquisition_log.append({
                    "iteration": knowledge_iteration,
                    "success": knowledge_result.success,
                    "search_query": knowledge_result.search_query,
                    "sources_count": knowledge_result.sources_count,
                    "error": knowledge_result.error
                })

                if knowledge_result.success and knowledge_result.knowledge:
                    logger.info("更新知识图谱")
                    update_count = await self._integrate_external_knowledge(knowledge_result.knowledge)
                    kg_updates += update_count
                    logger.info(f"本轮新增 {update_count} 个知识元素")
                else:
                    logger.warning(f"外部知识获取失败: {knowledge_result.error}")

                logger.info("进行知识充足性检查")
                sufficiency_result = await self._check_knowledge_sufficiency(problem, abstraction_level, abstraction_mode)
                if sufficiency_result.is_sufficient:
                    logger.info("知识充足，可以进行问题求解")
                    break
                elif knowledge_iteration == max_knowledge_iterations:
                    logger.info("达到最大迭代次数，使用当前知识进行求解")
                    break
                else:
                    logger.info(f"知识不足，继续第 {knowledge_iteration + 1} 轮知识获取")
                    logger.info(f"不足原因: {sufficiency_result.reason}")

            logger.info("开始基于充实知识图谱的多轮推理求解")

            for reasoning_iteration in range(1, max_reasoning_iterations + 1):
                logger.info(f"推理迭代 {reasoning_iteration}/{max_reasoning_iterations}")

                current_kg_context = await self._get_kg_context(problem, abstraction_level, abstraction_mode)

                messages = [
                    {
                        "role": "system",
当前是第{reasoning_iteration}轮推理，共{max_reasoning_iterations}轮。
请直接提供明确的最终答案，不要说"数据不足"、"需要更多信息"等内容。
要求：
1. 基于提供的知识图谱数据进行分析
2. 直接给出具体的答案结果
3. 对于数学问题，请逐步计算并显示最终结果
                    },
                    {
                        "role": "user",
知识图谱上下文: {current_kg_context}
之前的推理结果: {current_answer}
                    }
                ]

                loop = asyncio.get_event_loop()
                reasoning_result = await loop.run_in_executor(
                    None,
                    self.llm.chat,
                    messages
                )
                current_answer = reasoning_result
                reasoning_steps.append(f"推理步骤{reasoning_iteration}: {reasoning_result}")
                logger.info(f"第{reasoning_iteration}轮推理完成")

                reasoning_updates = await self._save_reasoning_step_to_kg(
                    problem, reasoning_result, reasoning_iteration
                )
                kg_updates += reasoning_updates

                if reasoning_iteration == max_reasoning_iterations or self._is_complete_answer(reasoning_result):
                    break
            logger.info("多轮推理完成")

            if learn_from_solution:
                additional_updates = await self._learn_from_solution(problem, current_answer)
                kg_updates += additional_updates
                logger.info(f"解决方案学习完成，额外更新了 {additional_updates} 个知识元素")

            execution_time = time.time() - start_time
            return KGOTSolveResult(
                answer=current_answer,
                execution_time=execution_time,
                iterations=reasoning_iteration,
                kg_updates=kg_updates,
                reasoning_steps=reasoning_steps,
                success=True
            )
        except Exception as e:
            logger.error(f"智能问题求解失败: {e}")
            return KGOTSolveResult(
                answer="",
                execution_time=time.time() - start_time,
                success=False,
                error=str(e),
                reasoning_steps=reasoning_steps
            )
    async def _get_kg_context(self, query: str, abstraction_level: int = None, abstraction_mode: str = "semantic") -> str:
        每轮推理都重新获取相关节点和关系
        try:

            return await self._get_enhanced_context(query, abstraction_level, abstraction_mode)
        except Exception as e:
            logger.error(f"获取KG上下文失败: {e}")
            return "知识图谱上下文获取失败"
    async def _learn_from_solution(self, problem: str, current_answer: str) -> int:
        基于最终答案提取实体关系并更新知识图谱
        try:

            update_result = await self.safe_update_knowledge_graph(problem, [current_answer])
            return update_result.get('kg_updates', 0)
        except Exception as e:
            logger.error(f"从解决方案学习失败: {e}")
            return 0
    async def _integrate_external_knowledge(self, external_knowledge) -> int:

        try:
            from .kg_backup_service import kg_backup_service

            new_nodes = []
            new_relationships = []

            for entity in external_knowledge.entities:
                node_data = {
                    "id": f"ext_{entity['name']}_{hash(entity['name']) % 10000}",
                    "labels": [entity.get('type', '外部实体')],
                    "properties": {
                        "name": entity['name'],
                        "source": external_knowledge.source,
                        "confidence": external_knowledge.confidence,
                        **entity.get('properties', {})
                    }
                }
                new_nodes.append(node_data)

            for relationship in external_knowledge.relationships:
                rel_data = {
                    "source_id": f"ext_{relationship['source']}_{hash(relationship['source']) % 10000}",
                    "target_id": f"ext_{relationship['target']}_{hash(relationship['target']) % 10000}",
                    "type": relationship.get('type', '相关'),
                    "properties": {
                        "source": external_knowledge.source,
                        "confidence": external_knowledge.confidence,
                        **relationship.get('properties', {})
                    }
                }
                new_relationships.append(rel_data)

            if new_nodes or new_relationships:
                update_result = await kg_backup_service.safe_update_with_new_data(
                    new_nodes=new_nodes,
                    new_relationships=new_relationships,
                    description=f"外部知识整合: {external_knowledge.source}"
                )
                if update_result['success']:
                    total_updates = update_result['nodes_inserted'] + update_result['relationships_inserted']
                    logger.info(f"外部知识整合成功，新增 {total_updates} 个元素")
                    return total_updates
                else:
                    logger.error(f"外部知识整合失败: {update_result['error']}")
                    return 0
            return 0
        except Exception as e:
            logger.error(f"外部知识整合失败: {e}")
            return 0
    async def _check_knowledge_sufficiency(self, problem: str, abstraction_level: int = None, abstraction_mode: str = "semantic"):

        try:

            retrieval_result = await self.pure_internal_retrieval(problem, abstraction_level, abstraction_mode)

            if retrieval_result.success and retrieval_result.context_nodes > 0:

                sufficiency_score = min(retrieval_result.context_nodes / 5.0, 1.0)
                is_sufficient = sufficiency_score >= 0.6
                return type('SufficiencyResult', (), {
                    'is_sufficient': is_sufficient,
                    'score': sufficiency_score,
                    'reason': f"相关节点数: {retrieval_result.context_nodes}, 充足度: {sufficiency_score:.2f}"
                })()
            else:
                return type('SufficiencyResult', (), {
                    'is_sufficient': False,
                    'score': 0.0,
                    'reason': "未找到相关知识节点"
                })()
        except Exception as e:
            logger.error(f"知识充足性检查失败: {e}")
            return type('SufficiencyResult', (), {
                'is_sufficient': False,
                'score': 0.0,
                'reason': f"检查失败: {str(e)}"
            })()
    async def pure_internal_retrieval(self, query: str, abstraction_level: int = None, abstraction_mode: str = "semantic") -> KGOTRetrieveResult:
        阶段1: 初始化
        阶段2: 多轮迭代推理循环 (专注于知识提取和分析)
        阶段3: 返回提取结果（不更新KG）
        Args:
            query: 用户查询
            abstraction_level: 层级抽象级别 (1-5)，None表示使用原始完整数据
            abstraction_mode: 抽象模式 (semantic, structural, community)

        start_time = time.time()
        current_answer = ""
        max_iterations = 2
        context_nodes = 0
        try:
            logger.info(f"开始知识提取: {query}")

            context_data = await self._get_comprehensive_internal_context(
                query, abstraction_level, abstraction_mode
            )
            if not context_data['nodes']:
                return KGOTRetrieveResult(
                    answer="抱歉，在当前知识图谱中没有找到与您查询相关的信息。",
                    execution_time=time.time() - start_time,
                    context_nodes=0,
                    retrieved_context="无相关数据"
                )
            context_nodes = len(context_data['nodes'])

            for iteration in range(1, max_iterations + 1):
                logger.info(f"知识提取迭代 {iteration}/{max_iterations}")

                context = await self._get_kg_context(query, abstraction_level, abstraction_mode)

                messages = [
                    {
                        "role": "system",
当前是第{iteration}轮提取，共{max_iterations}轮。
要求：
1. 基于提供的知识图谱数据进行分析
2. 提取相关的实体、关系和属性
3. 直接给出最佳分析结果
                    },
                    {
                        "role": "user",
知识图谱上下文: {context}
之前提取: {current_answer}
                    }
                ]

                if self._is_llm_enabled():
                    if not self._llm:
                        self._init_kgot_components(require_llm=True)
                    loop = asyncio.get_event_loop()
                    current_answer = await loop.run_in_executor(
                        None,
                        self.llm.chat,
                        messages
                    )
                else:

                    current_answer = self._generate_rule_based_answer(query, context_data)
                    break
                logger.info(f"第{iteration}轮知识提取完成")

                if iteration == max_iterations or self._is_complete_answer(current_answer):
                    break

            execution_time = time.time() - start_time
            return KGOTRetrieveResult(
                answer=current_answer,
                execution_time=execution_time,
                context_nodes=context_nodes,
                retrieved_context=context_data['formatted_context'],
                success=True
            )
        except Exception as e:
            logger.error(f"知识提取失败: {e}")
            return KGOTRetrieveResult(
                answer="",
                execution_time=time.time() - start_time,
                success=False,
                error=str(e)
            )

    async def _get_enhanced_context(self, query: str, abstraction_level: int = None, abstraction_mode: str = "semantic") -> str:
        try:

            direct_nodes = await self._get_direct_relevant_nodes(query, abstraction_level, abstraction_mode)

            reasoning_context = await self._get_reasoning_context(query, direct_nodes)

            structured_context = await self._build_structured_reasoning_context(
                query, direct_nodes, reasoning_context
            )
            return structured_context
        except Exception as e:
            logger.error(f"获取增强上下文失败: {e}")
            return "知识图谱上下文获取失败"
    async def _get_direct_relevant_nodes(self, query: str, abstraction_level: int = None, abstraction_mode: str = "semantic") -> List[Dict[str, Any]]:

        try:
            if abstraction_level is not None:
                logger.info(f"智能求解使用层级抽象数据源: level={abstraction_level}, mode={abstraction_mode}")
                abstracted_data = await self._get_abstracted_graph_data(abstraction_level, abstraction_mode, query)
                nodes = await self._search_in_abstracted_data(query, abstracted_data, limit=15)
            else:
                logger.info("智能求解使用原始完整数据源")
                loop = asyncio.get_event_loop()
                nodes = await loop.run_in_executor(
                    None,
                    self.kg.search,
                    query,
                    15
                )
            return nodes or []
        except Exception as e:
            logger.error(f"获取直接相关节点失败: {e}")
            return []
    async def _get_reasoning_context(self, query: str, direct_nodes: List[Dict[str, Any]]) -> Dict[str, Any]:

        try:
            reasoning_context = {
                'concepts': [],
                'relationships': [],
                'patterns': [],
                'domain_knowledge': []
            }

            query_concepts = await self._analyze_query_concepts(query)
            reasoning_context['concepts'] = query_concepts

            if direct_nodes:
                node_ids = [node.get('id') for node in direct_nodes if node.get('id')]
                relationships = await self._get_node_relationships(node_ids)
                reasoning_context['relationships'] = relationships

            patterns = await self._identify_reasoning_patterns(query, direct_nodes)
            reasoning_context['patterns'] = patterns

            domain_knowledge = await self._get_domain_knowledge(query_concepts)
            reasoning_context['domain_knowledge'] = domain_knowledge
            return reasoning_context
        except Exception as e:
            logger.error(f"获取推理上下文失败: {e}")
            return {'concepts': [], 'relationships': [], 'patterns': [], 'domain_knowledge': []}
    async def _analyze_query_concepts(self, query: str) -> List[Dict[str, Any]]:

        try:
            concepts = []

            if any(op in query for op in ['+', '-', '*', '/', '计算', '数字', '运算']):
                concepts.append({
                    'type': '数学运算',
                    'elements': ['数字', '运算符', '计算过程', '结果'],
                    'reasoning_type': '数值计算'
                })

            if any(word in query for word in ['如果', '那么', '因为', '所以', '推理', '逻辑']):
                concepts.append({
                    'type': '逻辑推理',
                    'elements': ['前提', '条件', '结论', '推理链'],
                    'reasoning_type': '逻辑演绎'
                })

            if any(word in query for word in ['关系', '连接', '影响', '导致', '相关']):
                concepts.append({
                    'type': '实体关系',
                    'elements': ['实体', '关系', '属性', '连接'],
                    'reasoning_type': '关系推理'
                })
            return concepts
        except Exception as e:
            logger.error(f"分析查询概念失败: {e}")
            return []
    async def _get_node_relationships(self, node_ids: List[str]) -> List[Dict[str, Any]]:

        try:
            if not node_ids:
                return []
            MATCH (a)-[r]->(b)
            WHERE a.id IN $node_ids OR b.id IN $node_ids
            RETURN a.id as source_id, type(r) as relationship_type, b.id as target_id, properties(r) as properties
            LIMIT 20
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.db.execute_query,
                cypher_query,
                {'node_ids': node_ids}
            )
            return results or []
        except Exception as e:
            logger.error(f"获取节点关系失败: {e}")
            return []
    async def _identify_reasoning_patterns(self, query: str, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        try:
            patterns = []

            if any(op in query for op in ['+', '-', '*', '/', '计算']):
                math_nodes = [n for n in nodes if any(label in ['数字', '运算符', '计算'] for label in n.get('labels', []))]
                if math_nodes:
                    patterns.append({
                        'type': '数学计算',
                        'description': '基于数字和运算符进行数值计算',
                        'required_elements': ['操作数', '运算符', '计算规则'],
                        'reasoning_steps': ['识别数字', '识别运算符', '应用运算规则', '计算结果']
                    })

            if any(word in query for word in ['然后', '接着', '最后', '步骤', '过程']):
                patterns.append({
                    'type': '序列推理',
                    'description': '按时间或逻辑顺序进行推理',
                    'required_elements': ['初始状态', '操作序列', '状态变化'],
                    'reasoning_steps': ['确定初始状态', '识别操作序列', '逐步应用操作', '得出最终状态']
                })

            if len(nodes) > 3:
                patterns.append({
                    'type': '组合推理',
                    'description': '组合多个知识片段进行推理',
                    'required_elements': ['多个知识片段', '组合规则', '推理链'],
                    'reasoning_steps': ['收集相关知识', '识别连接点', '构建推理链', '验证结论']
                })
            return patterns
        except Exception as e:
            logger.error(f"识别推理模式失败: {e}")
            return []
    async def _get_domain_knowledge(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        try:
            domain_knowledge = []
            for concept in concepts:
                if concept['type'] == '数学运算':
                    domain_knowledge.append({
                        'domain': '数学',
                        'rules': [
                            '运算优先级：括号 > 乘除 > 加减',
                            '数字可以进行四则运算',
                            '运算结果仍然是数字',
                            '运算过程遵循数学定律'
                        ],
                        'principles': [
                            '交换律：a + b = b + a',
                            '结合律：(a + b) + c = a + (b + c)',
                            '分配律：a * (b + c) = a * b + a * c'
                        ]
                    })
                elif concept['type'] == '逻辑推理':
                    domain_knowledge.append({
                        'domain': '逻辑',
                        'rules': [
                            '前提为真，推理有效，则结论为真',
                            '逻辑推理遵循演绎规则',
                            '避免循环论证',
                            '保持逻辑一致性'
                        ],
                        'principles': [
                            '三段论：大前提 + 小前提 → 结论',
                            '假言推理：如果P则Q，P为真，则Q为真',
                            '否定后件：如果P则Q，Q为假，则P为假'
                        ]
                    })
            return domain_knowledge
        except Exception as e:
            logger.error(f"获取领域知识失败: {e}")
            return []
    async def _build_structured_reasoning_context(self, query: str, direct_nodes: List[Dict[str, Any]], reasoning_context: Dict[str, Any]) -> str:

        try:
            context_parts = []

            context_parts.append("=== 查询分析 ===")
            context_parts.append(f"查询内容: {query}")
            if reasoning_context['concepts']:
                context_parts.append("识别的概念类型:")
                for concept in reasoning_context['concepts']:
                    context_parts.append(f"- {concept['type']}: {concept['reasoning_type']}")

            context_parts.append("\n=== 可用知识资源 ===")
            if direct_nodes:
                context_parts.append("相关节点:")
                for i, node in enumerate(direct_nodes[:10], 1):
                    node_info = f"{i}. {node.get('id', 'unknown')}"
                    if node.get('labels'):
                        node_info += f" (类型: {', '.join(node['labels'])})"
                    if node.get('properties'):
                        key_props = {k: v for k, v in node['properties'].items() if k in ['name', 'description', 'value']}
                        if key_props:
                            props_str = ", ".join([f"{k}: {v}" for k, v in key_props.items()])
                            node_info += f" [关键属性: {props_str}]"
                    context_parts.append(node_info)
            else:
                context_parts.append("未找到直接相关的节点")

            if reasoning_context['relationships']:
                context_parts.append("\n相关关系:")
                for rel in reasoning_context['relationships'][:5]:
                    context_parts.append(f"- {rel.get('source_id', '?')} --[{rel.get('relationship_type', '?')}]--> {rel.get('target_id', '?')}")

            context_parts.append("\n=== 推理指导 ===")
            if reasoning_context['patterns']:
                context_parts.append("适用的推理模式:")
                for pattern in reasoning_context['patterns']:
                    context_parts.append(f"- {pattern['type']}: {pattern['description']}")
                    context_parts.append(f"  推理步骤: {' → '.join(pattern['reasoning_steps'])}")

            if reasoning_context['domain_knowledge']:
                context_parts.append("\n=== 领域知识 ===")
                for domain in reasoning_context['domain_knowledge']:
                    context_parts.append(f"{domain['domain']}领域规则:")
                    for rule in domain['rules'][:3]:
                        context_parts.append(f"- {rule}")

            context_parts.append("\n=== 推理要求 ===")
            context_parts.append("请基于以上信息进行推理，要求:")
            context_parts.append("1. 仅使用提供的知识图谱信息")
            context_parts.append("2. 明确说明推理步骤和依据")
            context_parts.append("3. 如果信息不足，说明缺少什么信息")
            context_parts.append("4. 保持推理的逻辑性和一致性")
            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"构建结构化推理上下文失败: {e}")
            return f"推理上下文构建失败: {str(e)}"
    async def _get_comprehensive_internal_context(self, query: str, abstraction_level: int = None, abstraction_mode: str = "semantic") -> Dict[str, Any]:
        获取全面的内部知识图谱上下文
        支持基于层级抽象级别的数据源切换
        Args:
            query: 用户查询
            abstraction_level: 层级抽象级别，None表示使用原始数据
            abstraction_mode: 抽象模式
        try:

            if abstraction_level is not None:
                logger.info(f"🎯 数据源选择: 使用层级抽象数据源 (level={abstraction_level}, mode={abstraction_mode})")

                abstracted_data = await self._get_abstracted_graph_data(abstraction_level, abstraction_mode, query)
                logger.info(f"📊 抽象数据获取完成: {len(abstracted_data.get('hierarchy', {}))} 个层级")

                nodes = await self._search_in_abstracted_data(query, abstracted_data, limit=15)
                logger.info(f"🔍 抽象数据搜索完成: 找到 {len(nodes)} 个节点")
            else:
                logger.info(f"🗄️  数据源选择: 使用原始完整数据源 (直接查询Neo4j数据库)")

                loop = asyncio.get_event_loop()
                nodes = await loop.run_in_executor(
                    None,
                    self._enhanced_search_without_llm,
                    query,
                    15
                )
                logger.info(f"🔍 完整数据搜索完成: 找到 {len(nodes)} 个节点")
            if not nodes:
                logger.warning(f"⚠️  未找到相关节点，返回空结果")
                return {'nodes': [], 'relationships': [], 'formatted_context': ''}

            node_ids = [node.get('id') for node in nodes if node.get('id')]
            relationships = []
            logger.info(f"🔗 开始查询 {len(node_ids)} 个节点间的关系")
            if node_ids:

                MATCH (a)-[r]->(b)
                WHERE a.id IN $node_ids AND b.id IN $node_ids
                RETURN a.id as source, type(r) as relationship, b.id as target, properties(r) as props
                LIMIT 20
                loop = asyncio.get_event_loop()
                relationships = await loop.run_in_executor(
                    None,
                    self.db.execute_query,
                    cypher_query,
                    {'node_ids': node_ids}
                )
                logger.info(f"🔗 关系查询完成: 找到 {len(relationships)} 个关系")

            formatted_context = self._format_internal_context(nodes, relationships)
            logger.info(f"📝 上下文格式化完成: {len(formatted_context)} 字符")
            return {
                'nodes': nodes,
                'relationships': relationships,
                'formatted_context': formatted_context
            }
        except Exception as e:
            logger.error(f"获取内部上下文失败: {e}")
            return {'nodes': [], 'relationships': [], 'formatted_context': ''}
    def _format_internal_context(self, nodes: List[Dict], relationships: List[Dict]) -> str:
        格式化内部上下文信息 - 严格基于Neo4j数据
        确保只包含从数据库查询获得的实际数据，不添加任何外部信息
        context_parts = []

        context_parts.append("=== Neo4j知识图谱数据 ===")
        context_parts.append("以下数据完全来自Neo4j数据库的Cypher查询结果：")
        context_parts.append("")

        if nodes:
            context_parts.append("=== 节点数据 ===")
            for i, node in enumerate(nodes, 1):

                node_id = node.get('id', 'MISSING_ID')
                node_info = f"{i}. 节点ID: {node_id}"
                if node.get('labels'):
                    node_info += f" | 标签: {', '.join(node['labels'])}"
                else:
                    node_info += f" | 标签: 无"
                if node.get('properties'):

                    props = []
                    for k, v in node['properties'].items():
                        props.append(f"{k}={v}")
                    node_info += f" | 属性: {', '.join(props)}"
                else:
                    node_info += f" | 属性: 无"
                context_parts.append(node_info)

        if relationships:
            context_parts.append("")
            context_parts.append("=== 关系数据 ===")
            for i, rel in enumerate(relationships, 1):

                source = rel.get('source', 'MISSING_SOURCE')
                target = rel.get('target', 'MISSING_TARGET')
                rel_type = rel.get('relationship', 'MISSING_TYPE')
                rel_info = f"{i}. 关系: {source} --[{rel_type}]--> {target}"
                if rel.get('props'):

                    props = []
                    for k, v in rel['props'].items():
                        props.append(f"{k}={v}")
                    rel_info += f" | 关系属性: {', '.join(props)}"
                else:
                    rel_info += f" | 关系属性: 无"
                context_parts.append(rel_info)
        else:
            context_parts.append("")
            context_parts.append("=== 关系数据 ===")
            context_parts.append("无关系数据")

        context_parts.append("")
        context_parts.append("=== 数据完整性声明 ===")
        context_parts.append("以上所有数据均来自Neo4j数据库的实际查询结果，未添加任何外部信息或推测内容。")
        return "\n".join(context_parts) if context_parts else "Neo4j数据库中无相关数据"
    def _validate_pure_internal_answer(self, answer: str, context_data: Dict[str, Any]) -> str:
        try:

            has_node_reference = any(node_id in answer for node in context_data.get('nodes', [])
                                   for node_id in [node.get('id', '')])

            if not has_node_reference and "数据不足" not in answer and "图谱数据不足" not in answer:
                answer = answer + warning

            if context_data.get('nodes'):
                node_count = len(context_data['nodes'])
                rel_count = len(context_data.get('relationships', []))
                traceability = f"\n\n【数据追溯】：本回答基于 {node_count} 个节点和 {rel_count} 个关系的Neo4j查询结果。"
                answer = answer + traceability
            return answer
        except Exception as e:
            logger.error(f"回答验证失败: {e}")
            return answer + "\n\n【验证警告】：回答验证过程中出现异常，请谨慎对待回答内容的纯内部性。"
    async def _get_abstracted_graph_data(self, abstraction_level: int, abstraction_mode: str, query_context: str = None) -> Dict[str, Any]:
        获取层级抽象后的图数据
        Args:
            抽象后的图数据
        try:

            from app.services.hierarchical_abstraction_service import HierarchicalAbstractionService
            from app.services.graph_service import GraphService

            graph_service = GraphService()
            graph_data = graph_service.get_all_graph_data()

            abstraction_service = HierarchicalAbstractionService()

            abstraction_result = await abstraction_service.analyze_hierarchical_structure(
                graph_data, abstraction_level, abstraction_mode, query_context=query_context
            )
            return abstraction_result
        except Exception as e:
            logger.error(f"获取抽象图数据失败: {e}")

            return {'hierarchy': {}, 'analysis_metadata': {}}
    async def _search_in_abstracted_data(self, query: str, abstracted_data: Dict[str, Any], limit: int = 15) -> List[Dict[str, Any]]:
        在抽象后的数据中进行搜索
        Args:
            query: 搜索查询
            abstracted_data: 抽象后的图数据
            limit: 结果限制
        Returns:
            搜索结果节点列表
        try:
            results = []
            hierarchy = abstracted_data.get('hierarchy', {})

            keywords = self._extract_keywords(query)
            logger.info(f"在抽象数据中搜索关键词: {keywords}")

            relevant_node_ids = set()

            for level_key, level_data in hierarchy.items():
                if isinstance(level_data, dict):

                    if 'label_groups' in level_data:
                        for label, node_ids in level_data['label_groups'].items():

                            if any(keyword.lower() in label.lower() for keyword in keywords):
                                relevant_node_ids.update(node_ids)

                            for node_id in node_ids:
                                node_matches = await self._check_node_content_match(node_id, keywords)
                                if node_matches:
                                    relevant_node_ids.add(node_id)

                    for group_key, group_data in level_data.items():
                        if isinstance(group_data, dict):
                            for group_name, node_ids in group_data.items():
                                if isinstance(node_ids, list):

                                    if any(keyword.lower() in str(group_name).lower() for keyword in keywords):
                                        relevant_node_ids.update(node_ids)

                                    for node_id in node_ids:
                                        node_matches = await self._check_node_content_match(node_id, keywords)
                                        if node_matches:
                                            relevant_node_ids.add(node_id)

            if relevant_node_ids:
                logger.info(f"找到相关节点ID: {list(relevant_node_ids)[:10]}...")

                results = await self._get_nodes_by_ids(list(relevant_node_ids)[:limit])
            logger.info(f"在抽象数据中找到 {len(results)} 个匹配节点")
            return results
        except Exception as e:
            logger.error(f"在抽象数据中搜索失败: {e}")

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._enhanced_search_without_llm,
                query,
                limit
            )
    def _node_matches_keywords(self, node: Dict[str, Any], keywords: List[str]) -> bool:
        检查节点是否匹配关键词
        Args:
            node: 节点数据
            keywords: 关键词列表
        Returns:
            是否匹配
        try:

            node_texts = []

            if node.get('id'):
                node_texts.append(str(node['id']).lower())

            if node.get('labels'):
                node_texts.extend([label.lower() for label in node['labels']])

            if node.get('properties'):
                for key, value in node['properties'].items():
                    node_texts.append(str(value).lower())

            node_text = ' '.join(node_texts)
            for keyword in keywords:
                if keyword.lower() in node_text:
                    return True
            return False
        except Exception as e:
            logger.error(f"节点关键词匹配检查失败: {e}")
            return False
    async def _check_node_content_match(self, node_id: str, keywords: List[str]) -> bool:
            node_id: 节点ID
            keywords: 关键词列表
        Returns:
            是否匹配
        try:

            MATCH (n)
            WHERE n.id = $node_id
            RETURN n.id as id, labels(n) as labels, properties(n) as properties
            results = self.db.execute_query(cypher_query, {'node_id': node_id})
            if not results:
                return False
            node = results[0]

            return self._node_matches_keywords(node, keywords)
        except Exception as e:
            logger.error(f"检查节点内容匹配失败 {node_id}: {e}")
            return False
    async def _get_nodes_by_ids(self, node_ids: List[str]) -> List[Dict[str, Any]]:
        根据节点ID列表从数据库中获取完整节点信息
        Args:
            节点信息列表
        try:
            if not node_ids:
                return []

            MATCH (n)
            WHERE n.id IN $node_ids
            RETURN n.id as id, labels(n) as labels, properties(n) as properties
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.db.execute_query,
                cypher_query,
                {'node_ids': node_ids}
            )
            return results or []
        except Exception as e:
            logger.error(f"根据ID获取节点失败: {e}")
            return []
    async def _save_reasoning_step_to_kg(self, problem: str, reasoning_step: str, iteration: int) -> int:
        try:
            logger.info(f"保存推理步骤{iteration}到知识图谱")
            updates = 0

            step_node_id = f"reasoning_step_{abs(hash(problem + str(iteration))) % 1000000}"
            step_properties = {
                "problem": problem,
                "step_content": reasoning_step[:500],
                "iteration": iteration,
                "step_type": "reasoning_step",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            if await self._add_node_async(step_node_id, step_properties, ["ReasoningStep", "Process"]):
                updates += 1
                logger.info(f"创建推理步骤节点: {step_node_id}")

            problem_node_id = f"problem_{abs(hash(problem)) % 1000000}"
            problem_properties = {
                "question": problem,
                "type": "problem",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            if await self._add_node_async(problem_node_id, problem_properties, ["Problem", "Query"]):
                updates += 1
                logger.info(f"创建问题节点: {problem_node_id}")

            if await self._add_relationship_async(
                problem_node_id,
                step_node_id,
                "HAS_REASONING_STEP",
                {"step_order": iteration}
            ):
                updates += 1
                logger.info(f"创建问题到推理步骤的关系")

            concept_updates = await self._extract_reasoning_concepts(problem, reasoning_step, iteration, step_node_id)
            updates += concept_updates

            if self._is_math_problem(problem):
                math_updates = await self._extract_math_reasoning(problem, reasoning_step, iteration, step_node_id)
                updates += math_updates

            if iteration > 1:
                prev_step_node_id = f"reasoning_step_{abs(hash(problem + str(iteration - 1))) % 1000000}"
                if await self._add_relationship_async(
                    prev_step_node_id,
                    step_node_id,
                    "NEXT_STEP",
                    {"sequence": iteration}
                ):
                    updates += 1
                    logger.info(f"创建推理步骤序列关系")
            logger.info(f"推理步骤{iteration}保存完成，共更新{updates}个图谱元素")
            return updates
        except Exception as e:
            logger.error(f"保存推理步骤失败: {e}")
            return 0
    def _is_math_problem(self, problem: str) -> bool:

        math_indicators = ['+', '-', '*', '/', '=', '计算', '数字', '运算', 'calculate', 'compute', '求解']
        return any(indicator in problem for indicator in math_indicators)
    async def _extract_reasoning_concepts(self, problem: str, reasoning_step: str, iteration: int, step_node_id: str) -> int:

        try:
            updates = 0

            concepts = []

            import re
            numbers = re.findall(r'\d+\.?\d*', reasoning_step)
            for num in numbers:
                concept_id = f"number_{num}_{iteration}"
                concept_properties = {
                    "value": num,
                    "type": "number",
                    "from_reasoning": True,
                    "step": iteration
                }
                if await self._add_node_async(concept_id, concept_properties, ["Number", "Concept"]):
                    updates += 1

                    if await self._add_relationship_async(step_node_id, concept_id, "INVOLVES", {"role": "operand"}):
                        updates += 1

            operators = re.findall(r'[+\-*/=]', reasoning_step)
            for op in set(operators):
                op_id = f"operator_{op}_{iteration}"
                op_properties = {
                    "symbol": op,
                    "type": "operator",
                    "from_reasoning": True,
                    "step": iteration
                }
                if await self._add_node_async(op_id, op_properties, ["Operator", "Concept"]):
                    updates += 1

                    if await self._add_relationship_async(step_node_id, op_id, "USES", {"role": "operation"}):
                        updates += 1

            result_patterns = [
                r'结果是?[:：]?\s*(\d+\.?\d*)',
                r'答案是?[:：]?\s*(\d+\.?\d*)',
                r'等于\s*(\d+\.?\d*)',
                r'=\s*(\d+\.?\d*)'
            ]
            for pattern in result_patterns:
                matches = re.findall(pattern, reasoning_step)
                for result in matches:
                    result_id = f"result_{result}_{iteration}"
                    result_properties = {
                        "value": result,
                        "type": "result",
                        "from_reasoning": True,
                        "step": iteration
                    }
                    if await self._add_node_async(result_id, result_properties, ["Result", "Concept"]):
                        updates += 1

                        if await self._add_relationship_async(step_node_id, result_id, "PRODUCES", {"role": "output"}):
                            updates += 1
            return updates
        except Exception as e:
            logger.error(f"提取推理概念失败: {e}")
            return 0
    async def _extract_math_reasoning(self, problem: str, reasoning_step: str, iteration: int, step_node_id: str) -> int:

        try:
            updates = 0

            import re

            math_expressions = re.findall(r'(\d+\.?\d*)\s*([+\-*/])\s*(\d+\.?\d*)\s*=\s*(\d+\.?\d*)', reasoning_step)
            for expr in math_expressions:
                operand1, operator, operand2, result = expr

                expr_id = f"math_expr_{operand1}_{operator}_{operand2}_{iteration}"
                expr_properties = {
                    "expression": f"{operand1} {operator} {operand2} = {result}",
                    "operand1": operand1,
                    "operator": operator,
                    "operand2": operand2,
                    "result": result,
                    "type": "math_expression",
                    "step": iteration
                }
                if await self._add_node_async(expr_id, expr_properties, ["MathExpression", "Calculation"]):
                    updates += 1

                    if await self._add_relationship_async(step_node_id, expr_id, "CALCULATES", {"type": "math_operation"}):
                        updates += 1

            step_descriptions = [
                "识别数字", "识别运算符", "执行计算", "得出结果",
                "第一步计算", "第二步计算", "最终结果"
            ]
            for desc in step_descriptions:
                if desc in reasoning_step:
                    desc_id = f"calc_step_{desc.replace(' ', '_')}_{iteration}"
                    desc_properties = {
                        "description": desc,
                        "type": "calculation_step",
                        "step": iteration
                    }
                    if await self._add_node_async(desc_id, desc_properties, ["CalculationStep", "Process"]):
                        updates += 1

                        if await self._add_relationship_async(step_node_id, desc_id, "INCLUDES", {"type": "sub_process"}):
                            updates += 1
            return updates
        except Exception as e:
            logger.error(f"提取数学推理失败: {e}")
            return 0
    async def _extract_and_update_reasoning_knowledge(self, problem: str, reasoning_step: str, iteration: int) -> int:

        try:

问题: {problem}
推理步骤: {reasoning_step}
请提取其中涉及的：
1. 关键实体（概念、对象、人物等）
2. 实体间的关系
3. 推理中的中间结论
返回JSON格式:
{{
  "entities": [
    {{"id": "实体唯一标识", "type": "实体类型", "properties": {{"name": "实体名称", "description": "描述"}}}}
  ],
  "relationships": [
    {{"source": "源实体ID", "target": "目标实体ID", "type": "关系类型", "properties": {{"reasoning_step": {iteration}}}}}
  ]
            messages = [
                {"role": "system", "content": "你是一个知识提取专家，请从推理文本中提取结构化的知识。"},
                {"role": "user", "content": extract_prompt}
            ]
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.llm.chat,
                messages
            )

            try:
                if "```json" in response:
                    start = response.find("```json") + 7
                    end = response.find("```", start)
                    json_str = response[start:end].strip()
                else:
                    json_str = response
                extracted = json.loads(json_str)
            except:
                logger.warning("无法解析实体提取结果")
                return 0

            updates = 0

            for entity in extracted.get("entities", []):
                if await self._add_node_async(
                    entity.get("id", ""),
                    entity.get("properties", {}),
                    [entity.get("type", "ReasoningEntity")]
                ):
                    updates += 1

            for rel in extracted.get("relationships", []):
                if await self._add_relationship_async(
                    rel.get("source", ""),
                    rel.get("target", ""),
                    rel.get("type", "REASONING_RELATION"),
                    rel.get("properties", {})
                ):
                    updates += 1
            logger.info(f"从推理步骤{iteration}中提取并添加了{updates}个知识元素")
            return updates
        except Exception as e:
            logger.error(f"提取推理知识失败: {e}")
            return 0
    async def _create_problem_solution_node(self, problem: str, solution: str) -> int:

        try:
            problem_id = f"problem_{abs(hash(problem)) % 1000000}"
            properties = {
                "question": problem,
                "solution": solution[:1000],
                "type": "solved_problem",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            if await self._add_node_async(problem_id, properties, ["Problem", "Solved"]):
                return 1
            return 0
        except Exception as e:
            logger.error(f"创建问题解决方案节点失败: {e}")
            return 0
    async def _add_node_async(self, node_id: str, properties: Dict[str, Any], labels: List[str]) -> bool:

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.kg.add_node,
                node_id,
                properties,
                labels
            )
        except Exception as e:
            logger.error(f"异步添加节点失败: {e}")
            return False
    async def _add_relationship_async(self, source_id: str, target_id: str, rel_type: str, properties: Dict[str, Any] = None) -> bool:

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.kg.add_relationship,
                source_id,
                target_id,
                rel_type,
                properties or {}
            )
        except Exception as e:
            logger.error(f"异步添加关系失败: {e}")
            return False
    def _is_complete_answer(self, answer: str) -> bool:

        complete_indicators = ["答案是", "结论", "因此", "最终", "总结", "综上所述"]
        return any(indicator in answer for indicator in complete_indicators) and len(answer) > 100
    async def extract_and_add_knowledge(self, text: str) -> int:

        try:
            loop = asyncio.get_event_loop()
            updates = await loop.run_in_executor(
                None,
                self.retriever.add_knowledge,
                text
            )
            return updates
        except Exception as e:
            logger.error(f"知识提取失败: {e}")
            return 0
    async def search_nodes(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.kg.search,
                query_text,
                limit
            )
            return results
        except Exception as e:
            logger.error(f"节点搜索失败: {e}")
            return []
    def close(self):

        if self._kg:
            self._kg.close()
    def _enhanced_search(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:

        try:

            keywords = self._extract_keywords(query)
            logger.info(f"从查询 '{query}' 提取关键词: {keywords}")
            all_results = []

            for keyword in keywords:
                results = self.kg.search(keyword, limit=5)
                all_results.extend(results)

            if len(all_results) < 3:
                loose_results = self._loose_search(keywords, limit=10)
                all_results.extend(loose_results)

            unique_results = self._deduplicate_and_rank(all_results, keywords)
            return unique_results[:limit]
        except Exception as e:
            logger.error(f"增强搜索失败: {e}")
            return []
    def _extract_keywords(self, query: str) -> List[str]:


        keywords = []

        keyword_mapping = {
            "人工智能": ["人工智能", "AI", "智能"],
            "应用": ["应用", "应用领域", "用途"],
            "领域": ["领域", "方面", "范围"],
            "主要": ["主要", "重要", "核心"],
            "机器学习": ["机器学习", "ML"],
            "计算机视觉": ["计算机视觉", "视觉", "图像"],
            "机器人": ["机器人", "机器人技术", "robotics"],
            "医疗": ["医疗", "医疗AI", "健康"],
            "计算": ["计算", "运算", "calculation", "compute"],
            "结果": ["结果", "答案", "result"],
            "数字": ["数字", "数值", "number"],
            "表达式": ["表达式", "公式", "expression"],
            "数学": ["数学", "math", "mathematics"]
        }
        query_lower = query.lower()

        for key, variants in keyword_mapping.items():
            for variant in variants:
                if variant.lower() in query_lower:
                    keywords.extend(variants)
                    break

        import re

        numbers = re.findall(r'\d+\.?\d*', query)
        keywords.extend(numbers)

        if any(op in query for op in ['+', '-', '*', '/', '=', '计算', 'calculate', 'compute']):
            keywords.extend(['计算', '运算', '结果', '乘法', '加法', '减法', '除法'])

        multiply_pattern = r'(\d+)\s*\*\s*(\d+)'
        multiply_matches = re.findall(multiply_pattern, query)
        for match in multiply_matches:
            keywords.extend([match[0], match[1], f"{match[0]}*{match[1]}", "乘法运算"])

        math_terms = ['数字', '运算符', '表达式', '公式', 'number', 'operator', 'expression']
        for term in math_terms:
            if term.lower() in query_lower:
                keywords.extend(math_terms)

        if not keywords:

            stop_words = {"什么", "是", "的", "有", "吗", "呢", "？", "?", "。", "，", ",", "what", "is", "the"}
            words = [word.strip() for word in query.replace("？", " ").replace("?", " ").split()
                    if word.strip() and word.strip() not in stop_words and len(word.strip()) > 1]
            keywords.extend(words)
        return list(set(keywords))
    def _loose_search(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:

        try:

            MATCH (n)
            WHERE ANY(keyword IN $keywords
                      WHERE toLower(toString(n.name)) CONTAINS toLower(keyword)
                         OR toLower(toString(n.description)) CONTAINS toLower(keyword)
                         OR toLower(toString(n.type)) CONTAINS toLower(keyword))
            RETURN n.id as id, labels(n) as labels, properties(n) as properties
            LIMIT $limit
            results = self.kg.execute_cypher(cypher_query, {'keywords': keywords, 'limit': limit})
            return results
        except Exception as e:
            logger.error(f"宽松搜索失败: {e}")
            return []
    def _deduplicate_and_rank(self, results: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:


        seen_ids = set()
        unique_results = []
        for result in results:
            node_id = result.get('id')
            if node_id and node_id not in seen_ids:
                seen_ids.add(node_id)
                unique_results.append(result)

        def calculate_relevance(result):
            properties = result.get('properties', {})
            name = str(properties.get('name', '')).lower()
            description = str(properties.get('description', '')).lower()
            node_type = str(properties.get('type', '')).lower()
            score = 0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in name:
                    score += 3
                if keyword_lower in description:
                    score += 2
                if keyword_lower in node_type:
                    score += 1
            return score

        unique_results.sort(key=calculate_relevance, reverse=True)
        return unique_results
    def _generate_rule_based_answer(self, query: str, context_data: Dict[str, Any]) -> str:

        nodes = context_data.get('nodes', [])
        relationships = context_data.get('relationships', [])
        if not nodes:
            return "抱歉，在当前知识图谱中没有找到与您查询相关的信息。"

        query_lower = query.lower()

        answer_parts = []

        if any(word in query_lower for word in ["应用", "领域", "用途", "方面"]):
            applications = [node for node in nodes
                          if "应用" in str(node.get('properties', {}).get('type', '')).lower()
                          or "领域" in str(node.get('properties', {}).get('type', '')).lower()]
            if applications:
                for i, app in enumerate(applications, 1):
                    props = app.get('properties', {})
                    name = props.get('name', '未知')
                    description = props.get('description', '')
                    answer_parts.append(f"{i}. {name}：{description}")

        elif any(word in query_lower for word in ["什么", "是", "定义", "概念"]):
            concepts = [node for node in nodes
                       if "概念" in str(node.get('properties', {}).get('type', '')).lower()]
            if concepts:
                for concept in concepts:
                    props = concept.get('properties', {})
                    name = props.get('name', '未知')
                    description = props.get('description', '')
                    answer_parts.append(f"{name}是{description}")

        if not answer_parts:
            for i, node in enumerate(nodes[:5], 1):
                props = node.get('properties', {})
                name = props.get('name', '未知')
                description = props.get('description', '')
                node_type = props.get('type', '实体')
                answer_parts.append(f"{i}. {name}（{node_type}）：{description}")

        if relationships:
            for rel in relationships[:3]:
                source = rel.get('source', '未知')
                target = rel.get('target', '未知')
                rel_type = rel.get('relationship', '相关')
                answer_parts.append(f"• {source} {rel_type} {target}")
        return "\n".join(answer_parts)
    def _enhanced_search_without_llm(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:

        try:

            keywords = self._extract_keywords(query)
            logger.info(f"从查询 '{query}' 提取关键词: {keywords}")
            all_results = []

            for keyword in keywords:
                results = self._direct_search(keyword, limit=5)
                all_results.extend(results)

            if len(all_results) < 3:
                loose_results = self._direct_loose_search(keywords, limit=10)
                all_results.extend(loose_results)

            unique_results = self._deduplicate_and_rank(all_results, keywords)
            return unique_results[:limit]
        except Exception as e:
            logger.error(f"增强搜索失败: {e}")
            return []
    def _direct_search(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:

        try:
            MATCH (n)
            WHERE ANY(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $query_text)
            RETURN n.id as id, labels(n) as labels, properties(n) as properties
            LIMIT $limit
            results = self.db.execute_query(cypher_query, {'query_text': query_text, 'limit': limit})
            return results
        except Exception as e:
            logger.error(f"直接搜索失败: {e}")
            return []
    def _direct_loose_search(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:

        try:
            MATCH (n)
            WHERE ANY(keyword IN $keywords
                      WHERE toLower(toString(n.name)) CONTAINS toLower(keyword)
                         OR toLower(toString(n.description)) CONTAINS toLower(keyword)
                         OR toLower(toString(n.type)) CONTAINS toLower(keyword))
            RETURN n.id as id, labels(n) as labels, properties(n) as properties
            LIMIT $limit
            results = self.db.execute_query(cypher_query, {'keywords': keywords, 'limit': limit})
            return results
        except Exception as e:
            logger.error(f"直接宽松搜索失败: {e}")
            return []
    async def _extract_all_reasoning_knowledge(self, problem: str, reasoning_steps: List[str]) -> Dict[str, List[Dict[str, Any]]]:

        try:
            all_entities = []
            all_relationships = []
            for i, step in enumerate(reasoning_steps, 1):

问题: {problem}
推理步骤 {i}: {step}
请提取其中涉及的：
1. 关键实体（概念、对象、人物等）
2. 实体间的关系
3. 推理中的中间结论
返回JSON格式:
{{
  "entities": [
    {{"id": "实体唯一标识", "type": "实体类型", "properties": {{"name": "实体名称", "description": "描述"}}}}
  ],
  "relationships": [
    {{"source": "源实体ID", "target": "目标实体ID", "type": "关系类型", "properties": {{"reasoning_step": {i}}}}}
  ]
                messages = [
                    {"role": "system", "content": "你是一个知识提取专家，请从推理文本中提取结构化的知识。"},
                    {"role": "user", "content": extract_prompt}
                ]
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    self.llm.chat,
                    messages
                )

                try:
                    if "```json" in response:
                        start = response.find("```json") + 7
                        end = response.find("```", start)
                        json_str = response[start:end].strip()
                    else:
                        json_str = response
                    extracted = json.loads(json_str)

                    standard_data = data_transformer.kgot_to_standard(extracted)

                    all_entities.extend(standard_data['nodes'])
                    all_relationships.extend(standard_data['relationships'])
                except Exception as e:
                    logger.warning(f"无法解析推理步骤{i}的实体提取结果: {e}")
                    continue

            result_data = {
                'nodes': all_entities,
                'relationships': all_relationships
            }
            return data_transformer.validate_and_fix_data(result_data)
        except Exception as e:
            logger.error(f"提取推理知识失败: {e}")
            return {'nodes': [], 'relationships': []}
    async def safe_update_knowledge_graph(self, problem: str, reasoning_steps: List[str]) -> Dict[str, Any]:

        try:

            extracted_knowledge = await self._extract_all_reasoning_knowledge(problem, reasoning_steps)
            if not extracted_knowledge['nodes'] and not extracted_knowledge['relationships']:
                return {
                    'success': True,
                    'kg_updates': 0,
                    'message': '没有提取到新的知识图谱数据'
                }

            update_result = await kg_backup_service.safe_update_with_new_data(
                new_nodes=extracted_knowledge['nodes'],
                new_relationships=extracted_knowledge['relationships'],
                description=f"智能求解更新: {problem[:50]}..."
            )
            if update_result['success']:
                total_updates = update_result['nodes_inserted'] + update_result['relationships_inserted']
                return {
                    'success': True,
                    'kg_updates': total_updates,
                    'backup_id': update_result['backup_id'],
                    'message': f'知识图谱安全更新成功，新增 {total_updates} 个元素'
                }
            else:
                return {
                    'success': False,
                    'kg_updates': 0,
                    'error': update_result['error'],
                    'message': '知识图谱安全更新失败'
                }
        except Exception as e:
            logger.error(f"安全更新知识图谱失败: {e}")
            return {
                'success': False,
                'kg_updates': 0,
                'error': str(e),
                'message': '知识图谱安全更新异常'
            }
    async def clear_knowledge_graph(self):

        try:

            await self.db.execute_query("MATCH (n) DETACH DELETE n")
            logger.info("知识图谱已清空")
            return True
        except Exception as e:
            logger.error(f"清空知识图谱失败: {e}")
            return False
    async def add_node(self, node_id: str, label: str, node_type: str, properties: Dict[str, Any] = None):

        try:
            if properties is None:
                properties = {}

            MERGE (n:{node_type} {{id: $node_id}})
            SET n.label = $label

            for key, value in properties.items():
                cypher += f", n.{key} = ${key}"
            params = {
                'node_id': node_id,
                'label': label,
                **properties
            }
            await self.db.execute_query(cypher, params)
            logger.debug(f"添加节点: {node_id}")
            return True
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return False
    async def add_relationship(self, source_id: str, target_id: str, relationship_type: str, properties: Dict[str, Any] = None):

        try:
            if properties is None:
                properties = {}

            MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
            MERGE (a)-[r:{relationship_type}]->(b)

            if properties:
                cypher += " SET "
                prop_sets = []
                for key, value in properties.items():
                    prop_sets.append(f"r.{key} = ${key}")
                cypher += ", ".join(prop_sets)
            params = {
                'source_id': source_id,
                'target_id': target_id,
                **properties
            }
            await self.db.execute_query(cypher, params)
            logger.debug(f"添加关系: {source_id} -> {target_id}")
            return True
        except Exception as e:
            logger.error(f"添加关系失败: {e}")
            return False

enhanced_kgot_service = EnhancedKGOTService()