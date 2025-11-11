# import numpy as np
# from .preprocessing import handle_missing_values, handle_outliers

# def laplace_mechanism(value, epsilon, sensitivity):
#     scale = sensitivity / epsilon
#     noise = np.random.laplace(0, scale)
#     return value + noise

# def laplace_local_differential_privacy(input_data, epsilon, sensitivity):
#     result = handle_missing_values(input_data)
#     print("After handle_missing_values:", result, type(result))
#     result = handle_outliers(result)
#     print("After handle_outliers:", result, type(result))
#     noisy_data = []

#     for row in result:
#         try:
#             num = float(row)
#             num = laplace_mechanism(num, epsilon, sensitivity)
#             noisy_data.append(num)  # int 변환은 필요 없을 수도 있음
#         except ValueError:
#             continue
#     return noisy_data

import numpy as np
from .preprocessing import handle_missing_values, handle_outliers

def laplace_mechanism(value, epsilon, sensitivity):
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return value + noise

def laplace_local_differential_privacy(input_data, epsilon, sensitivity):
    # result = handle_missing_values(input_data)
    # result = handle_outliers(result)
    noisy_data = []

    for val in input_data:
        try:
            noisy_data.append(laplace_mechanism(float(val), epsilon, sensitivity))
        except (ValueError, TypeError):
            continue
    return noisy_data  # 항상 리스트 반환
