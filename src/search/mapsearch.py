import logging

import itertools

import grounding.sign_task as st
from grounding.semnet import Sign
import random

MAX_ITERATION = 100

world_model = None


def map_search(task):
    global world_model
    world_model = task.signs
    active_pm = task.goal_situation.meanings[1]
    check_pm = task.start_situation.meanings[1]
    logging.debug('Start: {0}'.format(check_pm.longstr()))
    logging.debug('Finish: {0}'.format(active_pm.longstr()))
    plans = map_iteration(active_pm, check_pm, [], 0)
    solution = long_relations(plans)
    solution.reverse()
    return solution



def map_iteration(active_pm, check_pm, current_plan, iteration):
    logging.debug('STEP {0}:'.format(iteration))
    logging.debug('\tSituation {0}'.format(active_pm.longstr()))
    if iteration >= MAX_ITERATION:
        logging.debug('\tMax iteration count')
        return None

    precedents = []
    plan_sign = None
    I_sign, I_obj, agents = get_agents()

    for name, sign in world_model.items():
        if name.startswith("plan_"): plan_sign = sign
        for index, cm in sign.meanings.items():
            if cm.includes('meaning', active_pm):
                precedents.extend(cm.sign.spread_up_activity_act('meaning', 1)) # searching for plan_sign
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
    agent = None
    if not precedents:
        for agent, cm in meanings:
            result, checked = _check_activity(cm, active_pm)
            if result:
                applicable_meanings.append((agent, checked))
    else:
        for cm in precedents + meanings:
            if isinstance(cm, list):
                agent = cm[0]
                cm = cm[1]
            result, checked = _check_activity(cm, active_pm)
            if result:
                applicable_meanings.append((agent, checked))

    # TODO: replace to metarule apply
    apl = [ag for ag in agents if not ag == I_sign]
    apl.append(I_obj)
    candidates = _meta_check_activity(applicable_meanings, active_pm, check_pm, [x for x, _, _, _ in current_plan], apl)

    if candidates:
        candidates = _check_experience(candidates, plan_sign, I_obj, I_sign)

    if not candidates:
        logging.debug('\tNot found applicable scripts ({0})'.format([x for _, x, _, _ in current_plan]))
        # TODO: if no experience -> choose with whom the longest plan <<= return a len(recursive_plans)
        return None

    logging.debug('\tFound {0} variants'.format(len(candidates)))
    final_plans = []


    for counter, name, script, ag_mask in candidates:
        logging.debug('\tChoose {0}: {1} -> {2}'.format(counter, name, script))

        plan = current_plan.copy()
        plan.append((active_pm, name, script, ag_mask))
        next_pm = _time_shift_backward(active_pm, script)
        if next_pm.includes('meaning', check_pm):
            final_plans.append(plan)
            print("len of final plan is: {0}".format(len(plan)))
        else:
            recursive_plans = map_iteration(next_pm, check_pm, plan, iteration + 1)
            if recursive_plans:
                final_plans.extend(recursive_plans)

    return final_plans

def long_relations(plans):
    busiest = []
    for index, plan in enumerate(plans):
        previous_agent = ""
        agents = {}
        counter = 0
        plan_agents = []
        # нахождение длин подряд идущих действий у одного агента
        for action in plan:
            if action[3] not in agents:
                agents[action[3]] = 1
                previous_agent = action[3]
                counter = 1
                plan_agents.append(action[3])
            elif not previous_agent == action[3]:
                previous_agent = action[3]
                counter = 1
            elif previous_agent == action[3]:
                counter+=1
                if agents[action[3]] < counter:
                    agents[action[3]] = counter
        # выбираем самую длинную последовательность действий в плане - она будет главной характеристикой плана
        longest = 0
        agent=""
        for element in range(len(agents)):
            item = agents.popitem()
            if item[1] > longest:
                longest = item[1]
                agent = item[0]
        busiest.append((index, agent, longest, plan_agents))
    cheap = []
    alternative = []
    cheapest = []
    longest = 0
    min_agents = 100
    # находим самую длинную последовательность действий
    for plan in busiest:
        if plan[2] > longest:
            longest = plan[2]
    # находим наименьшее число агентов в самых длинных планах
    for plan in busiest:
        if plan[2] == longest:
            if len(plan[3]) < min_agents:
                min_agents = len(plan[3])
    # из 2 предыдущих выбираем тот, в котором фигурирую я - если таких нет говорим об этом
    for plan in busiest:
        if plan[2] == longest and len(plan[3]) == min_agents and "I" in plan[3]:
            plans_copy = plans.copy()
            cheap.append(plans_copy.pop(plan[0]))
        elif plan[2] == longest and len(plan[3]) == min_agents and not "I" in plan[3]:
            plans_copy = plans.copy()
            alternative.append(plans_copy.pop(plan[0]))
    if len(cheap) >= 1:
        cheapest.extend(random.choice(cheap))
    elif len(cheap) == 0 and len(alternative):
        logging.info("There are no plans in which I figure")
        cheapest.extend(random.choice(alternative))

    return cheapest


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
    return I_sign, I_obj, agent_back

def _check_experience(candidates, plan_sign, I_obj, I_sign):
    exp_agents = set()
    if not plan_sign is None:
        for con in plan_sign.out_meanings:
            exp_agents.add(con.out_sign)
        if I_obj in exp_agents:
            exp_agents.remove(I_obj)
            exp_agents.add(I_sign)
        exp_agents = [ag.name for ag in exp_agents]
        for cand in candidates.copy():
            if not cand[3] in exp_agents and not cand[3] is None:
                candidates.remove(cand)
    return candidates

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

        agents2 = agents.copy()
        agents2.remove(I_sign)
        agents2.add(I_obj)
        roles = []
        for mean, attribute in ag.items():
            if mean == I_sign:
                mean = I_obj
            for agent in agents2:
                roles2 = []
                variants = set()
                type = {}
                if agent == mean:
                    for elem in attribute:
                        if elem[1] == agent.name:
                            roles.append(elem[0])
                        elif elem[0] == agent.name:
                            variants.add(elem[1])
                    for elem in attribute:
                        if elem[1] in variants and not elem[0] in roles and not elem[0] == agent.name:
                            type.setdefault(elem[0], []).extend(elem[1])
                        if elem[1] in variants or elem[1] in type and not elem[0] == agent.name:
                            roles2.append(elem[0])
                    roles = list(set(roles2)&set(roles))
                    if len(type):
                        meanings.append((agent.name, type))

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
                    for type, elems in mean[1].items():
                        for elem in elems:
                            if all(elem in cm_meaning and mean[0] in cm_meaning or elem in cm_meaning \
                                   and type in cm_meaning for cm_meaning in cm_meanings):
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
                        script.append([agent.name, cm])
                        return script
        else:
            return False

    ma_combinations = mix_pairs(replace_map)

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


def _meta_check_activity(scripts, active_pm, check_pm, prev_pms, agents):
    heuristic = []
    for agent, script in scripts:
        estimation = _time_shift_backward(active_pm, script)
        for prev in prev_pms:
            if estimation.resonate('meaning', prev, False, False, agents):
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
