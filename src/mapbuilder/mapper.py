from grounding.semnet import Sign


class Mapbuilder:

    def __init__(self, m, n, blocks):
        self.length = m
        self.width = n
        self.blocks = blocks
        self.directions = ['north', 'east', 'south', 'west']
        self.name = 'start'

    def build(self):
        signs = {}
        cells = []
        walls = []
        dirs = []

        situation = Sign(self.name)
        signs[self.name] = situation
        sit_meaning = situation.add_meaning()


        near = Sign('Near')
        signs['Near'] = near

        for cell_id in range (self.length*self.width):
            cell_sign = Sign('pos_' + str(cell_id))
            signs['pos_' + str(cell_id)] = cell_sign
            cells.append(cell_sign)
        for wall_id in range (2*self.width + 2*self.length):
            wall_sign = Sign('wall_' + str(wall_id))
            signs['wall_'+ str(wall_id)] = wall_sign
            walls.append(wall_sign)
        for dir in self.directions:
            dir_sign = Sign(dir)
            signs[dir] = dir_sign
            dirs.append(dir)

        prev_column = None
        for column in range(self.length):

            col_cells = cells[:self.width]
            cells = [pos for pos in cells if pos not in col_cells]

            if prev_column: horiz = list(zip(prev_column, col_cells))

            prev_cell = None

            for id, cell in enumerate(col_cells):
                near_mean = near.add_meaning()
                wall = walls.pop(0)
                wall_mean = wall.add_meaning()
                cell_mean = cell.add_meaning()
                con = near_mean.add_feature(cell_mean)
                conn = near_mean.add_feature(wall_mean, effect=True)
                cell.add_out_meaning(con)
                wall.add_out_meaning(conn)
                connector = sit_meaning.add_feature(near_mean)
                near.add_out_meaning(connector)
                if id == 0:
                    dir = signs['north']
                    con = sit_meaning.add_feature(dir.add_meaning(), connector.in_order)
                    dir.add_out_meaning(con)
                elif id == len(col_cells) - 1:
                    dir = signs['south']
                    con = sit_meaning.add_feature(dir.add_meaning(), connector.in_order)
                    dir.add_out_meaning(con)

                if column == 0 or column == self.length -1:
                    near_mean = near.add_meaning()
                    wall = walls.pop(0)
                    wall_mean = wall.add_meaning()
                    cell_mean = cell.add_meaning()
                    con = near_mean.add_feature(cell_mean)
                    conn = near_mean.add_feature(wall_mean, effect=True)
                    cell.add_out_meaning(con)
                    wall.add_out_meaning(conn)
                    connector = sit_meaning.add_feature(near_mean)
                    near.add_out_meaning(connector)
                    if column == 0:
                        west = signs['west']
                        con = sit_meaning.add_feature(west.add_meaning(), connector.in_order)
                        west.add_out_meaning(con)
                    elif column == self.length - 1:
                        east = signs['east']
                        con = sit_meaning.add_feature(east.add_meaning(), connector.in_order)
                        east.add_out_meaning(con)
                if not prev_cell:
                    prev_cell = cell
                else:
                    #in above direction
                    near_mean = near.add_meaning()
                    cell_mean = cell.add_meaning()
                    prev_cell_mean = prev_cell.add_meaning()
                    con = near_mean.add_feature(cell_mean)
                    conn = near_mean.add_feature(prev_cell_mean, effect=True)
                    cell.add_out_meaning(con)
                    prev_cell.add_out_meaning(conn)
                    connector = sit_meaning.add_feature(near_mean)
                    near.add_out_meaning(connector)
                    north = signs['north']
                    con = sit_meaning.add_feature(north.add_meaning(), connector.in_order)
                    north.add_out_meaning(con)
                    # in bottom direction
                    near_mean = near.add_meaning()
                    cell_mean = cell.add_meaning()
                    prev_cell_mean = prev_cell.add_meaning()
                    con = near_mean.add_feature(cell_mean, effect=True)
                    conn = near_mean.add_feature(prev_cell_mean)
                    cell.add_out_meaning(con)
                    prev_cell.add_out_meaning(conn)
                    connector = sit_meaning.add_feature(near_mean)
                    near.add_out_meaning(connector)
                    south = signs['south']
                    con = sit_meaning.add_feature(south.add_meaning(), connector.in_order)
                    south.add_out_meaning(con)
                if prev_column:
                    neightbor = [lt for lt in horiz if cell in lt]
                    left_cell = neightbor[0][0]
                    # in left direction
                    near_mean = near.add_meaning()
                    cell_mean = cell.add_meaning()
                    left_cell_mean = left_cell.add_meaning()
                    con = near_mean.add_feature(cell_mean)
                    conn = near_mean.add_feature(left_cell_mean, effect=True)
                    cell.add_out_meaning(con)
                    left_cell.add_out_meaning(conn)
                    connector = sit_meaning.add_feature(near_mean)
                    near.add_out_meaning(connector)
                    west = signs['west']
                    con = sit_meaning.add_feature(west.add_meaning(), connector.in_order)
                    west.add_out_meaning(con)
                    # in right direction
                    near_mean = near.add_meaning()
                    cell_mean = cell.add_meaning()
                    left_cell_mean = left_cell.add_meaning()
                    con = near_mean.add_feature(cell_mean, effect=True)
                    conn = near_mean.add_feature(left_cell_mean)
                    cell.add_out_meaning(con)
                    left_cell.add_out_meaning(conn)
                    connector = sit_meaning.add_feature(near_mean)
                    near.add_out_meaning(connector)
                    east = signs['east']
                    con = sit_meaning.add_feature(east.add_meaning(), connector.in_order)
                    east.add_out_meaning(con)
                    print()
            prev_column = col_cells
        print()


if __name__ == '__main__':

    map = Mapbuilder(3, 2, 0)
    map.build()
