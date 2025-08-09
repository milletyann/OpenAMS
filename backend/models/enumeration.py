from enum import Enum

# === SPORTS === #
class Sport(str, Enum):
    Various = "Divers"
    Mobilite = "Mobilité"
    Athletisme = "Athlétisme"
    Volleyball = "Volley-ball"
    
# training session names
class AthleTrainings(str, Enum):
    sprintDep = "Sprint - Départ"
    sprintLac = "Sprint - Lactique"
    sprintTech = "Sprint - Technique"
    sprintGammes = "Sprint - Gammes"
    
    haiesTech = "Haies - Technique"
    haiesPassages = "Haies - Passages"
    haiesGammes = "Haies - Gammes"
    
    aerobieH = "Course - Aérobie Haute"
    aerobieB = "Course - Aérobie Basse"
    
    longTech = "Longueur - Technique"
    longElanR = "Longueur - Élan réduit"
    longElanC = "Longueur - Élan complet"
    longGammes = "Longueur - Gammes"
    
    hautTech = "Hauteur - Technique"
    hautElanR = "Hauteur - Élan réduit"
    hautElanC = "Hauteur - Élan complet"
    hautGammes = "Hauteur - Gammes"

    percheTech = "Perche - Technique"
    percheElanR = "Perche - Élan réduit"
    percheElanC = "Perche - Élan complet"
    percheGammes = "Perche - Gammes"
    
    poidsTech = "Poids - Technique"
    poidsElanR = "Poids - Élan réduit"
    poidsElanC = "Poids - Élan complet"
    poidsGammes = "Poids - Gammes"
    
    disqueTech = "Disque - Technique"
    disqueElanR = "Disque - Élan réduit"
    disqueElanC = "Disque - Élan complet"
    disqueGammes = "Disque - Gammes"
    
    javTech = "Javelot - Technique"
    javElanR = "Javelot - Élan réduit"
    javElanC = "Javelot - Élan complet"
    javGammes = "Javelot - Gammes"
    
    lancerPpg = "Lancer - PPG"
    force = "Muscu - Force"
    puiss = "Muscu - Puissance"
    explo = "Muscu - Explosivité"
    ppg = "PPG"
    bondissements = "Bondissements"
    
    compDeca = "Compétition - Décathlon"
    comp100 = "Compétition - 100m"
    compLong = "Compétition - Longueur"
    compPoids = "Compétition - Poids"
    compHaut = "Compétition - Hauteur"
    comp400 = "Compétition - 400m"
    compHaies = "Compétition - 110mH"
    compDisque = "Compétition - Disque"
    compPerche = "Compétition - Perche"
    compJav = "Compétition - Javelot"
    comp1500 = "Compétition - 1500m"
    
class VolleyTrainings(str, Enum):
    tactique = "Tactique"
    technique = "Technique"
    match = "Match"
    ppg = "PPG"
    muscu = "Muscu"
    coordination = "Coordination"

class MobiliteTrainings(str, Enum):
    gen = "Général"
    epaules = "Spécifique - Épaules"
    hanches = "Spécifique - Hanches"
    dos = "Spécifique - Dos"
    jambes = "Spécifique - Jambes"
    bdc = "Spécifique - Bas du corps"
    hdc = "Spécifique - Haut du corps"
    
class DiversTrainings(str, Enum):
    prev_blessure = "Prévention Blessure"
    sport_co = "Sport collectif"
    rando = "Randonnée"
    sortie = "Sortie entre copains"
    raquettes = "Sport de raquette"

# performance names
class AthlePerf(str, Enum):
    deca = "Décathlon"
    sprint100 = "100m"
    long = "Longueur"
    poids = "Poids"
    haut = "Hauteur"
    sprint400 = "400m"
    sprint110H = "110mH"
    sprint100H = "100mH"
    disque = "Disque"
    perche = "Perche"
    jav = "Javelot"
    course1500 = "1500m"
    
    hepta = "Heptathlon"
    sprint60 = "60m"
    sprint60H = "60mH"
    course1000 = "1000m"

class AthlePerfNonMarked(str, Enum):
    sprint200 = "200m"
    sprint400H = "400mH"
    sprint800 = "800m"
    course3000 = "3000m"
    course3000SC = "3000m Steeple"
    course5k = "5000m"
    course10k = "10k"
    courseHM = "Semi-marathon"
    courseM = "Marathon"
    marteau = "Marteau"
    tripleS = "Triple-Saut"

class MuscuPerf(str, Enum):
    squatFull = "Force - Full Squat"
    squatDemi = "Force - 1/2 Squat"
    squatQuart = "Force - 1/4 Squat"
    deadlift = "Force - Deadlift"
    bench = "Force - Développé Couché"
    hipThrust = "Force - Hip Thrust"
    
    #puissance = "Muscu - Puissance"
    cleanJerk = "Puissance - Épaulé Jeté"
    snatch = "Puissance - Arraché"
    clean = "Puissance - Épaulé"
    jerk = "Puissance - Jeté"
    
    #explo = "Muscu - Explosivité"    

class MobilitePerf(str, Enum):
    geFacial = "GE Facial"
    geFrontalG = "GE Frontal Gauche"
    geFrontalD = "GE Frontal Droit"
    hand2Toes = "Hand-to-toes"

class VolleyPerf(str, Enum):
    att = "Attaque"
    digs = "Digs"
    recep = "Recep"
    serviceAce = "Service - Ace"
    servReussis = "Service - réussis"
    contre = "Contre"


# === USER === #
class Role(Enum):
    Athlete = "Athlète"
    Coach = "Coach"
    
class Sexe(Enum):
    M = "M"
    F = "F"
