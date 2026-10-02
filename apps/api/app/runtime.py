from .config import settings
from .services.landmark_service import HolisticLandmarkService
from .services.temporal_model import TemporalTemplateModel

perception = HolisticLandmarkService()
model = TemporalTemplateModel(settings.model_dir)
