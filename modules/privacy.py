import numpy as np
from preprocessing import handle_missing_values, handle_outliers

def laplace_mechanism(value, epsilon, sensitivity):
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return value + noise

def laplace_local_differential_privacy(input_data, epsilon, sensitivity):
    result = handle_missing_values(input_data)
    result = handle_outliers(result)
    noisy_data = []

    for row in result:
        noisy_row = []
        for item in row:
            try:
                num = float(item)
                num = laplace_mechanism(num, epsilon, sensitivity)
                noisy_row.append(str(int(num)))
            except ValueError:
                noisy_row.append(item)
        noisy_data.append(noisy_row)

    return noisy_data
