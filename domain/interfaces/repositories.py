from abc import ABC, abstractmethod
from domain.entities.video import Video


class IVideoRepository(ABC):
    @abstractmethod
    def register_video(self, video: Video, s3_key: str):
        """Registers a video in the database."""
        pass