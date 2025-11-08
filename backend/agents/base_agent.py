"""Base class for all agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for agents."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task."""
        pass

    def report_progress(self, status: str, message: str) -> Dict[str, Any]:
        """Report progress update."""
        return {
            "agent": self.name,
            "status": status,
            "message": message
        }

    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(f"[{self.name}] {message}")

    def log_error(self, message: str):
        """Log error message."""
        self.logger.error(f"[{self.name}] {message}")
