from sqlmodel import SQLModel, Field, Relationship
from datetime import date
from typing import Optional, List
from enum import Enum


class InjuryType(str, Enum):
    Faiblesse = "Faiblesse Musculaire"
    Raideur = "Raideur Musculaire"
    Entorse = "Entorse"
    Elongation = "Élongation"
    Dechirure = "Déchirure"
    Tendinite = "Tendinite"
    Fracture = "Fracture"
    Luxation = "Luxation"
    Contracture = "Contracture"
    Commotion = "Commotion"
    Hematome = "Hématome"
    RuptureLigamentaire = "Rupture Ligamentaire"
    Autre = "Autre"
    
class CapacityRestriction(str, Enum):
    pass
    
class BodyArea(str, Enum):
    Tete = "Tête"
    Cou = "Cou"
    Nuque = "Nuque"
    Trapeze = "Trapèze"
    Epaule = "Épaule"
    Bras = "Bras"
    AvantBras = "AvantBras"
    Main = "Main"
    Poignet = "Poignet"
    Coude = "Coude"
    Dos = "Dos"
    Lombaires = "Lombaires"
    Abdominaux = "Abdominaux"
    Pectoraux = "Pectoraux"
    Hanche = "Hanche"
    Quadriceps = "Quadriceps"
    Adducteur = "Adducteur"
    Ischio = "Ischio-Jambier"
    Fessier = "Fessier"
    Psoas = "Psoas"
    Genou = "Genou"
    Tibia = "Tibia"
    Mollet = "Mollet"
    Cheville = "Cheville"
    Pied = "Pied"
    

class PhysicalIssueTicket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    date_opened: str
    athlete_id: int = Field(foreign_key="user.id")
    area_concerned: BodyArea
    injury_type: InjuryType
    notes: Optional[str] = None
    is_closed: bool

    followups: List["PhysicalIssueFollowUp"] = Relationship(back_populates="ticket")


class PhysicalIssueFollowUp(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="physicalissueticket.id")
    date: str
    pain_intensity: int
    capacity_restriction: str
    status_notes: Optional[str] = None
    treatments_applied: Optional[str] = None

    ticket: Optional[PhysicalIssueTicket] = Relationship(back_populates="followups")
