from abc import ABC, abstractmethod

from diffsage.models.provider import ProviderRequest, ProviderResponse


class BaseProvider(ABC):
    @abstractmethod
    def generate(self, request: ProviderRequest) -> ProviderResponse: ...
