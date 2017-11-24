import itertools
from collections import namedtuple

from grounding.semnet import Sign


class Mapbuilder:

    def __init__(self, ox, oy, Robots, Blocks):
        self.length = ox
        self.width = oy
        self.directions = ['north-west', 'north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west']
        self.name = 'start_situation'
        self.dimension = 4
        self.signs = {}
        self.robots = Robots
        self.blocks = Blocks
        self.cells = []
        for object in itertools.chain(self.robots, self.blocks):
            self.signs[object['name']] = Sign(object['name'])

    def build_cells(self):
        """
        Can build 2 types of cells - global cells and local-robot's cells
        :return: 16 cells
        """
        cells = []
        walls = []
        dirs = []

        situation = Sign(self.name)
        self.signs[self.name] = situation
        sit_meaning = situation.add_meaning()

        near = Sign('Near')
        self.signs['Near'] = near

        def make_near(obj1, obj2, dir = None):
            obj1_mean = obj1.add_meaning()
            obj2_mean = obj2.add_meaning()
            near = self.signs['Near']
            near_mean = near.add_meaning()
            con = near_mean.add_feature(obj1_mean)
            conn = near_mean.add_feature(obj2_mean, effect=True)
            obj1.add_out_meaning(con)
            obj2.add_out_meaning(conn)
            connector = sit_meaning.add_feature(near_mean)
            near.add_out_meaning(connector)
            if dir:
                con = sit_meaning.add_feature(dir.add_meaning(), connector.in_order)
                dir.add_out_meaning(con)
            else:
                return connector

        def connect_cells(pair0, pair1):
            make_near(pair0[0], pair0[1], self.signs['east'])
            make_near(pair0[1], pair0[0], self.signs['west'])
            make_near(pair1[1], pair0[0], self.signs['north-west'])
            make_near(pair0[0], pair1[1], self.signs['south-east'])
            make_near(pair1[0], pair0[1], self.signs['north-east'])
            make_near(pair0[1], pair1[0], self.signs['south-west'])

        for cell_id in range (self.dimension**2):
            cell_sign = Sign('pos_' + str(cell_id))
            self.signs['pos_' + str(cell_id)] = cell_sign
            cells.append(cell_sign)
            self.cells.append([cell_sign])
        for wall_id in range (self.dimension**2):
            wall_sign = Sign('wall_' + str(wall_id))
            self.signs['wall_'+ str(wall_id)] = wall_sign
            walls.append(wall_sign)
        for dir in self.directions:
            dir_sign = Sign(dir)
            self.signs[dir] = dir_sign
            dirs.append(dir)

        prev_column = None
        for column in range(self.dimension):
            col_cells = cells[:self.dimension]
            cells = [pos for pos in cells if pos not in col_cells]
            if prev_column: horiz = list(zip(prev_column, col_cells))
            prev_cell = None
            for id, cell in enumerate(col_cells):
                # make walls in top or bottom sides of the column
                if id==0 or id == len(col_cells)-1:
                    wall = walls.pop(0)
                    connector = make_near(cell, wall)
                    if id == 0:
                        dir = self.signs['north']
                        con = sit_meaning.add_feature(dir.add_meaning(), connector.in_order)
                        dir.add_out_meaning(con)
                    elif id == len(col_cells) - 1:
                        dir = self.signs['south']
                        con = sit_meaning.add_feature(dir.add_meaning(), connector.in_order)
                        dir.add_out_meaning(con)
                # make walls in left or right sides of the column
                if column == 0 or column == self.dimension - 1:
                    wall = walls.pop(0)
                    connector = make_near(cell, wall)
                    if column == 0:
                        west = self.signs['west']
                        con = sit_meaning.add_feature(west.add_meaning(), connector.in_order)
                        west.add_out_meaning(con)

                    elif column == self.dimension - 1:
                        east = self.signs['east']
                        con = sit_meaning.add_feature(east.add_meaning(), connector.in_order)
                        east.add_out_meaning(con)
                # connect cells
                if not prev_cell:
                    prev_cell = cell
                else:
                    #in above direction
                    make_near(cell, prev_cell, self.signs['north'])
                    # in bottom direction
                    make_near(prev_cell, cell, self.signs['south'])
            if prev_column:
                for id, neitb in enumerate(horiz):
                    if id != len(horiz) - 1:
                        connect_cells(horiz[id], horiz[id+1])
                    else:
                        make_near(neitb[0], neitb[1], self.signs['east'])
                        make_near(neitb[1], neitb[0], self.signs['west'])
            prev_column = col_cells
        return situation

    def stretch_map(self):
        """
        there is a relationship between concepts far, nearby, beside, within
        the limits of the dependence of the size of the robot and the map
        :return:
        """

        length = 0
        width = 0
        slipx = round(self.length/self.dimension, 1)
        slipy = round(self.width/self.dimension, 1)
        column = 0
        for cell in self.cells:
            column+=1
            cell.extend((length, width, length+slipx, width+slipy))
            width +=slipy
            if column % self.dimension ==0:
                length +=slipx
                width = 0
        print()



    def localize_objects(self, searchobject = None):
        """
        there is robots localization in cells
        :return: tupe(cell name, object) or list of tuples if not arg
        """
        localization = []
        for cell in self.cells:
            if not len(cell) > 1:
                self.stretch_map()
                break
        for object in itertools.chain(self.robots, self.blocks):
            if searchobject and searchobject == object['name']:
                for cell_dimensions in self.cells:
                    if cell_dimensions[1] <= object['ox'] <= cell_dimensions[3] and cell_dimensions[2] <= object[
                        'oy'] <= cell_dimensions[4]:
                        localization.append((cell_dimensions[0], self.signs[object['name']]))
            elif not searchobject:
                for cell_dimensions in self.cells:
                    if cell_dimensions[1] <= object['ox'] <= cell_dimensions[3] and cell_dimensions[2] <= object['oy'] <= cell_dimensions[4]:
                        localization.append((cell_dimensions[0], self.signs[object['name']]))
        return localization



if __name__ == '__main__':


    robots = [{'name':'Robot1', 'diametr': 0.5, 'ox': 1, 'oy': 1}]
    blocks = [{'name':'Block1','diametr': 0.1, 'ox': 88, 'oy': 48}]


    map = Mapbuilder(ox = 100, oy = 50, Robots = robots, Blocks = blocks)
    sit = map.build_cells()
    map.localize_objects()