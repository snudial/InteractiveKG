"""Maintenance script: clear and regenerate the display_name of every node.

Use this to repair display_names that were stored with stray markdown markup.
"""

import asyncio
import logging

from app.database.connection import db_connection
from app.services.auto_display_name_processor import auto_display_name_processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLEAR_DISPLAY_NAMES_QUERY = """
MATCH (n)
WHERE n.display_name IS NOT NULL
REMOVE n.display_name
RETURN count(n) AS cleared_count
"""


async def regenerate_all_display_names():
    """Remove every stored display_name, then regenerate them from scratch."""
    try:
        logger.info("Clearing all existing display_name values...")
        with db_connection.get_session() as session:
            result = session.run(CLEAR_DISPLAY_NAMES_QUERY)
            record = result.single()
            cleared_count = record["cleared_count"] if record else 0
            logger.info("Cleared display_name on %d nodes", cleared_count)

        logger.info("Regenerating all display_name values...")
        result = await auto_display_name_processor.process_data_change_event(node_ids=None)
        logger.info("Regeneration finished: %s", result)

        return {
            "cleared_count": cleared_count,
            "regeneration_result": result,
        }
    except Exception as e:
        logger.error("Failed to regenerate display_name values: %s", e)
        raise


if __name__ == "__main__":
    result = asyncio.run(regenerate_all_display_names())
    print(f"\nDone. Result: {result}")
