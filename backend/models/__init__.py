# app/models/__init__.py
from .user import User, UserCreate
from .training import TrainingSession, UserTrainingLinks

__all__ = ["User", "UserCreate", "TrainingSession", "UserTrainingLinks"]
