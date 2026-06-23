import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import pottslab as pl
import os

img = cv.imread('pic/1.png')
imgrgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
plt.axis('off')
plt.imshow(imgrgb)
plt.show()

imgf64 = img.astype(np.float64) / 255.0
seg = pl.min_l2_potts_2d(imgf64, gamma=0.8)

segShow = np.clip(seg * 255, 0, 255).astype(np.uint8)
imgrgb = cv.cvtColor(segShow, cv.COLOR_BGR2RGB)
plt.axis('off')
plt.imshow(imgrgb)
plt.show()

imgGray = cv.cvtColor(segShow, cv.COLOR_BGR2GRAY)
h, w = imgGray.shape
print(h, w)

kernel = np.ones((3, 3), dtype=np.float32) / 9

# print(imgGray)
imgMean = cv.filter2D(imgGray.astype(np.float32), -1, kernel)
# print(imgMean)

imgMean = np.round(imgMean).astype(np.uint8)
# print(imgMean)

jointHistogram = np.zeros((256, 256), dtype=np.float64)

for i in range(h):
    for j in range(w):
        g = imgGray[i, j]
        m = imgMean[i, j]
        jointHistogram[g, m] += 1

P = jointHistogram / jointHistogram.sum()

P2 = P[P > 0]

entropy = -np.sum(P2 * np.log(P2))
print(entropy)

# print("unique gray:", len(np.unique(imgGray)))

# print("joint nonzero:",
#       np.count_nonzero(jointHistogram))

# print("entropy:",
#       -np.sum(P2*np.log(P2)))