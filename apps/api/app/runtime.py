from .config import settings
from .services.hybrid_model import HybridRecognitionModel
from .services.landmark_service import HolisticLandmarkService

perception = HolisticLandmarkService(settings.bootstrap_dir / "holistic_landmarker.task")
model = HybridRecognitionModel(
    settings.model_dir,
    settings.bootstrap_dir,
    enable_bootstrap=settings.enable_bootstrap_model,
)
