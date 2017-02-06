import logging

import grounding.sign_task as st
from grounding.semnet import Sign
from itertools import groupby

MAX_ITERATION = 100

world_model = None


def map_search(task):
    global world_model
    world_model = task.signs
    active_pm = task.goal_situation.meanings[1]
    check_pm = task.start_situation.meanings[1]
    logging.debug('Start: {0}'.format(check_pm.longstr()))
    logging.debug('Finish: {0}'.format(active_pm.longstr()))

    plans = map_iteration(active_pm, check_pm, [], 0, [])
    if plans:
        current_plans = []
        logging.debug('Found {0} variants'.format(len(plans)))
        for key, group in groupby(plans, lambda x: x[0]):
            current_plans.append([key, list(reversed(min(group, key=len)[1]))])
            # current_plans.append(min(group, key=len))
        for plan in current_plans:
            logging.info('Plan: agent = {0}, len={1}, {2}'.format(plan[0].name, len(plan[1]), [name for _, name, _ in plan[1]]))
        return [(name, script) for _, name, script in plan[1]]
    else:
        logging.debug('Variant are not found')
    return None


def map_iteration(active_pm, check_pm, current_plan, iteration, aim_plans, current_agent=None):
    logging.debug('STEP {0}:'.format(iteration))
    logging.debug('\tSituation {0}'.format(active_pm.longstr()))
    if iteration >= MAX_ITERATION:
        logging.debug('\tMax iteration count')
        return None

    # Check meanings for current situations
    precedents = []
    for name, sign in world_model.items():
        # c минингами только блоки а b c d, предикаты(handempty, clear, on, ontable)
        for index, cm in sign.meanings.items():
            if cm.includes('meaning', active_pm):
                precedents.extend(cm.sign.spread_up_activity_act('meaning', 1))

    # Activate all current signs (their meanings)
    # active-chains = list of signs with their out indices like a new indices. List of
    # lists with causal matrix that connect finish sign with meaning 1 with signs with their own meanings
    active_chains = active_pm.spread_down_activity('meaning', 2)
    active_signif = set()
    # find all significances (actions) for all current signs
    for chain in active_chains:
        pm = chain[-1]
        # |= add elements after = to set active_signif
        # повышает уровень абстракии с блока имя_блока до object (a-block-block?x/block?y-object) - на этом уровне берет
        # out_significance с индексами - возращает список из действий, которые можно совершить с этим блоком
        # в случае а:1 это список 4 каузальных матриц unstack:1, stack:1, put-down:1, pick-up:1
        active_signif |= pm.sign.spread_up_activity_act('significance', 3)

    meanings = []
    for pm_signif in active_signif:
        # find all roles and role replacements in each significance (action)
        # создает список списков каузальных матриц с данным действием (например pick-up:1 block?x: 1 block: 1/2/3/4
        # a/b/c/d: 1
        chains = pm_signif.spread_down_activity('significance', 3)
        merged_chains = []
        #
        for chain in chains:
            for achain in active_chains:
                if chain[-1].sign == achain[-1].sign and len(chain) > 2 and chain not in merged_chains:
                    merged_chains.append(chain)
                    break
        # Replace role in abstract actions to generate scripts
        # возвращает список действий, которые можно совершить с блоками (stack 1-12)
        scripts = _generate_meanings(merged_chains)
        meanings.extend(scripts)
    # ищет совпадающие знаки в эффектах каузальных матриц минингов скриптов и искомой ситуации
    # applicable_minings = put-down 32 put-down 33 stack 31
    applicable_meanings = []
    for cm in precedents + meanings:
        result, checked = _check_activity(cm, active_pm)
        if result:
            applicable_meanings.append(checked)

    # TODO: replace to metarule apply
    # находят применимые скрипты и составляется ситуация из знаков, после применения данного скрипта.
    candidates = _meta_check_activity(applicable_meanings, active_pm, check_pm, [x for x, _, _ in current_plan])

    if not candidates:
        logging.debug('\tNot found applicable scripts ({0})'.format([x for _, x, _ in current_plan]))
        return None

    logging.debug('\tFound {0} variants'.format(len(candidates)))
    final_plans = []
    if current_agent is not None and len(aim_plans):
        if current_agent not in [plan[0] for plan in aim_plans]:
            candidates = [cand for cand in candidates if get_agent(cand[2]) == current_agent]

    for counter, name, script in candidates:
        logging.debug('\tChoose {0}: {1} -> {2}'.format(counter, name, script))

        plan = current_plan.copy()
        plan.append((active_pm, name, script))
        agent = get_agent(script)
        if current_agent is None:
            current_agent = agent
        if len(final_plans):
            aim_plans.extend(final_plans)
            if not all(agents == agent for agents in action_agents(plan)):
                break
            else: current_agent = agent

        if not agent == current_agent:
            break
        # найденный скрипт применяется к ситуации и возвращает новую ситуацию
        next_pm = _time_shift_backward(active_pm, script)
        # если новая ситуация совпадает по знакам с начальной ситуацией - возвращаем финальный план
        if next_pm.includes('meaning', check_pm):
            final_plans.append((current_agent, plan))
        else:
            recursive_plans = map_iteration(next_pm, check_pm, plan, iteration + 1, aim_plans, agent)
            if recursive_plans:
                final_plans.extend(recursive_plans)

    return final_plans

def action_agents(plan):
    plan_agents = []
    for _, _, script in plan:
        agent = get_agent(script)
        plan_agents.append(agent)
    return plan_agents

def get_agent(script):
    roles = []
    for event in script.cause:
        for conn in event.coincidences:
            for connector in conn.out_sign.out_significances:
                roles.append(connector.in_sign.name)
            if "agent" in roles:
                return conn.out_sign

def _generate_meanings(chains):
    replace_map = {}
    main_pm = None
    # compose pairs - role-replacer
    for chain in chains:
        if not chain[1].sign in replace_map:
            replace_map[chain[1].sign] = [chain[-1]]
        else:
            if not chain[-1] in replace_map[chain[1].sign]:
                replace_map[chain[1].sign].append(chain[-1])
        main_pm = chain[0]

    combinations = []
    ma_combinations = []
    roles = []
    unique = []

    def create_combinations(role_map, current):
        comb = []
        for role_sign in role_map:
            for obj_pm in role_map[role_sign]:
                new_current = current.copy()
                new_current[role_sign] = obj_pm
                comb.append(new_current)
        return comb


    def create_ma_combinations(role_map):
        used_roles = []
        for role_sign in role_map:
            if not role_sign in roles :
                roles.append(role_sign)
            for r in role_map:
                if not r in roles:
                    roles.append(r)
                if not [role_sign, r] or not [r, role_sign] in used_roles:
                    used_roles.append([role_sign, r])
                    if not r == role_sign:
                        for obj_pm in role_map[role_sign]:
                            others = {}
                            current = {}
                            current[role_sign] = obj_pm
                            others[r] = role_map[r].copy()
                            if role_sign.find_role() == r.find_role():
                                others[r].remove(obj_pm)
                            combinations.extend(create_combinations(others, current))
                    # elif not role_sign.find_role() == r.find_role():
                    #     for obj in role_map[role_sign]:
                    #         others = {}
                    #         current = {}
                    #         current[role_sign] = obj
                    #         others[r] = role_map[r].copy()
                    #         combinations.extend(create_combinations(others, current))

    create_ma_combinations(replace_map)

    def is_unique(pair_items, item3):
        if not any(pair_items[0] in item and pair_items[1] in item and item3 in item for item in unique):
            unique.append([pair_items[0], pair_items[1], item3])
            return True
        return False

    def mix_pairs(combinations):
        others = []
        blocks = []
        for pair in combinations:
            list_keys = list(pair.keys())
            if not list_keys[0].find_role() == list_keys[1].find_role():
                others.append(pair)
            else: blocks.append(pair)
        for pair in others:
            for block in blocks:
                new_chain = {}
                pair_items = list(pair.items())
                block_items = list(block.items())
                for item1 in pair_items:
                    for item2 in block_items:
                        if item1[0] == item2[0] and item1[1] == item2[1]:
                            for new_item in block_items:
                                if not new_item == item2:
                                    if is_unique(pair_items, new_item):
                                        new_chain.update(pair)
                                        new_chain.update(dict([new_item]))
                                        ma_combinations.append(new_chain)


    if len(roles) > 2:
        mix_pairs(combinations)
    else: ma_combinations = combinations
    pms = []
    # create combinations like block?y:b:1 block?x:a:1
    for ma_combination in ma_combinations:
        cm = main_pm.copy('significance', 'meaning')
        for role_sign, obj_pm in ma_combination.items():
            obj_cm = obj_pm.copy('significance', 'meaning')
            # заменяет км мининг знака роли в действии на км мининга знака блока block?x/?y - a/b/c/d
            cm.replace('meaning', role_sign, obj_cm)
        pms.append(cm)

    return pms


def _check_activity(pm, active_pm):
    result = True
    for event in pm.effect:
        for fevent in active_pm.cause:
            #проверка на совпадение выходящих знаков 2 каузальных матриц минингов
            if event.resonate('meaning', fevent):
                break
        else:
            result = False
            break

    if not result:
        expanded = pm.expand('meaning')
        if not len(expanded.effect) == 0:
            return _check_activity(expanded, active_pm)
        else:
            return False, pm
    return result, pm


def _time_shift_backward(active_pm, script):
    next_pm = Sign(st.SIT_PREFIX + str(st.SIT_COUNTER))
    world_model[next_pm.name] = next_pm
    pm = next_pm.add_meaning()
    st.SIT_COUNTER += 1
    copied = {}
    for event in active_pm.cause:
        for es in script.effect:
            # если event.conins.connector.out_sign != script.coins.connector.out_sign = false
            # если знаки равны - сравнивают условия и эффекты км out_sign
            if event.resonate('meaning', es):
                break
        else:
            pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))
    for event in script.cause:
        pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))

    return pm


def _meta_check_activity(scripts, active_pm, check_pm, prev_pms):
    heuristic = []
    for script in scripts:
        estimation = _time_shift_backward(active_pm, script)
        for prev in prev_pms:
            if estimation.resonate('meaning', prev, False, False):
                break
        else:
            counter = 0
            for event in estimation.cause:
                for ce in check_pm.cause:
                    if event.resonate('meaning', ce):
                        counter += 1
                        break
            heuristic.append((counter, script.sign.name, script))
    if heuristic:
        best_heuristics = max(heuristic, key=lambda x: x[0])
        return list(filter(lambda x: x[0] == best_heuristics[0], heuristic))
    else:
        return None
