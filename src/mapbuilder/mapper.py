import itertools
from collections import namedtuple

from grounding.semnet import Sign



def build_cells(proportions, signs, name, robot = None):
    """
    Can build 2 types of cells - global cells and local-robot's cells
    :return: 16 cells
    """
    cells = []
    used_cells = []
    walls = []
    if robot:
        cell_prefix = robot+'cell_'
    else:
        cell_prefix = 'cell_'
        wall_prefix = 'wall_'

    if not name in signs:
        situation = Sign(name)
        signs[name] = situation
        sit_meaning = situation.add_meaning()
    else:
        situation = signs[name]
        sit_meaning = situation.add_meaning()


    def make_near(obj1, obj2, dir = None):
        obj1_mean = obj1.add_meaning()
        obj2_mean = obj2.add_meaning()
        near = signs['Beside']
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
        make_near(pair0[0], pair0[1], signs['east'])
        make_near(pair0[1], pair0[0], signs['west'])
        make_near(pair1[1], pair0[0], signs['north-west'])
        make_near(pair0[0], pair1[1], signs['south-east'])
        make_near(pair1[0], pair0[1], signs['north-east'])
        make_near(pair0[1], pair1[0], signs['south-west'])

    for cell_id in range (proportions**2):
        cell_sign = Sign(cell_prefix + str(cell_id))
        signs[cell_prefix + str(cell_id)] = cell_sign
        cells.append(cell_sign)
        used_cells.append(cell_sign)
    if not robot:
        for wall_id in range (proportions*4):
            wall_sign = Sign(wall_prefix + str(wall_id))
            signs[wall_prefix + str(wall_id)] = wall_sign
            walls.append(wall_sign)


    prev_column = None
    for column in range(proportions):
        col_cells = cells[:proportions]
        cells = [pos for pos in cells if pos not in col_cells]
        if prev_column: horiz = list(zip(prev_column, col_cells))
        prev_cell = None
        for id, cell in enumerate(col_cells):
            if not robot:
                # make walls in top or bottom sides of the column
                if id==0 or id == len(col_cells)-1:
                    wall = walls.pop(0)
                    connector = make_near(cell, wall)
                    if id == 0:
                        dir = signs['north']
                        con = sit_meaning.add_feature(dir.add_meaning(), connector.in_order)
                        dir.add_out_meaning(con)
                    elif id == len(col_cells) - 1:
                        dir = signs['south']
                        con = sit_meaning.add_feature(dir.add_meaning(), connector.in_order)
                        dir.add_out_meaning(con)
                # make walls in left or right sides of the column
                if column == 0 or column == proportions - 1:
                    wall = walls.pop(0)
                    connector = make_near(cell, wall)
                    if column == 0:
                        west = signs['west']
                        con = sit_meaning.add_feature(west.add_meaning(), connector.in_order)
                        west.add_out_meaning(con)

                    elif column == proportions - 1:
                        east = signs['east']
                        con = sit_meaning.add_feature(east.add_meaning(), connector.in_order)
                        east.add_out_meaning(con)
            # connect cells
            if not prev_cell:
                prev_cell = cell
            else:
                #in above direction
                make_near(cell, prev_cell, signs['north'])
                # in bottom direction
                make_near(prev_cell, cell, signs['south'])
        if prev_column:
            for id, neitb in enumerate(horiz):
                if id != len(horiz) - 1:
                    connect_cells(horiz[id], horiz[id+1])
                else:
                    make_near(neitb[0], neitb[1], signs['east'])
                    make_near(neitb[1], neitb[0], signs['west'])
        prev_column = col_cells
    return sit_meaning, used_cells

def stretch_map(slipx, slipy, proportions, robots=None):
    """
    there is a relationship between concepts far, nearby, beside, within
    the limits of the dependence of the size of the robot and the map
    :return:
    """
    def mapping(width0, length0):
        cells = []
        length = length0
        width = width0
        column = 0
        nonlocal slipx, slipy, proportions, cells_number
        for cell in range(cells_number):
            column+=1
            cells.append((length, width, length+slipx, width+slipy))
            width +=slipy
            if column % proportions ==0:
                length +=slipx
                width = width0
        return cells

    cells_number = proportions**2
    cells = []

    if not robots:
        cells.extend(mapping(0, 0))
    else:
        coords = [(robot['name'], robot['ox'], robot['oy']) for robot in robots]
        for place in coords:
            width0= place[1] - 2.5*slipx
            length0 = place[2] - 2.5*slipy
            cells.append([place[0], mapping(width0, length0)])

    return cells


def signify(directions, robots, blocks):
    """
    #TODO read from pddl and connect to grounding

    :param directions:
    :param robots:
    :param blocks:
    :return: signs
    """

    signs = {}

    for dir in directions:
        signs[dir] = Sign(dir)
    for robot in robots:
        name = robot['name']
        signs[name] = Sign(name)
    for block in blocks:
        name = block['name']
        signs[name] = Sign(name)
    signs['Around'] = Sign('Around')
    signs['Beside'] = Sign('Beside')
    signs['Near'] = Sign('Near')
    signs['Far'] = Sign('Far')


    return signs

def localize_objects(cells, cells_signs,robots, blocks,searchobject = None):
    """
    there is objects and subjects localization in cells
    :return: list of tuples(cell name, object)
    """
    localization = {}

    cells_describe = list(zip(cells_signs, cells))

    for object in itertools.chain(robots, blocks):
        if searchobject and searchobject == object['name']:
            for cell in cells_describe:
                if cell[1][0] <= object['ox'] <= cell[1][2] and cell[1][1] <= object[
                    'oy'] <= cell[1][3]:
                    localization[object['name']]= [cell[0], cell[1]]
        elif not searchobject:
            for cell in cells_describe:
                if cell[1][0] <= object['ox'] <= cell[1][2] and cell[1][1] <= object[
                    'oy'] <= cell[1][3]:
                    localization[object['name']] = [cell[0], cell[1]]
    return localization


def mapbuilder(robots, blocks, dimension, proportions):
    directions = ['north-west', 'north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west']

    slipx = round(dimension[0] / proportions, 1)
    slipy = round(dimension[1] / proportions, 1)
    global_cells = stretch_map(slipx, slipy, proportions)
    signs = signify(directions, robots, blocks)
    situation, global_cells_signs = build_cells(proportions, signs, 'map')
    localized = localize_objects(global_cells, global_cells_signs,robots, blocks)

    rcell_width = max([robot['diametr'] for robot in robots])
    rcell_length = round((rcell_width*slipx)/slipy, 1)
    robot_cells = stretch_map(rcell_length, rcell_width, proportions, robots)
    robot_near = []
    for robot in robots:
        robot_near.append(build_cells(proportions, signs, 'Near', robot['name']))


    return None


if __name__ == '__main__':


    robots = [{'name':'Robot1', 'diametr': 0.5, 'ox': 1, 'oy': 1}]
    blocks = [{'name':'Block1','diametr': 0.1, 'ox': 88, 'oy': 48}]
    dimension = (100, 50)
    proportions = 5



    mapbuilder(robots, blocks, dimension, proportions)


    #map = Mapbuilder(ox = 100, oy = 50, Robots = robots, Blocks = blocks)
    #sit = map.build_cells()
    #map.localize_objects()