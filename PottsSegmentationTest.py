from pottslab import min_l2_potts_2d
import cv2 as cv
import numpy as np

img = cv.imread('pic/1.png')

print(img.shape, img.dtype)

# if img.dtype is uint8, it is need to convert to float64 with value [0,1]
imgf64 = img.astype(np.float64) / 255.0

seg = min_l2_potts_2d(imgf64, gamma=0.8)

print(seg.shape, seg.dtype)
print(seg.min(), seg.max())

segShow = np.clip(seg * 255, 0, 255).astype(np.uint8)

cv.imshow('img', segShow)
cv.waitKey(0)
cv.destroyAllWindows()