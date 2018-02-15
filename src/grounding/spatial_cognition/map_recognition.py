import numpy as np
import cv2

# загрузите изображение, смените цвет на оттенки серого и уменьшите резкость
image = cv2.imread("test.jpg")
print(image)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# gray = cv2.GaussianBlur(gray, (3, 3), 0)
edged = cv2.Canny(gray, 10, 250)
# cv2.imwrite("output.jpg", edged)
# kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
# closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]
total = 0

for c in cnts:
    # аппроксимируем (сглаживаем) контур
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)
    print("block:")
    print(approx)

    # если у контура 4 вершины, предполагаем, что это книга
    if len(approx) == 8:
        cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)
        total += 1
print("Я нашёл {0} кубиков на этой картинке".format(total))
cv2.imwrite("output.jpg", image)