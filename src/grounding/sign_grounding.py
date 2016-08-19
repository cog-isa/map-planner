import itertools
import logging
from collections import defaultdict

from grounding.semnet import Sign
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
    signs = {}
    for obj in objects:
        obj_sign = Sign(obj)
        obj_sign.add_significance()
        signs[obj] = obj_sign
    for tp, objects in type_map.items():
        tp_sign = Sign(tp.name)
        for obj in objects:
            obj_sign = signs[obj]
            tp_signif, _ = tp_sign.add_significance()
            index = tp_signif.add_feature((obj_sign, 0))
            obj_sign.add_out_significance(tp_signif, index)
        signs[tp.name] = tp_sign

    for predicate in predicates:
        pred_sign = Sign(predicate.name)
        if len(predicate.signature) == 2:  # on(block?x, block?y)
            significance, _ = pred_sign.add_significance()

            def update_significance(fact, effect=False):
                role_name = fact[1][0].name + fact[0]  # (?x, (block,))
                if role_name not in signs:
                    signs[role_name] = Sign(role_name)
                role_sign = signs[role_name]
                obj_sign = signs[fact[1][0].name]
                role_signif, _ = role_sign.add_significance()
                idx1 = role_signif.add_feature((obj_sign, 0))
                obj_sign.add_out_significance(role_signif, idx1)
                idx2 = significance.add_feature((role_sign, 0), effect=effect)
                role_sign.add_out_significance(significance, idx2)

            update_significance(predicate.signature[0])
            update_significance(predicate.signature[1])

        signs[predicate.name] = pred_sign

    for action in actions:
        act_sign = Sign(action.name)
        act_signif, _ = act_sign.add_significance()

        def update_significance(predicate, effect=False):
            pred_sign = signs[predicate.name]
            idx = act_signif.add_feature((pred_sign, 0), effect=effect)
            pred_sign.add_out_significance(act_signif, idx)
            if len(predicate.signature) == 1:
                fact = predicate.signature[0]
                role_sign = signs[fact[1][0].name + fact[0]]
                idxr = act_signif.add_feature((role_sign, 0), idx, effect=effect)
                role_sign.add_out_significance(act_signif, idxr)

        for predicate in action.precondition:
            update_significance(predicate)
        for predicate in action.effect.addlist:
            update_significance(predicate, effect=True)
        signs[action.name] = act_sign

    start_situation = _define_situation('*start*', problem.initial_state, signs)
    goal_situation = _define_situation('*finish*', problem.goal, signs)

    _expand_situation1(goal_situation, signs)  # For task
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
    sit_meaning, _ = situation.add_meaning()
    for predicate in predicates:
        pred_sign = signs[predicate.name]
        pred_meaning, pred_conn = pred_sign.add_meaning()
        idx = sit_meaning.add_feature((pred_sign, pred_conn))
        pred_sign.add_out_meaning(sit_meaning, idx)
        if len(predicate.signature) == 1:
            sig_sign = signs[predicate.signature[0][0]]
            _, sig_conn = sig_sign.add_meaning()
            idxs = sit_meaning.add_feature((sig_sign, sig_conn), idx)
            sig_sign.add_out_meaning(sit_meaning, idxs)
        elif len(predicate.signature) > 1:
            for fact in predicate.signature:
                fact_sign = signs[fact[0]]
                _, fact_conn = fact_sign.add_meaning()
                idxf = pred_meaning.add_feature((fact_sign, fact_conn))
                fact_sign.add_out_meaning(pred_meaning, idxf)

    return situation


def _expand_situation1(goal_situation, signs):
    _, conn1 = signs['handempty'].add_meaning()
    id1 = goal_situation.meanings[0].add_feature((signs['handempty'], conn1))
    signs['handempty'].add_out_meaning(goal_situation.meanings[0], id1)

    _, conn2 = signs['ontable'].add_meaning()
    _, conn3 = signs['a'].add_meaning()
    id2 = goal_situation.meanings[0].add_feature((signs['ontable'], conn2))
    goal_situation.meanings[0].add_feature((signs['a'], conn3), id2)
    signs['ontable'].add_out_meaning(goal_situation.meanings[0], id2)
    signs['a'].add_out_meaning(goal_situation.meanings[0], id2)

    _, conn4 = signs['clear'].add_meaning()
    _, conn5 = signs['d'].add_meaning()
    id4 = goal_situation.meanings[0].add_feature((signs['clear'], conn4))
    goal_situation.meanings[0].add_feature((signs['d'], conn5), id4)
    signs['clear'].add_out_meaning(goal_situation.meanings[0], id4)
    signs['d'].add_out_meaning(goal_situation.meanings[0], id4)


def _expand_situation2(goal_situation, signs):
    _, conn1 = signs['handempty'].add_meaning()
    id1 = goal_situation.meanings[0].add_feature((signs['handempty'], conn1))
    signs['handempty'].add_out_meaning(goal_situation.meanings[0], id1)

    _, conn2 = signs['ontable'].add_meaning()
    _, conn3 = signs['b'].add_meaning()
    id2 = goal_situation.meanings[0].add_feature((signs['ontable'], conn2))
    goal_situation.meanings[0].add_feature((signs['b'], conn3), id2)
    signs['ontable'].add_out_meaning(goal_situation.meanings[0], id2)
    signs['b'].add_out_meaning(goal_situation.meanings[0], id2)

    _, conn4 = signs['clear'].add_meaning()
    _, conn5 = signs['d'].add_meaning()
    id4 = goal_situation.meanings[0].add_feature((signs['clear'], conn4))
    goal_situation.meanings[0].add_feature((signs['d'], conn5), id4)
    signs['clear'].add_out_meaning(goal_situation.meanings[0], id4)
    signs['d'].add_out_meaning(goal_situation.meanings[0], id4)
