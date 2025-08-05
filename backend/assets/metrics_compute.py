import numpy as np

daily_measurements = {
    "sleep_duration": 7.5,
    "sleep_quality": 8,
    "resting_heart_rate": 50,
    "hand_grip_test": 60,
    "longest_expiration_test": 50,
    "one_leg_proprio_test": 100,
}

metrics_data = {
    "sleep_duration": {
        'weight': 1,
        'direction': 'high',
        'function': 'sigmoid',
        'parameters': {
            'lower_midpoint': 5,
            'upper_midpoint': 8.5,
            'steepness': 1,
            'floor': 0,
            'ceil': 1,
            'alpha': 0.59,
        }
    },
    "sleep_quality": {
        'weight': 0.9,
        'direction': 'high',
        'function': 'sigmoid',
        'parameters': {
            'lower_midpoint': 4,
            'upper_midpoint': 10,
            'steepness': 1,
            'floor': 0,
            'ceil': 1,
            'alpha': 0.4,
        }
    },
    "resting_heart_rate": {
        'weight': 0.9,
        'direction': 'low',
        'function': 'sigmoid',
        'parameters': {
            'lower_midpoint': 40,
            'upper_midpoint': 70,
            'steepness': 0.5,
            'floor': 0,
            'ceil': 1,
            'alpha': 0.571,
        }
    },
    "hand_grip_test":{
        'weight': 0.8,
        'direction': 'high',
        'function': 'sigmoid',
        'parameters': {
            'lower_midpoint': 40,
            'upper_midpoint': 70,
            'steepness': 0.5,
            'floor': 0,
            'ceil': 1,
            'alpha': 0.571,
        }
    },
    "longest_expiration_test":{
        'weight': 0.8,
        'direction': 'high',
        'function': 'sigmoid',
        'parameters': {        
            'lower_midpoint': 30,
            'upper_midpoint': 60,
            'steepness': 0.3,
            'floor': 0,
            'ceil': 1,
            'alpha': 0.5,
        }
    },
    "one_leg_proprio_test":{
        'weight': 0.8,
        'direction': 'high',
        'function': 'sigmoid',
        'parameters': {
            'lower_midpoint': 45,
            'upper_midpoint': 120,
            'steepness': 0.1,
            'floor': 0,
            'ceil': 1,
            'alpha': 0.375,
        }
    },
}

# === Score de récupération === #

# Calcul du score global
def recovery_score(measurements):
    normalized_scores = []
    metric_names = metrics_data.keys()
    weight_sum = 0
    for metric, value in measurements.items():
        if metric in metric_names and value: # 'and value' pour skip les valeurs None (les 4 tests optionnels s'ils ne sont pas renseignés)
            score, weight = normalize_metric(value, metric)
            weight_sum += weight
            normalized_scores.append(score)
            
    if weight_sum == 0:
        return 0.0
    
    combined_score = np.sum(normalized_scores)/weight_sum
    return round(combined_score * 10, 2)


# Calcul de la valeur normalisée par métrique
def normalize_metric(value, metric_name):
    weigth = metrics_data[metric_name]['weight']
    direction = metrics_data[metric_name]['direction']
    
    lower_midpoint = metrics_data[metric_name]['parameters']['lower_midpoint']
    upper_midpoint = metrics_data[metric_name]['parameters']['upper_midpoint']
    steepness = metrics_data[metric_name]['parameters']['steepness']
    floor = metrics_data[metric_name]['parameters']['floor']
    ceil = metrics_data[metric_name]['parameters']['ceil']
    alpha = metrics_data[metric_name]['parameters']['alpha']

    if metrics_data[metric_name]['function'] == 'sigmoid':    
        score = logistic_score(value, lower_midpoint, upper_midpoint, steepness, floor, ceil)
        if direction == "low":
            score = 1 - score
    
    else:
        print(f"La fonction {metrics_data[metric_name]['function']} n'est pas encore écrite.")
        return 0, 0 # placeholder for returning a score and a weight if fallback no with no associated function
    
    return score*weigth, weigth

# SIGMOID
def logistic_score(x, lower_midpoint, upper_midpoint, steepness=1.0, floor=0.0, ceil=1.0):
    midpoint = (lower_midpoint+upper_midpoint)/2
    raw_score = 1 / (1 + np.exp(-steepness * (x - midpoint)))
    
    return floor + (ceil - floor) * raw_score

if __name__ == '__main__':
    recovery = recovery_score(daily_measurements)
    print(f"Recovery score: {recovery}/10")