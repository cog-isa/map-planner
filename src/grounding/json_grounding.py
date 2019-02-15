import itertools
import logging
import re
import sys
from copy import deepcopy, copy
from functools import reduce
from mapplanner.grounding.semnet import Sign
from mapplanner.grounding.sign_task import Task

signs = {}


def locater(location_name, map_size, objects, walls):
    dislocations = {}
    place_map = {}
    itera = 0
    start_x = map_size[0]
    start_y = map_size[1]

    blocksize = (map_size[2] - map_size[0]) / 3, (map_size[3] - map_size[1]) / 3

    for i in range(3):
        for j in range(3):
            fy = j * blocksize[1] + blocksize[1] + start_y
            fx = i * blocksize[0] + blocksize[0] + start_x
            dislocations[location_name + str(itera)] = [i * blocksize[0] + start_x, j * blocksize[1] + start_y, fx, fy]
            itera += 1

    for lkey, lvalue in dislocations.items():
        for ckey, cvalue in objects.items():
            object_x = cvalue['x']
            object_y = cvalue['y']
            if lvalue[0] <= object_x <= lvalue[2] and lvalue[1] <= object_y <= lvalue[3]:
                place_map.setdefault(lkey, set()).add(ckey)
            else:
                place_map.setdefault(lkey, set()).add(0)
        for wall in walls:
            if wall[1] <= lvalue[1] <= wall[3] and wall[0] <= lvalue[0] <= wall[2]:
                place_map.setdefault(lkey, set()).add('wall')
            elif wall[1] <= lvalue[3] <= wall[3] and wall[0] <= lvalue[2] <= wall[2]:
                place_map.setdefault(lkey, set()).add('wall')
            elif wall[3] <= lvalue[3] <= wall[1] and wall[0] <= lvalue[2] <= wall[2]:
                place_map.setdefault(lkey, set()).add('wall')
            elif lvalue[0] <= wall[0] <= lvalue[2] and wall[1] <= lvalue[1] <= wall[3]:
                place_map.setdefault(lkey, set()).add('wall')
            elif lvalue[0] <= wall[2] <= lvalue[2] and wall[1] <= lvalue[3] <= wall[3]:
                place_map.setdefault(lkey, set()).add('wall')
            elif lvalue[1] <= wall[1] <= lvalue[3] and wall[0] <= lvalue[0] <= wall[2]:
                place_map.setdefault(lkey, set()).add('wall')
            elif lvalue[1] <= wall[3] <= lvalue[3] and wall[0] <= lvalue[2] <= wall[2]:
                place_map.setdefault(lkey, set()).add('wall')
    for cell_name, signif in place_map.items():
        if len(signif) > 1 and 0 in signif:
            signif.remove(0)
    # remove border elements in cell, where less elements. Because clarification is needed
    for cell_name, signif in place_map.items():
        for element in signif:
            if element != 0 and not 'wall' in element:
                for cell_name2, signif2 in place_map.items():
                    if element in signif2 and cell_name != cell_name2:
                        if signif2 > signif:
                            signif.remove(element)
                            if len(signif) == 0:
                                signif.add(0)
                        else:
                            signif2.remove(element)
                            if len(signif2) == 0:
                                signif2.add(0)

    return dislocations, place_map


def scale(slist):
    newl = []
    for s in slist:
        if s != 0 and s % 3 > 0:
            s -= s % 3
            newl.append(s)
        elif s < 0 and s % 3 != 0:
            s += s % 3
            newl.append(s)
        else:
            newl.append(s)
    return newl


def size_founder(reg_loc, obj_loc, ag, border, cl_lv=0):
    others = set()
    target = None
    others.add(ag)
    reg_loc = scale(reg_loc)
    dislocations, place_map = locater('proto-cell', reg_loc, obj_loc, border)
    for cell, filling in place_map.items():
        if ag in filling:
            others = filling - others
            target = cell
            break
    if others:
        cl_lv += 1
        proto = scale(dislocations[target])
        size, cl_lv = size_founder(proto, obj_loc, ag, border, cl_lv)
    else:
        size = scale(dislocations[target])
        if not size[3] - size[1] > obj_loc[ag]['r'] or not size[2] - size[0] > obj_loc[ag]['r']:
            raise Exception('Can not place object! Too little space!')
            # sys.exit(1)
    return size, cl_lv


def belonging(cell, reg):
    Rx = (cell[2] - cell[0]) // 2
    Ry = (cell[3] - cell[1]) // 2
    a = reg[0] <= cell[0] and reg[1] <= cell[1]
    b = reg[2] >= cell[2] and reg[3] >= cell[3]
    if a and b:
        return True
    elif cell[0] <= reg[0] and cell[1] >= reg[1] and b:
        if reg[0] - cell[0] <= Rx:
            return True
    elif cell[0] >= reg[0] and cell[1] <= reg[1] and b:
        if reg[1] - cell[1] <= Ry:
            return True
    elif a and cell[2] >= reg[2] and cell[3] <= reg[3]:
        if cell[2] - reg[2] <= Rx:
            return True
    elif a and cell[2] <= reg[2] and cell[3] >= reg[3]:
        if cell[3] - reg[3] <= Ry:
            return True
    elif cell[0] <= reg[0] and cell[1] <= reg[1] and b:
        if reg[1] - cell[1] <= Ry and reg[0] - cell[0] <= Rx:
            return True
    elif cell[2] >= reg[2] and cell[3] >= reg[3] and a:
        if cell[2] - reg[2] <= Rx and cell[3] - reg[3] <= Ry:
            return True
    elif reg[0] < cell[0] and reg[1] > cell[1] and reg[2] < cell[2] and reg[3] > cell[3]:
        if cell[2] - reg[2] <= Rx and reg[1] - cell[1] <= Ry:
            return True
    elif reg[0] > cell[0] and reg[1] < cell[1] and reg[2] > cell[2] and reg[3] < cell[3]:
        if reg[0] - cell[0] <= Rx and cell[3] - reg[3] <= Ry:
            return True
    return False


def signify_connection(signs):
    Send = Sign("Send")
    send_signif = Send.add_significance()
    Broadcast = Sign("Broadcast")
    brdct_signif = Broadcast.add_significance()
    connector = brdct_signif.add_feature(send_signif)
    Send.add_out_significance(connector)
    Approve = Sign("Approve")
    approve_signif = Approve.add_significance()
    connector = approve_signif.add_feature(send_signif)
    Send.add_out_significance(connector)
    signs[Send.name] = Send
    signs[Broadcast.name] = Broadcast
    signs[Approve.name] = Approve

    They_sign = signs["They"]
    agents = They_sign.spread_up_activity_obj("significance", 1)
    agents_type = []
    for agent in agents:
        agents_type.append({cm.sign for cm in agent.sign.spread_up_activity_obj("significance", 1)})
    types = []
    if agents_type:
        types = [t for t in reduce(lambda x, y: x & y, agents_type) if t != signs["object"]]
    if types and len(agents):
        type = types[0]
    else:
        type = signs["I"]

    They_signif = They_sign.add_significance()
    brdct_signif = Broadcast.add_significance()
    connector = They_signif.add_feature(brdct_signif)
    Broadcast.add_out_significance(connector)
    type_signif = type.add_significance()
    approve_signif = Approve.add_significance()

    connector = type_signif.add_feature(approve_signif)
    Approve.add_out_significance(connector)

    brdct_signif = Broadcast.add_significance()
    executer = brdct_signif.add_execution(Broadcast.name.lower(), effect=True)
    Send.add_out_significance(executer)

    approve_signif = Approve.add_significance()
    executer = approve_signif.add_execution(Approve.name.lower(), effect=True)
    Send.add_out_significance(executer)


def adjoints(cdisl, rdisl):
    y_f = (cdisl[3] - cdisl[1]) // 2
    x_f = (cdisl[2] - cdisl[0]) // 2
    if rdisl[0] - x_f <= cdisl[2] <= rdisl[0] + x_f and rdisl[1] - y_f <= cdisl[3] <= rdisl[1] + y_f:
        return True
    elif rdisl[0] - x_f <= cdisl[0] and cdisl[2] <= rdisl[2] + x_f and rdisl[1] - y_f <= cdisl[3] <= rdisl[1] + y_f:
        return True
    elif rdisl[2] - x_f <= cdisl[0] <= rdisl[2] + x_f and rdisl[1] - y_f <= cdisl[3] <= rdisl[1] + y_f:
        return True
    elif rdisl[2] - x_f <= cdisl[0] <= rdisl[2] + x_f and rdisl[1] - y_f <= cdisl[1] and cdisl[3] <= rdisl[3] + y_f:
        return True
    elif rdisl[2] - x_f <= cdisl[0] <= rdisl[2] + x_f and rdisl[3] - y_f <= cdisl[1] <= rdisl[3] + y_f:
        return True
    elif rdisl[0] - x_f <= cdisl[0] and cdisl[2] <= rdisl[2] + x_f and rdisl[3] - y_f <= cdisl[1] <= rdisl[3] + y_f:
        return True
    elif rdisl[0] - x_f <= cdisl[2] <= rdisl[0] + x_f and rdisl[3] - y_f <= cdisl[1] <= rdisl[3] + y_f:
        return True
    elif rdisl[0] - x_f <= cdisl[2] <= rdisl[0] + x_f and rdisl[1] - y_f <= cdisl[1] and cdisl[3] <= rdisl[3] + y_f:
        return True
    return False


def cell_creater(size, obj_loc, region_location, wall, cl_lv=0):
    cell_loc = {}
    near_loc = {}
    ysize = size[3] - size[1]
    xsize = size[2] - size[0]
    new_region = [size[0] - xsize, size[1] - ysize, size[2] + xsize, size[3] + ysize]
    new_region = scale(new_region)
    cell_coords, cell_map = locater('cell-', new_region, obj_loc, wall)
    if len(cell_map['cell-4']) > 1:
        cl_lv += 1
        ysize = (size[3] - size[1]) // 3
        xsize = (size[2] - size[0]) // 3
        new_cell = [size[0] + xsize, size[1] + ysize, size[2] - xsize, size[3] - ysize]
        cell_loc, cell_map, near_loc, cell_coords, cl_lv = cell_creater(new_cell, obj_loc, region_location, wall, cl_lv)
    if not cell_loc and not near_loc:
        for cell, cdisl in cell_coords.items():
            for region, rdisl in region_location.items():
                if belonging(cdisl, rdisl):
                    cell_loc.setdefault(region, []).append(cell)
                    break
            else:
                cell_loc.setdefault('wall', []).append(cell)
            for region, rdisl in region_location.items():
                if adjoints(cdisl, rdisl):
                    near_loc.setdefault(cell, set()).add(region)
            if cell not in near_loc:
                near_loc.setdefault(cell, set()).add(0)

    return cell_loc, cell_map, near_loc, cell_coords, cl_lv


def signs_markup(parsed_map, static_map, agent, size=None, cl_lv=0):
    # place objects on map
    """
    :param parsed_map - dict vs objects
    :param agent - planning agent
    :param static_map - static map repr
    :return devision on regions, cells and cell_location
    """
    map_size = static_map.get('map_size')
    objects = parsed_map.get('objects')
    map_size = scale(map_size)
    # cl_lv = 0

    rmap = [0, 0]
    rmap.extend(map_size)

    # division into regions
    region_location, region_map = locater('region-', rmap, objects, static_map['wall'])

    # division into cells
    # cell size finding
    if not size:
        size = 0
        for key, value in region_map.items():
            if agent in value:
                new_val = deepcopy(value)
                new_val.remove(agent)
                if new_val:
                    try:
                        size, cl_lv = size_founder(region_location[key], objects, agent, static_map['wall'], cl_lv=1)
                    except Exception:
                        logging.info('Can not place object! Too little space!')
                        sys.exit(1)
                    break
                else:
                    size = region_location[key]
                    break
    else:
        if not size[0] <= objects[agent]['x'] <= size[2] or not size[1] <= objects[agent]['y'] <= size[3]:
            new_x = (size[2] - size[0]) / 2
            new_y = (size[3] - size[1]) / 2
            size = objects[agent]['x'] - new_x, objects[agent]['y'] - new_y, objects[agent]['x'] + new_x, \
                   objects[agent]['y'] + new_y
    cell_location, cell_map, near_loc, cell_coords, cl_lv = cell_creater(size, objects, region_location,
                                                                         static_map['wall'], cl_lv)

    return region_map, cell_map, cell_location, near_loc, cell_coords, size, cl_lv


def compare(s_matrix, pm):
    if not pm.is_empty():
        iner_signs = pm.get_signs()
        causas = [el for el in s_matrix if 'cause' in el]
        effects = [el for el in s_matrix if 'effect' in el]
        elements = []
        if causas:
            for el in causas:
                elements.extend([obj[0] for obj in get_attributes(s_matrix[el], signs)])
        if effects:
            for el in effects:
                elements.extend([obj[0] for obj in get_attributes(s_matrix[el], signs)])
        if iner_signs == set(elements):
            return pm
    return None


def get_attributes(iner, signs):
    matrices = []
    if isinstance(iner, list):
        for s_name in iner:
            obj_sign = signs[s_name]
            obj_signif = obj_sign.significances[1]
            matrices.append((obj_sign, obj_signif))
        return matrices
    elif isinstance(iner, dict):
        for s_name, s_matrix in iner.items():
            if [el for el in iner if not 'cause' in el and not 'effect' in el]:
                if s_name not in signs:
                    s_name = [s for s in signs if s in s_name][0]
                el_sign = signs[s_name]
                pms = getattr(el_sign, 'significances')
                for index, pm in pms.items():
                    el_signif = compare(s_matrix, pm)
                    if el_signif:
                        break
                else:
                    el_signif = el_sign.add_significance()
                    causas = [el for el in s_matrix if 'cause' in el]
                    effects = [el for el in s_matrix if 'effect' in el]
                    if causas:
                        elements = []
                        for el in causas:
                            elements.extend(get_attributes(s_matrix[el], signs))
                        for elem in elements:
                            connector = el_signif.add_feature(elem[1])
                            elem[0].add_out_significance(connector)
                    if effects:
                        elements = []
                        for el in effects:
                            elements.extend(get_attributes(s_matrix[el], signs))
                        for elem in elements:
                            connector = el_signif.add_feature(elem[1], effect=True)
                            elem[0].add_out_significance(connector)
                matrices.append((el_sign, el_signif))

        return matrices


def get_reg_location(cell_location, near_loc, region, signs):
    closely = [reg for reg in near_loc['cell-4'] if not reg == 0]
    nearly = set()
    for cell, regions in near_loc.items():
        if cell != 'cell-4':
            for reg in regions:
                nearly.add(reg)
    if region in cell_location:
        if 'cell-4' in cell_location[region]:
            return signs['include']
    if closely:
        if region in closely:
            return signs['closely']
    if region in nearly:
        return signs['nearly']
    return signs['faraway']


def resonated(signif, regions_struct, region, contain_reg, signs):
    inner_matrices = signif.spread_down_activity('significance', 5)
    if not inner_matrices:
        return False
    elif contain_reg == region:
        ssign = signif.get_signs()
        if signs['region?x'] in ssign and signs['cell?x'] in ssign:
            return True
    else:
        location = regions_struct[contain_reg][region][0]
        for matr in inner_matrices:
            if [s for s in matr if "region?y" in s.sign.name]:
                if matr[1].sign.name == location or matr[0].sign.name == location:
                    for m in inner_matrices:
                        if m[-1].sign.name == "cell-4":
                            return True
                break

    return False


def get_struct():
    regions = {}

    def itera(nclosely, nnearly):
        ncl = {}
        nnear = {}
        for nc in nclosely:
            ncl['region-' + str(nc[0])] = 'closely', nc[1]
        for nn in nnearly:
            nnear['region-' + str(nn[0])] = 'nearly', nn[1]
        ncl.update(nnear)
        return ncl

    ncl = itera([(1, 'below'), (3, 'right'), (4, 'below-right')],
                [(6, 'right'), (7, 'right'), (2, 'below'), (5, 'below'), (8, 'below-right')])
    regions.setdefault('region-0', {}).update(ncl)
    ncl = itera([(0, 'above'), (3, 'above-right'), (4, 'right'), (5, 'below-right'), (2, 'below')],
                [(6, 'right'), (7, 'right'), (8, 'right')])
    regions.setdefault('region-1', {}).update(ncl)
    ncl = itera([(1, 'above'), (4, 'above-right'), (5, 'right')],
                [(0, 'above'), (3, 'above'), (6, 'above-right'), (7, 'right'), (8, 'right')])
    regions.setdefault('region-2', {}).update(ncl)
    ncl = itera([(0, 'left'), (1, 'below-left'), (4, 'below'), (6, 'right'), (7, 'below-right')],
                [(2, 'below'), (5, 'below'), (8, 'below')])
    regions.setdefault('region-3', {}).update(ncl)
    ncl = itera([(0, 'above-left'), (1, 'left'), (2, 'below-left'), (3, 'above'), (5, 'below'), (6, 'above-right'),
                 (7, 'right'), (8, 'below-right')], [])
    regions.setdefault('region-4', {}).update(ncl)
    ncl = itera([(1, 'above-left'), (2, 'left'), (4, 'above'), (7, 'above-right'), (8, 'right')],
                [(0, 'above'), (3, 'above'), (6, 'above')])
    regions.setdefault('region-5', {}).update(ncl)
    ncl = itera([(3, 'left'), (4, 'below-left'), (7, 'below')],
                [(0, 'left'), (1, 'left'), (2, 'below-left'), (5, 'below'), (8, 'below')])
    regions.setdefault('region-6', {}).update(ncl)
    ncl = itera([(3, 'above-left'), (4, 'left'), (5, 'below-left'), (6, 'above'), (8, 'below')],
                [(0, 'left'), (1, 'left'), (2, 'left')])
    regions.setdefault('region-7', {}).update(ncl)
    ncl = itera([(4, 'above-left'), (7, 'above'), (5, 'left')],
                [(0, 'above-left'), (1, 'left'), (2, 'left'), (3, 'above'), (6, 'above')])
    regions.setdefault('region-8', {}).update(ncl)
    return regions


def state_prediction(agent, map, holding=None):
    agent_state = {}
    agent_state['name'] = agent
    if isinstance(map, dict):
        orientation = map['agent-orientation']
        agent_state['direction'] = signs[orientation]
        if 'agent-actuator' in map:
            agent_state['actuator'] = map['agent-actuator']
        else:
            agent_state['actuator'] = None
    elif isinstance(map, list):
        agent_state['direction'] = map[0]
        agent_state['actuator'] = map[1]
    else:
        agent_state['direction'] = map
        if holding:
            agent_state['actuator'] = holding
        else:
            agent_state['actuator'] = None

    return agent_state


def define_map(map_name, region_map, cell_location, near_loc, regions_struct, signs):
    signs[map_name] = Sign(map_name)
    map_meaning = signs[map_name].add_meaning()
    elements = {}
    contain_sign = signs['contain']
    region_sign = signs['region']
    few_sign = signs['few']
    noth_sign = signs['nothing']
    location_signif = \
    [matr for _, matr in signs['location'].significances.items() if signs['direction'] in matr.get_signs()][0]
    contain_reg = [region for region, cells in cell_location.items() if 'cell-4' in cells][0]

    def get_or_add(sign):
        if sign not in elements:
            meaning = sign.add_meaning()
            elements[sign] = meaning
        return elements.get(sign)

    for region, objects in region_map.items():
        region_x = signs[region]
        flag = False
        if 0 in objects:
            flag = True
            objects.remove(0)
            objects.add("nothing")
            cont_signif = [signif for _, signif in contain_sign.significances.items() if
                           signs['region'] in signif.get_signs() and noth_sign in signif.get_signs()][0]
        else:
            cont_signif = [signif for _, signif in contain_sign.significances.items() if
                           signs['region'] in signif.get_signs() and signs['object'] in signif.get_signs()][0]
        connectors = []
        for object in objects:
            if object in signs:
                ob_sign = signs[object]
            else:
                ob_sign = Sign(object)
                signs[object] = ob_sign
                for s_name, sign in signs.items():
                    if s_name in object and s_name != object:
                        obj_signif = ob_sign.add_significance()
                        tp_signif = sign.add_significance()
                        connector = tp_signif.add_feature(obj_signif, zero_out=True)
                        ob_sign.add_out_significance(connector)
                        break

            ob_meaning = get_or_add(ob_sign)

            # TODO change few to others
            pm = cont_signif.copy('significance', 'meaning')

            region_mean = region_x.add_meaning()
            pm.replace('meaning', region_sign, region_mean)
            pm.replace('meaning', signs['object'], ob_meaning)
            if not flag:
                few_meaning = few_sign.add_meaning()
                pm.replace('meaning', signs['amount'], few_meaning)

            if connectors:
                con = connectors[0]
                connector = map_meaning.add_feature(pm, con.in_order)
            else:
                connector = map_meaning.add_feature(pm)
            contain_sign.add_out_meaning(connector)
            if not connectors:
                connectors.append(connector)

        loc_sign = get_reg_location(cell_location, near_loc, region, signs)
        connector = connectors[0]
        am = None
        for id, signif in loc_sign.significances.items():
            if resonated(signif, regions_struct, region, contain_reg, signs):
                am = signif.copy('significance', 'meaning')
                break

        cell_meaning = signs["cell-4"].add_meaning()
        am.replace('meaning', signs["cell?x"], cell_meaning)
        inner_matrices = am.spread_down_activity('meaning', 3)
        for lmatrice in inner_matrices:
            if lmatrice[-1].sign.name == "region?z":
                reg_meaning = signs[region].add_meaning()
                am.replace('meaning', signs["region?z"], reg_meaning)
                break
        else:
            for lmatrice in inner_matrices:
                if lmatrice[-1].sign.name == "region?y":
                    reg_meaning = signs[region].add_meaning()
                    am.replace('meaning', signs["region?y"], reg_meaning)
        reg_meaning = signs[contain_reg].add_meaning()
        am.replace('meaning', signs["region?x"], reg_meaning)

        # direction matrice
        if contain_reg != region:
            dir_sign = signs[regions_struct[contain_reg][region][1]]
        else:
            dir_sign = signs["inside"]
        dir_matr = dir_sign.add_meaning()

        # location matrice
        location_am = location_signif.copy('significance', 'meaning')
        location_am.replace('meaning', signs['distance'], am)
        location_am.replace('meaning', signs['direction'], dir_matr)
        con = map_meaning.add_feature(location_am, connector.in_order)
        loc_sign.add_out_meaning(con)

    return map_meaning


def update_situation(sit_meaning, cell_map, signs, fast_est=None):
    # add ontable by logic
    if not fast_est:
        for cell, items in cell_map.items():
            if len(items) > 1:
                attributes = get_attributes(list(items), signs)
                roles = set()
                chains = {}
                for atr in attributes:
                    roles |= set(atr[0].find_attribute())
                    chains.setdefault(atr[0], set()).update(atr[0].spread_up_activity_obj('significance', 2))
                if len(roles) == len(attributes) or len(attributes) > 2:
                    predicates = {}
                    for role in roles:
                        predicates[role] = role.get_predicates()
                    com_preds = set()
                    for key1, item1 in predicates.items():
                        com_preds |= {s.name for s in item1}
                        for key2, item2 in predicates.items():
                            if key1 != key2:
                                for com in copy(com_preds):
                                    if not com in {s.name for s in item2}:
                                        com_preds.remove(com)

                    upper_roles = set()
                    for _, chain in chains.items():
                        upper_roles |= {ch.sign for ch in chain}
                    signifs = set()
                    for pred in com_preds:
                        for _, sig in getattr(signs[pred], "significances").items():
                            if len(sig.cause) == len(roles):
                                if sig.get_signs() <= upper_roles:
                                    signifs.add(sig)
                    if signifs:
                        signif = signifs.pop()
                        signif_signs = signif.get_signs()
                        replace = []
                        for sign in signif_signs:
                            for key, chain in chains.items():
                                if sign in [s.sign for s in chain]:
                                    replace.append((sign, key.add_meaning()))
                        merge_roles = []
                        for el1 in replace:
                            for el2 in replace:
                                if el1 != el2 and el1[0] != el2[0]:
                                    if el1[0] in signif_signs and el2[0] in signif_signs:
                                        if not (el1, el2) in merge_roles and not (el2, el1) in merge_roles:
                                            merge_roles.append((el1, el2))
                        matrices = []
                        for elem in merge_roles:
                            mean = signif.copy('significance', 'meaning')
                            for pair in elem:
                                mean.replace('meaning', pair[0], pair[1])
                            matrices.append(mean)
                        for matrixe in matrices:
                            connector = sit_meaning.add_feature(matrixe)
                            matrixe.sign.add_out_meaning(connector)
    else:
        target_signs = ['holding', 'handempty', 'ontable']
        copied = {}
        for event in fast_est:
            if len(event.coincidences) == 1:
                for fevent in sit_meaning.cause:
                    if event.resonate('meaning', fevent):
                        break
                else:
                    if [con.get_out_cm('meaning').sign.name for con in event.coincidences][0] in target_signs:
                        sit_meaning.cause.append(event.copy(sit_meaning, 'meaning', 'meaning', copied))
                        # sit_meaning.add_event(event, False)
    return sit_meaning


def define_situation(sit_name, cell_map, events, agent_state, signs):
    signs[sit_name] = Sign(sit_name)
    sit_meaning = signs[sit_name].add_meaning()
    contain_sign = signs['contain']
    cellx = signs['cell?x']
    celly = signs['cell?y']

    few_sign = signs['few']
    location_signif = \
        [matr for _, matr in signs['location'].significances.items() if signs['direction'] in matr.get_signs()][0]
    cell_distr = {'cell-0': 'above-left', 'cell-1': 'left', 'cell-2': 'below-left', 'cell-3': 'above', \
                  'cell-5': 'below', 'cell-6': 'above-right', 'cell-7': 'right', 'cell-8': 'below-right'}

    mapper = {cell: value for cell, value in cell_map.items() if cell != 'cell-4'}

    agent = agent_state['name']
    orientation = agent_state['direction']
    actuator = agent_state['actuator']

    for cell, objects in mapper.items():
        noth_sign = signs['nothing']
        flag = False
        if 0 in objects:
            flag = True
            cont_signif = [signif for _, signif in contain_sign.significances.items() if
                           celly in signif.get_signs() and noth_sign in signif.get_signs()][0]
        else:
            cont_signif = [signif for _, signif in contain_sign.significances.items() if
                           celly in signif.get_signs() and signs['object'] in signif.get_signs()][0]
        cont_am = []
        connectors = []
        if flag:
            noth_meaning = noth_sign.add_meaning()
            cont_meaning = cont_signif.copy('significance', 'meaning')
            cont_meaning.replace('meaning', noth_sign, noth_meaning)
            cell_meaning = signs[cell].add_meaning()
            cont_meaning.replace('meaning', celly, cell_meaning)
            cont_am.append(cont_meaning)

        else:
            for obj in objects:
                obj_meaning = signs[obj].add_meaning()
                cont_meaning = cont_signif.copy('significance', 'meaning')
                cont_meaning.replace('meaning', signs['object'], obj_meaning)
                few_meaning = few_sign.add_meaning()
                cell_meaning = signs[cell].add_meaning()
                cont_meaning.replace('meaning', signs['amount'], few_meaning)
                cont_meaning.replace('meaning', celly, cell_meaning)
                cont_am.append(cont_meaning)

        for mean in cont_am:
            if not connectors:
                connector = sit_meaning.add_feature(mean)
                contain_sign.add_out_meaning(connector)
                connectors.append(connector)
            else:
                connector = sit_meaning.add_feature(mean, connectors[0].in_order)
                contain_sign.add_out_meaning(connector)

        dir_y = signs[cell_distr[cell]]
        diry_meaning = dir_y.add_meaning()

        closely_signif = [signif for _, signif in signs['closely'].significances.items() if
                          cellx in signif.get_signs() and celly in signif.get_signs()][0]
        closely_meaning = closely_signif.copy('significance', 'meaning')
        cellx_mean = signs['cell-4'].add_meaning()
        celly_mean = signs[cell].add_meaning()
        closely_meaning.replace('meaning', cellx, cellx_mean)
        closely_meaning.replace('meaning', celly, celly_mean)

        location_meaning = location_signif.copy('significance', 'meaning')
        location_meaning.replace('meaning', signs['distance'], closely_meaning)
        location_meaning.replace('meaning', signs['direction'], diry_meaning)
        connector = sit_meaning.add_feature(location_meaning, connectors[0].in_order)
        location_meaning.sign.add_out_meaning(connector)

    empl_signif = [signif for _, signif in signs['employment'].significances.items() if cellx in signif.get_signs()][0]
    empl_meaning = empl_signif.copy('significance', 'meaning')
    cellx_mean = signs['cell-4'].add_meaning()
    empl_meaning.replace('meaning', cellx, cellx_mean)
    Ag_mean = agent.add_meaning()
    empl_meaning.replace('meaning', signs['agent'], Ag_mean)
    conn = sit_meaning.add_feature(empl_meaning)
    empl_meaning.sign.add_out_meaning(conn)

    dir = signs['direction']
    orientation_mean = orientation.add_meaning()
    orient_signif = [signif for _, signif in signs['orientation'].significances.items() if dir in signif.get_signs()][0]
    orient_meaning = orient_signif.copy('significance', 'meaning')
    orient_meaning.replace('meaning', dir, orientation_mean)
    Ag_mean = agent.add_meaning()
    orient_meaning.replace('meaning', signs['agent'], Ag_mean)
    conn = sit_meaning.add_feature(orient_meaning)
    orient_meaning.sign.add_out_meaning(conn)

    if actuator:
        if isinstance(actuator, dict):
            if len(actuator) == 2:
                ag = actuator.pop('agent')[0]
                key, item = actuator.popitem()
                act_sign = signs[key]
                pred_mean = None
                for key, cm in act_sign.meanings.items():
                    pred_mean = cm
                    if pred_mean:
                        break
                if not pred_mean:
                    pred_mean = act_sign.add_meaning()
                # pred_mean = getattr(signs[key], 'meanings')[1]
                ag_mean = signs[ag].add_meaning()
                connector = sit_meaning.add_feature(pred_mean)
                pred_mean.sign.add_out_meaning(connector)
                conn = sit_meaning.add_feature(ag_mean, connector.in_order)
                ag_mean.sign.add_out_meaning(conn)
            else:
                key, item = actuator.popitem()
                pred_sign = signs[key]
                causal_signs = {signs[it] for it in itertools.chain(item['cause'], item['effect'])}
                signifs = getattr(pred_sign, 'significances')
                means = getattr(pred_sign, 'meanings')
                mean = None
                for _, si in means.items():
                    if causal_signs == si.get_signs():
                        mean = si
                        break
                else:
                    for _, si in signifs.items():
                        smaller = si.spread_down_activity('significance', 3)
                        variations = itertools.combinations([l[-1].sign for l in smaller], 2)
                        for var in variations:
                            if set(var) == causal_signs:
                                replace_map = {}
                                for sign in var:
                                    for sm in smaller:
                                        if sm[-1].sign == sign:
                                            if sm[-3].sign != pred_sign:
                                                replace_map[sm[-3].sign] = sign.add_meaning()
                                            else:
                                                replace_map[sm[-2].sign] = sign.add_meaning()
                                            break
                                mean = si.copy('significance', 'meaning')
                                for key, item in replace_map.items():
                                    mean.replace('meaning', key, item)
                                break

                if mean:
                    conn = sit_meaning.add_feature(mean)
                    mean.sign.add_out_meaning(conn)

            sit_meaning = update_situation(sit_meaning, cell_map, signs)
        else:
            actuator = actuator.copy('meaning', 'meaning')
            conn = sit_meaning.add_feature(actuator)
            actuator.sign.add_out_meaning(conn)

    for event in events:
        copied = {}
        sit_meaning.cause.append(event.copy(sit_meaning, 'meaning', 'meaning', copied))

    return sit_meaning


def _clear_model(exp_signs, structure):
    for type, smaller in list(structure.items()).copy():
        if exp_signs.get(type):
            for object in smaller.copy():
                if exp_signs.get(object):
                    smaller.remove(object)
            if not smaller:
                structure.pop(type)
    return structure


def _ground_predicates(predicates, signs):
    # ground predicates
    for predicate_name, smaller in predicates.items():
        variations = [pr for pr in smaller if predicate_name in pr]
        if not predicate_name in signs:
            pred_sign = Sign(predicate_name)
            signs[predicate_name] = pred_sign
        else:
            pred_sign = signs[predicate_name]
        if 'cause' and 'effect' in smaller:
            pred_signif = pred_sign.add_significance()
            for part, iner in smaller.items():
                matrices = get_attributes(iner, signs)
                for el in matrices:
                    if part == "cause":
                        connector = pred_signif.add_feature(el[1], effect=False, zero_out=True)
                    else:
                        connector = pred_signif.add_feature(el[1], effect=True, zero_out=True)
                    el[0].add_out_significance(connector)
        elif variations:
            for part, iner in smaller.items():
                mixed = []
                matrices = []
                pred_signif = pred_sign.add_significance()
                causas = [el for el in iner if 'cause' in el]
                effects = [el for el in iner if 'effect' in el]
                for element in causas:
                    if not 'any' in iner[element]:
                        matrices = get_attributes(iner[element], signs)
                        for el in matrices:
                            connector = pred_signif.add_feature(el[1], effect=False, zero_out=True)
                            el[0].add_out_significance(connector)
                    else:
                        for key, el in iner[element].items():
                            matrices.extend(get_attributes(el, signs))
                        mixed.append(matrices)
                        matrices = []

                for element in effects:
                    if not 'any' in iner[element]:
                        matrices = get_attributes(iner[element], signs)
                        for el in matrices:
                            connector = pred_signif.add_feature(el[1], effect=True, zero_out=True)
                            el[0].add_out_significance(connector)
                    else:
                        for key, el in iner[element].items():
                            matrices.extend(get_attributes(el, signs))
                        mixed.append(matrices)
                        matrices = []
                if mixed:
                    combinations = itertools.product(mixed[0], mixed[1])
                    history = []
                    for element in combinations:
                        el_signs = element[0][0], element[1][0]
                        if not element[0][0] == element[1][0] and el_signs not in history:
                            history.append(el_signs)
                            history.append((el_signs[1], el_signs[0]))
                            pred_signif = pred_sign.add_significance()
                            connector = pred_signif.add_feature(element[0][1], effect=False)
                            element[0][0].add_out_significance(connector)
                            connector = pred_signif.add_feature(element[1][1], effect=True)
                            element[1][0].add_out_significance(connector)


def _ground_actions(actions, obj_means, I_sign, signs):
    events = []
    # ground actions
    for action_name, smaller in actions.items():
        matrices = []
        if not action_name in signs:
            act_sign = Sign(action_name)
            signs[action_name] = act_sign
            act_signif = act_sign.add_significance()
        else:
            act_sign = signs[action_name]
            act_signif = act_sign.add_significance()

        def get_predicate(pr_name, pr_model):
            pr_name = re.sub(r'[^\w\s{P}]+|[\d]+', r'', pr_name).strip()
            pr_sign = signs[pr_name]
            model_signs = [el for el in itertools.chain(pr_model['cause'], pr_model['effect'])]
            for id, matrice in pr_sign.significances.items():
                matrice_signs = [s.name for s in matrice.get_signs()]
                if len(matrice_signs) == len(model_signs):
                    for el in model_signs:
                        if not el in matrice_signs:
                            break
                    else:
                        return matrice
            return None

        for part, iner in smaller.items():
            for predicate, conditions in iner.items():
                matrices.append(get_predicate(predicate, conditions))
            for el in matrices:
                if part == "cause":
                    connector = act_signif.add_feature(el, effect=False)
                else:
                    connector = act_signif.add_feature(el, effect=True)
                el.sign.add_out_significance(connector)
            matrices = []

        act_mean = act_signif.copy('significance', 'meaning')
        # I_mean_predicates = I_sign.add_meaning()
        act_mean.replace('meaning', signs['agent'], obj_means[I_sign])
        connector = act_mean.add_feature(obj_means[I_sign])
        efconnector = act_mean.add_feature(obj_means[I_sign], effect=True)
        events.append(act_mean.effect[abs(efconnector.in_order) - 1])
        I_sign.add_out_meaning(connector)
    return events


def _exp_events(signs, agents):
    events = []
    for s in signs:
        if s.startswith("*start*") and len(s) > 7:
            if signs[s].meanings:
                cm = signs[s].meanings[1]
            else:
                im = signs[s].images[1]
                cm = im.copy('image', 'meaning')
            for event in cm.cause:
                if len(event.coincidences) == 1:
                    for con in event.coincidences:
                        if con.out_sign.name in agents:
                            events.append(event)
            break
    return events


def state_fixation(state, el_coords, signs, element):
    """
    :param state: cm of described state on meanings network
    :param el_coords: coords from signs_markup function
    :param signs: active sign base
    :return: state matrix on images network
    """
    im = state.sign.add_image()

    for number in range(9):
        cs = signs[element + '-' + str(number)]
        cimage = cs.add_image()
        coords = el_coords[element + '-' + str(number)]
        cimage.add_view(coords, effect=False)
        connector = im.add_feature(cimage, effect=False)
        cs.add_out_image(connector)

    return im


def spatial_ground(problem, agent, logic, exp_signs=None):
    initial_state = problem.initial_state
    initial_state.update(problem.map)
    goal_state = problem.goal
    goal_state.update(problem.map)
    # TODO change in multiagent variant
    agent = 'agent'

    obj_signifs = {}
    obj_means = {}

    I_sign = Sign("I")
    agents = ['I']
    They_sign = Sign("They")
    obj_means[I_sign] = I_sign.add_meaning()
    obj_signifs[I_sign] = I_sign.add_significance()
    signs[I_sign.name] = I_sign
    obj_means[They_sign] = They_sign.add_meaning()
    obj_signifs[They_sign] = They_sign.add_significance()
    signs[They_sign.name] = They_sign
    Clarify = Sign('Clarify')
    signs[Clarify.name] = Clarify
    Abstract = Sign('Abstract')
    signs[Abstract.name] = Abstract

    types = problem.domain['types']
    roles = problem.domain['roles']

    if exp_signs:
        types = _clear_model(exp_signs, types)
        roles = _clear_model(exp_signs, roles)

    # ground types
    for type_name, smaller in types.items():
        if not type_name in signs and not exp_signs:
            type_sign = Sign(type_name)
            signs[type_name] = type_sign
        else:
            if exp_signs:
                type_sign = exp_signs[type_name]
            else:
                type_sign = signs[type_name]
        if smaller:
            for obj in smaller:
                if not obj in signs:
                    obj_sign = Sign(obj)
                    signs[obj] = obj_sign
                else:
                    obj_sign = signs[obj]

                obj_signif = obj_sign.add_significance()
                obj_signifs[obj_sign] = obj_signif
                tp_signif = type_sign.add_significance()
                connector = tp_signif.add_feature(obj_signif, zero_out=True)
                obj_sign.add_out_significance(connector)
                if obj_sign.name == agent:
                    connector = obj_signif.add_feature(obj_signifs[I_sign], zero_out=True)
                    I_sign.add_out_significance(connector)
        else:
            obj_signifs[type_sign] = type_sign.add_significance()

    for role_name, smaller in roles.items():
        role_sign = Sign(role_name)
        signs[role_name] = role_sign

        for object in smaller:
            obj_sign = signs[object]
            obj_signif = obj_sign.significances[1]
            role_signif = role_sign.add_significance()
            connector = role_signif.add_feature(obj_signif, zero_out=True)
            obj_sign.add_out_significance(connector)

    if exp_signs:
        ws = {**signs, **exp_signs}['wall']
    else:
        ws = signs['wall']
    views = []
    if ws.images:
        for num, im in ws.images.items():
            if len(im.cause):
                for view in im.cause[0].coincidences:
                    if view.view:
                        views.append(view.view)
    for wall in problem.map['wall']:
        if wall not in views:
            cimage = ws.add_image()
            cimage.add_view(wall, effect=False)

    if not exp_signs:
        _ground_predicates(problem.domain['predicates'], signs)
        events = _ground_actions(problem.domain['actions'], obj_means, I_sign, signs)
    else:
        signs.update(exp_signs)
        events = _exp_events(exp_signs, agents)

    # Define start situation
    maps = {}
    maps[0] = problem.initial_state
    ms = maps[0].pop('map_size')
    walls = maps[0].pop('wall')
    static_map = {'map_size': ms, 'wall': walls}

    region_map, cell_map, cell_location, near_loc, cell_coords, size, cl_lv = signs_markup(initial_state, static_map,
                                                                                           agent)
    regions_struct = get_struct()
    map_pms = define_map('*map*', region_map, cell_location, near_loc, regions_struct, signs)
    agent_state_start = state_prediction(I_sign, initial_state)
    start_situation = define_situation('*start*', cell_map, events, agent_state_start, signs)
    state_fixation(start_situation, cell_coords, signs, 'cell')
    problem.initial_state['cl_lv'] = cl_lv
    # Define goal situation
    region_map, cell_map, cell_location, near_loc, cell_coords, size, cl_lv = signs_markup(goal_state, static_map,
                                                                                           agent)
    agent_state_finish = state_prediction(I_sign, goal_state)
    goal_situation = define_situation('*finish*', cell_map, events, agent_state_finish, signs)
    goal_map = define_map('*goal_map*', region_map, cell_location, near_loc, regions_struct, signs)
    state_fixation(goal_situation, cell_coords, signs, 'cell')

    # TODO change in multiagent version
    signify_connection(signs)
    problem.goal['cl_lv'] = cl_lv
    cells = {}
    cells[0] = cell_map
    additions = []
    additions.extend([maps, regions_struct, cells, static_map])

    return Task(problem.name, signs, None, start_situation.sign, goal_situation.sign, logic, goal_map.sign, map_pms,
                additions, problem.initial_state, {key:value for key, value in problem.goal.items() if key not in static_map})


class Problem:
    def __init__(self, domain, problem_parsed, constraints):
        """
        name: The name of the problem
        domain: The domain in which the problem has to be solved
        init: A list of facts describing the initial state
        goal: A list of facts describing the goal state
        map: A tree of facts describing map
        constraints: A list of facts describing agents' capabilities
        """
        self.name = problem_parsed['task-name']
        self.domain = domain
        self.initial_state = problem_parsed['start']
        self.goal = problem_parsed['finish']
        self.map = problem_parsed['map']
        self.constraints = constraints

    def __repr__(self):
        return ('< Problem definition: %s '
                'Domain: %s Initial State: %s Goal State : %s >' %
                (self.name, self.domain['domain-name'],
                 self.initial_state,
                 self.goal))

    __str__ = __repr__
