from abc import ABC, abstractmethod
from pathlib import Path

class VideoEngine(ABC):
    @abstractmethod
    def render(self, scene_path: Path, metadata: dict, output_path: Path) -> Path:
        """
        Generates a video from the scene.
        Returns path to generated video.
        """
        pass