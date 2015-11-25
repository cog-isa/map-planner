import logging


def pma_search(task):
    current_image = task.goal_situation.meaning[0].copy()
    start_image = task.start_situation.meaning[0]
    plan = []

    while not _including(current_image, start_image):
        meanings = _define_meanings(current_image, task.signs)
        best_info = _get_best_script(meanings)
        plan.append((current_image, best_info[0]))
        current_situation = _replace(current_image, *best_info[1:])

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


def _define_meanings(current_image, signs):
    current_signs = current_image.get_components()
    scripts_dict = {}

    # build scripts (specified significances) dictionary
    for sign in current_signs:
        for name, scrs in _find_scripts(sign, signs).items():
            old_comp = scripts_dict.get(name, set())
            for scr in scrs:
                old_comp |= _specify(scr, current_signs - {sign})
            scripts_dict[name] = old_comp

    # TODO: order of columns is very important?
    useful_scripts = set()
    for name in scripts_dict:
        for script in scripts_dict[name]:
            included = []
            for val in script.effects:
                for i, column in enumerate(current_image.conditions):
                    if i not in included and val == column:
                        included.append(i)
                        break
            if len(included) == len(script.effects):
                useful_scripts.add((name, script.copy(), tuple(included)))

    return useful_scripts


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


def _replace(situation, action, columns):
    new_situation = situation.copy()
    for i, column in enumerate(columns):
        new_situation.conditions[column] = (new_situation.conditions[column] -
                                            action.effects[i]) | action.conditions[i]
    if len(columns) < len(action.conditions):
        new_situation.conditions.update(action.conditions[len(columns):])
    return new_situation


def _is_signified(sign, test):
    return test in sign.significance or any([_is_signified(s, test) for s in sign.significance])


def _get_best_script(candidates):
    return candidates.pop()
