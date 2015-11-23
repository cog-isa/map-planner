import logging
from sign_task import SignImage

def pma_search(task):
    scripts = {}
    goals = task.goal_situation.images[0].get_components()
    for sign in goals:
        for name, scrs in _find_scripts(sign, task.signs).items():
            old_comp = scripts.get(name, set())
            for scr in scrs:
                old_comp |= _specify(scr, goals - {sign})
            scripts[name] = old_comp

    useful_scripts = set()
    cumulate = []
    reset = False
    for column in task.goal_situation.images[0].conditions:
        if reset:
            cumulate = []
            reset = False
        cumulate.append(column)
        for name, variants in scripts.items():
            for script in variants:
                if all([x in script.effects for x in cumulate]):
                    useful_scripts.add(script)
                    reset = True

    logging.debug('Initial scripts: {0}', useful_scripts)


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
