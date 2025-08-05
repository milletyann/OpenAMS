from enum import Enum

class Sport(str, Enum):
    Various = "Divers"
    Mobilite = "Mobilité"
    Athletisme = "Athlétisme"
    Volleyball = "Volley-ball"
    
class Role(Enum):
    Athlete = "Athlète"
    Coach = "Coach"
    
class Sexe(Enum):
    M = "M"
    F = "F"