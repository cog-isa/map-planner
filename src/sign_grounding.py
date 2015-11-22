__author__ = 'Aleksandr'

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

    return Task(problem.name, signs, start_situation, goal_situation)


def _significance_from_actions(signs, actions):
    for action in actions:
        procedural_sign = signs[action.name]
        _significance_from_predicates(procedural_sign, signs, action.precondition)
        _significance_from_predicates(procedural_sign, signs, action.effect.addlist, False)


def _significance_from_predicates(procedural_sign, signs, predicates, condition=True):
    column = 0
    for pred in predicates:
        relation_sign = signs[pred.name]
        procedural_sign.update_image(column, relation_sign, condition)
        relation_sign.significance.add(procedural_sign)
        for val, tp in pred.signature:
            role_name = tp[0].name + val
            if role_name not in signs:
                sign_image = SignImage([{signs[tp[0].name]}])
                signs[role_name] = Sign(role_name, image=sign_image)
            procedural_sign.update_image(column, signs[role_name], condition)
            signs[role_name].significance.add(procedural_sign)
            column += 1
        if not pred.signature:
            column += 1


def _significance_from_abstracts(signs):
    for sign in signs.values():
        for parent in signs.values():
            if not sign == parent and not parent.is_action() and parent.is_absorbing(sign):
                sign.significance.add(parent)


def _define_situation(name, predicates, signs):
    situation = Sign(name)
    column = 0
    for pred in predicates:
        situation.update_image(column, signs[pred.name])
        for val, _ in pred.signature:
            situation.update_image(column, signs[val])
            column += 1
        if not pred.signature:
            column += 1
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
