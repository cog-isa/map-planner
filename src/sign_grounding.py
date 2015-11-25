import logging
import itertools
from collections import defaultdict
from sign_task import SignImage, Sign, Task


def ground(problem):
    domain = problem.domain
    actions = domain.actions.values()
    predicates = domain.predicates.values()

    # Objects
    objects = problem.objects
    objects.update(domain.constants)
    logging.debug('Objects:\n%s' % objects)

    # Get the names of the static predicates
    statics = _get_statics(predicates, actions)
    logging.debug("Static predicates:\n%s" % statics)

    # Create a map from types to objects
    type_map = _create_type_map(objects)
    logging.debug("Type to object map:\n%s" % type_map)

    # Sign world model
    signs = {action.name: Sign(action.name) for action in actions}
    for obj in objects:
        signs[obj] = Sign(obj)
    for tp, objects in type_map.items():
        sign = Sign(tp.name)
        for obj in objects:
            sign_image = SignImage([{signs[obj]}], sign=sign)
            sign.images.append(sign_image)
        signs[tp.name] = sign

    for pred in predicates:
        signs[pred.name] = Sign(pred.name)

    _significance_from_actions(signs, actions)
    _significance_from_abstracts(signs)

    start_situation = _define_situation('*start*', problem.initial_state, signs)
    goal_situation = _define_situation('*finish*', problem.goal, signs)

    _expand_situation(goal_situation, signs)
    return Task(problem.name, signs, start_situation, goal_situation)


def _expand_situation(goal_situation, signs):
    # TODO: add common approach
    goal_situation.meaning[0].conditions.append({signs['handempty']})
    goal_situation.meaning[0].conditions.append({signs['ontable'], signs['a']})
    goal_situation.meaning[0].conditions.append({signs['clear'], signs['d']})


def _significance_from_actions(signs, actions):
    for action in actions:
        procedural_sign = signs[action.name]
        _significance_from_predicates(procedural_sign, signs, action.precondition)
        _significance_from_predicates(procedural_sign, signs, action.effect.addlist, False)


def _significance_from_predicates(procedural_sign, signs, predicates, condition=True):
    for column, pred in enumerate(predicates):
        relation_sign = signs[pred.name]
        procedural_sign.update_image(column, relation_sign, condition)
        relation_sign.significance.add(procedural_sign)
        if len(pred.signature) == 1:
            val, types = pred.signature[0]
            role_name = types[0].name + val
            if role_name not in signs:
                sign_image = SignImage([{signs[types[0].name]}])
                signs[role_name] = Sign(role_name, image=sign_image)
            procedural_sign.update_image(column, signs[role_name], condition)
            signs[role_name].significance.add(procedural_sign)
        elif len(pred.signature) == 2:
            val1, types1 = pred.signature[0]
            val2, types2 = pred.signature[1]
            role1_name = types1[0].name + val1
            role2_name = types2[0].name + val2
            if role1_name not in signs:
                sign_image = SignImage([{signs[types1[0].name]}])
                signs[role1_name] = Sign(role1_name, image=sign_image)
            relation_sign.update_image(0, signs[role1_name])
            signs[role1_name].significance.add(relation_sign)
            if role2_name not in signs:
                sign_image = SignImage([{signs[types2[0].name]}])
                signs[role2_name] = Sign(role2_name, image=sign_image)
            relation_sign.update_image(0, signs[role2_name], False)
            signs[role2_name].significance.add(relation_sign)
        else:
            logging.error('Not supported predicate {0}'.format(pred.name))


def _significance_from_abstracts(signs):
    for sign in signs.values():
        for parent in signs.values():
            if not sign == parent and not parent.is_action() and parent.is_absorbing(sign):
                sign.significance.add(parent)


def _define_situation(name, predicates, signs):
    situation = Sign(name)
    sit_meaning = SignImage([])
    for column, pred in enumerate(predicates):
        pred_sign = signs[pred.name]
        sit_meaning.update(column, signs[pred.name], True)
        if pred_sign.is_action():
            signs[pred.name].meaning[column] =SignImage(conditions=[{signs[pred.signature[0][0]]}],
                                                   effects=[{signs[pred.signature[1][0]]}])
        elif len(pred.signature) > 0:
            sit_meaning.update(column, signs[pred.signature[0][0]], True)

    situation.meaning[0] = sit_meaning
    return situation


def _get_statics(predicates, actions):
    """
    Determine all static predicates and return them as a list.

    We want to know the statics to avoid grounded actions with static
    preconditions violated. A static predicate is a predicate which
    doesn't occur in an effect of an action.
    """

    def get_effects(action):
        return action.effect.addlist | action.effect.dellist

    effects = [get_effects(action) for action in actions]
    effects = set(itertools.chain(*effects))

    def static(predicate):
        return not any(predicate.name == eff.name for eff in effects)

    statics = [pred.name for pred in predicates if static(pred)]
    return statics


def _create_type_map(objects):
    """
    Create a map from each type to its objects.

    For each object we know the type. This returns a dictionary
    from each type to a set of objects (of this type). We also
    have to care about type hierarchy. An object
    of a subtype is a specialization of a specific type. We have
    to put this object into the set of the supertype, too.
    """
    type_map = defaultdict(set)

    # for every type we append the corresponding object
    for object_name, object_type in objects.items():
        parent_type = object_type.parent
        while True:
            type_map[object_type].add(object_name)
            object_type, parent_type = parent_type, object_type.parent
            if parent_type is None:
                # if object_type is None:
                break

    # TODO sets in map should be ordered lists
    return type_map
