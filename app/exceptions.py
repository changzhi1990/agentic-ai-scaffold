class BenchmarkAgentError(Exception):
    """Base exception for the benchmark agent."""


class ConfigurationError(BenchmarkAgentError):
    """Raised when configuration files are invalid."""


class CommandExecutionError(BenchmarkAgentError):
    """Raised when a shell command cannot be executed."""
