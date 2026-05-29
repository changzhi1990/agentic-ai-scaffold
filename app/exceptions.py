"""Custom exceptions for the agent runtime."""


class AgentError(Exception):
    """Base exception for agent runtime failures."""


class ConfigurationError(AgentError):
    """Raised when configuration is invalid."""


class KnowledgeError(AgentError):
    """Raised when knowledge retrieval fails."""


class LLMError(AgentError):
    """Raised when the configured LLM backend fails."""


class ToolExecutionError(AgentError):
    """Raised when a tool cannot be executed."""
