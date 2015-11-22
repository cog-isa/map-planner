import logging
import itertools


def pma_search(task):
    scripts = []
    for sign in itertools.chain(*task.start_situation.images[0].conditions):
        scripts.append(_find_scripts(sign, task.signs))
    logging.debug('Initial scripts: {0}', scripts)


def _find_scripts(sign, signs):
    scripts = []
    for comp in sign.significance:
        if comp.is_action():
            script = comp.images[0].copy()
            scripts.append(script)
        else:
            for scr in _find_scripts(comp, signs):
                scr.replace(comp, sign)
                scripts.append(scr)

    return scripts


def _specify(sign, signs):
    pass
