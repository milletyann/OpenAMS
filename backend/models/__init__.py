# app/models/__init__.py
from .athlete import Athlete, AthleteCreate
from .training import TrainingSession, AthleteTrainingLink

__all__ = ["Athlete", "AthleteCreate", "TrainingSession", "AthleteTrainingLink"]
