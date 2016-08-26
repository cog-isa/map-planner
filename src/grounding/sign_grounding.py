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

    # Create a map from types to objects
    type_map = _create_type_map(objects)
    logging.debug("Type to object map:\n%s" % type_map)

    # Sign world model
    signs = {}
    obj_signifs = {}
    for obj in objects:
        obj_sign = Sign(obj)
        obj_signifs[obj] = obj_sign.add_significance()
        signs[obj] = obj_sign
    for tp, objects in type_map.items():
        tp_sign = Sign(tp.name)
        for obj in objects:
            obj_signif = obj_signifs[obj]
            tp_signif = tp_sign.add_significance()
            connector = tp_signif.add_feature(obj_signif, zero_out=True)
            signs[obj].add_out_significance(connector)
        signs[tp.name] = tp_sign

    for predicate in predicates:
        pred_sign = Sign(predicate.name)
        significance = pred_sign.add_significance()
        if len(predicate.signature) == 2:  # on(block?x, block?y)
            def update_significance(fact, effect=False):
                role_name = fact[1][0].name + fact[0]  # (?x, (block,))
                if role_name not in signs:
                    signs[role_name] = Sign(role_name)
                role_sign = signs[role_name]
                obj_sign = signs[fact[1][0].name]
                role_signif = role_sign.add_significance()
                conn = role_signif.add_feature(obj_sign.significances[1], zero_out=True)
                obj_sign.add_out_significance(conn)
                conn = significance.add_feature(role_signif, effect=effect, zero_out=True)
                role_sign.add_out_significance(conn)

            update_significance(predicate.signature[0])
            update_significance(predicate.signature[1])

        signs[predicate.name] = pred_sign

    for action in actions:
        act_sign = Sign(action.name)
        act_signif = act_sign.add_significance()

        def update_significance(predicate, effect=False):
            pred_sign = signs[predicate.name]
            connector = act_signif.add_feature(pred_sign.significances[1], effect=effect)
            pred_sign.add_out_significance(connector)
            if len(predicate.signature) == 1:
                fact = predicate.signature[0]
                role_sign = signs[fact[1][0].name + fact[0]]
                conn = act_signif.add_feature(role_sign.significances[1], connector.in_order, effect=effect,
                                              zero_out=True)
                role_sign.add_out_significance(conn)

        for predicate in action.precondition:
            update_significance(predicate)
        for predicate in action.effect.addlist:
            update_significance(predicate, effect=True)
        signs[action.name] = act_sign

    start_situation = _define_situation('*start*', problem.initial_state, signs)
    goal_situation = _define_situation('*finish*', problem.goal, signs)

    _expand_situation1(goal_situation, signs)  # For task
    return Task(problem.name, signs, start_situation, goal_situation)


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
    sit_meaning = situation.add_meaning()
    elements = {}

    def get_or_add(sign):
        if sign not in elements:
            meaning = sign.add_meaning()
            elements[sign] = meaning
        return elements.get(sign)

    for predicate in predicates:
        pred_sign = signs[predicate.name]
        pred_meaning = pred_sign.add_meaning()
        connector = sit_meaning.add_feature(pred_meaning)
        pred_sign.add_out_meaning(connector)
        if len(predicate.signature) == 1:
            sig_sign = signs[predicate.signature[0][0]]
            sig_meaning = get_or_add(sig_sign)
            conn = sit_meaning.add_feature(sig_meaning, connector.in_order)
            sig_sign.add_out_meaning(conn)
        elif len(predicate.signature) > 1:
            for fact in predicate.signature:
                fact_sign = signs[fact[0]]
                fact_meaning = get_or_add(fact_sign)
                conn = pred_meaning.add_feature(fact_meaning)
                fact_sign.add_out_meaning(conn)

    return situation


def _expand_situation1(goal_situation, signs):
    h_mean = signs['handempty'].add_meaning()
    connector = goal_situation.meanings[1].add_feature(h_mean)
    signs['handempty'].add_out_meaning(connector)

    ont_mean = signs['ontable'].add_meaning()
    a_mean = signs['a'].add_meaning()
    connector = goal_situation.meanings[1].add_feature(ont_mean)
    conn = goal_situation.meanings[1].add_feature(a_mean, connector.in_order)
    signs['ontable'].add_out_meaning(conn)
    signs['a'].add_out_meaning(conn)

    cl_mean = signs['clear'].add_meaning()
    d_mean = signs['d'].add_meaning()
    connector = goal_situation.meanings[1].add_feature(cl_mean)
    conn = goal_situation.meanings[1].add_feature(d_mean, connector.in_order)
    signs['clear'].add_out_meaning(conn)
    signs['d'].add_out_meaning(conn)


def _expand_situation2(goal_situation, signs):
    h_mean = signs['handempty'].add_meaning()
    conn = goal_situation.meanings[1].add_feature(h_mean)
    signs['handempty'].add_out_meaning(conn)

    ont_mean = signs['ontable'].add_meaning()
    b_mean = signs['b'].add_meaning()
    conn = goal_situation.meanings[1].add_feature(ont_mean)
    connb = goal_situation.meanings[1].add_feature(b_mean, conn.in_order)
    signs['ontable'].add_out_meaning(conn)
    signs['b'].add_out_meaning(connb)

    cl_mean = signs['clear'].add_meaning()
    d_mean = signs['d'].add_meaning()
    conn = goal_situation.meanings[1].add_feature(cl_mean)
    connd = goal_situation.meanings[1].add_feature(d_mean, conn.in_order)
    signs['clear'].add_out_meaning(conn)
    signs['d'].add_out_meaning(connd)
