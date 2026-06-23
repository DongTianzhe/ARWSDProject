from fracDimPy import generate_fbm_curve, box_counting
import cv2

image = cv2.imread('pic/4.png', cv2.IMREAD_GRAYSCALE)

edge = cv2.Canny(image, 100, 200)

# cv2.imshow('detect', edge)

# cv2.waitKey(0)
# cv2.destroyAllWindows()

D, result = box_counting(edge, data_type='image')
print(f"Box-counting dimension: {D:.4f} R-square: {result['R2']:.4f}")
