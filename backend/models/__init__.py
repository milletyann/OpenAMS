# app/models/__init__.py
from .user import User, UserCreate
from .training import TrainingSession, UserTrainingLinks, CoachTrainingLinks
from .performance import Performance
from .health_check import HealthCheck, HealthCheckCreate
from .decathlon import Decathlon, DecathlonPerformance, DecathlonAthleteLink

__all__ = ["User", "UserCreate", "TrainingSession", "UserTrainingLinks", "CoachTrainingLinks", "Performance", "HealthCheck", "HealthCheckCreate", "Decathlon", "DecathlonPerformance", "DecathlonAthleteLink"]
