import numpy as np
import argparse

men_ec = {
    "100m": [25.4347, 18.00, 1.81],
    "longjump": [0.14354, 220.00, 1.40],
    "shotput": [51.39, 1.50, 1.05],
    "highjump": [0.8465, 75.00, 1.42],
    "400m": [1.53775, 82.00, 1.81],
    "110mH": [5.74352, 28.50, 1.92],
    "discus": [12.91, 4.00, 1.10],
    "polevault": [0.2797, 100.00, 1.35],
    "javelin": [10.14, 7.00, 1.08],
    "1500m": [0.03768, 480.00, 1.85],
    "60m": [58.0150, 11.50, 1.81],
    "60mH": [20.5173, 15.50, 1.92],
    "1000m": [0.08713, 305.50, 1.85],
}

women_ec = {
    "200m": [4.99087, 42.50, 1.81],
    "800m": [0.11193, 254.00, 1.88],
    "100mH": [9.23076, 26.70, 1.835],
    "highjump": [1.84523, 75.00, 1.348],
    "longjump": [0.188807, 210.00, 1.41],
    "shotput": [56.0211, 1.50, 1.05],
    "javelin": [15.9803, 3.80, 1.04],
    "100m": [17.8570, 21.0, 1.81],
    "400m": [1.34285, 91.7, 1.81],
    "1500m": [0.02883, 535, 1.88],
    "polevault": [0.44125, 100, 1.35],
    "discus": [12.3311, 3.00, 1.10],
    "60mH": [20.0479, 17.00, 1.835],
}

throws = ['discus', 'javelin', 'shotput']
jumps = ['longjump', 'highjump', 'polevault']
races = ['60m', '60mH', '100m', '100mH', '110mH', '200m', '400m', '800m', '1000m', '1500m']

def throw_score(perf, coefs):
    a, b, c = coefs
    # conversion de la perf en mètres
    perf /= 100
    # calcul de la perf
    return int(np.floor(a*(perf-b)**c)), a*(perf-b)**c

def jump_score(perf, coefs):
    a, b, c = coefs
    # perf en centimètres
    # calcul de la perf
    return int(np.floor(a*(perf-b)**c)), a*(perf-b)**c

def race_score(perf, coefs):
    a, b, c = coefs
    # perf en secondes
    return int(np.floor(a*(b-perf)**c)), a*(b - perf)**c


# if __name__ == "__main__":
#     # Créer un objet ArgumentParser
#     parser = argparse.ArgumentParser(description='Un programme CLI qui prend deux strings et un float.')

#     # Ajouter les arguments
#     parser.add_argument('sex', type=str, help='Premier argument de type string')
#     parser.add_argument('event', type=str, help='Deuxième argument de type string')
#     parser.add_argument('perf', type=float, help='Argument de type float')

#     # Analyser les arguments
#     args = parser.parse_args()
    
#     sex = args.sex
#     event = args.event
#     perf = args.perf
    
#     if sex == 'M':
#         coefs = men_ec[event]
#     elif sex == 'F':
#         coefs = women_ec[event]

#     if event in throws:
#         points = throw_score(perf, coefs)
#     elif event in jumps:
#         points = jump_score(perf, coefs)
#     elif event in races:
#         points = race_score(perf, coefs)
        
#     print(f"Coefficiens pour l'épreuve {event} ({sex}): {coefs}")
#     print(f"Pour la perf {perf}, cela vaut {points[0]} points!")
    
    