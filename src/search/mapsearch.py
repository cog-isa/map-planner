import itertools
import logging

MAX_ITERATION = 100


def map_search(task):
    current_fragment = task.goal_situation.meanings[0]
    start_fragment = task.start_situation.meanings[0]
    logging.debug('Start: {0}, finish: {1}'.format(start_fragment, current_fragment))

    plans = map_iteration(current_fragment, start_fragment, [], 0)
    logging.debug('Found {0} variants'.format(len(plans)))
    if plans:
        plan = sorted(plans, key=lambda x: len(x))[0]
        reversed(plan)
        logging.info('Plan: len={0}, {1}'.format(len(plan), [name for _, name, _ in plan]))
        return [(name, script) for _, name, script in plan]

    return None


def map_iteration(current_fragment, start_fragment, current_plan, iteration):
    logging.debug('STEP {0}:'.format(iteration))
    if iteration >= MAX_ITERATION:
        logging.debug('\tMax iteration count')
        return None

    current_signs = current_fragment.get_signs()
    significances = []
    for sign in current_signs:
        if not sign.is_action():
            significances.extend(sign.get_own_scripts())
            significances.extend(sign.get_inherited_scripts())

    meanings = []
    for significance in significances:
        meanings.extend(_interpret(significance, current_signs))

    applicable_meaning = _get_applicable(meanings, current_fragment)

    heuristics = _select_meanings(applicable_meaning, current_fragment,
                                  start_fragment, [x for x, _, _ in current_plan])

    if not heuristics:
        logging.debug('\tNot found applicable scripts ({0})'.format([x for _, x, _ in current_plan]))
        return None

    logging.debug('\tFound {0} variants'.format(len(heuristics)))
    final_plans = []
    for counter, name, script in heuristics:
        logging.debug('\tChoose {0}: {1} -> {2}'.format(counter, name, script))

        plan = current_plan.copy()
        plan.append((current_fragment, name, script))
        next_fragment = _apply_script(current_fragment, script)

        if next_fragment > start_fragment:
            final_plans.append(plan)
        else:
            recursive_plans = map_iteration(next_fragment, start_fragment, plan, iteration + 1)
            if recursive_plans:
                final_plans.extend(recursive_plans)

    return final_plans


def _interpret(significance, signs):
    meanings = []
    return meanings


def _generate_scripts(signs):
    """
    Generate scripts without abstract signs
    :param signs: All Sign
    :return: dict of generated scripts
    """
    scripts_dict = {}
    for sign in signs:
        if not sign.is_action() and len(sign.get_parents()) > 0:
            frg_dict = _generate_fragments(sign)
            # TODO: add recursion generation not only for tow roles
            for name, fragment in frg_dict.items():
                replaced = set()
                for other_sign in signs - {sign}:
                    if not other_sign.is_action() and len(other_sign.get_parents()) > 0:
                        replaced |= _replace_parent(fragment, other_sign)

                if not replaced:
                    scripts_dict[name] = scripts_dict.get(name, set()) | {fragment}
                else:
                    scripts_dict[name] = scripts_dict.get(name, set()) | replaced
    return scripts_dict


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


def _get_signs(fragment):
    """
    Get all signs (recursive) from fragment
    :param fragment: NetworkFragment
    :return: set of Sign
    """
    result = set()
    for column in itertools.chain(fragment.left, fragment.right):
        for index, element in column:
            if element.is_action():
                result |= _get_signs(element.meaning[index])
            else:
                result.add(element)
    return result


def _generate_fragments(sign):
    """
    Generate scripts from sign
    :param sign: Start Sign
    :return: dict of fragments with replaced sign
    """
    fragment_dict = {}
    for m in sign.significance:
        for index, component in m.get_components():
            if component.is_action():
                _, new_mean = _create_meaning_from_image(component, component.images[0])
                fragment_dict[component.name] = new_mean
            else:
                parent_dict = _generate_fragments(component)
                for name, frg in parent_dict.items():
                    idx, _ = _create_meaning_from_image(sign, sign.images[0])
                    _replace(frg, (-1, component), (idx, sign))
                    fragment_dict[name] = frg

    return fragment_dict


def _replace_parent(script, sign):
    """
    Replace first occurrence parent sign to child sign
    :param script: NetworkFragment
    :param sign: Replacer Sign
    :return: replaced scripts
    """
    replaced = set()
    for index, component in script.get_components():
        if not component.is_action() and sign.has_parent(component):
            fragment = _create_meaning_from_script(script)
            index, _ = _create_meaning_from_image(sign, sign.images[0])
            _replace(fragment, (-1, component), (index, sign))
            replaced.add(fragment)

    return replaced


def _create_meaning_from_image(sign, image):
    """
    Add new meaning element for sign from its image
    :param sign: Sign for create meaning
    :return: pair of (meaning index, new fragment)
    """
    fragment = NetworkFragment([])
    for c_idx, column in enumerate(image.left):
        for index, component in column:
            idx, _ = _create_meaning_from_image(component, component.images[index])
            fragment.add((idx, component), column_index=c_idx)
    for c_idx, column in enumerate(image.right):
        for index, component in column:
            idx, _ = _create_meaning_from_image(component, component.images[index])
            fragment.add((idx, component), False, c_idx)
    sign.meaning.append(fragment)

    return len(sign.meaning) - 1, fragment


def _create_meaning_from_meaning(sign, mean_frag):
    """
    Add new meaning element for sign from its image
    :param sign: Sign for create meaning
    :return: pair of (meaning index, new fragment)
    """
    fragment = NetworkFragment([])
    for c_idx, column in enumerate(mean_frag.left):
        for index, component in column:
            idx, _ = _create_meaning_from_meaning(component, component.meaning[index])
            fragment.add((idx, component), column_index=c_idx)
    for c_idx, column in enumerate(mean_frag.right):
        for index, component in column:
            idx, _ = _create_meaning_from_meaning(component, component.meaning[index])
            fragment.add((idx, component), False, c_idx)
    sign.meaning.append(fragment)

    return len(sign.meaning) - 1, fragment


def _create_meaning_from_script(script):
    """
    Add new meaning element for sign from its image
    :param script: Script from create meaning
    :return:new fragment NetworkFragment
    """
    fragment = NetworkFragment([])
    for c_idx, column in enumerate(script.left):
        for index, component in column:
            idx, _ = _create_meaning_from_meaning(component, component.meaning[index])
            fragment.add((index, component), column_index=c_idx)
    for c_idx, column in enumerate(script.right):
        for index, component in column:
            idx, _ = _create_meaning_from_meaning(component, component.meaning[index])
            fragment.add((idx, component), False, c_idx)

    return fragment


def _replace(fragment, old_pair, new_pair):
    """
    Recurrent replace in fragment old element ot new element
    :param fragment: NetworkFragment for replace
    :param old_pair: old pair of (index, Sign)
    :param new_pair: new pair of (index, Sign)
    :return:
    """

    def _replace_part(index, part):
        new_column = set()
        for idn, val in part[index]:
            if val.is_action():
                idx, frg = _create_meaning_from_meaning(val, val.meaning[idn])
                _replace(frg, old_pair, new_pair)
                new_column.add((idx, val))
            elif old_pair[0] >= 0 and (idn, val) == old_pair:
                new_column.add(new_pair)
            elif old_pair[0] == -1 and val == old_pair[1]:
                new_column.add(new_pair)
            else:
                new_column.add((idn, val))
        part[index] = new_column

    for i in range(len(fragment.left)):
        _replace_part(i, fragment.left)
    for i in range(len(fragment.right)):
        _replace_part(i, fragment.right)
