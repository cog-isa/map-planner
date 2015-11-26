import logging
import itertools
from collections import defaultdict
from sign_task import NetworkFragment, Sign, Task


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
            sign.images[0].add((0, signs[obj]))
        signs[tp.name] = sign

    for predicate in predicates:
        signs[predicate.name] = Sign(predicate.name)

    _significance_from_actions(signs, actions)
    _significance_from_abstracts(signs)

    start_situation = _define_situation('*start*', problem.initial_state, signs)
    goal_situation = _define_situation('*finish*', problem.goal, signs)

    _expand_situation(goal_situation, signs)
    return Task(problem.name, signs, start_situation, goal_situation)


def _significance_from_actions(signs, actions):
    for action in actions:
        procedural_sign = signs[action.name]
        _significance_from_predicates(procedural_sign, signs, action.precondition)
        _significance_from_predicates(procedural_sign, signs, action.effect.addlist, False)


def _significance_from_predicates(procedural_sign, signs, predicates, not_delayed=True):
    # TODO: not only for first images
    for column, predicate in enumerate(predicates):
        def add_to_significance(sig_to_update, without_delay, signature):
            role_name = signature[1][0].name + signature[0]
            if role_name not in signs:
                sign_image = NetworkFragment([{(0, signs[signature[1][0].name])}])
                signs[role_name] = Sign(role_name, image=sign_image)
            sig_to_update.images[0].add((0, signs[role_name]), without_delay, column)
            signs[role_name].significance[0].add((0, sig_to_update))

        predicate_sign = signs[predicate.name]
        procedural_sign.images[0].add((0, predicate_sign), not_delayed, column)
        predicate_sign.significance[0].add((0, procedural_sign))

        if len(predicate.signature) == 1:
            add_to_significance(procedural_sign, not_delayed, predicate.signature[0])
        elif len(predicate.signature) == 2 and predicate_sign.images[0].is_empty():
            add_to_significance(predicate_sign, True, predicate.signature[0])
            add_to_significance(predicate_sign, False, predicate.signature[1])
        else:
            logging.error('Not supported predicate {0}'.format(predicate.name))


def _significance_from_abstracts(signs):
    for sign in signs.values():
        for parent in signs.values():
            if not sign == parent and not parent.is_action() and sign in parent:
                sign.significance[0].add((0, parent))


def _define_situation(name, predicates, signs):
    # TODO: define meanings with recursion
    situation = Sign(name)
    situation.meaning.append(NetworkFragment([]))
    for column, predicate in enumerate(predicates):
        if len(predicate.signature) == 1:
            sign1 = signs[predicate.signature[0][0]]
            sign1.meaning.append(sign1.images[0].copy())
            situation.meaning[0].add((len(sign1.meaning) - 1, sign1), column_index=column)
        if len(predicate.signature) == 2:
            sign1 = signs[predicate.signature[0][0]]
            sign1.meaning.append(sign1.images[0].copy())
            sign2 = signs[predicate.signature[1][0]]
            sign2.meaning.append(sign2.images[0].copy())
            fragment = NetworkFragment([])
            fragment.add((len(sign1.meaning), sign1))
            fragment.add((len(sign2.meaning), sign2), False)
            signs[predicate.name].meaning.append(fragment)
        else:
            signs[predicate.name].meaning.append(NetworkFragment([])
                                                 )
        situation.meaning[0].add((len(signs[predicate.name].meaning) - 1, signs[predicate.name]),
                                 column_index=column)

    return situation


def _expand_situation(goal_situation, signs):
    # TODO: add common approach
    signs['handempty'].meaning.append(NetworkFragment([]))
    goal_situation.meaning[0].add((len(signs['handempty'].meaning) - 1, signs['handempty']))

    signs['ontable'].meaning.append(NetworkFragment([]))
    signs['a'].meaning.append(NetworkFragment([]))
    column = len(goal_situation.meaning[0].left)
    goal_situation.meaning[0].add((len(signs['ontable'].meaning) - 1, signs['ontable']), column_index=column)
    goal_situation.meaning[0].add((len(signs['a'].meaning) - 1, signs['a']), column_index=column)

    signs['clear'].meaning.append(NetworkFragment([]))
    signs['d'].meaning.append(NetworkFragment([]))
    column = len(goal_situation.meaning[0].left)
    goal_situation.meaning[0].add((len(signs['clear'].meaning) - 1, signs['clear']), column_index=column)
    goal_situation.meaning[0].add((len(signs['d'].meaning) - 1, signs['d']), column_index=column)


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
