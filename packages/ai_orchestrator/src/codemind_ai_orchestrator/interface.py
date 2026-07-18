from abc import ABC, abstractmethod

from codemind_shared_types.schemas import (
    FileSummaryDTO,
    FindingDetailDTO,
    ParsedSymbol,
    ProposedFixDTO,
    RetrievedChunkDTO,
    SubsystemDTO,
)


class AIProvider(ABC):
    @abstractmethod
    async def summarize_file(
        self, *, file_path: str, content: str, symbols: list[ParsedSymbol]
    ) -> str: ...

    @abstractmethod
    async def summarize_directory(
        self, *, dir_path: str, file_summaries: list[FileSummaryDTO]
    ) -> str: ...

    @abstractmethod
    async def identify_subsystems(self, *, file_paths: list[str]) -> list[SubsystemDTO]: ...

    @abstractmethod
    async def answer_repository_question(
        self, *, question: str, citations: list[RetrievedChunkDTO]
    ) -> str: ...

    @abstractmethod
    async def propose_fix(
        self, *, finding: FindingDetailDTO, file_content: str
    ) -> ProposedFixDTO: ...
