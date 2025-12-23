import asyncio
import logging
import time
import json
import os
import sys
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from ..database.connection import db_connection
from ..config.llm_config import get_llm_config, is_llm_enabled
logger = logging.getLogger(__name__)
@dataclass
class KGOTSolveResult:

    answer: str
    execution_time: float
    iterations: int = 1
    kg_updates: int = 0
    success: bool = True
    error: Optional[str] = None
    reasoning_steps: List[str] = None
@dataclass
class KGOTRetrieveResult:

    answer: str
    execution_time: float
    context_nodes: int = 0
    success: bool = True
    error: Optional[str] = None
    retrieved_context: str = ""
class ExternalKGOTService:


    def __init__(self):
        self.db = db_connection
        self._llm_config = None
        self._llm_enabled = None

        current_file_dir = os.path.dirname(__file__)
        backend_dir = os.path.dirname(os.path.dirname(current_file_dir))
        nokgot_dir = os.path.dirname(backend_dir)
        workspace_root = os.path.dirname(nokgot_dir)
        self.kgot_project_root = os.path.join(workspace_root, "knowledge-graph-of-thoughts")

        self._setup_kgot_environment()

        if self.kgot_project_root not in sys.path:
            sys.path.insert(0, self.kgot_project_root)

        if not os.path.exists(self.kgot_project_root):
            raise FileNotFoundError(f"外部 KGOT 项目路径不存在: {self.kgot_project_root}")
        logger.info(f"外部 KGOT 项目路径: {self.kgot_project_root}")
        logger.info(f"已配置外部 KGOT 项目使用数据库: {self.db.uri} (用户: {self.db.username})")
    def _setup_kgot_environment(self):
        os.environ['NEO4J_URI'] = self.db.uri
        os.environ['NEO4J_USER'] = self.db.username
        os.environ['NEO4J_PASSWORD'] = self.db.password

        os.environ['PYTHON_EXECUTOR_URI'] = "http://localhost:16000/run"

        logger.info(f"设置外部 KGOT 环境变量:")
        logger.info(f"  NEO4J_URI: {os.environ['NEO4J_URI']}")
        logger.info(f"  NEO4J_USER: {os.environ['NEO4J_USER']}")
        logger.info(f"  NEO4J_PASSWORD: {'*' * len(os.environ['NEO4J_PASSWORD'])}")
        logger.info(f"  PYTHON_EXECUTOR_URI: {os.environ['PYTHON_EXECUTOR_URI']}")

        self._update_kgot_env_file()
    def _update_kgot_env_file(self):
        kgot_env_file = os.path.join(self.kgot_project_root, "kgot", ".env")
        try:
            env_content = f"""NEO4J_URI={self.db.uri}
NEO4J_USER={self.db.username}
NEO4J_PASSWORD={self.db.password}

PYTHON_EXECUTOR_URI=http://localhost:16000/run

RDF4J_READ_URI=http://localhost:8080/rdf4j-server/repositories/kgot
RDF4J_WRITE_URI=http://localhost:8080/rdf4j-server/repositories/kgot/statements
"""
            with open(kgot_env_file, 'w') as f:
                f.write(env_content)
            logger.info(f"已更新外部 KGOT 项目的 .env 文件: {kgot_env_file}")
        except Exception as e:
            logger.warning(f"更新外部 KGOT 项目 .env 文件失败: {e}")

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
    @property
    def llm_enabled(self):

        return self._is_llm_enabled()
    def _create_llm_config_file(self) -> str:

        llm_config = self._get_llm_config()
        if not llm_config:
            raise ValueError("LLM 配置未找到")


        config_data = {
            "gpt-4o-mini": {
                "model": "gpt-4o-mini-2024-07-18",
                "temperature": 0,
                "organization": "",
                "api_key": llm_config.api_key,
                "model_family": "OpenAI"
            }
        }


        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(config_data, temp_file, indent=2)
        temp_file.close()

        logger.info(f"创建临时 LLM 配置文件: {temp_file.name}")
        return temp_file.name
    def _create_statistics_file(self) -> str:

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.write('{}')
        temp_file.close()
        logger.info(f"创建临时统计文件: {temp_file.name}")
        return temp_file.name
    def _create_tools_config_file(self) -> str:


        config_data = [
            {
                "name": "SERPAPI",
                "env": {
                    "SERPAPI_API_KEY": ""
                }
            }
        ]

        config_file_path = os.path.join(self.kgot_project_root, "kgot", "config_tools.json")

        os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
        with open(config_file_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        additional_config_data = [
            {
                "name": "HUGGINGFACE",
                "env": {
                    "HUGGINGFACE_TOKEN": ""
                }
            }
        ]
        additional_config_file_path = os.path.join(
            self.kgot_project_root, "kgot", "tools", "tools_v2_3", "additional_config_tools.json"
        )

        os.makedirs(os.path.dirname(additional_config_file_path), exist_ok=True)
        with open(additional_config_file_path, 'w') as f:
            json.dump(additional_config_data, f, indent=2)
        logger.info(f"创建工具配置文件: {config_file_path}")
        logger.info(f"创建附加工具配置文件: {additional_config_file_path}")
        return config_file_path
    def _cleanup_temp_files(self, *file_paths):

        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"清理临时文件: {file_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败 {file_path}: {e}")
    async def enhanced_problem_solving(self, problem: str, learn_from_solution: bool = True,
                                     abstraction_level: int = None, abstraction_mode: str = "semantic") -> KGOTSolveResult:
        start_time = time.time()

        if not self.llm_enabled:
            return KGOTSolveResult(
                answer="",
                execution_time=time.time() - start_time,
                success=False,
                error="LLM 未启用，无法使用智能求解功能"
            )

        llm_config_file = None
        stats_file = None
        tools_config_file = None
        try:

            llm_config_file = self._create_llm_config_file()
            stats_file = self._create_statistics_file()
            tools_config_file = self._create_tools_config_file()


            from kgot.controller.neo4j.queryRetrieve import Controller

            original_cwd = os.getcwd()
            os.chdir(self.kgot_project_root)
            try:

                if not self.db.driver:
                    self.db.connect()

                logger.info(f"使用数据库连接: {self.db.uri} (用户: {self.db.username})")

                controller = Controller(
                    neo4j_uri=self.db.uri,
                    neo4j_username=self.db.username,
                    neo4j_pwd=self.db.password,
                    python_executor_uri="http://localhost:16000/run",
                    llm_execution_model="gpt-4o-mini",
                    llm_execution_temperature=0.0,
                    statistics_file_name=stats_file,
                    llm_planning_model="gpt-4o-mini",
                    llm_planning_temperature=0.0,
                    config_llm_path=llm_config_file,
                    max_iterations=5
                )
                logger.info("外部 KGOT queryRetrieve 控制器初始化成功")
            finally:

                os.chdir(original_cwd)

            logger.info(f"Starting intelligent problem solving: {problem}")


            solution, iterations = await asyncio.get_event_loop().run_in_executor(
                None,
                controller.run,
                problem,
                "",
                [],
                0,
                ""
            )

            execution_time = time.time() - start_time

            logger.info(f"Intelligent problem solving completed, time: {execution_time:.2f}s, iterations: {iterations}")

            return KGOTSolveResult(
                answer=solution,
                execution_time=execution_time,
                iterations=iterations,
                kg_updates=1 if solution else 0,
                success=bool(solution),
                reasoning_steps=[f"External KGOT queryRetrieve controller executed, iterations: {iterations}"]
            )

        except Exception as e:
            logger.error(f"Intelligent problem solving failed: {e}")
            return KGOTSolveResult(
                answer="",
                execution_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
        finally:

            self._cleanup_temp_files(llm_config_file, stats_file, tools_config_file)
    async def pure_internal_retrieval(self, query: str, abstraction_level: int = None,
                                    abstraction_mode: str = "semantic", view_mode: str = "detailed") -> KGOTRetrieveResult:
        start_time = time.time()

        if not self.llm_enabled:
            return KGOTRetrieveResult(
                answer="",
                execution_time=time.time() - start_time,
                success=False,
                error="LLM not enabled, cannot use pure internal retrieval function"
            )

        llm_config_file = None
        stats_file = None
        tools_config_file = None
        try:

            llm_config_file = self._create_llm_config_file()
            stats_file = self._create_statistics_file()
            tools_config_file = self._create_tools_config_file()


            from kgot.controller.neo4j.directRetrieve import Controller
            from kgot.utils.llm_utils import init_llm_utils

            original_cwd = os.getcwd()
            os.chdir(self.kgot_project_root)
            try:

                if not self.db.driver:
                    self.db.connect()

                logger.info(f"使用数据库连接: {self.db.uri} (用户: {self.db.username})")

                logger.info(f"预先初始化LLM配置: {llm_config_file}")
                init_llm_utils(llm_config_file, 1)


                try:
                    logger.info(f"正在初始化 directRetrieve 控制器（纯内部检索模式，禁用所有外部工具）...")
                    logger.info(f"  - Neo4j URI: {self.db.uri}")
                    logger.info(f"  - Python Executor URI: http://localhost:16000/run")
                    logger.info(f"  - LLM Config: {llm_config_file}")
                    logger.info(f"  - Stats File: {stats_file}")
                    controller = Controller(
                        neo4j_uri=self.db.uri,
                        neo4j_username=self.db.username,
                        neo4j_pwd=self.db.password,
                        python_executor_uri="http://localhost:16000/run",
                        llm_execution_model="gpt-4o-mini",
                        llm_execution_temperature=0.0,
                        llm_planning_model="gpt-4o-mini",
                        llm_planning_temperature=0.0,
                        statistics_file_name=stats_file,
                        config_llm_path=llm_config_file
                    )



                    controller.tools = []
                    controller.tool_names = {}

                    from kgot.utils.llm_utils import get_llm
                    controller.llm_execution = get_llm(
                        controller.llm_execution_model,
                        controller.llm_execution_temperature,
                        controller.config_llm_path
                    )
                    logger.info("✅ directRetrieve 控制器初始化成功（所有外部工具已禁用）")
                except SystemExit as e:

                    logger.error(f"❌ Controller 初始化失败，SystemExit 被触发: {e}")
                    logger.error("这通常是因为 Python Docker 容器连接测试失败")
                    logger.error("请检查:")
                    logger.error("  1. Docker 容器是否在运行: docker ps | grep python")
                    logger.error("  2. 端口 16000 是否可访问: curl -X POST http://localhost:16000/run")
                    logger.error("  3. 容器日志: docker logs python")
                    raise Exception(f"Failed to initialize KGOT Controller. Docker connection test failed. Please ensure Docker container is running on port 16000. SystemExit code: {e.code}")
                logger.info("外部 KGOT directRetrieve 控制器初始化成功")
            finally:

                os.chdir(original_cwd)

            logger.info(f"开始纯内部检索: {query}")

            def pure_retrieve_logic():
                import re
                try:



                    all_entities_and_relationships = controller.graph.get_current_graph_state()
                    logger.info(f"原始数据库状态（包含最新编辑）: {all_entities_and_relationships[:200]}...")


                    if view_mode == "community" and abstraction_level is not None and abstraction_level > 0:


                        logger.info(f"🔍 社群视图 - 过滤数据以匹配抽象层级 {abstraction_level} - 返回 Community 内部的原始节点")
                        existing_entities_and_relationships = self._filter_for_community_members(
                            all_entities_and_relationships, abstraction_level
                        )
                        logger.info(f"✅ 过滤后的社群成员数据: {existing_entities_and_relationships[:300]}...")
                    else:


                        logger.info(f"🔍 {'详细视图' if view_mode == 'detailed' else 'Level 0'} - 使用原始数据（排除 Community 节点）")
                        existing_entities_and_relationships = self._filter_exclude_communities(
                            all_entities_and_relationships
                        )
                        logger.info(f"✅ 过滤后的原始数据: {existing_entities_and_relationships[:300]}...")



                    is_empty = False
                    if not existing_entities_and_relationships:
                        is_empty = True
                    elif existing_entities_and_relationships.strip() == "No nodes found in the database.":
                        is_empty = True
                    elif existing_entities_and_relationships.strip() == "No relevant information found in the database.":
                        is_empty = True
                    elif "Nodes:\n  No nodes found\n" in existing_entities_and_relationships:
                        is_empty = True
                    elif not re.search(r'\{neo4j_id:\d+', existing_entities_and_relationships):

                        is_empty = True

                    if is_empty:
                        logger.warning(f"数据库为空或过滤后无数据，返回空结果")
                        return "No relevant information found in the database", 1

                    from kgot.controller.neo4j.directRetrieve.llm_invocation_handle import define_retrieve_query
                    retrieve_query = define_retrieve_query(
                        controller.llm_planning,
                        query,
                        existing_entities_and_relationships,
                        "",
                        controller.usage_statistics
                    )
                    logger.info(f"生成的检索查询: {retrieve_query}")


                    solutions = controller._perform_retrieve_branch(
                        query,
                        existing_entities_and_relationships,
                        retrieve_query
                    )
                    logger.info(f"检索到的解决方案: {solutions}")



                    if not solutions or all(not sol.strip() for sol in solutions if sol):

                        from kgot.controller.neo4j.directRetrieve.llm_invocation_handle import generate_forced_solution, parse_solution_with_llm
                        forced_solution = generate_forced_solution(
                            controller.llm_planning, query, existing_entities_and_relationships, controller.usage_statistics
                        )
                        if isinstance(forced_solution, str):
                            forced_solution = [forced_solution]

                        solution = parse_solution_with_llm(
                            controller.llm_planning, query, forced_solution[0] if forced_solution else "",
                            controller.gaia_formatter, controller.usage_statistics
                        )
                    else:

                        from kgot.controller.neo4j.directRetrieve.llm_invocation_handle import parse_solution_with_llm, define_final_solution
                        array_parsed_solutions = []
                        for sol in solutions:


                            for i in range(controller.max_final_solution_parsing):
                                array_parsed_solutions.append(
                                    parse_solution_with_llm(controller.llm_planning, query, sol, controller.gaia_formatter, controller.usage_statistics)
                                )
                        if all(not parsed_sol.strip() for parsed_sol in array_parsed_solutions if parsed_sol):

                            from kgot.controller.neo4j.directRetrieve.llm_invocation_handle import generate_forced_solution
                            forced_solution = generate_forced_solution(
                                controller.llm_planning, query, existing_entities_and_relationships, controller.usage_statistics
                            )
                            solution = parse_solution_with_llm(
                                controller.llm_planning, query, forced_solution, controller.gaia_formatter, controller.usage_statistics
                            )
                        else:

                            solution = define_final_solution(
                                controller.llm_planning, query, str(solutions), array_parsed_solutions, controller.usage_statistics
                            )

                    logger.info(f"✅ 纯内部检索完成，答案基于用户编辑后的最新图谱数据")
                    return solution, 1
                except Exception as e:
                    logger.error(f"Error during pure internal retrieval: {e}")
                    import traceback
                    traceback.print_exc()
                    return f"Error during retrieval: {str(e)}", 1

            result = await asyncio.get_event_loop().run_in_executor(
                None, pure_retrieve_logic
            )

            if isinstance(result, tuple):
                answer, iterations = result

                if isinstance(answer, tuple):
                    if len(answer) > 0:
                        answer = str(answer[0])
                    else:
                        answer = "No relevant information found"

                elif isinstance(answer, str) and answer.startswith("('") and answer.endswith("')"):
                    try:
                        import ast
                        parsed_result = ast.literal_eval(answer)
                        if isinstance(parsed_result, tuple) and len(parsed_result) >= 1:
                            answer = str(parsed_result[0])
                        else:
                            answer = "No relevant information found"
                    except:

                        answer = str(answer)
                else:

                    answer = str(answer)
            else:
                answer = str(result)
                iterations = 1
            execution_time = time.time() - start_time

            is_successful = bool(answer) and answer not in ["No relevant information found", "No solution found", "No relevant information found in the database"]
            logger.info(f"Pure internal retrieval completed, time: {execution_time:.2f}s, success: {is_successful}")
            logger.info(f"Answer: {answer[:100]}..." if len(answer) > 100 else f"Answer: {answer}")
            return KGOTRetrieveResult(
                answer=answer,
                execution_time=execution_time,
                context_nodes=1 if is_successful else 0,
                success=is_successful,
                retrieved_context=f"External KGOT directRetrieve controller retrieval result"
            )

        except Exception as e:
            logger.error(f"Pure internal retrieval failed: {e}")
            return KGOTRetrieveResult(
                answer="",
                execution_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
        finally:

            self._cleanup_temp_files(llm_config_file, stats_file, tools_config_file)
    def _filter_for_community_view(self, graph_state: str, abstraction_level: int) -> str:
        import re



        parts = graph_state.split('Relationships:')
        if len(parts) != 2:
            logger.warning("Could not split graph state into Nodes and Relationships sections")
            return "No nodes found in the database."
        nodes_section = parts[0]
        relationships_section = parts[1]

        filtered_nodes = []
        node_ids = set()
        matching_nodes = []


        community_label_pattern = r'Label: Community\s*\n((?:\s+\{neo4j_id:\d+, properties:\{[^}]+\}\}\n?)+)'
        total_nodes = len(re.findall(r'\{neo4j_id:\d+', nodes_section))
        community_nodes = 0

        for label_match in re.finditer(community_label_pattern, nodes_section):
            nodes_data = label_match.group(1)


            node_data_pattern = r'(\{neo4j_id:(\d+), properties:\{[^}]+\}\})'
            for node_match in re.finditer(node_data_pattern, nodes_data):
                community_nodes += 1
                node_str = node_match.group(1)

                level_match = re.search(r"'abstraction_level':\s*(\d+)", node_str)
                if level_match:
                    node_level = int(level_match.group(1))
                    logger.debug(f"Found Community node with level {node_level}, target level: {abstraction_level}")
                    if node_level == abstraction_level:

                        id_match = re.search(r"'id':\s*'([^']+)'", node_str)
                        if id_match:
                            node_id = id_match.group(1)
                            node_ids.add(node_id)
                            matching_nodes.append(node_str)
                            logger.info(f"✅ Added Community node '{node_id}' (level {node_level}) to filtered list")

        if matching_nodes:
            filtered_nodes.append("  Label: Community")
            for node_str in matching_nodes:
                filtered_nodes.append(f"    {node_str}")
        logger.info(f"📊 Total nodes: {total_nodes}, Community nodes: {community_nodes}, Filtered nodes: {len(filtered_nodes)}")

        filtered_relationships = []
        if node_ids:

            rel_pattern = r'\{source: \{neo4j_id: \d+, label: Community\}, target: \{neo4j_id: \d+, label: Community\}, properties: \{[^}]+\}\}'
            for rel_match in re.finditer(rel_pattern, relationships_section):
                rel_str = rel_match.group(0)

                level_match = re.search(r"'abstraction_level':\s*(\d+)", rel_str)
                if level_match and int(level_match.group(1)) == abstraction_level:
                    filtered_relationships.append(f"    {rel_str}")
        logger.info(f"🔗 Filtered relationships: {len(filtered_relationships)}")

        if not filtered_nodes:
            return "No relevant information found in the database."
        filtered_state = "This is the current state of the Neo4j database.\n"
        filtered_state += "Nodes:\n"
        filtered_state += "\n".join(filtered_nodes)
        filtered_state += "\n"
        filtered_state += "Relationships:\n"
        if filtered_relationships:
            filtered_state += "\n".join(filtered_relationships)
        filtered_state += "\n"
        logger.info(f"✅ Filtered community view data: {len(filtered_state)} characters, {len(filtered_nodes)} nodes, {len(filtered_relationships)} relationships")
        return filtered_state
    def _filter_exclude_communities(self, graph_state: str) -> str:
        import re



        parts = graph_state.split('Relationships:')
        if len(parts) != 2:
            logger.warning("Could not split graph state into Nodes and Relationships sections")
            return "No nodes found in the database."
        nodes_section = parts[0]
        relationships_section = parts[1]

        filtered_nodes = []
        node_ids = set()
        node_neo4j_ids = set()


        label_pattern = r'Label: ([^\n]+)\n((?:\s+\{neo4j_id:\d+, properties:\{[^}]+\}\}\n?)+)'

        for label_match in re.finditer(label_pattern, nodes_section):
            label = label_match.group(1).strip()
            nodes_data = label_match.group(2)


            if label == 'Community':
                continue


            node_data_pattern = r'(\{neo4j_id:(\d+), properties:\{[^}]+\}\})'
            for node_match in re.finditer(node_data_pattern, nodes_data):
                node_str = node_match.group(1)
                neo4j_id = node_match.group(2)


                uid_match = re.search(r"'_internal_uid':\s*'([^']+)'", node_str)
                if not uid_match:
                    uid_match = re.search(r'"_internal_uid":\s*"([^"]+)"', node_str)
                if uid_match:
                    node_ids.add(uid_match.group(1))
                    node_neo4j_ids.add(neo4j_id)
                    filtered_nodes.append(f"  Label: {label}\n    {node_str}")
                    logger.debug(f"✅ Added {label} node to filtered list")
        logger.info(f"📊 Filtered nodes: {len(filtered_nodes)} (excluding Community nodes)")

        filtered_relationships = []
        if filtered_nodes:

            rel_pattern = r'(\{source: \{neo4j_id: (\d+), label: ([^}]+)\}, target: \{neo4j_id: (\d+), label: ([^}]+)\}, properties: \{[^}]+\}\})'

            for rel_match in re.finditer(rel_pattern, relationships_section):
                rel_str = rel_match.group(1)
                source_neo4j_id = rel_match.group(2)
                source_label = rel_match.group(3).strip()
                target_neo4j_id = rel_match.group(4)
                target_label = rel_match.group(5).strip()


                rel_type_match = re.search(r"'type':\s*'([^']+)'", rel_str)
                if not rel_type_match:
                    rel_type_match = re.search(r'"type":\s*"([^"]+)"', rel_str)
                rel_type = rel_type_match.group(1) if rel_type_match else ""


                if 'MEMBER_OF' in rel_type or 'COMMUNITY_EDGE' in rel_type:
                    continue


                if source_neo4j_id in node_neo4j_ids and target_neo4j_id in node_neo4j_ids:
                    filtered_relationships.append(f"    {rel_str}")
                    logger.debug(f"✅ Added relationship between {source_label} and {target_label}")
        logger.info(f"🔗 Filtered relationships: {len(filtered_relationships)}")

        if not filtered_nodes:
            logger.warning("No non-Community nodes found after filtering")
            return "No nodes found in the database."
        filtered_state = "This is the current state of the Neo4j database.\n"
        filtered_state += "Nodes:\n"
        filtered_state += "\n".join(filtered_nodes)
        filtered_state += "\n"
        filtered_state += "Relationships:\n"
        if filtered_relationships:
            filtered_state += "\n".join(filtered_relationships)
        filtered_state += "\n"
        logger.info(f"✅ Filtered data: {len(filtered_state)} characters, {len(filtered_nodes)} nodes, {len(filtered_relationships)} relationships")
        return filtered_state
    def _filter_for_community_members(self, graph_state: str, abstraction_level: int) -> str:
        import re


        parts = graph_state.split('Relationships:')
        if len(parts) != 2:
            logger.warning("Could not split graph state into Nodes and Relationships sections")
            return "No nodes found in the database."
        nodes_section = parts[0]
        relationships_section = parts[1]

        community_node_ids = set()
        community_label_pattern = r'Label: Community\s*\n((?:\s+\{neo4j_id:\d+, properties:\{[^}]+\}\}\n?)+)'

        for label_match in re.finditer(community_label_pattern, nodes_section):
            nodes_data = label_match.group(1)
            node_data_pattern = r'(\{neo4j_id:(\d+), properties:\{[^}]+\}\})'
            for node_match in re.finditer(node_data_pattern, nodes_data):
                node_str = node_match.group(1)
                level_match = re.search(r"'abstraction_level':\s*(\d+)", node_str)
                if level_match and int(level_match.group(1)) == abstraction_level:
                    id_match = re.search(r"'id':\s*'([^']+)'", node_str)
                    if id_match:
                        community_node_ids.add(id_match.group(1))
                        logger.debug(f"Found Community node at level {abstraction_level}: {id_match.group(1)}")
        if not community_node_ids:
            logger.warning(f"No Community nodes found at abstraction level {abstraction_level}")
            return "No relevant information found in the database."


        member_node_ids = set()

        try:
            with self.db.get_session() as session:

                for community_id in community_node_ids:
                    member_query = """
                    MATCH (m)-[:MEMBER_OF]->(c:Community)
                    WHERE (c.id = $community_id OR c._internal_uid = $community_id)
                    RETURN collect(coalesce(m._internal_uid, m.id)) as direct_members
                    """
                    result = session.run(member_query, community_id=community_id)
                    record = result.single()

                    if record and record['direct_members']:

                        def expand_members_recursive(member_ids_list):

                            for member_id in member_ids_list:
                                check_query = """
                                MATCH (n)
                                WHERE (n._internal_uid = $id OR n.id = $id)
                                RETURN labels(n) as labels
                                """
                                check_result = session.run(check_query, id=member_id)
                                check_record = check_result.single()

                                if check_record and 'Community' in check_record['labels']:
                                    nested_query = """
                                    MATCH (m)-[:MEMBER_OF]->(c:Community)
                                    WHERE (c.id = $community_id OR c._internal_uid = $community_id)
                                    RETURN collect(coalesce(m._internal_uid, m.id)) as nested_members
                                    """
                                    nested_result = session.run(nested_query, community_id=member_id)
                                    nested_record = nested_result.single()
                                    if nested_record and nested_record['nested_members']:

                                        expand_members_recursive(nested_record['nested_members'])
                                else:

                                    member_node_ids.add(member_id)

                        expand_members_recursive(record['direct_members'])

                logger.info(f"📊 Found {len(member_node_ids)} original nodes in {len(community_node_ids)} communities at level {abstraction_level}")
        except Exception as e:
            logger.error(f"Error querying community members: {e}")
            import traceback
            traceback.print_exc()
            return "No relevant information found in the database."
        if not member_node_ids:
            logger.warning("No member nodes found in communities")
            return "No relevant information found in the database."

        filtered_nodes = []
        node_neo4j_ids = set()
        node_uids = set()


        label_pattern = r'Label: ([^\n]+)\n((?:\s+\{neo4j_id:\d+, properties:\{[^}]+\}\}\n?)+)'
        for label_match in re.finditer(label_pattern, nodes_section):
            label = label_match.group(1).strip()
            nodes_data = label_match.group(2)


            if label == 'Community':
                continue


            node_data_pattern = r'(\{neo4j_id:(\d+), properties:\{[^}]+\}\})'
            for node_match in re.finditer(node_data_pattern, nodes_data):
                node_str = node_match.group(1)
                neo4j_id = node_match.group(2)


                uid_match = re.search(r"'_internal_uid':\s*'([^']+)'", node_str)
                if not uid_match:
                    uid_match = re.search(r'"_internal_uid":\s*"([^"]+)"', node_str)
                id_match = re.search(r"'id':\s*'([^']+)'", node_str)
                if not id_match:
                    id_match = re.search(r'"id":\s*"([^"]+)"', node_str)

                node_uid = uid_match.group(1) if uid_match else None
                node_id = id_match.group(1) if id_match else None


                if (node_uid and node_uid in member_node_ids) or (node_id and node_id in member_node_ids):
                    node_neo4j_ids.add(neo4j_id)
                    if node_uid:
                        node_uids.add(node_uid)
                    if node_id:
                        node_uids.add(node_id)
                    filtered_nodes.append(f"  Label: {label}\n    {node_str}")
                    logger.debug(f"✅ Added member node: {node_uid or node_id}")
        logger.info(f"📊 Filtered {len(filtered_nodes)} member nodes from communities")

        filtered_relationships = []
        if filtered_nodes:
            rel_pattern = r'(\{source: \{neo4j_id: (\d+), label: ([^}]+)\}, target: \{neo4j_id: (\d+), label: ([^}]+)\}, properties: \{[^}]+\}\})'

            for rel_match in re.finditer(rel_pattern, relationships_section):
                rel_str = rel_match.group(1)
                source_neo4j_id = rel_match.group(2)
                target_neo4j_id = rel_match.group(4)


                rel_type_match = re.search(r"'type':\s*'([^']+)'", rel_str)
                if not rel_type_match:
                    rel_type_match = re.search(r'"type":\s*"([^"]+)"', rel_str)
                rel_type = rel_type_match.group(1) if rel_type_match else ""


                if 'MEMBER_OF' in rel_type or 'COMMUNITY_EDGE' in rel_type:
                    continue


                if source_neo4j_id in node_neo4j_ids and target_neo4j_id in node_neo4j_ids:
                    filtered_relationships.append(f"    {rel_str}")
        logger.info(f"🔗 Filtered {len(filtered_relationships)} relationships between member nodes")

        if not filtered_nodes:
            return "No relevant information found in the database."
        filtered_state = "This is the current state of the Neo4j database.\n"
        filtered_state += "Nodes:\n"
        filtered_state += "\n".join(filtered_nodes)
        filtered_state += "\n"
        filtered_state += "Relationships:\n"
        if filtered_relationships:
            filtered_state += "\n".join(filtered_relationships)
        filtered_state += "\n"
        logger.info(f"✅ Filtered community members data: {len(filtered_state)} characters, {len(filtered_nodes)} nodes, {len(filtered_relationships)} relationships")
        return filtered_state

external_kgot_service = ExternalKGOTService()