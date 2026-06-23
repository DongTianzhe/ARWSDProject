from fracDimPy import generate_fbm_curve, box_counting
import numpy as np

curve, actualDim = generate_fbm_curve(dimension=1.5, length=2048)

x = np.arange(len(curve))
D, result = box_counting((x, curve), data_type='curve')
print(f"盒计数维数: {D:.4f}, R²: {result['R2']:.4f}")