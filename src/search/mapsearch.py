import logging

import itertools

import grounding.sign_task as st
from grounding.semnet import Sign
from itertools import groupby

MAX_ITERATION = 100

world_model = None


def map_search(task):
    global world_model
    world_model = task.signs
    active_pm = task.goal_situation.meanings[1]
    check_pm = task.start_situation.meanings[1]
    logging.debug('Start: {0}'.format(check_pm.longstr()))
    logging.debug('Finish: {0}'.format(active_pm.longstr()))
    solution = []
    plans = map_iteration(active_pm, check_pm, [], 0)
    plans = plans[0]
    if plans:
        for plan in plans:
            solution.append([plan[1], plan[len(plan)-1]])
        solution.reverse()
        logging.info('Found {0} variants'.format(len(plans)))
        logging.info('Plan {0}'.format(solution))
    return solution
    # if plans:
    #     current_plans = []
    #     logging.debug('Found {0} variants'.format(len(plans)))
    #     for key, group in groupby(plans, lambda x: x[0]):
    #         current_plans.append([key, list(reversed(min(group, key=len)[1]))])
    #     for plan in current_plans:
    #         logging.info('Plan: agent = {0}, len={1}, {2}'.format(plan[0].name, len(plan[1]), [name for _, name, _ in plan[1]]))
    #     return [(name, script) for _, name, script in plan[1]]
    # else:
    #     logging.debug('Variant are not found')
    # return None


def map_iteration(active_pm, check_pm, current_plan, iteration):
    logging.debug('STEP {0}:'.format(iteration))
    logging.debug('\tSituation {0}'.format(active_pm.longstr()))
    if iteration >= MAX_ITERATION:
        logging.debug('\tMax iteration count')
        return None

    precedents = []
    agents = set()
    for name, sign in world_model.items():
        if name == "I" or name == "They": agents.add(sign)
        for index, cm in sign.meanings.items():
            if cm.includes('meaning', active_pm):
                precedents.extend(cm.sign.spread_up_activity_act('meaning', 1))
    active_chains = active_pm.spread_down_activity('meaning', 2)
    active_signif = set()

    agent_pm = None
    for chain in active_chains:
        pm = chain[-1]
        active_signif |= pm.sign.spread_up_activity_act('significance', 3)

    meanings = []
    for pm_signif in active_signif:
        chains = pm_signif.spread_down_activity('significance', 3)
        merged_chains = []
        for chain in chains:
            for achain in active_chains:
                if chain[-1].sign == achain[-1].sign and len(chain) > 2 and chain not in merged_chains:
                    merged_chains.append(chain)
                    break
        scripts = _generate_meanings(merged_chains, agents)
        meanings.extend(scripts)
    applicable_meanings = []
    for agent, cm in precedents + meanings:
        result, checked = _check_activity(cm, active_pm)
        if result:
            applicable_meanings.append((agent, checked))


    # TODO: replace to metarule apply
    candidates = _meta_check_activity(applicable_meanings, active_pm, check_pm, [x for x, _, _, _ in current_plan])

    if not candidates:
        logging.debug('\tNot found applicable scripts ({0})'.format([x for _, x, _, _ in current_plan]))
        return None

    logging.debug('\tFound {0} variants'.format(len(candidates)))
    final_plans = []
    # if current_agent is not None and len(aim_plans):
    #     if current_agent not in [plan[0] for plan in aim_plans]:
    #         candidates = [cand for cand in candidates if get_agent(cand[2]) == current_agent]

    for counter, name, script, ag_mask in candidates:
        logging.debug('\tChoose {0}: {1} -> {2}'.format(counter, name, script))

        plan = current_plan.copy()
        plan.append((active_pm, name, script, ag_mask))
        # agent = get_agent(script)
        # if current_agent is None:
        #     current_agent = agent
        # if not agent == current_agent:
        #     break
        next_pm = _time_shift_backward(active_pm, script)
        if next_pm.includes('meaning', check_pm):
            final_plans.append(plan)
        else:
            recursive_plans = map_iteration(next_pm, check_pm, plan, iteration + 1)
            if recursive_plans:
                final_plans.extend(recursive_plans)

    return final_plans



def action_agents(plan):
    plan_agents = []
    for _, _, script in plan:
        agent = get_agent(script)
        plan_agents.append(agent)
    return plan_agents

def get_agent(script):
    roles = []
    for event in script.cause:
        for conn in event.coincidences:
            for connector in conn.out_sign.out_significances:
                roles.append(connector.in_sign.name)
            if "agent" in roles:
                return conn.out_sign

def _generate_meanings(chains, agents):
    replace_map = {}
    main_pm = None
    # compose pairs - role-replacer
    for chain in chains:
        if not chain[1].sign in replace_map:
            replace_map[chain[1].sign] = [chain[-1]]
        else:
            if not chain[-1] in replace_map[chain[1].sign]:
                replace_map[chain[1].sign].append(chain[-1])
        main_pm = chain[0]

    combinations = []
    ma_combinations = []
    roles = []
    unique3 = []
    unique4 = []

    def create_combinations(role_map, current):
        comb = []
        for role_sign in role_map:
            for obj_pm in role_map[role_sign]:
                new_current = current.copy()
                new_current[role_sign] = obj_pm
                comb.append(new_current)
        return comb


    def create_ma_combinations(role_map):
        used_roles = []
        for role_sign in role_map:
            if not role_sign in roles :
                roles.append(role_sign)
            for r in role_map:
                if not r in roles:
                    roles.append(r)
                if not [role_sign, r] or not [r, role_sign] in used_roles:
                    used_roles.append([role_sign, r])
                    if not r == role_sign:
                        for obj_pm in role_map[role_sign]:
                            others = {}
                            current = {}
                            current[role_sign] = obj_pm
                            others[r] = role_map[r].copy()
                            if role_sign.find_role() == r.find_role():
                                others[r].remove(obj_pm)
                            combinations.extend(create_combinations(others, current))


    if len(replace_map) > 1:
        create_ma_combinations(replace_map)
    else:
        combinations = create_combinations(replace_map, {})


    def is_unique(pair_items, item3):
        if len(pair_items) == 2:
            if not any(pair_items[0] in item and pair_items[1] in item and item3 in item for item in unique3):
                unique3.append([pair_items[0], pair_items[1], item3])
                return True
        if len(pair_items) == 3:
            if not any(pair_items[0] in item and pair_items[1] in item and pair_items[2] in item and item3 in item for item in unique4):
                unique4.append([pair_items[0], pair_items[1], pair_items[2], item3])
                return True
        return False

    def can_be_mixed(pair, element):
        typemap_p = []
        typemap_el = []
        values = []
        agent1 = None
        agent2 = None
        for elem in pair:
            role = elem[0].name
            typemap_p.append(role)
            if role == "agent?ag":
                agent1 = elem[1]
            values.append(elem[1])
        for elem in element:
            role = elem[0].name
            typemap_el.append(role)
            if role == "agent?ag":
                agent2 = elem[1]
        new = list(set(element) - set(pair))

        if typemap_p == typemap_el:
            return False
        elif agent1 and agent2 and not agent1 == agent2:
            return False
        elif len(list(set(typemap_el) - set(typemap_p))) < 1:
            return False
        elif new[0][1] in values:
            return False
        else:
            return True



    def mix_pairs3(combinations, roles):
        for pair in combinations:
            pair = list(pair.items())
            for element in combinations:
                element = list(element.items())
                if not pair == element:
                    if can_be_mixed(pair, element):
                        new = set(element) - set(pair)
                        if len(new):
                            new = tuple(new)[0]
                            if len(pair) == roles-1:
                                if is_unique(pair, new):
                                    pair.append(new)
                                    if len(pair) == roles:
                                        ma_combinations.append({elem[0]: elem[1] for elem in pair})
                                        pair.remove(new)
                                        continue
                            else:
                                pair.append(new)
        ma_combinations2 = [ma_combination for ma_combination in ma_combinations if len(ma_combination) == roles]
        return ma_combinations2

    def mix_pairs4(combinations):
        ma_combinations = []
        combinations = mix_pairs3(combinations, 3)
        for combination in combinations:
            combination = list(combination.items())
            for other_comb in combinations:
                other_comb = list(other_comb.items())
                if not combination == other_comb:
                    dif = tuple(set(other_comb) - set(combination))[0]
                    if len(dif):
                        if can_be_mixed(combination, other_comb):
                            if is_unique(combination, dif):
                                combination.append(dif)
                                ma_combinations.append({elem[0]: elem[1] for elem in combination})
                                combination.remove(dif)
                                continue
        ma_combinations2 = [ma_combination for ma_combination in ma_combinations if len(ma_combination) == 4]

        return ma_combinations2

    def suitable(cm, agents):
        meanings = list()
        cm_meanings = []
        con = set()
        ag = {}
        local = []
        script = []
        cm_agent = []
        for agent in agents:
            for connector in agent.out_meanings:
                if connector.out_sign == agent:
                    local.append((connector.in_sign.name, connector.out_sign.name))
                else:
                    meanings.append((connector.in_sign.name, connector.out_sign.name))
            ag[agent]=list(set(meanings))
            meanings = []
        for mean, attribute in ag.items():
            roles = []
            variants = set()
            # my_role = None
            for mask, agent in local:
                if agent == mean.name:
                    my_role = mask
                    for elem in attribute:
                        if elem[1] == mask:
                            roles.append(elem[0])
                    for role in roles:
                        for elem in attribute:
                            if elem[0] == role and not elem[1] == mask:
                                variants.add(elem[1])
                    type = max(elem for elem in variants)
                    variants.remove(type)
                    meanings.append((my_role, variants, type))
        for event in itertools.chain(cm.cause, cm.effect):
            for connector in event.coincidences:
                con.add(connector.out_sign.name)
            if roles[0] in con or roles[1] in con:
                cm_meanings.append(con)
                con = set()
                continue
            elif "handempty" in con and len(con) == 2:
                cm_agent = list(con)
                cm_agent.remove("handempty")


        if len(cm_meanings):
            for mean in meanings:
                if any(mean[0] in cm_meaning for cm_meaning in cm_meanings):
                    for elem in mean[1]:
                        if all(elem in cm_meaning and mean[0] in cm_meaning or elem in cm_meaning and mean[2] in cm_meaning for cm_meaning in cm_meanings):
                            for role in local:
                                if mean[0] == role[0]:
                                    script.append([role[1], cm])
                                    return script
        elif cm_agent:
                for mask, agent in local:
                    if mask == cm_agent[0]:
                        script.append([agent, cm])
                        return script
        else:
            return False

    if len(roles) == 3:
        ma_combinations = mix_pairs3(combinations, 3)
    elif len(roles) == 4:
        ma_combinations = mix_pairs4(combinations)
    else: ma_combinations = combinations
    pms = []
    for ma_combination in ma_combinations:
        cm = main_pm.copy('significance', 'meaning')
        for role_sign, obj_pm in ma_combination.items():
            obj_cm = obj_pm.copy('significance', 'meaning')
            cm.replace('meaning', role_sign, obj_cm)
        test = suitable(cm, agents)
        if test:
            pms.append(test[0])

    return pms


def _check_activity(pm, active_pm):
    result = True
    for event in pm.effect:
        for fevent in active_pm.cause:
            if event.resonate('meaning', fevent):
                break
        else:
            result = False
            break

    if not result:
        expanded = pm.expand('meaning')
        if not len(expanded.effect) == 0:
            return _check_activity(expanded, active_pm)
        else:
            return False, pm
    return result, pm


def _time_shift_backward(active_pm, script):
    next_pm = Sign(st.SIT_PREFIX + str(st.SIT_COUNTER))
    world_model[next_pm.name] = next_pm
    pm = next_pm.add_meaning()
    st.SIT_COUNTER += 1
    copied = {}
    for event in active_pm.cause:
        for es in script.effect:
            if event.resonate('meaning', es):
                break
        else:
            pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))
    for event in script.cause:
        pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))

    return pm


def _meta_check_activity(scripts, active_pm, check_pm, prev_pms):
    heuristic = []
    for agent, script in scripts:
        estimation = _time_shift_backward(active_pm, script)
        for prev in prev_pms:
            if estimation.resonate('meaning', prev, False, False):
                break
        else:
            counter = 0
            for event in estimation.cause:
                for ce in check_pm.cause:
                    if event.resonate('meaning', ce):
                        counter += 1
                        break
            heuristic.append((counter, script.sign.name, script, agent))
    if heuristic:
        # if len(heuristic)>1:
        #     heur = heuristic.copy()
        #     for heu in heur:
        #         if not heu[1] == "wait":
        #             for heu2 in heur:
        #                 if heu2[1] == "wait":
        #                     if heu2 in heuristic:
        #                         heuristic.remove(heu2)
        best_heuristics = max(heuristic, key=lambda x: x[0])
        return list(filter(lambda x: x[0] == best_heuristics[0], heuristic))
    else:
        return None
