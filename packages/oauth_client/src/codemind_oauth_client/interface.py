from abc import ABC, abstractmethod

from codemind_shared_types.schemas import OAuthUserInfoDTO


class OAuthProvider(ABC):
    @abstractmethod
    def authorize_url(self, *, state: str) -> str: ...

    @abstractmethod
    async def exchange_code(self, *, code: str) -> OAuthUserInfoDTO: ...
