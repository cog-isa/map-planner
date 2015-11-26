import logging
import itertools
from sign_task import NetworkFragment


def pma_search(task):
    current_fragment = task.goal_situation.meaning[0].copy()
    start_fragment = task.start_situation.meaning[0]
    plan = []

    # while not current_fragment > start_fragment:
    current_signs = _get_signs(current_fragment)
    scripts_dict = _generate_scripts(current_signs)

    logging.info('Plan: {0}', [x[1] for x in plan])


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
            fragment.add((index, component), column_index=c_idx)
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
            fragment.add((index, component), column_index=c_idx)
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
