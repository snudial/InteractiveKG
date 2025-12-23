import os
from typing import Dict, Any
class CleanupConfig:



    DEFAULT_CONFIG = {

        "auto_cleanup_enabled": True,


        "min_duplicates_threshold": 2,
        "cleanup_timeout_seconds": 30,


        "cleanup_after_kgot_solve": True,
        "cleanup_after_kgot_retrieve": False,


        "max_cleanup_batch_size": 100,
        "cleanup_delay_seconds": 0.1,


        "log_cleanup_details": True,
        "log_cleanup_statistics": True,


        "continue_on_cleanup_error": True,
        "max_cleanup_retries": 2,
    }

    @classmethod
    def get_config(cls) -> Dict[str, Any]:

        config = cls.DEFAULT_CONFIG.copy()


        config.update({
            "auto_cleanup_enabled": cls._get_bool_env("AUTO_CLEANUP_ENABLED", config["auto_cleanup_enabled"]),
            "min_duplicates_threshold": cls._get_int_env("MIN_DUPLICATES_THRESHOLD", config["min_duplicates_threshold"]),
            "cleanup_timeout_seconds": cls._get_int_env("CLEANUP_TIMEOUT_SECONDS", config["cleanup_timeout_seconds"]),
            "cleanup_after_kgot_solve": cls._get_bool_env("CLEANUP_AFTER_KGOT_SOLVE", config["cleanup_after_kgot_solve"]),
            "cleanup_after_kgot_retrieve": cls._get_bool_env("CLEANUP_AFTER_KGOT_RETRIEVE", config["cleanup_after_kgot_retrieve"]),
            "max_cleanup_batch_size": cls._get_int_env("MAX_CLEANUP_BATCH_SIZE", config["max_cleanup_batch_size"]),
            "log_cleanup_details": cls._get_bool_env("LOG_CLEANUP_DETAILS", config["log_cleanup_details"]),
            "log_cleanup_statistics": cls._get_bool_env("LOG_CLEANUP_STATISTICS", config["log_cleanup_statistics"]),
            "continue_on_cleanup_error": cls._get_bool_env("CONTINUE_ON_CLEANUP_ERROR", config["continue_on_cleanup_error"]),
            "max_cleanup_retries": cls._get_int_env("MAX_CLEANUP_RETRIES", config["max_cleanup_retries"]),
        })

        return config

    @staticmethod
    def _get_bool_env(key: str, default: bool) -> bool:

        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        return default

    @staticmethod
    def _get_int_env(key: str, default: int) -> int:

        try:
            return int(os.getenv(key, str(default)))
        except (ValueError, TypeError):
            return default

    @classmethod
    def is_auto_cleanup_enabled(cls) -> bool:

        return cls.get_config()["auto_cleanup_enabled"]

    @classmethod
    def should_cleanup_after_kgot_solve(cls) -> bool:

        config = cls.get_config()
        return config["auto_cleanup_enabled"] and config["cleanup_after_kgot_solve"]

    @classmethod
    def should_cleanup_after_kgot_retrieve(cls) -> bool:

        config = cls.get_config()
        return config["auto_cleanup_enabled"] and config["cleanup_after_kgot_retrieve"]

    @classmethod
    def get_cleanup_parameters(cls) -> Dict[str, Any]:

        config = cls.get_config()
        return {
            "min_duplicates_threshold": config["min_duplicates_threshold"],
            "timeout_seconds": config["cleanup_timeout_seconds"],
            "max_batch_size": config["max_cleanup_batch_size"],
            "delay_seconds": config["cleanup_delay_seconds"],
            "max_retries": config["max_cleanup_retries"],
        }

    @classmethod
    def get_logging_config(cls) -> Dict[str, bool]:

        config = cls.get_config()
        return {
            "log_details": config["log_cleanup_details"],
            "log_statistics": config["log_cleanup_statistics"],
        }

    @classmethod
    def should_continue_on_error(cls) -> bool:

        return cls.get_config()["continue_on_cleanup_error"]

cleanup_config = CleanupConfig()