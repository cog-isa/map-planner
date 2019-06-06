import logging
from collections import defaultdict

import itertools
from mapcore.grounding.semnet import Sign
from mapcore.grounding.sign_task import Task


def ground(problem, agent, exp_signs=None):
    domain = problem.domain
    actions = domain.actions.values()
    predicates = domain.predicates.values()

    # Objects
    objects = problem.objects
    objects.update(domain.constants)
    logging.debug('Objects:\n%s' % objects)

    # Remove old type_map
    if exp_signs:
        objects = _update_exp_signs(exp_signs, objects)

    # Create a map from types to objects
    type_map = _create_type_map(objects)
    logging.debug("Type to object map:\n%s" % type_map)

    # Create type subtype map
    subtype_map = _create_subtype(domain.types)

    obj_signifs = {}
    obj_means = {}

    # Check logic in exp
    if exp_signs:
        signs = exp_signs
        I_sign = signs['I']
        obj_means[I_sign] = I_sign.meanings[1]
        obj_signifs[I_sign] = I_sign.significances[1]
    else:
        signs = {}
        I_sign = Sign("I")
        obj_means[I_sign] = I_sign.add_meaning()
        obj_signifs[I_sign] = I_sign.add_significance()
        signs[I_sign.name] = I_sign

    for obj in objects:
        obj_sign = Sign(obj)
        obj_signifs[obj] = obj_sign.add_significance()
        signs[obj] = obj_sign
        if obj_sign.name == agent:
            connector = obj_signifs[obj].add_feature(obj_signifs[I_sign], zero_out=True)
            I_sign.add_out_significance(connector)

    for tp, objects in type_map.items():
        if exp_signs:
            tp_sign = signs[tp.name]
        else:
            tp_sign = Sign(tp.name)
        for obj in objects:
            obj_signif = obj_signifs[obj]
            tp_signif = tp_sign.add_significance()
            connector = tp_signif.add_feature(obj_signif, zero_out=True)
            signs[obj].add_out_significance(connector)
        if not exp_signs:
            signs[tp.name] = tp_sign

    if not exp_signs:
        updated_predicates = _update_predicates(predicates, actions)
        signify_predicates(predicates, updated_predicates, signs, subtype_map)
        signify_actions(actions, signs, obj_means)

    start_situation, pms = _define_situation('*start*', problem.initial_state, signs, 'image')
    goal_situation, pms = _define_situation('*finish*', problem.goal, signs, 'image')
    if problem.name.startswith("blocks"):
        list_signs = task_signs(problem)
        _expand_situation_ma_blocks(goal_situation, signs, pms, list_signs)  # For task
    elif problem.name.startswith("logistics"):
        _expand_situation_ma_logistics(goal_situation, signs, pms)
    return Task(problem.name, signs, start_situation, goal_situation)


def signify_predicates(predicates, updated_predicates, signs, subtype_map):
    for predicate in predicates:
        pred_sign = Sign(predicate.name)
        signs[predicate.name] = pred_sign
        if len(predicate.signature) == 2:
            signifs = []

            def update_significance(fact, predicate, subtype_map, updated_predicates, effect=False):
                role_name = fact[1][0].name + fact[0]
                fact_name = fact[1][0].name
                roles = []
                roles.append(role_name)
                role_signifs = []
                subroles = []
                if role_name not in signs:
                    signs[role_name] = Sign(role_name)
                if fact_name in subtype_map.keys():
                    subroles = subtype_map[fact_name]
                    for role, signif in subtype_map.items():
                        if fact_name in signif:
                            for srole in subroles:
                                srole_name = role + "?" + srole
                                signs[srole_name] = Sign(srole_name)
                                if not srole_name in roles:
                                    roles.append(srole_name)
                                sfact_name = fact_name + "?" + srole
                                signs[sfact_name] = Sign(sfact_name)
                                if not sfact_name in roles:
                                    roles.append(sfact_name)
                used_facts = set()
                for updated_fact in updated_predicates[pred_sign.name]:
                    updated_fact_name = updated_fact[1][0].name
                    updated_fact_role = updated_fact[1][0].name + updated_fact[0]
                    predicate_names = [signa[1][0].name for signa in predicate.signature]
                    if fact_name == updated_fact_name:
                        srole_name = updated_fact_role
                        used_facts.add(updated_fact[0][1:])
                        if srole_name not in signs:
                            signs[srole_name] = Sign(srole_name)
                        if not srole_name in roles:
                            roles.append(srole_name)
                    elif fact[0] == updated_fact[0]:
                        srole_name = updated_fact_role
                        used_facts.add(updated_fact_name)
                        if srole_name not in signs:
                            signs[srole_name] = Sign(srole_name)
                        if not srole_name in roles:
                            roles.append(srole_name)
                    elif updated_fact_name in subtype_map[fact_name] and not updated_fact_name in predicate_names:
                        srole_name = updated_fact_role
                        used_facts.add(updated_fact_name)
                        if srole_name not in signs:
                            signs[srole_name] = Sign(srole_name)
                        if not srole_name in roles:
                            roles.append(srole_name)
                for role_name in roles:
                    role_sign = signs[role_name]
                    obj_sign = signs[fact_name]
                    spec_sign = None
                    if obj_sign.name in role_sign.name:
                            spec_sign = role_sign.name[len(obj_sign.name)+1 : ]
                    smaller_roles = []
                    if spec_sign and subroles:
                        for srole in subroles:
                            if spec_sign in srole:
                                smaller_roles.append(srole)
                    if not smaller_roles and spec_sign:
                        smaller_roles = [obj for obj in used_facts if spec_sign in obj and obj in signs]
                    if smaller_roles:
                        for obj in smaller_roles:
                            updated_obj_sign = signs[obj]
                            if not obj_sign == updated_obj_sign:
                                role_signif = role_sign.add_significance()
                                connector = role_signif.add_feature(updated_obj_sign.significances[1], zero_out=True)
                                updated_obj_sign.add_out_significance(connector)
                                role_signifs.append(role_signif)
                            else:
                                role_signif = role_sign.add_significance()
                                conn = role_signif.add_feature(obj_sign.significances[1], zero_out=True)
                                obj_sign.add_out_significance(conn)
                                role_signifs.append(role_signif)
                    else:
                        role_signif = role_sign.add_significance()
                        conn = role_signif.add_feature(obj_sign.significances[1], zero_out=True)
                        obj_sign.add_out_significance(conn)
                        role_signifs.append(role_signif)

                if not signifs:
                    signifs.extend(role_signifs)
                else:
                    role_signs = [cm.sign for cm in role_signifs]
                    if signifs[0].sign in role_signs and signifs[1].sign in role_signs:
                        significance = pred_sign.add_significance()
                        conn = significance.add_feature(signifs[0], effect=False, zero_out=True)
                        signifs[0].sign.add_out_significance(conn)
                        connector = significance.add_feature(signifs[1], effect=effect, zero_out=True)
                        signifs[1].sign.add_out_significance(connector)
                    else:
                        for pair in itertools.product(signifs, role_signifs):
                            significance = pred_sign.add_significance()
                            conn = significance.add_feature(pair[0], effect=False, zero_out=True)
                            pair[0].sign.add_out_significance(conn)
                            connector = significance.add_feature(pair[1], effect=effect, zero_out=True)
                            pair[1].sign.add_out_significance(connector)

            update_significance(predicate.signature[0], predicate, subtype_map, updated_predicates)
            update_significance(predicate.signature[1], predicate, subtype_map, updated_predicates)
        elif len(predicate.signature):
            pred_sign.add_significance()


def signify_actions(actions, signs, obj_means):
    for action in actions:
        act_sign = Sign(action.name)
        act_signif = act_sign.add_significance()

        def update_significance(predicate, signature, effect=False):
            pred_sign = signs[predicate.name]
            if len(pred_sign.significances) > 1:
                pred_cm = pred_resonate('significance', pred_sign, predicate, signs, signature)
            elif len(pred_sign.significances) == 0:
                pred_cm = pred_sign.add_significance()
            else:
                pred_cm = pred_sign.significances[1]
            connector = act_signif.add_feature(pred_cm, effect=effect)
            pred_sign.add_out_significance(connector)
            if len(predicate.signature) == 1:
                fact = predicate.signature[0]
                role_sign = signs[fact[1][0].name + fact[0]]
                conn = act_signif.add_feature(role_sign.significances[1], connector.in_order, effect=effect,
                                              zero_out=True)
                role_sign.add_out_significance(conn)
            elif not len(predicate.signature) == 0:
                if not predicate.signature[0][1][0].name == predicate.signature[1][1][0].name:
                    for role_sign in pred_cm.get_signs():
                        connector_new = act_signif.add_feature(role_sign.significances[1], connector.in_order,
                                                               effect=effect,
                                                               zero_out=True)
                        role_sign.add_out_significance(connector_new)

        for predicate in action.precondition:
            update_significance(predicate,  action.signature, False)
        for predicate in action.effect.addlist:
            update_significance(predicate, action.signature, True)
        signs[action.name] = act_sign
        I_sign = signs['I']
        act_meaning= act_signif.copy('significance', 'meaning')
        connector = act_meaning.add_feature(obj_means[I_sign])
        efconnector = act_meaning.add_feature(obj_means[I_sign], effect=True)
        I_sign.add_out_meaning(connector)


def pred_resonate(base, sign, predicate, signs, signature):
    cms = getattr(sign, base + 's')
    roles = []
    for fact in predicate.signature:
        sfact = [signa for signa in signature if fact[0] == signa[0]]
        if sfact:
            if sfact[0][1][0].name+sfact[0][0] in signs:
                roles.extend(sfact)
        else:
            roles.append(fact)
    roles = [signs[signa[1][0].name + signa[0]] for signa in roles]
    for index, cm in cms.items():
        if not len(cm.cause) + len(cm.effect) == len(predicate.signature):
            continue
        cm_signs = cm.get_signs()
        for role in roles:
            if not role in cm_signs:
                break
        else:
            return cm
    return None

def _update_predicates(predicates, actions):
    predicates = {pred.name: set(pred.signature) for pred in predicates}
    for action in actions:
        actions_predicates = action.precondition.copy()
        actions_predicates.extend([pred for pred in action.effect.addlist.copy()])
        for predicate in actions_predicates:
            predicates[predicate.name] |= set(predicate.signature)
            for fact in predicate.signature:
                for action_fact in action.signature:
                    if fact[0] == action_fact[0] and fact in predicates[predicate.name]:
                        predicates[predicate.name].add(action_fact)

    return predicates


def task_signs(problem):
    signs = []
    above = []
    bottom = []
    for pred in problem.goal:
        if pred.name == "on":
            above.append(pred.signature[0][0])
            bottom.append(pred.signature[1][0])
    signs.append(list(set(above) - set(bottom))[0])
    signs.append(list(set(bottom) - set(above))[0])
    return signs


def _update_exp_signs(signs, objects):
    for obj, type in list(objects.items()).copy():
        if signs.get(obj):
            try:
                objects.pop(obj)
            except KeyError:
                break

    return objects


def _create_subtype(types):
    """
    Create a map of types/subtypes to make true role signs
    """
    subtype_map = defaultdict(set)

    for object_name, object_type in types.items():
        parent_type = object_type.parent
        if parent_type:
            subtype_map[parent_type.name].add(object_type.name)
    return subtype_map


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


def _define_situation(name, predicates, signs, network = 'image'):
    situation = Sign(name)
    sit_cm = getattr(situation, 'add_'+network)()
    elements = {}

    def get_or_add(sign):
        if sign not in elements:
            cm = getattr(sign, 'add_'+network)()
            elements[sign] = cm
        return elements.get(sign)

    for predicate in predicates:
        pred_sign = signs[predicate.name]
        pred_cm = getattr(pred_sign, 'add_'+network)()
        connector = sit_cm.add_feature(pred_cm)
        getattr(pred_sign, 'add_out_'+network)(connector)
        if len(predicate.signature) == 1:
            sig_sign = signs[predicate.signature[0][0]]
            sig_cm = get_or_add(sig_sign)
            conn = sit_cm.add_feature(sig_cm, connector.in_order)
            getattr(sig_sign, 'add_out_' + network)(conn)
        elif len(predicate.signature) > 1:
            pre_signs = set()
            for fact in predicate.signature:
                role_signs = [con.in_sign for con in getattr(signs[fact[0]], 'out_significances') if con.in_sign.name != 'object']
                for el in role_signs:
                    if el.significances:
                        if len(el.significances[1].cause) == 1 and len(el.significances[1].effect) == 0:
                            pre_signs.add(el)
            if len(pre_signs) < len(predicate.signature):
                for fact in predicate.signature:
                    fact_sign = signs[fact[0]]
                    fact_cm = get_or_add(fact_sign)
                    conn = pred_cm.add_feature(fact_cm)
                    getattr(fact_sign, 'add_out_' + network)(conn)
            else:
                for fact in predicate.signature:
                    fact_sign = signs[fact[0]]
                    fact_image = get_or_add(fact_sign)
                    conn = sit_cm.add_feature(fact_image, connector.in_order)
                    getattr(fact_sign, 'add_out_' + network)(conn)
                    conn = pred_cm.add_feature(fact_image)
                    getattr(fact_sign, 'add_out_' + network)(conn)

    return situation, elements


def _expand_situation_ma_blocks(goal_situation, signs, pms, list_signs):
    ont_image = signs['ontable'].add_image()
    a_image = pms[signs[list_signs[1]]]
    connector = goal_situation.images[1].add_feature(ont_image)
    conn = goal_situation.images[1].add_feature(a_image, connector.in_order)
    signs['ontable'].add_out_image(conn)
    signs[list_signs[1]].add_out_image(conn)
    cl_image = signs['clear'].add_image()
    d_image = pms[signs[list_signs[0]]]
    connector = goal_situation.images[1].add_feature(cl_image)
    conn = goal_situation.images[1].add_feature(d_image, connector.in_order)
    signs['clear'].add_out_image(conn)
    signs[list_signs[0]].add_out_image(conn)
    he_image = signs['handempty'].add_image()
    connector = goal_situation.images[1].add_feature(he_image)
    signs['handempty'].add_out_image(connector)

def _expand_situation_ma_logistics(goal_situation, signs, pms):

    at_image = signs['at'].add_image()
    tru1_image = signs['tru1'].add_image()
    pos1_image = pms[signs['pos1']]
    connector = at_image.add_feature(tru1_image)
    connector = at_image.add_feature(pos1_image)
    connector = goal_situation.images[1].add_feature(at_image)
    conn = goal_situation.images[1].add_feature(tru1_image, connector.in_order)
    con = goal_situation.images[1].add_feature(pos1_image, connector.in_order)
    signs['at'].add_out_images(connector)
    signs['tru1'].add_out_image(conn)
    signs['pos1'].add_out_image(con)
