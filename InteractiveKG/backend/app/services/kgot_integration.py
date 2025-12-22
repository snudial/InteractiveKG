import logging
from typing import Optional
from .external_kgot_service import external_kgot_service, KGOTSolveResult, KGOTRetrieveResult
logger = logging.getLogger(__name__)
class EnhancedKGOTService:


    def __init__(self):

        self._external_service = external_kgot_service
        logger.info("EnhancedKGOTService 初始化完成，使用外部 KGOT 项目集成")
    @property
    def llm_enabled(self):

        return self._external_service.llm_enabled
    async def enhanced_problem_solving(self, problem: str, learn_from_solution: bool = True,
                                     abstraction_level: int = None, abstraction_mode: str = "semantic") -> KGOTSolveResult:
        logger.info(f"委托智能问题求解到外部 KGOT 服务: {problem}")
        return await self._external_service.enhanced_problem_solving(
            problem=problem,
            learn_from_solution=learn_from_solution,
            abstraction_level=abstraction_level,
            abstraction_mode=abstraction_mode
        )
    async def pure_internal_retrieval(self, query: str, abstraction_level: int = None,
                                    abstraction_mode: str = "semantic", view_mode: str = "detailed") -> KGOTRetrieveResult:
        logger.info(f"委托纯内部检索到外部 KGOT 服务: {query}, view_mode: {view_mode}")
        return await self._external_service.pure_internal_retrieval(
            query=query,
            abstraction_level=abstraction_level,
            abstraction_mode=abstraction_mode,
            view_mode=view_mode
        )

enhanced_kgot_service = EnhancedKGOTService()