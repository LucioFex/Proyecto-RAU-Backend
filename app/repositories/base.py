from abc import ABC, abstractmethod

class BaseRepo(ABC):
    @abstractmethod
    def _gen_id(self) -> str: ...
