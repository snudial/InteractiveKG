临时脚本：清除并重新生成所有节点的display_name
用于修复包含markdown标记的错误display_name
import asyncio
import logging
from app.database.connection import db_connection
from app.services.auto_display_name_processor import auto_display_name_processor
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
async def regenerate_all_display_names():

    try:

        logger.info("清除所有现有的display_name...")
        with db_connection.get_session() as session:
                MATCH (n)
                WHERE n.display_name IS NOT NULL
                REMOVE n.display_name
                RETURN count(n) as cleared_count
            record = result.single()
            cleared_count = record["cleared_count"] if record else 0
            logger.info(f"已清除 {cleared_count} 个节点的display_name")

        logger.info("开始重新生成所有display_name...")
        result = await auto_display_name_processor.process_data_change_event(node_ids=None)
        logger.info(f"重新生成完成: {result}")
        return {
            "cleared_count": cleared_count,
            "regeneration_result": result
        }
    except Exception as e:
        logger.error(f"重新生成display_name失败: {e}")
        raise
if __name__ == "__main__":
    result = asyncio.run(regenerate_all_display_names())
    print(f"\n完成！结果: {result}")