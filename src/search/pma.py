import logging


def pma_search(task):
    current_situation = task.goal_situation.images[0].copy()
    plan = []

    while not _including(current_situation, task.start_situation.images[0]):
        useful_scripts = _find_useful_scripts(current_situation, task.signs)
        best_info = _get_best_script(useful_scripts)
        plan.append((current_situation, best_info[0]))
        current_situation = _replace(current_situation, *best_info[1:])

    logging.info('Plan: {0}', [x[1] for x in plan])


def _including(big_situation, small_situation):
    # TODO: not all variants
    included = []
    for s_column in small_situation.conditions:
        for j, b_column in enumerate(big_situation.conditions):
            if j not in included and s_column < b_column:
                included.append(j)
                break
        else:
            return False
    return True


def _get_best_script(candidates):
    return candidates.pop()


def _find_useful_scripts(current_situation, signs):
    current_signs = current_situation.get_components()
    scripts_dict = {}

    for sign in current_signs:
        for name, scrs in _find_scripts(sign, signs).items():
            old_comp = scripts_dict.get(name, set())
            for scr in scrs:
                old_comp |= _specify(scr, current_signs - {sign})
            scripts_dict[name] = old_comp

    useful_scripts = set()
    for name in scripts_dict:
        # action, action start applied index, situation start applied index, length of applied part
        for val in scripts_dict[name]:
            useful_scripts.add((name, val.copy(), -1, -1, 0))
    for i, column in enumerate(current_situation.conditions):
        active_scripts = set()
        prev_scrips = useful_scripts.copy()
        while useful_scripts:
            name, script, act_index, sit_index, size = useful_scripts.pop()
            if act_index == -1:  # action is not active
                for j in range(len(script.effects)):
                    if column <= script.effects[j]:
                        active_scripts.add((name, script, j, i, 1))
                        break
            elif sit_index + size == i and act_index + size < len(script.effects):  # action is active
                if column <= script.effects[act_index + size]:
                    active_scripts.add((name, script, act_index, sit_index, size + 1))
        if not active_scripts:
            useful_scripts = prev_scrips
            break
        else:
            useful_scripts = active_scripts

    return useful_scripts


def _replace(situation, action, act_index, sit_index, size):
    new_situation = situation.copy()
    for i in range(size):
        new_situation.conditions[sit_index + i] = (new_situation.conditions[sit_index + i] -
                                                   action.effects[act_index + i]) | action.conditions[i]
    if size < len(action.conditions):
        new_situation.conditions = new_situation.conditions[:sit_index + size] + action.conditions[
                                                                                 size:] + new_situation.conditions[
                                                                                          sit_index + size:]
    return new_situation


def _find_scripts(sign, signs):
    scripts = {}
    for comp in sign.significance:
        if comp.is_action():
            old_comp = scripts.get(comp.name, set())
            old_comp |= {comp.images[0].copy()}
            scripts[comp.name] = old_comp
        else:
            for name, scrs in _find_scripts(comp, signs).items():
                for scr in scrs:
                    scr.replace(comp, sign)
                    old_comp = scripts.get(name, set())
                    old_comp |= {scr}
                    scripts[name] = old_comp

    return scripts


def _specify(script, signs):
    specified = set()
    for sign in signs:
        for comp in script.get_components():
            if _is_signified(sign, comp):
                new_script = script.copy()
                new_script.replace(comp, sign)
                specified |= _specify(new_script, signs - {sign})
    if not specified:
        specified |= {script}

    return specified


def _is_signified(sign, test):
    return test in sign.significance or any([_is_signified(s, test) for s in sign.significance])
