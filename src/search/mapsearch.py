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
            if cm.includes('meaning', active_pm):# распространение активности на
                precedents.extend(cm.sign.spread_up_activity_act('meaning', 1)) # личностных смыслах от матриц начальной и целевой ситуаций

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
        return None

    logging.debug('\tFound {0} variants'.format(len(candidates)))
    final_plans = []

    # print("len of candidates is: {0}".format(len(candidates)))

    for counter, name, script, ag_mask in candidates:
        logging.debug('\tChoose {0}: {1} -> {2}'.format(counter, name, script))

        plan = current_plan.copy()
        plan.append((active_pm, name, script, ag_mask.name))
        # if maxLen and len(plan)> maxLen:
        #     return None
        next_pm = _time_shift_backward(active_pm, script, agents)
        if next_pm.includes('meaning', check_pm):
            final_plans.append(plan)
            print("len of final plan is: {0}. Len of candidates: {1}".format(len(plan), len(candidates)))
        else:
            recursive_plans = map_iteration(next_pm, check_pm, plan, iteration + 1)
            if recursive_plans:
                #maxLen = len(recursive_plans[0])
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
    I_obj = [con.in_sign for con in I_sign.out_significances if con.out_sign.name == "I"][0]
    agents = world_model['agent'].significances
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
        actions = []
        exp_candidates = []
        for con in plan_sign.out_meanings:
            actions.append(con.in_sign.meanings[con.in_index])
        for action in actions:
            for cand in candidates:
                if action == cand[2]:
                    exp_candidates.append(cand)
        if exp_candidates:
            candidates = exp_candidates
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

    connectors = [agent.out_meanings for agent in agents]

    unrenewed = {}
    for agent_con in connectors:
        for con in agent_con:
            if con.in_sign == main_pm.sign:
                unrenewed.setdefault(con.out_sign, []).append(con.in_sign.meanings[con.in_index])

    roles = []
    predicates = set()
    # от знака блока в out_meanings -->> blocktype ->>> in_index
    for role_sign, variants in replace_map.items():
        for variant in variants:
            predicates |= variant.sign.spread_up_activity_obj('meaning', 1)
        for role in roles:
            if variants == role[0]:
                continue
        else:
            roles.append((variants, predicates))
        predicates = set()

    predicate_signs = []

    for pms, role in roles:
        others = []
        [others.extend(pm) for pm, _ in roles if not pm == pms]
        others = [pm.sign for pm in others]
        pms_signs = [pm.sign for pm in pms]
        for r in role:
           pred_signs = list(r.get_signs())
           if len(r.cause) > len(roles):
               continue
           if pred_signs[0] in others and pred_signs[1] in pms_signs or pred_signs[0] in pms_signs and pred_signs[1] in others:
               predicate_signs.append(pred_signs)
               predicates.add(r.sign)


    for s in predicate_signs.copy():
        others = [el for el in predicate_signs if el[1] == s[1] and el[0] == s[0] or el[1] == s[0] and el[0] == s[1]]
        for el in others:
            predicate_signs.remove(el)
        predicate_signs.append(s)



    pms = []
    for agent, lpm in unrenewed.items():
        for pm in lpm:
            pm_signs = pm.get_signs()
            new_map = {}
            role_signX = []
            variants = set()
            variantsX = set()
            variantsY = set()
            role_signs = replace_map.keys() & pm_signs
            if role_signs:
                for event in itertools.chain(pm.cause, pm.effect):
                    for pred in predicates:
                        ev_signs = event.get_signs()
                        if pred in ev_signs:
                            for pred_sign in predicate_signs:
                                if any(sign for sign in pred_sign if sign in ev_signs):
                                    role_signX = list(ev_signs - set(pred_sign))
                                    role_signX.remove(pred)
                                    variants |= set(pred_sign) - ev_signs
                role_signY = list(role_signs - set(role_signX))

                for role, pmd in replace_map.items():
                    variantsX |= {cm for cm in pmd if cm.sign in variants}
                    if any(cm for cm in pmd if cm.sign in variants):
                        variantsY |= set(pmd)

                new_map.setdefault(*role_signX, []).extend(variantsX)
                if role_signY:
                    new_map.setdefault(*role_signY, []).extend(list(variantsY))


                ma_combinations = mix_pairs(new_map)
                for ma_combination in ma_combinations:
                    cm = pm.copy('meaning', 'meaning')
                    for role_sign, obj_pm in ma_combination.items():
                        obj_cm = obj_pm.copy('significance', 'meaning')
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


def _time_shift_backward(active_pm, script, agents):
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
        estimation = _time_shift_backward(active_pm, script, agents)
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
