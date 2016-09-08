import logging

import grounding.sign_task as st
from grounding.semnet import Sign

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
    if plans:
        logging.debug('Found {0} variants'.format(len(plans)))
        plan = sorted(plans, key=lambda x: len(x))[0]
        reversed(plan)
        logging.info('Plan: len={0}, {1}'.format(len(plan), [name for _, name, _ in plan]))
        return [(name, script) for _, name, script in plan]
    else:
        logging.debug('Variant are not found')
    return None


def map_iteration(active_pm, check_pm, current_plan, iteration):
    logging.debug('STEP {0}:'.format(iteration))
    logging.debug('\tSituation {0}'.format(active_pm.longstr()))
    if iteration >= MAX_ITERATION:
        logging.debug('\tMax iteration count')
        return None

    # Check meanings for current situations
    precedents = []
    for name, sign in world_model.items():
        for index, cm in sign.meanings.items():
            if cm.includes('meaning', active_pm):
                precedents.extend(cm.sign.spread_up_activity_act('meaning', 1))

    # Activate all current signs (their meanings)
    active_chains = active_pm.spread_down_activity('meaning', 2)
    active_signif = set()
    # find all significances (actions) for all current signs
    for chain in active_chains:
        pm = chain[-1]
        active_signif |= pm.sign.spread_up_activity_act('significance', 3)

    meanings = []
    for pm_signif in active_signif:
        # find all roles and role replacements in each significance (action)
        chains = pm_signif.spread_down_activity('significance', 3)
        merged_chains = []
        for chain in chains:
            for achain in active_chains:
                if chain[-1].sign == achain[-1].sign and len(chain) > 2 and chain not in merged_chains:
                    merged_chains.append(chain)
                    break
        # Replace role in abstract actions to generate scripts
        scripts = _generate_meanings(merged_chains)
        meanings.extend(scripts)

    applicable_meanings = []
    for cm in precedents + meanings:
        result, checked = _check_activity(cm, active_pm)
        if result:
            applicable_meanings.append(checked)

    # TODO: replace to metarule apply
    candidates = _meta_check_activity(applicable_meanings, active_pm, check_pm, [x for x, _, _ in current_plan])

    if not candidates:
        logging.debug('\tNot found applicable scripts ({0})'.format([x for _, x, _ in current_plan]))
        return None

    logging.debug('\tFound {0} variants'.format(len(candidates)))
    final_plans = []
    for counter, name, script in candidates:
        logging.debug('\tChoose {0}: {1} -> {2}'.format(counter, name, script))

        plan = current_plan.copy()
        plan.append((active_pm, name, script))
        next_pm = _time_shift_backward(active_pm, script)

        if next_pm.includes('meaning', check_pm):
            final_plans.append(plan)
        else:
            recursive_plans = map_iteration(next_pm, check_pm, plan, iteration + 1)
            if recursive_plans:
                final_plans.extend(recursive_plans)

    return final_plans


def _generate_meanings(chains):
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

    def create_combinations(role_map, current=None):
        if current is None:
            current = {}
        for role_sign in role_map:
            for obj_pm in role_map[role_sign]:
                new_current = current.copy()
                new_current[role_sign] = obj_pm
                if len(role_map) > 1:
                    others = {}
                    for r in role_map:
                        if not r == role_sign:
                            others[r] = role_map[r].copy()
                            others[r].remove(obj_pm)
                    create_combinations(others, new_current)
                else:
                    combinations.append(new_current)
            break

    create_combinations(replace_map)
    pms = []
    for combination in combinations:
        cm = main_pm.copy('significance', 'meaning')
        for role_sign, obj_pm in combination.items():
            obj_cm = obj_pm.copy('significance', 'meaning')
            cm.replace('meaning', role_sign, obj_cm)
        pms.append(cm)

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
    for script in scripts:
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
            heuristic.append((counter, script.sign.name, script))
    if heuristic:
        best_heuristics = max(heuristic, key=lambda x: x[0])
        return list(filter(lambda x: x[0] == best_heuristics[0], heuristic))
    else:
        return None
