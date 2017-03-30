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
    if plans:
        plans = plans[0]
        for plan in plans:
            solution.append([plan[1], plan[len(plan)-1]])
        solution.reverse()
        logging.info('Found {0} variants'.format(len(plans)))
        logging.info('Plan {0}'.format(solution))
    return solution



def map_iteration(active_pm, check_pm, current_plan, iteration):
    logging.debug('STEP {0}:'.format(iteration))
    logging.debug('\tSituation {0}'.format(active_pm.longstr()))
    if iteration >= MAX_ITERATION:
        logging.debug('\tMax iteration count')
        return None

    precedents = []
    agents = get_agents()
    for name, sign in world_model.items():
        for index, cm in sign.meanings.items():
            if cm.includes('meaning', active_pm):
                precedents.extend(cm.sign.spread_up_activity_act('meaning', 1))
    active_chains = active_pm.spread_down_activity('meaning', 2)
    active_signif = set()

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

def get_agents():
    agent_back = set()
    I_sign = world_model['I']
    agent_back.add(I_sign)
    I_obj = [con.in_sign for con in I_sign.out_meanings if con.out_sign.name == "I"][0]
    agents = world_model['agent'].meanings
    for num, cause in agents.items():
        for con in cause.cause[0].coincidences:
            if not con.out_sign == I_obj:
                agent_back.add(con.out_sign)
    return agent_back


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



    def get_role(obj, roles):
        for role in roles:
            if obj in role[1]:
                return role

    def mix_pairs(replace_map):
        new_chain = {}
        elements = []
        merged_chains = []
        used_roles = []
        replace_map = list(replace_map.items())

        for item in replace_map:
            elements.append(item[1])
        elements = list(itertools.product(*elements))
        clean_el = elements.copy()
        for element in clean_el:
            if not len(set(element)) == len(element):
                elements.remove(element)
        for element in elements:
            for obj in element:
                avalaible_roles = [x for x in replace_map if x not in used_roles]
                role = get_role(obj, avalaible_roles)
                if role:
                    used_roles.append(role)
                    new_chain[role[0]] = obj
            merged_chains.append(new_chain)
            new_chain = {}
            used_roles = []
        return merged_chains


    def suitable(cm, agents):
        meanings = list()
        cm_meanings = []
        con = set()
        ag = {}
        script = []
        cm_agent = []
        I_sign = world_model['I']
        I_obj = [con.in_sign for con in I_sign.out_meanings if con.out_sign.name == "I"][0]
        for agent in agents:
            if agent == I_sign:
                for connector in agent.out_meanings:
                    if not connector.out_sign == agent:
                        meanings.append((connector.in_sign.name, connector.out_sign.name))
            else:
                for connector in agent.out_meanings:
                    meanings.append((connector.in_sign.name, connector.out_sign.name))
            ag[agent] = list(set(meanings))
            meanings = []
        # agent_list = [ag[0] for ag in local]
        agents2 = agents.copy()
        agents2.remove(I_sign)
        agents2.add(I_obj)
        for mean, attribute in ag.items():
            if mean == I_sign:
                mean = I_obj
            # my_role = None

            for agent in agents2:
                roles = []
                roles2 = []
                variants = set()
                type = None
                if agent == mean:
                    for elem in attribute:
                        if elem[1] == agent.name:
                            roles.append(elem[0])
                        elif elem[0] == agent.name:
                            variants.add(elem[1])
                    for elem in attribute:
                        if elem[1] in variants and not elem[0] in roles and not elem[0] == agent.name:
                            type = elem[0]
                        if elem[1] in variants or elem[1] == type and not elem[0] == agent.name:
                            roles2.append(elem[0])
                    roles = list(set(roles2)&set(roles))
                    if type:
                        meanings.append((agent.name, variants, type)) # получает [(a1 {g, a}, huge)]

        for event in itertools.chain(cm.cause, cm.effect):
            for connector in event.coincidences:
                con.add(connector.out_sign.name)
            if len(roles):
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
                            for role in agents2:
                                if mean[0] == role.name:
                                    if role == I_obj:
                                        script.append([I_sign.name, cm])
                                    else:
                                        script.append([role.name, cm])
                                    return script
        elif cm_agent:
                for agent in agents2:
                    if agent.name == cm_agent[0]:
                        script.append([agent, cm])
                        return script
        else:
            return False

    ma_combinations = mix_pairs(replace_map)

    # if len(roles) == 3:
    #     ma_combinations = mix_pairs3(combinations, 3)
    # elif len(roles) == 4:
    #     ma_combinations = mix_pairs4(combinations)
    # else: ma_combinations = combinations
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
        best_heuristics = max(heuristic, key=lambda x: x[0])
        return list(filter(lambda x: x[0] == best_heuristics[0], heuristic))
    else:
        return None
