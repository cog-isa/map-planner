import logging
from semnet import Sign

SIT_COUNTER = 0
MAX_ITERATION = 100


def map_search(task):
    active_pm = task.goal_situation.meanings[0]
    check_pm = task.start_situation.meanings[0]
    logging.debug('Start: {0}, finish: {1}'.format(check_pm, active_pm))

    plans = map_iteration(active_pm, check_pm, [], 0)
    logging.debug('Found {0} variants'.format(len(plans)))
    if plans:
        plan = sorted(plans, key=lambda x: len(x))[0]
        reversed(plan)
        logging.info('Plan: len={0}, {1}'.format(len(plan), [name for _, name, _ in plan]))
        return [(name, script) for _, name, script in plan]

    return None


def map_iteration(active_pm, check_pm, current_plan, iteration):
    logging.debug('STEP {0}:'.format(iteration))
    if iteration >= MAX_ITERATION:
        logging.debug('\tMax iteration count')
        return None

    active_chains = active_pm.spread_down_activity('meaning', 2)  # Select current signs
    active_signif = set()
    for chain in active_chains:
        pm = chain[-1]
        active_signif |= pm.sign.spread_up_activity_act('significance', 3)

    meanings = []
    for pm_signif in active_signif:
        chains = pm_signif.spread_down_activity('significance', 3)  # check connected signs with actions
        merged_chains = []
        for chain in chains:
            for achain in active_chains:
                if chain[-1].sign == achain[-1].sign:
                    merged_chains.append(chain)
                    break
        scripts = _merge_activity(merged_chains)  # Replace role in abstract actions to generate scripts
        meanings.extend(scripts)

    applicable_meanings = _check_activity(meanings, active_pm)

    # TODO: replace to metarule apply
    heuristics = _meta_check_activity(applicable_meanings, active_pm, check_pm, [x for x, _, _ in current_plan])

    if not heuristics:
        logging.debug('\tNot found applicable scripts ({0})'.format([x for _, x, _ in current_plan]))
        return None

    logging.debug('\tFound {0} variants'.format(len(heuristics)))
    final_plans = []
    for counter, name, script in heuristics:
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


def _merge_activity(chains):
    replace_map = {}
    main_pm = None
    for chain in chains:
        if not chain[1].sign in replace_map:
            replace_map[chain[1].sign] = [chain[-1].sign]
        else:
            if not chain[-1].sign in replace_map[chain[1].sign]:
                replace_map[chain[1].sign].append(chain[-1].sign)
        main_pm = chain[0]

    def reccur_replacement(base, new_base, base_pm, role_map):
        result = []
        for role in role_map:
            for obj in role_map[role]:
                new_pm, _ = base_pm.copy_replace(base, new_base, role, obj)
                if len(role_map) > 1:
                    others = {}
                    for r in role_map:
                        if not r == role:
                            others[r] = role_map[r].copy()
                            others[r].remove(obj)
                    result.extend(reccur_replacement('meaning', 'meaning', new_pm, others))
                else:
                    result.append(new_pm)
        return result

    # TODO: really many extra meanings (from not fully substituted)
    pms = reccur_replacement('significance', 'meaning', main_pm, replace_map)
    return pms


def _check_activity(meanings, active_pm):
    selected = []

    def check_pm(pm):
        for event in pm.effect:
            for fevent in active_pm.cause:
                if event.resonate('meaning', fevent):
                    break
            else:
                return False

        return True

    for pm in meanings:
        if check_pm(pm):
            selected.append(pm)
    return selected


def _time_shift_backward(active_pm, script):
    global SIT_COUNTER
    next_pm = Sign(str(SIT_COUNTER))
    pm, _ = next_pm.add_meaning()
    SIT_COUNTER += 1
    for event in active_pm.cause:
        for es in script.effect:
            if event.resonate('meaning', es):
                break
        else:
            pm.add_event(event.copy_replace('meaning', 'meaning'))
    for event in script.cause:
        pm.add_event(event.copy_replace('meaning', 'meaning'))

    return pm


def _meta_check_activity(scripts, active_pm, check_pm, prev_pms):
    heuristic = []
    for script in scripts:
        estimation = _time_shift_backward(active_pm, script)
        for prev in prev_pms:
            if estimation.resonate('meaning', prev, False):
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
