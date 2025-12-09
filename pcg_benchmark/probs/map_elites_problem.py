from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class _DBStructValue:
    info_name: str
    max: float
    min: float = 0.0

@dataclass
class DBStruct:
    X_behavior: _DBStructValue
    Y_behavior: _DBStructValue

class MapElitesInterface(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def descriptor_space(self) -> DBStruct:
        pass

    def behavior_descriptor(self, info) -> tuple[float, float]:
        db_struct = self.descriptor_space()
        x_behavior = info[db_struct.X_behavior.info_name]
        y_behavior = info[db_struct.Y_behavior.info_name]
        return x_behavior, y_behavior

