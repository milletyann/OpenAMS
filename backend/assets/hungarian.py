import numpy as np
import argparse

men_ec = {
    "100m": [25.4347, 18.00, 1.81],
    "Longueur": [0.14354, 220.00, 1.40],
    "Poids": [51.39, 1.50, 1.05],
    "Hauteur": [0.8465, 75.00, 1.42],
    "400m": [1.53775, 82.00, 1.81],
    "110mH": [5.74352, 28.50, 1.92],
    "Disque": [12.91, 4.00, 1.10],
    "Perche": [0.2797, 100.00, 1.35],
    "Javelot": [10.14, 7.00, 1.08],
    "1500m": [0.03768, 480.00, 1.85],
    "60m": [58.0150, 11.50, 1.81],
    "60mH": [20.5173, 15.50, 1.92],
    "1000m": [0.08713, 305.50, 1.85],
}

women_ec = {
    "100m": [17.8570, 21.0, 1.81],
    "Longueur": [0.188807, 210.00, 1.41],
    "Poids": [56.0211, 1.50, 1.05],
    "Hauteur": [1.84523, 75.00, 1.348],
    "400m": [1.34285, 91.7, 1.81],
    "100mH": [9.23076, 26.70, 1.835],
    "Disque": [12.3311, 3.00, 1.10],
    "Perche": [0.44125, 100, 1.35],
    "Javelot": [15.9803, 3.80, 1.04],
    "60mH": [20.0479, 17.00, 1.835],
    "1500m": [0.02883, 535, 1.88],
    "200m": [4.99087, 42.50, 1.81],
    "800m": [0.11193, 254.00, 1.88],
    "60m": [46.0849, 13.0, 1.81],
    "1000m": [0.07068, 337.0, 1.88],
}

throws = ['Disque', 'Javelot', 'Poids']
jumps = ['Longueur', 'Hauteur', 'Perche']
races = ['60m', '60mH', '100m', '100mH', '110mH', '200m', '400m', '800m', '1000m', '1500m']

def compute_hungarian_score(event, sex, perf):
    # éviter les erreurs pour les épreuves qu'on peut pas calculer
    if (event not in men_ec) and (event not in women_ec):
        return 0
    
    
    if sex == 'M':
        coefs = men_ec[event]
    elif sex == 'F':
        coefs = women_ec[event]
    else:
        # Si le sexe est "Autre", on ne sait pas quelles équations utiliser.
        return 0

    if event in throws:
        perf /= 100
    # À partir de là les distances sont en m pour les lancers, cm pour les sauts, et les temps sont en s
    
    a, b, c = coefs
    if (event in throws) or (event in jumps):
        if (perf - b) <= 0:
            # la perf est trop mauvaise pour valoir des points
            return 0
        return int(np.floor(a*(perf-b)**c))
    elif event in races:
        if (b - perf) <= 0:
            # la perf est trop mauvaise pour valoir des points
            return 0
        return int(np.floor(a*(b-perf)**c))
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Ajouter les arguments
    parser.add_argument('sex', type=str, help="Sexe de l'athlète")
    parser.add_argument('event', type=str, help="Discipline concernée")
    parser.add_argument('perf', type=float, help="Performance réalisée")

    # Analyser les arguments
    args = parser.parse_args()
    
    event = args.event
    sex = args.sex
    perf = args.perf

    points = compute_hungarian_score(event, sex, perf)
    
    print(f'{perf}: {points}')
    
    