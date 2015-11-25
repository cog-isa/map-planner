import logging


def pma_search(task):
    scripts_dict = {}
    scripts = set()
    goals = task.goal_situation.images[0].get_components()
    for sign in goals:
        for name, scrs in _find_scripts(sign, task.signs).items():
            old_comp = scripts_dict.get(name, set())
            for scr in scrs:
                result = _specify(scr, goals - {sign})
                old_comp |= result
                scripts |= result
            scripts_dict[name] = old_comp

    useful_scripts = {(x, 0, 0) for x in scripts}
    for i, column in enumerate(task.goal_situation.images[0].conditions):
        active_scripts = set()
        prev_scrips = useful_scripts.copy()
        while useful_scripts:
            script, index, size = useful_scripts.pop()
            for j in range(index, len(script.effects)):
                if column <= script.effects[j]:
                    active_scripts.add((script, index, size + 1))
        if not active_scripts:
            useful_scripts = prev_scrips
            break
        else:
            useful_scripts = active_scripts

    _replace(task.goal_situation.images[0], *useful_scripts.pop())
    logging.debug('Initial scripts: {0}', useful_scripts)


def _replace(situation, action, index, size):
    for i in range(size):
        if situation.conditions[i] <= action.effects[i + index]:
            situation.conditions[i] = (situation.conditions[i] - action.effects[i + index]) | action.conditions[i + index]


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
