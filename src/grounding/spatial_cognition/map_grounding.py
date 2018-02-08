import numpy as np
import cv2
from PIL import Image, ImageDraw
from collections import Counter

def pil_to_list(img):
    return np.array(img.getdata(), np.uint8).reshape(img.size[1], img.size[0], 3)


def experiment_slam_input():



    im = Image.open('spatial_cognition/robots_map.jpg')
    img_drawer = ImageDraw.Draw(im)
    block_sizes = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20, 24, 30, 32, 40, 48, 60, 64, 80, 96, 120, 160, 192, 240, 320,
                   480, 960]
    block_size = block_sizes[2]
    n, m = im.height, im.width
    # ss = set()
    for i in range(n):
        for j in range(m):
            q = sum(im.getpixel((i, j))) // 3
            offset = 253
            if q > offset:
                img_drawer.point((i, j), fill=(0, 0, 0))
            elif q > 50:
                img_drawer.point((i, j), fill=(255, 255, 255))
            else:
                img_drawer.point((i, j), fill=(0, 0, 0))

    # N, M = n // block_size, m // block_size
    # maze = np.zeros(shape=(N, M)).astype(int)


    for i in range(n // block_size):
        for j in range(m // block_size):
            colors_sum = 0
            x, y = i, j
            for ii in range(x * block_size, x * block_size + block_size):
                for jj in range(y * block_size, y * block_size + block_size):
                    colors_sum += sum(im.getpixel((ii, jj))) // 3

            colors_sum /= block_size * block_size
            # ss.add(colors_sum)
            for ii in range(x * block_size, x * block_size + block_size):
                for jj in range(y * block_size, y * block_size + block_size):
                    # if colors_sum > 240:
                    #     maze[j][i] = 0
                    # else:
                    #     maze[j][i] = 1
                    if colors_sum > 240:
                        img_drawer.point((ii, jj), fill=(255, 255, 255))
                    else:
                        img_drawer.point((ii, jj), fill=(0, 0, 0))

    block_size *= 2

    prev_color = []
    for i in range(n // block_size):
        for j in range(m // block_size):
            x, y = i, j
            for ii in range(x * block_size, x * block_size + block_size):
                for jj in range(y * block_size, y * block_size + block_size):
                    prev_color.append(sum(im.getpixel((ii, jj))) // 3)
            common_color = Counter(prev_color).most_common()[0][0]
            for ii in range(x * block_size, x * block_size + block_size):
                for jj in range(y * block_size, y * block_size + block_size):
                    if common_color > 240:
                        img_drawer.point((ii, jj), fill=(255, 255, 255))
                    else:
                        img_drawer.point((ii, jj), fill=(0, 0, 0))
            prev_color = []

    #TODO выделение комнат

    open_cv_image = np.array(im)
    # Convert RGB to BGR
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    edged = cv2.Canny(open_cv_image, 10, 250)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
    # cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]
    # total = 0
    # for c in cnts:
    #     # аппроксимируем (сглаживаем) контур
    #     peri = cv2.arcLength(c, True)
    #     approx = cv2.approxPolyDP(c, 0.02 * peri, True)
    #
    #     # если у контура 4 вершины, предполагаем, что это книга
    #     if len(approx) == 4:
    #         cv2.drawContours(open_cv_image, [approx], -1, (0, 255, 0), 4)
    #         total += 1
    # print(total)
    cv2.imwrite("spatial_cognition/robots_map_1.jpg", edged)

    #TODO выделение коридоров

    #TODO отрисовка робота, стола, блоков

    # im.save('spatial_cognition/robots_map_1.jpg')


if __name__ == '__main__':
    experiment_slam_input()