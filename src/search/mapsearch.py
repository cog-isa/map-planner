import logging

import itertools

import grounding.sign_task as st
from grounding.semnet import Sign
import random
from functools import reduce

MAX_ITERATION = 60

world_model = None
constraints = None

def map_search(task):
    global world_model
    global constraints
    world_model = task.signs
    active_pm = task.goal_situation.meanings[1]
    check_pm = task.start_situation.meanings[1]
    constraints = task.constraints
    logging.debug('Start: {0}'.format(check_pm.longstr()))
    logging.debug('Finish: {0}'.format(active_pm.longstr()))
    plans = map_iteration(active_pm, check_pm, [], 0)
    if plans:
        solution = long_relations(plans)
        solution.reverse()
    else:
        logging.info('No solution can be found!')
        return None
    return solution


def map_iteration(active_pm, check_pm, current_plan, iteration, exp_actions=[]):
    logging.debug('STEP {0}:'.format(iteration))
    logging.debug('\tSituation {0}'.format(active_pm.longstr()))
    if iteration >= MAX_ITERATION:
        logging.debug('\tMax iteration count')
        return None

    precedents = []
    plan_signs = []
    I_sign, I_obj, agents = get_agents()

    for name, sign in world_model.items():
        if name.startswith("action_"): plan_signs.append(sign)
        for index, cm in sign.meanings.items():
            if cm.includes('meaning', active_pm):
                precedents.extend(cm.sign.spread_up_activity_act('meaning', 1))
            elif not cm.sign.significances and active_pm.includes('meaning', cm):
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
    agent = None
    if not precedents:
        for agent, cm in meanings:
            result, checked = _check_activity(cm, active_pm)
            if result:
                applicable_meanings.append((agent, checked))
    else:
        for cm in precedents + meanings:
            if isinstance(cm, tuple):
                agent = cm[0]
                cm = cm[1]
            result, checked = _check_activity(cm, active_pm)
            if result:
                applicable_meanings.append((agent, checked))

    # TODO: replace to metarule apply

    candidates = _meta_check_activity(applicable_meanings, active_pm, check_pm, [x for x, _, _, _ in current_plan])

    # TODO если есть разные реализации действий - какой из них выбирать (нужно создать разные кауз. матрицы на 1 знак действия)
    if not exp_actions and iteration == 0:
        exp_actions = _get_experience(agents)

    if candidates and plan_signs:
        candidates = _check_experience(candidates, exp_actions)

    if not candidates:
        logging.debug('\tNot found applicable scripts ({0})'.format([x for _, x, _, _ in current_plan]))
        return None

    logging.debug('\tFound {0} variants'.format(len(candidates)))
    final_plans = []


    print("len of curent plan is: {0}. Len of candidates: {1}".format(len(current_plan), len(candidates)))
    # if len(current_plan) > 10:
    #     print([(pl[1], pl[3].name) for pl in current_plan])
    for counter, name, script, ag_mask in candidates:

        logging.debug('\tChoose {0}: {1} -> {2}'.format(counter, name, script))
        plan = current_plan.copy()
        plan.append((active_pm, name, script, ag_mask))
        # if maxLen and len(plan)> maxLen:
        #     return None
        next_pm = _time_shift_backward(active_pm, script)
        if next_pm.includes('meaning', check_pm):
            final_plans.append(plan)
            print("len of final plan is: {0}. Len of candidates: {1}".format(len(plan), len(candidates)))
        else:
            recursive_plans = map_iteration(next_pm, check_pm, plan, iteration + 1, exp_actions)
            if recursive_plans:
                # maxLen = len(recursive_plans[0])
                final_plans.extend(recursive_plans)

    return final_plans


def _get_experience(agents):
    actions = []
    for agent in agents:
        for connector in agent.out_meanings:
            cm = connector.in_sign.meanings[connector.in_index]
            if max([len(event.coincidences) for event in itertools.chain(cm.cause, cm.effect)]) > 1:
                if cm.is_causal():
                    #for sign
                    for pm in actions:
                        if pm.resonate('meaning', cm):
                            break
                    else:
                        actions.append(cm)

    return actions


def long_relations(plans):
    logging.info("in long relations")
    # отбираем самые короткие планы
    min = len(plans[0])
    for plan in plans:
        if len(plan) < min:
            min = len(plan)
    plans = [plan for plan in plans if len(plan) == min]

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
                if not action[3] is None:
                    plan_agents.append(action[3].name)
                else:
                    plan_agents.append(str(action[3]))
            elif not previous_agent == action[3]:
                previous_agent = action[3]
                counter = 1
            elif previous_agent == action[3]:
                counter += 1
                if agents[action[3]] < counter:
                    agents[action[3]] = counter
        # выбираем самую длинную последовательность действий в плане - она будет главной характеристикой плана
        longest = 0
        agent = ""
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
        if plan[3][0]:
            if plan[2] == longest and len(plan[3]) == min_agents and "I" in plan[3]:
                plans_copy = plans.copy()
                cheap.append(plans_copy.pop(plan[0]))
            elif plan[2] == longest and len(plan[3]) == min_agents and not "I" in plan[3]:
                plans_copy = plans.copy()
                alternative.append(plans_copy.pop(plan[0]))
        else:
            plans_copy = plans.copy()
            cheap.append(plans_copy.pop(plan[0]))
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
    I_obj = [con.in_sign for con in I_sign.out_significances if con.out_sign.name == "I"][0]
    They_sign = world_model["They"]
    agents = They_sign.spread_up_activity_obj("significance", 1)
    for cm in agents:
        agent_back.add(cm.sign)
    return I_sign, I_obj, agent_back


def _check_experience(candidates, exp_actions):
    actions = []
    for candidate in candidates:
        if candidate[3]:
            if candidate[2] in exp_actions:
                actions.append(candidate)
    if actions:
        return actions
    else:
        return candidates


def mix_pairs(replace_map):
    new_chain = {}
    elements = []
    merged_chains = []
    used_roles = []
    replace_map = list(replace_map.items())

    def get_role(obj, roles):
        for role in roles:
            if obj in role[1]:
                return role

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

    connectors = [agent.out_meanings for agent in agents]

    unrenewed = {}
    for agent_con in connectors:
        for con in agent_con:
            if con.in_sign == main_pm.sign:
                unrenewed.setdefault(con.out_sign, set()).add(con.in_sign.meanings[con.in_index])

    new_map = {}

    pms = []
    for agent, lpm in unrenewed.items():
        # firstly full signed actions from experience
        for pm in lpm.copy():
            pm_signs = pm.get_signs()
            role_signs = replace_map.keys() & pm_signs
            if not role_signs:
                lpm.remove(pm)
                if not pms:
                    pms.append((agent, pm))
                else:
                    for _, pmd in pms.copy():
                        if pmd.resonate('meaning', pm):
                            break
                    else:
                        pms.append((agent, pm))

        for pm in lpm:
            pm_signs = pm.get_signs()
            role_signs = replace_map.keys() & pm_signs
            for role_sign in role_signs:
                new_map[role_sign] = replace_map[role_sign]


            # search for changed in grounding
            old_map = {}
            changed_event = []
            changed_signs = set()
            for key, value in replace_map.items():
                if key not in new_map:
                    old_map[key] = value
            for key, value in old_map.items():
                value_signs = {cm.sign for cm in value}
                for event in itertools.chain(pm.cause, pm.effect):
                    event_signs = event.get_signs()
                    changed_sign = event_signs & value_signs
                    if changed_sign:
                        changed_signs |= changed_sign
                        changed_event.append((event_signs - changed_signs))

            predicates = set()
            for changed_sign in changed_signs:
                predicates |= {cm.sign for cm in changed_sign.spread_up_activity_obj('meaning', 1)}
            # search for pred name where changed
            predicates_signs = set()
            for element in changed_event:
                predicates_signs |= predicates & element

            # search for object signs to change
            if agent.name != "I":
                agent_name = agent.name
            else:
                agent_name = list(agent.spread_up_activity_obj('significance', 1))[0].sign.name
            if agent_name in constraints:
                agent_predicates = [pred for pred in constraints[agent_name] if world_model[pred.name] in predicates_signs]
            else:
                agent_predicates = []
            predicates_signatures = []
            for pred in agent_predicates:
                predicates_signatures.append([signa[0] for signa in pred.signature])
            #predicates_objects = {world_model[signa[0]] for signa in predicates_signatures}
            changed = []
            for sign in changed_signs:
                changed = [signa for signa in predicates_signatures if sign.name in signa]
            predicates_objects = set()
            for sign in changed_signs:
                for signa in changed:
                    for element in signa:
                        if element != sign.name:
                            predicates_objects.add(world_model[element])

            if changed_event:
                changed_event = reduce(lambda x, y: x|y, changed_event)
            else:
                pass

            for key, item in new_map.copy().items():
                if key in changed_event:
                    new_dict = {}
                    if predicates_objects:
                        new_dict[key] = [cm for cm in new_map[key] if cm.sign in predicates_objects]
                        if not new_dict[key]:
                            new_dict[key] = new_map[key]
                        new_map.update(new_dict)

            ma_combinations = mix_pairs(new_map)

            # search for contrast pm and pms matrixes
            # exp_combinations = []
            # for cm in pms:
            #     map = {}
            #     if agent in cm[1].get_signs():
            #         if max([len(event.coincidences) for event in itertools.chain(cm[1].cause, cm[1].effect)]) > 1:
            #             sub1 = pm - cm[1]
            #             sub2 = cm[1] - pm
            #             if len(sub1) == len(sub2):
            #                 for e1, e2 in zip(sub1, sub2):
            #                     values = list(e2.get_signs() - e1.get_signs())
            #                     keys = list(e1.get_signs() - e2.get_signs())
            #                     for pair in itertools.product(values, keys):
            #                         if pair[1] in new_map.keys():
            #                             if pair[0] in [cm.sign for cm in new_map[pair[1]]]:
            #                                 value = [cm for cm in new_map[pair[1]] if cm.sign == pair[0]][0]
            #                                 map[pair[1]] = value
            #     if map:
            #         exp_combinations.append(map)
            #
            # ma_combinations = [comb for comb in ma_combinations if not comb in exp_combinations]

            for ma_combination in ma_combinations:
                cm = pm.copy('meaning', 'meaning')

                for role_sign, obj_pm in ma_combination.items():
                    obj_cm = obj_pm.copy('significance', 'meaning')
                    # role_sign = [sign for sign in cm.get_signs() if sign == role_sign][0]
                    cm.replace('meaning', role_sign, obj_cm)
                if not pms:
                    pms.append((agent, cm))
                else:
                    for _, pmd in pms.copy():
                        if pmd.resonate('meaning', cm):
                            break
                    else:
                        pms.append((agent, cm))

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
            for event in [event for event in estimation.cause if len(event.coincidences) > 1]:
                for ce in [event for event in check_pm.cause if len(event.coincidences) > 1]:
                    if event.resonate('meaning', ce):
                        counter += 1
                        break

            heuristic.append((counter, script.sign.name, script, agent))
    if heuristic:
        best_heuristics = max(heuristic, key=lambda x: x[0])
        return list(filter(lambda x: x[0] == best_heuristics[0], heuristic))
    else:
        return None
