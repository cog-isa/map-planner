import logging
from collections import defaultdict

import itertools
from functools import reduce

from grounding.semnet import Sign
from .sign_task import Task
from search.mapsearch import mix_pairs


def ground(problem, agent, subjects, exp_signs=None):
    domain = problem.domain
    actions = domain.actions.values()
    predicates = domain.predicates.values()
    constraints = problem.constraints

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
    subtype_map = _crate_subtype(domain.types)

    obj_signifs = {}
    obj_means = {}
    events = []

    # Sign world model
    if exp_signs:
        signs = exp_signs
        finish = exp_signs[[key for key in exp_signs.keys() if "finish" in key][0]]
        finish_cm = finish.meanings.get(1)
        for event in finish_cm.cause:
            for connector in event.coincidences:
                if not connector.in_sign == finish:
                    events.append(event)
        I_sign = signs['I']
        They_sign = signs['They']
        obj_means[I_sign] = I_sign.meanings[1]
        obj_signifs[I_sign] = I_sign.significances[1]
        obj_means[They_sign] = They_sign.meanings[1]
        obj_signifs[They_sign] = They_sign.significances[1]
    else:
        signs = {}
        I_sign = Sign("I")
        They_sign = Sign("They")
        obj_means[I_sign] = I_sign.add_meaning()
        obj_signifs[I_sign] = I_sign.add_significance()
        signs[I_sign.name] = I_sign
        obj_means[They_sign] = They_sign.add_meaning()
        obj_signifs[They_sign] = They_sign.add_significance()
        signs[They_sign.name] = They_sign

    for obj in objects:
        obj_sign = Sign(obj)
        obj_signifs[obj] = obj_sign.add_significance()
        obj_means[obj] = obj_sign.add_meaning()
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

    for sub in subjects:
        if sub != agent:
            connector = obj_signifs[sub].add_feature(obj_signifs[They_sign], zero_out=True)
            They_sign.add_out_significance(connector)

    if not exp_signs:
        updated_predicates = _update_predicates(predicates, actions)
        signify_predicates(predicates, updated_predicates, signs, subtype_map)
        signify_actions(actions, constraints, signs, agent, events, obj_means)
        signify_connection(signs)

    start_situation, pms = _define_situation('*start*', problem.initial_state, signs, events)
    goal_situation, pms = _define_situation('*finish*', problem.goal, signs, events)
    # expand_ma(start_situation, goal_situation, signs, type_map, actions, problem.initial_state, problem.goal)
    if problem.name.startswith("blocks"):
        list_signs = task_signs(problem)
        _expand_situation_ma_blocks(goal_situation, signs, pms, list_signs)  # For task
    elif problem.name.startswith("logistics"):
        _expand_situation_ma_logistics(goal_situation, signs, pms)
    return Task(problem.name, signs, constraints, start_situation, goal_situation)


def expand_ma(start_situation, goal_situation, signs, type_map, actions, start, goal):
    upload_events = start_situation.meanings[1] - goal_situation.meanings[1]
    goal_added_events = goal_situation.meanings[1] - start_situation.meanings[1]
    goal_events = [goal_situation.meanings[1].get_event(event + 1) for event in
                   range(len(goal_situation.meanings[1].cause))]
    # TODO найти те предикаты в которых не учавствуют объекты из гоал и скопировать в гоал
    # TODO находим разницу целевой и начальной сит - смотрим по действиям если предикат из
    # TODO разницы в add действия - берем и означиваем все дел эффекты действия - если они в
    # TODO предикатах начальной ситуации - удаляем их, а оставшиеся после общего отбора предикаты кидаем в целевую ситуацию

    difference = []
    for predicate in goal:
        predicate_obj = {ptuple[0] for ptuple in predicate.signature}
        for pred in start:
            if predicate.name != pred.name:
                continue
            if len(predicate.signature) != len(pred.signature):
                continue
            pred_obj = {ptuple[0] for ptuple in pred.signature}
            if predicate_obj == pred_obj:
                break

        else:
            difference.append(predicate)

    action_used = []
    for action in actions:
        for predicate in action.effect.addlist:
            for pred in difference:
                type_map = {}
                if predicate.name == pred.name:
                    for index, ptuple in enumerate(predicate.signature):
                        type_map[ptuple[0]] = pred.signature[index][0]
                    action_used.append((action, type_map))

    predicates_to_delete = []

    for action, replacemap in action_used:
        for pred in action.effect.dellist:
            if len(pred.signature) > len(replacemap):
                continue
            flag = False
            for fact in pred.signature:
                if not fact[0] in replacemap.keys():
                    flag = True
                    break
            if flag:
                continue
            used_fact = {}
            used_fact["name"] = pred.name
            for key, attribute in replacemap.items():
                for index, fact in enumerate(pred.signature):
                    if fact[0] == key:
                        used_fact[index] = attribute
            predicates_to_delete.append(used_fact)

    print()


def signify_predicates(predicates, updated_predicates, signs, subtype_map):
    for predicate in predicates:
        pred_sign = Sign(predicate.name)
        # significance = pred_sign.add_significance()
        signs[predicate.name] = pred_sign
        if len(predicate.signature) == 2:
            signifs = []

            def update_significance(fact, predicate, subtype_map, updated_predicates, effect=False):
                role_name = fact[1][0].name + fact[0]
                fact_name = fact[1][0].name
                roles = []
                roles.append(role_name)
                role_signifs = []
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
                    smaller_roles = [obj for obj in used_facts if obj in role_name and obj in signs]
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


def signify_actions(actions, constraints, signs, agent, events, obj_means):
    for action in actions:
        act_sign = Sign(action.name)
        act_signif = act_sign.add_significance()

        def update_significance(predicate, signature, effect=False):
            pred_sign = signs[predicate.name]
            if len(pred_sign.significances) > 1:
                pred_cm = pred_resonate('significance', pred_sign, predicate, signs, signature)
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
            elif not predicate.signature[0][1][0].name == predicate.signature[1][1][0].name:
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

        if constraints:
            if not action.agents:
                nonspecialized(constraints, act_signif, signs, agent, obj_means, events)
            else:
                specialized(action, signs, events, obj_means, act_signif, agent, constraints)

        else:
            specialized(action, signs, events, obj_means, act_signif, agent, constraints)

def spec(action, signs, events, obj_means, act_signif, agent, constraints):
    print()
    pass



def specialized(action, signs, events, obj_means, act_signif, agent, constraints):
    agent_signs = []
    agents_with_constraints = []
    for ag in action.agents:
        for cm in signs[ag].significances.values():
            agent_signs.extend(list(cm.get_signs())) #add current agents's signs
    for ag in constraints.keys():
        agents_with_constraints.append(signs[ag])
    agent_roles = {}
    # receiving all agent's roles.
    for ag in agent_signs:
        for a in ag.get_role():
            if a.name != "object":
                agent_roles.setdefault(ag, set()).update(a.get_role())
    for ag in agent_roles.keys():
        act_mean = act_signif.copy('significance', 'meaning')
        role_signs = [sign for sign in act_mean.get_signs() if sign in agent_roles[ag]]
        for role_sign in role_signs: # changing agent's roles to agents cms
            if role_sign in act_mean.get_signs():
                # logging.info("action {0}, role_sign {1}".format(act_signif.sign.name, role_sign.name))
                act_mean.replace('meaning', role_sign, obj_means[ag.name])
        if ag in agents_with_constraints:
            predicates = [pred for pred in constraints[ag.name]]
            role_signifs = {}

            non_agent_preds = []
            agent_preds = []
            for pred in predicates:
                for signa in pred.signature:
                    if signa[0] == ag.name:
                        agent_preds.append(pred) # predicates with agent signature
                        break
                    else:
                        continue
                else:
                    non_agent_preds.append(pred) # predicates without agent signature

            agent_signs= []
            for predicate in agent_preds:
                agent_signs.extend([signa[0] for signa in predicate.signature if signa[0] != ag.name])
            #agent_signs = [pred.signature[1][0] for pred in agent_preds]
            for pred in non_agent_preds.copy():
                signatures = []
                for signa in pred.signature:
                    signatures.append(signa[0])
                if not any(signa in agent_signs for signa in signatures):
                    non_agent_preds.remove(pred)
            non_agent_preds_signs = {signs[pred.name] for pred in non_agent_preds}
            for event in itertools.chain(act_mean.cause, act_mean.effect):
                event_signs = event.get_signs()
                if ag in event_signs:
                    pred_signs = [pred for pred in predicates if signs[pred.name] in event_signs]
                    if pred_signs:
                        event_signs.remove(ag)
                        for pred in pred_signs:
                            #TODO убрать package?obj
                            role_signature = {sign for sign in event_signs if sign != signs[pred.name]}
                            for role in role_signature:
                                pred_roles = [signif.get_signs() for _, signif in role.significances.items()]
                                pred_role = set()
                                while len(pred_roles):
                                    for role1 in pred_roles.copy():
                                        role2 = list(role1)[0]
                                        if not role2 in pred_role:
                                            pred_role.add(role2)
                                            pred_roles.remove(role1)
                                        else:
                                            pred_roles.remove(role1)
                                # в этот словарь складываем роль из матрицы к типу из предиката
                                role_signifs.setdefault(role, set()).update(pred_role)
                            # теперь заменяем знак типа на знак объекта и обновл. матрицу действия
                            for key, pred_signats in role_signifs.items():
                                for pred_signat in pred_signats.copy():
                                    for signa in pred.signature:
                                        if signa[1][0].name == pred_signat.name:
                                            pred_signats.remove(pred_signat)
                                            pred_signats.add(signs[signa[0]])
                elif event_signs & non_agent_preds_signs:
                    for predicate in non_agent_preds:
                        pred_signats = {signs[signa[0]] for signa in predicate.signature}
                        used_signs = reduce(lambda x, y: x|y, role_signifs.values())
                        new_signs = pred_signats - used_signs
                        # if not signs[signa[0]] in role_signifs.values()
                        for pred_sign in new_signs:
                            #pred_sign = signs[predicate.signature[0][0]]
                            attribute = pred_sign.find_attribute()
                            depth = 2
                            while depth > 0:
                                if not attribute in event_signs:
                                    attribute = attribute.find_attribute()
                                    if attribute in event_signs:
                                        break
                                    else:
                                        depth-=1
                            else:
                                continue
                            role_signifs.setdefault(attribute, set()).add(pred_sign)

            #TODO
            obj_sign = signs['package?obj']
            if obj_sign in role_signifs.keys():
                role_signifs.pop(obj_sign)


            pairs = mix_pairs(role_signifs)
            for pair in pairs:
                act_mean_constr = act_mean.copy('meaning', 'meaning')
                for role_sign, obj in pair.items():
                    act_mean_constr.replace('meaning', role_sign, obj_means[obj.name])
                if ag.name == agent:
                    I_sign = signs["I"]
                    connector = act_mean_constr.add_feature(obj_means[I_sign])
                    efconnector = act_mean_constr.add_feature(obj_means[I_sign], effect=True)
                    events.append(act_mean_constr.effect[abs(efconnector.in_order) - 1])
                    I_sign.add_out_meaning(connector)
                else:
                    connector = act_mean_constr.add_feature(obj_means[ag.name])
                    efconnector = act_mean_constr.add_feature(obj_means[ag.name], effect=True)
                    events.append(act_mean_constr.effect[abs(efconnector.in_order) - 1])
                    ag.add_out_meaning(connector)
        else:
            if ag.name == agent:
                I_sign = signs["I"]
                connector = act_mean.add_feature(obj_means[I_sign])
                efconnector = act_mean.add_feature(obj_means[I_sign], effect=True)
                events.append(act_mean.effect[abs(efconnector.in_order) - 1])
                I_sign.add_out_meaning(connector)
            else:
                connector = act_mean.add_feature(obj_means[ag.name])
                efconnector = act_mean.add_feature(obj_means[ag.name], effect=True)
                events.append(act_mean.effect[abs(efconnector.in_order) - 1])
                ag.add_out_meaning(connector)

def nonspecialized(constraints, act_signif, signs, agent, obj_means, events):
    for ag, constraint in constraints.items():
        predicates = {pred.name for pred in constraint}
        signatures = [pred.signature for pred in constraint]
        variants = []
        csignatures = signatures.copy()
        for signa in signatures:
            csignatures.remove(signa)
            signat = [signat[0] for signat in csignatures if signat[1] == signa[1]]
            if len(signat):
                signat.append(signa[0])
                if not signat in variants:
                    variants.append(signat)
        for variant in variants:
            act_mean = act_signif.copy('significance', 'meaning')
            for event in itertools.chain(act_mean.cause, act_mean.effect):
                ev_signs = [connector.out_sign for connector in event.coincidences]
                if any(signs[pred] in ev_signs for pred in predicates):
                    for var in variant:
                        role_sign = [role_sign for role_sign in list(signs[var[1][0].name].get_role()) if
                                     role_sign in ev_signs]
                        if role_sign:
                            role_sign = role_sign[0]
                            act_mean.replace('meaning', role_sign, obj_means[var[0]])
                            # event.replace('meaning', role_sign, obj_means[var[0]], [])
            if ag == agent:
                I_sign = signs["I"]
                connector = act_mean.add_feature(obj_means[I_sign])
                efconnector = act_mean.add_feature(obj_means[I_sign], effect=True)
                events.append(act_mean.effect[abs(efconnector.in_order) - 1])
                I_sign.add_out_meaning(connector)
            else:
                connector = act_mean.add_feature(obj_means[ag])
                efconnector = act_mean.add_feature(obj_means[ag], effect=True)
                events.append(act_mean.effect[abs(efconnector.in_order) - 1])
                signs[ag].add_out_meaning(connector)

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
            #pm = cm.copy('significance', 'significance')
            return cm
    return None


def signify_connection(signs):
    Send = Sign("Send")
    send_signif = Send.add_significance()
    Broadcast = Sign("Broadcast")
    brdct_signif = Broadcast.add_significance()
    connector = brdct_signif.add_feature(send_signif)
    Send.add_out_significance(connector)
    Approve = Sign("Approve")
    approve_signif = Approve.add_significance()
    connector = approve_signif.add_feature(send_signif)
    Send.add_out_significance(connector)
    signs[Send.name] = Send
    signs[Broadcast.name] = Broadcast
    signs[Approve.name] = Approve

    They_sign = signs["They"]
    agents = They_sign.spread_up_activity_obj("significance", 1)
    agents_type = []
    for agent in agents:
        agents_type.append({cm.sign for cm in agent.sign.spread_up_activity_obj("significance", 1)})
    # for type1 in agents_type:
    #     for type2 in agents_type:
    #         if type1 != type2:
    #             type |= type1 & type2
    #         else:
    #             type = [t for t in type2 if t.name != "object"][0]
    types = [t for t in reduce(lambda x,y: x&y, agents_type) if t != signs["object"]]
    if types and len(agents):
        type = types[0]
    else:
        type = signs["I"]



    They_signif = They_sign.add_significance()
    brdct_signif = Broadcast.add_significance()
    connector = They_signif.add_feature(brdct_signif)
    Broadcast.add_out_significance(connector)
    type_signif = type.add_significance()
    approve_signif = Approve.add_significance()
    # They_signif = They_sign.add_significance()
    connector = type_signif.add_feature(approve_signif)
    Approve.add_out_significance(connector)

    brdct_signif = Broadcast.add_significance()
    executer = brdct_signif.add_execution(Broadcast.name.lower(), effect=True)
    Send.add_out_significance(executer)

    approve_signif = Approve.add_significance()
    executer = approve_signif.add_execution(Approve.name.lower(), effect=True)
    Send.add_out_significance(executer)


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
                        #predicates[predicate.name].remove(fact)
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


def _crate_subtype(types):
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


def _define_situation(name, predicates, signs, events):
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
            pre_signs = set()
            for fact in predicate.signature:
                pre_signs.add(signs[fact[0]].find_attribute())
            if len(pre_signs) < len(predicate.signature):
                for fact in predicate.signature:
                    fact_sign = signs[fact[0]]
                    fact_meaning = get_or_add(fact_sign)
                    conn = pred_meaning.add_feature(fact_meaning)
                    fact_sign.add_out_meaning(conn)
            else:
                for fact in predicate.signature:
                    fact_sign = signs[fact[0]]
                    fact_meaning = get_or_add(fact_sign)
                    conn = sit_meaning.add_feature(fact_meaning, connector.in_order)
                    fact_sign.add_out_meaning(conn)
                    con3 = pred_meaning.add_feature(fact_meaning)
                    fact_sign.add_out_meaning(con3)

    for event in events:
        sit_meaning.add_event(event)

    return situation, elements


def _expand_situation_ma_blocks(goal_situation, signs, pms, list_signs):
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


def _expand_situation_ma_logistics(goal_situation, signs, pms):
    # at_mean = signs['at'].add_meaning()
    # apn_mean = signs['apn1'].add_meaning()
    # apt_mean = pms[signs['apt1']]
    # connector = at_mean.add_feature(apn_mean)
    # connector = at_mean.add_feature(apt_mean)
    # connector = goal_situation.meanings[1].add_feature(at_mean)
    # conn = goal_situation.meanings[1].add_feature(apn_mean, connector.in_order)
    # con = goal_situation.meanings[1].add_feature(apt_mean, connector.in_order)
    # signs['at'].add_out_meaning(connector)
    # signs['apn1'].add_out_meaning(conn)
    # signs['apt1'].add_out_meaning(con)

    at_mean = signs['at'].add_meaning()
    tru1_mean = signs['tru1'].add_meaning()
    pos1_mean = pms[signs['pos1']]
    connector = at_mean.add_feature(tru1_mean)
    connector = at_mean.add_feature(pos1_mean)
    connector = goal_situation.meanings[1].add_feature(at_mean)
    conn = goal_situation.meanings[1].add_feature(tru1_mean, connector.in_order)
    con = goal_situation.meanings[1].add_feature(pos1_mean, connector.in_order)
    signs['at'].add_out_meaning(connector)
    signs['tru1'].add_out_meaning(conn)
    signs['pos1'].add_out_meaning(con)

    # at_mean = signs['at'].add_meaning()
    # tru2_mean = signs['tru2'].add_meaning()
    # pos2_mean = pms[signs['pos2']]
    # connector = at_mean.add_feature(tru2_mean)
    # connector = at_mean.add_feature(pos2_mean)
    # connector = goal_situation.meanings[1].add_feature(at_mean)
    # conn = goal_situation.meanings[1].add_feature(tru2_mean, connector.in_order)
    # con = goal_situation.meanings[1].add_feature(pos2_mean, connector.in_order)
    # signs['at'].add_out_meaning(connector)
    # signs['tru2'].add_out_meaning(conn)
    # signs['pos2'].add_out_meaning(con)