import itertools
import logging
from collections import defaultdict

from semnet import Sign, PredictionMatrix
from .sign_task import Task


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
    signs = {obj: Sign(obj) for obj in objects}
    for tp, objects in type_map.items():
        sign = Sign(tp.name)
        for obj in objects:
            sign.significances[0].add_feature(signs[obj].significances[0])
        signs[tp.name] = sign

    for predicate in predicates:
        pred_sign = Sign(predicate.name)
        for signature in predicate.signature:
            role_name = signature[1][0].name + signature[0]  # (?x, (block,))
            if role_name not in signs:
                signs[role_name] = Sign(role_name)
                signs[role_name].significances[0].add_feature(signs[signature[1][0].name].significances[0])
            pred_sign.significances[0].add_feature(signs[role_name].significances[0])
        signs[predicate.name] = pred_sign

    # TODO: if signature in action is different from signature in predicate declaration
    for action in actions:
        signs[action.name] = Sign(action.name)
        for predicate in action.precondition:
            signs[action.name].significances[0].add_feature(signs[predicate.name].significances[0])
        for predicate in action.effect.addlist:
            signs[action.name].significances[0].add_feature(signs[predicate.name].significances[0], effect=True)

    start_situation = _define_situation('*start*', problem.initial_state, signs)
    goal_situation = _define_situation('*finish*', problem.goal, signs)

    # _expand_situation1(goal_situation, signs)  # For task
    return Task(problem.name, signs, start_situation, goal_situation)


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


def _define_situation(name, predicates, signs):
    situation = Sign(name)
    for predicate in predicates:
        pred_meaning = signs[predicate.name].get_new_meaning()
        situation.meanings[0].add_feature(pred_meaning)
        for signature in predicate.signature:
            sig_meaning = signs[signature[0]].get_new_meaning()
            pred_meaning.add_feature(sig_meaning)

    return situation

# def _expand_situation1(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['a'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['a'].meaning) - 1, signs['a']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['d'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['d'].meaning) - 1, signs['d']), column_index=column)

# def _expand_situation2(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['b'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['b'].meaning) - 1, signs['b']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['d'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['d'].meaning) - 1, signs['d']), column_index=column)
#
#
# def _expand_situation3(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['d'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['d'].meaning) - 1, signs['d']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['a'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['a'].meaning) - 1, signs['a']), column_index=column)
#
#
# def _expand_situation4(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['c'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['c'].meaning) - 1, signs['c']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['a'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['a'].meaning) - 1, signs['a']), column_index=column)
#
#
# def _expand_situation5(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['e'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['e'].meaning) - 1, signs['e']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['d'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['d'].meaning) - 1, signs['d']), column_index=column)
#
#
# def _expand_situation6(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['a'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['a'].meaning) - 1, signs['a']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['d'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['d'].meaning) - 1, signs['d']), column_index=column)
#
#
# def _expand_situation7(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['d'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['d'].meaning) - 1, signs['d']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['c'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['c'].meaning) - 1, signs['c']), column_index=column)
#
#
# def _expand_situation8(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['d'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['d'].meaning) - 1, signs['d']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['e'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['e'].meaning) - 1, signs['e']), column_index=column)
#
#
# def _expand_situation9(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['d'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['d'].meaning) - 1, signs['d']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['e'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['e'].meaning) - 1, signs['e']), column_index=column)
#
#
# def _expand_situation10(goal_situation, signs):
#     # TODO: add common approach
#     signs['handempty'].meaning.append(NetworkFragment([]))
#     goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))
#
#     signs['ontable'].meaning.append(NetworkFragment([]))
#     signs['e'].meaning.append(NetworkFragment([]))
#
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['e'].meaning) - 1, signs['e']), column_index=column)
#
#     signs['clear'].meaning.append(NetworkFragment([]))
#     signs['a'].meaning.append(NetworkFragment([]))
#     column = len(goal_situation.meaning[0].left)
#     goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
#     goal_situation.meaning[0].add((len(signs['a'].meaning) - 1, signs['a']), column_index=column)
#
