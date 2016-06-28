import itertools
import logging

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
                if chain[-1].sign == achain[-1].sign:
                    merged_chains.append(chain)
                    break
        scripts = merge_activity(merged_chains)
        meanings.extend(scripts)

    applicable_meaning = _get_applicable(meanings, active_pm)

    heuristics = _select_meanings(applicable_meaning, active_pm,
                                  check_pm, [x for x, _, _ in current_plan])

    if not heuristics:
        logging.debug('\tNot found applicable scripts ({0})'.format([x for _, x, _ in current_plan]))
        return None

    logging.debug('\tFound {0} variants'.format(len(heuristics)))
    final_plans = []
    for counter, name, script in heuristics:
        logging.debug('\tChoose {0}: {1} -> {2}'.format(counter, name, script))

        plan = current_plan.copy()
        plan.append((active_pm, name, script))
        next_fragment = _apply_script(active_pm, script)

        if next_fragment > check_pm:
            final_plans.append(plan)
        else:
            recursive_plans = map_iteration(next_fragment, check_pm, plan, iteration + 1)
            if recursive_plans:
                final_plans.extend(recursive_plans)

    return final_plans


def merge_activity(chains):
    pms = []
    for chain in chains:
        pm, idx = chain[0].replace('significance', 'meaning', chain[1], chain[-1])
        pms.append(pm)
    return pms


def _apply_script(fragment, script):
    new_frag = fragment.copy()
    to_remove = script.right
    to_add = script.left
    for i, column in enumerate(to_remove):
        index = new_frag.get_column_index(column)
        if i < len(to_add):
            new_frag.left[index] = to_add[i]
        else:
            del new_frag.left[index]

    for i in range(len(to_remove), len(to_add)):
        new_frag.left.append(to_add[i])

    return new_frag


def _select_meanings(applicable_dict, current_situation, ref_situation, prev_situations):
    heuristic = []
    for name, scripts in applicable_dict.items():
        for script in scripts:
            estimation = _apply_script(current_situation, script)
            for prev in prev_situations:
                if _deep_equal_signs(prev, estimation):
                    break
            else:
                counter = 0
                for column in estimation.left:
                    if ref_situation.get_column_index(column) >= 0:
                        counter += 1
                heuristic.append((counter, name, script))
    if heuristic:
        best_heuristics = max(heuristic, key=lambda x: x[0])
        return list(filter(lambda x: x[0] == best_heuristics[0], heuristic))
    else:
        return None


def _deep_equal_signs(sit1, sit2):
    if not len(sit1.left) == len(sit2.left):
        return False

    signs1_map = {}
    signs2_map = {}
    for column in sit1.left + sit1.right:
        for index, sign in column:
            signs1_map[sign.name] = signs1_map.get(sign.name, []) + [(sign, index)]
    for column in sit2.left + sit2.right:
        for index, sign in column:
            signs2_map[sign.name] = signs2_map.get(sign.name, []) + [(sign, index)]

    for name, signs1 in signs1_map.items():
        if name not in signs2_map:
            return False
        signs2 = signs2_map[name]
        if not len(signs1) == len(signs2):
            return False
        if len(signs1) > 0:
            checked = []
            for sign1, index1 in signs1:
                for i, (sign2, index2) in enumerate(signs2):
                    if i not in checked and _deep_equal_signs(sign1.meaning[index1], sign2.meaning[index2]):
                        checked.append(i)
                        break
                else:
                    return False
    return True


def _get_applicable(script_dict, situation):
    applicable_dict = {}
    for name, scripts in script_dict.items():
        for script in scripts:
            for column in script.right:
                if situation.get_column_index(column) == -1:
                    break
            else:
                prev_scripts = applicable_dict.get(name, set())
                for old_script in prev_scripts:
                    if old_script.equal_signs(script):
                        break
                else:
                    applicable_dict[name] = prev_scripts | {script}

    return applicable_dict
