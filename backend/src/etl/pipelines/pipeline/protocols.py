import logging
from typing import Any, Protocol, TypeVar, runtime_checkable

# Type variables for generic protocols
T = TypeVar('T')
ConfigT = TypeVar('ConfigT')
DataT = TypeVar('DataT')


@runtime_checkable
class PipelineProtocol(Protocol[ConfigT]):
    """Protocol defining the interface for all pipelines"""
    config: ConfigT
    logger: logging.Logger

    async def run(self, **kwargs) -> dict[str, Any]:
        """Execute the pipeline and return results"""
        ...

@runtime_checkable
class ProcessorProtocol(Protocol[T]):
    """Protocol for data processors"""

    async def process(self, data: T, config: Any, output_dir: str) -> Any:
        """Process data and return results"""
        ...

@runtime_checkable
class ExtractorProtocol(Protocol[T]):
    """Protocol for data extractors"""

    async def extract(self, **kwargs) -> T:
        """Extract data and return results"""
        ...

@runtime_checkable
class SaverProtocol(Protocol[T]):
    """Protocol for data savers"""

    async def save(self, data: T, **kwargs) -> bool:
        """Save data and return success status"""
        ...

@runtime_checkable
class ParserProtocol(Protocol[T]):
    """Protocol for document parsers"""

    async def parse(self, file_path: str, **kwargs) -> T:
        """Parse document and return structured data"""
        ...

