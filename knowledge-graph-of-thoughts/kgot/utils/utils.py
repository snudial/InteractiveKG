







import os
from typing import Any

def ensure_file_path_exists(logs_file: str) -> None:
    Create the directories of a filepath if not existing already.
    Args:
        logs_file (str): Path to the file.

    directory = os.path.dirname(logs_file)

    if directory != '' and not os.path.exists(directory):

        os.makedirs(directory)
def is_empty_solution(solution: Any) -> bool:
    Check if a solution is empty.
    Args:
        solution (Any): The solution to check.
    Returns:
        bool: True if the solution is empty, False otherwise.

    if solution is None:
        return True


    if isinstance(solution, dict):

        return not solution or all(is_empty_solution(value) for value in solution.values())


    if isinstance(solution, list):

        return not solution or all(is_empty_solution(element) for element in solution)


    return False