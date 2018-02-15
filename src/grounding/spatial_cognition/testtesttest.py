import cv2
import numpy as np
blank_image = np.zeros((10,10,3), np.uint8)
cv2.rectangle(blank_image, (2, 2), (5, 5), (0, 255, 255), -1)

print(blank_image)

cv2.imwrite('test2.jpg', blank_image)