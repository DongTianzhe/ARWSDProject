import cv2 as cv
import numpy as np

img = cv.imread('pic/4.png', cv.IMREAD_GRAYSCALE)

blur = cv.GaussianBlur(img, (5, 5), 0)

edges = cv.Canny(blur, 100, 200)

# cv.imshow('edges', edges)

# cv.waitKey(0)
# cv.destroyAllWindows()

edgePixels = np.count_nonzero(edges)
imgPixels = img.size
# print(edgePixels, imgPixels)

edgeDensity = edgePixels / imgPixels
print(edgeDensity)