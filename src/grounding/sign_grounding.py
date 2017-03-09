import logging
from collections import defaultdict

from grounding.semnet import Sign
from .sign_task import Task


def ground(problem, agent):
    domain = problem.domain
    actions = domain.actions.values()
    predicates = domain.predicates.values()
    constraints = problem.constraints


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
    obj_means = {}
    I_sign = Sign("I")
    They_sign = Sign("They")
    obj_means[I_sign] = I_sign.add_meaning()
    signs[I_sign.name] = I_sign
    obj_means[They_sign] = They_sign.add_meaning()
    signs[They_sign.name] = They_sign
    for obj in objects:
        obj_sign = Sign(obj)
        obj_signifs[obj] = obj_sign.add_significance()
        obj_means[obj] = obj_sign.add_meaning()
        signs[obj] = obj_sign
        if obj_sign.name == agent:
            connector = obj_means[obj].add_feature(obj_means[I_sign], zero_out=True)
            I_sign.add_out_meaning(connector)

    for tp, objects in type_map.items():
        tp_sign = Sign(tp.name)
        for obj in objects:
            obj_signif = obj_signifs[obj]
            obj_mean = obj_means[obj]
            tp_signif = tp_sign.add_significance()
            tp_mean = tp_sign.add_meaning()
            connector = tp_signif.add_feature(obj_signif, zero_out=True)
            signs[obj].add_out_significance(connector)
            connector = tp_mean.add_feature(obj_mean, zero_out=True)
            signs[obj].add_out_meaning(connector)
            if tp_sign.name == "agent" and not obj == agent:
                connector = obj_mean.add_feature(obj_means[They_sign], zero_out=True)
                They_sign.add_out_meaning(connector)
        signs[tp.name] = tp_sign

    for predicate in predicates:
        pred_sign = Sign(predicate.name)
        significance = pred_sign.add_significance()
        signs[predicate.name] = pred_sign
        if len(predicate.signature) == 2:
            def update_significance(fact, effect=False):
                role_name = fact[1][0].name + fact[0]
                if role_name not in signs:
                    signs[role_name] = Sign(role_name)
                role_sign = signs[role_name]
                obj_sign = signs[fact[1][0].name]
                role_signif = role_sign.add_significance()
                conn = role_signif.add_feature(obj_sign.significances[1], zero_out=True)
                obj_sign.add_out_significance(conn)
                conn = significance.add_feature(role_signif, effect=effect, zero_out=True)
                role_sign.add_out_significance(conn)
            def update_meanings(predicate, constraints):
                pred_sign = signs[predicate.name]
                meaning = pred_sign.add_meaning()
                for ag, preds in constraints.items():
                    if ag == agent:
                        for pred in preds:
                            for fact in pred.signature:
                                sign = signs[fact[0]]
                                obj_mean = obj_means[sign.name]
                                connector = meaning.add_feature(obj_mean, zero_out=True)
                                I_sign.add_out_meaning(connector)
                    else:
                        for pred in preds:
                            for fact in pred.signature:
                                sign = signs[fact[0]]
                                obj_mean = obj_means[sign.name]
                                connector = meaning.add_feature(obj_mean, zero_out=True)
                                They_sign.add_out_meaning(connector)


            update_significance(predicate.signature[0])
            update_significance(predicate.signature[1])
            if not predicate.signature[0][1][0].name == predicate.signature[1][1][0].name:
                update_meanings(predicate, constraints)




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
            elif not predicate.signature[0][1][0].name == predicate.signature[1][1][0].name:
                for fact in predicate.signature:
                    role_sign = signs[fact[1][0].name + fact[0]]
                    connector_new = act_signif.add_feature(role_sign.significances[1], connector.in_order, effect=effect,
                                                       zero_out=True)
                    role_sign.add_out_significance(connector_new)

        for predicate in action.precondition:
            update_significance(predicate)
        for predicate in action.effect.addlist:
            update_significance(predicate, effect=True)
        signs[action.name] = act_sign

    start_situation, pms = _define_situation('*start*', problem.initial_state, signs)
    goal_situation, pms = _define_situation('*finish*', problem.goal, signs)
    list_signs = task_signs(problem)
    _expand_situation_ma(goal_situation, signs, pms, list_signs)  # For task
    return Task(problem.name, signs, start_situation, goal_situation)

def task_signs(problem):
    signs= []
    above = []
    bottom = []
    for pred in problem.goal:
        if pred.name == "on":
            above.append(pred.signature[0][0])
            bottom.append(pred.signature[1][0])
    signs.append(list(set(above) - set(bottom))[0])
    signs.append(list(set(bottom) - set(above))[0])
    return signs

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

    return situation, elements

def _expand_situation_ma(goal_situation, signs, pms, list_signs):
    ont_mean = signs['ontable'].add_meaning()
    a_mean = pms[signs[list_signs[1]]]
    connector = goal_situation.meanings[1].add_feature(ont_mean)
    conn = goal_situation.meanings[1].add_feature(a_mean, connector.in_order)
    signs['ontable'].add_out_meaning(conn)
    signs[list_signs[1]].add_out_meaning(conn)
    cl_mean = signs['clear'].add_meaning()
    d_mean = pms[signs[list_signs[0]]]
    connector = goal_situation.meanings[1].add_feature(cl_mean)
    conn = goal_situation.meanings[1].add_feature(d_mean, connector.in_order)
    signs['clear'].add_out_meaning(conn)
    signs[list_signs[0]].add_out_meaning(conn)

def _expand_situation1(goal_situation, signs, pms, list_signs):
    h_mean = signs['handempty'].add_meaning()
    connector = goal_situation.meanings[1].add_feature(h_mean)
    signs['handempty'].add_out_meaning(connector)
    ont_mean = signs['ontable'].add_meaning()
    a_mean = pms[signs['a']]
    connector = goal_situation.meanings[1].add_feature(ont_mean)
    conn = goal_situation.meanings[1].add_feature(a_mean, connector.in_order)
    signs['ontable'].add_out_meaning(conn)
    signs['a'].add_out_meaning(conn)
    cl_mean = signs['clear'].add_meaning()
    d_mean = pms[signs['d']]
    connector = goal_situation.meanings[1].add_feature(cl_mean)
    conn = goal_situation.meanings[1].add_feature(d_mean, connector.in_order)
    signs['clear'].add_out_meaning(conn)
    signs['d'].add_out_meaning(conn)

#todO remake to MA-pddl
def _expand_situation(goal_situation, signs, pms, list_signs):
    h_mean = signs['handempty'].add_meaning()
    conn = goal_situation.meanings[1].add_feature(h_mean)
    signs['handempty'].add_out_meaning(conn)

    ont_mean = signs['ontable'].add_meaning()
    sign_ont_mean = pms[signs[list_signs[1]]]
    conn = goal_situation.meanings[1].add_feature(ont_mean)
    conn_ont_sign = goal_situation.meanings[1].add_feature(sign_ont_mean, conn.in_order)
    signs['ontable'].add_out_meaning(conn)
    signs[list_signs[1]].add_out_meaning(conn_ont_sign)

    cl_mean = signs['clear'].add_meaning()
    sign_cl_mean = pms[signs[list_signs[0]]]
    conn = goal_situation.meanings[1].add_feature(cl_mean)
    conn_cl = goal_situation.meanings[1].add_feature(sign_cl_mean, conn.in_order)
    signs['clear'].add_out_meaning(conn)
    signs[list_signs[0]].add_out_meaning(conn_cl)

def _expand_situation2(goal_situation, signs, pms):
    h_mean = signs['handempty'].add_meaning()
    conn = goal_situation.meanings[1].add_feature(h_mean)
    signs['handempty'].add_out_meaning(conn)

    ont_mean = signs['ontable'].add_meaning()
    b_mean = pms[signs['b']]
    conn = goal_situation.meanings[1].add_feature(ont_mean)
    connb = goal_situation.meanings[1].add_feature(b_mean, conn.in_order)
    signs['ontable'].add_out_meaning(conn)
    signs['b'].add_out_meaning(connb)

    cl_mean = signs['clear'].add_meaning()
    d_mean = pms[signs['d']]
    conn = goal_situation.meanings[1].add_feature(cl_mean)
    connd = goal_situation.meanings[1].add_feature(d_mean, conn.in_order)
    signs['clear'].add_out_meaning(conn)
    signs['d'].add_out_meaning(connd)

def _expand_situation3(goal_situation, signs, pms):
    h_mean = signs['handempty'].add_meaning()
    conn = goal_situation.meanings[1].add_feature(h_mean)
    signs['handempty'].add_out_meaning(conn)

    ont_mean = signs['ontable'].add_meaning()
    d_mean = pms[signs['d']]
    conn = goal_situation.meanings[1].add_feature(ont_mean)
    connb = goal_situation.meanings[1].add_feature(d_mean, conn.in_order)
    signs['ontable'].add_out_meaning(conn)
    signs['b'].add_out_meaning(connb)

    cl_mean = signs['clear'].add_meaning()
    a_mean = pms[signs['a']]
    conn = goal_situation.meanings[1].add_feature(cl_mean)
    connd = goal_situation.meanings[1].add_feature(a_mean, conn.in_order)
    signs['clear'].add_out_meaning(conn)
    signs['a'].add_out_meaning(connd)

