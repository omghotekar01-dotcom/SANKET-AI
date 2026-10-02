from .config import settings
from .services.hybrid_model import HybridRecognitionModel
from .services.landmark_service import HolisticLandmarkService

# The legacy Solutions Holistic graph does not require an external .task model.
perception = HolisticLandmarkService()
model = HybridRecognitionModel(
    settings.model_dir,
    settings.bootstrap_dir,
    enable_bootstrap=settings.enable_bootstrap_model,
)
