import numpy as np
from PIL import Image, ImageDraw
import random
import cv2

def map_builder(n, m, rooms):

    image = np.zeros((n, m), np.uint8)
    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

    #room1
    cv2.rectangle(image, (80, 50), (150, 160), (255, 255, 255), -1)
    #hallway top
    cv2.rectangle(image, (80, 163), (297, 210), (255, 255, 255), -1)
    #room2
    cv2.rectangle(image, (300, 260), (450, 310), (255, 255, 255), -1)
    # hallway main
    cv2.rectangle(image, (250, 210), (297, 460), (255, 255, 255), -1)
    # room3
    cv2.rectangle(image, (80, 410), (247, 460), (255, 255, 255), -1)
    # door 1
    cv2.rectangle(image, (80, 160), (100, 163), (255, 255, 255), -1)
    # door 2
    cv2.rectangle(image, (297, 290), (300, 310), (255, 255, 255), -1)
    # door 3
    cv2.rectangle(image, (247, 440), (250, 460), (255, 255, 255), -1)

    return image

def placer(image, block_size):
    place = []
    for i in range(image.shape[0] // block_size):
        for j in range(image.shape[1] // block_size):
            local_place = []
            colors_sum = 0
            for ii in range(i * block_size, i * block_size + block_size):
                for jj in range(j * block_size, j * block_size + block_size):
                    colors_sum += image[ii][jj][0]
                    local_place.append((ii, jj))
            colors_sum /= block_size * block_size
            if colors_sum == 255:
                place.append(local_place)
    return place

def agent_placer(image, block_size):
    place = placer(image, block_size)
    pl = random.choice(place)
    centre = round(pl[0][1]+(block_size*0.5)), round(pl[0][0]+(block_size*0.5))
    orient = tuple(reversed(pl[round(len(pl) - block_size*0.5)]))

    color = np.random.random_integers(0, 255, size=(1, 3)).tolist()
    cv2.circle(image, centre, round(block_size*0.5), *color, 2)
    cv2.arrowedLine(image, centre, orient, *color, 2)


    return image

def tables_placer(image,block_size):
    place = placer(image, block_size)
    pl = random.choice(place)
    color = np.random.random_integers(0, 255, size=(1, 3)).tolist()
    px = pl[0][1], pl[0][0]+ round(block_size*0.5)
    py = pl[len(pl)-1][1],pl[len(pl)-1][0] - round(block_size*0.5)+1
    pz = px[0], pl[len(pl)-1][0]
    pj = py[0], pl[len(pl)-1][0]
    cv2.line(image, px, py, *color, 2)
    cv2.line(image, px, pz, *color, 2)
    cv2.line(image, py, pj, *color, 2)

    return image

def block_placer(image, block_size):
    place = placer(image, block_size)
    pl = random.choice(place)
    color = np.random.random_integers(0, 255, size=(1, 3)).tolist()
    px = tuple(reversed(pl[0]))
    py = pl[len(pl) - 1][1] - round(block_size * 0.5) + 1, pl[len(pl) - 1][0]- round(block_size * 0.5) + 1

    cv2.rectangle(image, px, py, *color, -1)


    return image



def object_builder(image, agents = 1, tables = 1, blocks = 1):
    block_size = 20
    for agent in range(agents):
        image = agent_placer(image, block_size)
    for table in range(tables):
        image = tables_placer(image, block_size)
    for block in range(blocks):
        image = block_placer(image,block_size)

    return image


if __name__ == "__main__":

   image_name = "test.jpg"
   image = map_builder(480, 620, 3)

   image = object_builder(image, 2, 2, 6)

   cv2.imwrite(image_name, image)
