from abc import ABC, abstractmethod

from codemind_shared_types.schemas import InstallationDTO, RepositoryDTO, RepositorySnapshot


class GitHubClient(ABC):
    @abstractmethod
    async def list_installations(self, *, user_id: str) -> list[InstallationDTO]: ...

    @abstractmethod
    async def list_repositories(self, *, installation_id: str) -> list[RepositoryDTO]: ...

    @abstractmethod
    async def get_repository_snapshot(
        self, *, installation_id: str, external_repo_id: str
    ) -> RepositorySnapshot: ...
