import logging

import mapplanner.grounding.sign_task as st
import random
from mapplanner.grounding.json_grounding import *
from mapplanner.grounding.semnet import Sign

MAX_CL_LV = 3

class MapSearch():
    def __init__ (self, task, LogicalSearch, ref):
        self.world_model = task.signs
        self.check_pm = task.goal_situation.meanings[1]
        self.active_pm = task.start_situation.meanings[1]
        self.constraints = task.constraints
        self.logic = task.logic
        self.active_map = task.map_precisions
        self.additions = task.additions
        self.exp_actions = []
        self.agents = set()
        self.I_sign = None
        self.I_obj = None
        self.LogicalSearch = LogicalSearch
        self.refinement_lv = ref
        self.init_state = task.init
        self.goal_state = task.goal
        self.clarification_lv = task.init['cl_lv']
        self.exp_sits = []
        self.exp_maps = []
        self.exp_acts = {}
        if task.goal_map:
            self.check_map = task.goal_map.meanings[1]
        else:
            self.check_map = None
        self.MAX_ITERATION = 30
        logging.debug('Start: {0}'.format(self.check_pm.longstr()))
        logging.debug('Finish: {0}'.format(self.active_pm.longstr()))

    def search_plan(self):
        self.I_sign, self.I_obj, self.agents = self.__get_agents()
        plans = self._map_iteration(self.active_pm, self.active_map, iteration=0, current_plan=[])
        return plans

    def _logic_expand(self, LogicalSearch):
        if LogicalSearch:
            print(LogicalSearch)
        pass

    def _precedent_search(self, active_pm):
        precedents = []
        # plan_signs = []

        for name, sign in self.world_model.items():
            # if name.startswith("action_"): plan_signs.append(sign)
            for index, cm in sign.meanings.items():
                if cm.includes('meaning', active_pm):
                    precedents.extend(cm.sign.spread_up_activity_act('meaning', 1))
                elif not cm.sign.significances and active_pm.includes('meaning', cm):
                    precedents.extend(cm.sign.spread_up_activity_act('meaning', 1))
        return precedents


    def _map_iteration(self, active_pm, active_map, iteration, current_plan, prev_state = [], MI = None, Ch_pm = None, Ch_m = None):
        logging.debug('STEP {0}:'.format(iteration))
        logging.debug('\tSituation {0}'.format(active_pm.longstr()))

        MAX_ITERATION = self.MAX_ITERATION
        if not Ch_pm and not Ch_m:
            check_pm= self.check_pm
            check_map = self.check_map
        else:
            check_pm = Ch_pm
            check_map = Ch_m
        if iteration >= MAX_ITERATION:
            logging.debug('\tMax iteration count')
            return None

        precedents = self._precedent_search(active_pm)

        active_chains = active_pm.spread_down_activity('meaning', 4)
        active_signif = set()

        for chain in active_chains:
            pm = chain[-1]
            active_signif |= pm.sign.spread_up_activity_act('significance', 3)

        if precedents and self.refinement_lv > 0:
            self.exp_sits = [sign.meanings[1] for name, sign in self.world_model.items() if 'exp_situation' in name]
            self.exp_maps = [sign.meanings[1] for name, sign in self.world_model.items() if 'exp_map' in name]
            self.exp_acts = self.hierarch_acts()

        meanings = []
        for pm_signif in active_signif:
            chains = pm_signif.spread_down_activity('significance', 6)
            merged_chains = []
            for chain in chains:
                for achain in active_chains:
                    if chain[-1].sign == achain[-1].sign and len(chain) > 2 and chain not in merged_chains:
                        merged_chains.append(chain)
                        break
            scripts = self._generate_meanings(merged_chains)
            meanings.extend(scripts)
        applicable_meanings = []
        agent = None
        if not precedents:
            for agent, cm in meanings:
                result, checked = self._check_activity(cm, active_pm)
                if result:
                    applicable_meanings.append((agent, checked))
        else:
            for cm in precedents + meanings:
                if isinstance(cm, tuple):
                    agent = cm[0]
                    cm = cm[1]
                result, checked = self._check_activity(cm, active_pm)
                if result:
                    applicable_meanings.append((agent, checked))

        prev_act = None
        if current_plan:
            prev_act = current_plan[-1][1]

        candidates = self._meta_check_activity(active_pm, applicable_meanings, [x for x, _, _, _, _,_ in current_plan], iteration, prev_state, prev_act)

        if not candidates:
            logging.debug('\tNot found applicable scripts ({0})'.format([x for _, x, _, _, _,_ in current_plan]))
            return None

        logging.debug('\tFound {0} variants'.format(len(candidates)))
        final_plans = []

        if candidates[0][0] == 0:
            # there are no actions that let to achieve the goal
            current_plan, active_pm, active_map, iteration = self.clarify_search('agent', active_pm, check_pm, iteration, current_plan)
            # TODO save old situation matrix using CM - clarification [old_pm, new_pm]
            candidates = []
            final_plans.append(current_plan)
            plan_actions = [x.sign.name for _, _, x, _, _, _ in current_plan]
            logging.info("len of detected plan is: {0}".format(len(current_plan)))
            logging.info(plan_actions)

        logging.info("len of curent plan is: {0}. Len of candidates: {1}".format(len(current_plan), len(candidates)))

        for counter, name, script, ag_mask in candidates:
            logging.debug('\tChoose {0}: {1} -> {2}'.format(counter, name, script))
            plan = copy(current_plan)

            subplan = None
            if self.logic == 'spatial':
                next_pm, next_map, prev_state, direction = self._step_generating(active_pm, active_map, script, agent, iteration, prev_state, True)
                ag_place = (prev_state[-1][2] - prev_state[-1][0]) // 2 + prev_state[-1][0], (
                            prev_state[-1][3] - prev_state[-1][1]) // 2 + prev_state[-1][1]
                if script.sign.images and self.refinement_lv >0:
                    acts = []
                    for act in script.sign.images[1].spread_down_activity('image', 2):
                        if act[1] not in acts:
                            acts.append(act[1])
                    self.exp_sits.append(next_pm)
                    self.exp_maps.append(active_map)
                    self.exp_maps.append(self.check_map)
                    subplan = self.hierarchical_exp_search(active_pm, active_map, next_pm, next_map, iteration, prev_state, acts)

                if not subplan:
                    plan.append((active_pm, name, script, ag_mask, (ag_place, direction), (active_map, self.clarification_lv)))
                else:
                    plan.extend(subplan)
                    logging.info(
                        'action {0} was changed to {1}'.format(script.sign.name, [part[1] for part in subplan]))
                if self.clarification_lv > 0:
                    # there are some actions that let to achieve the goal, check the higher lev of hierarchy
                    next_pm, next_map, iteration, plan = self.abstract_search('agent', next_pm, next_map, iteration, plan)


            else:
                next_pm = self._time_shift_forward(active_pm, script)
                if script.sign.images and self.refinement_lv > 0:
                    acts = []
                    for act in script.sign.images[1].spread_down_activity('image', 2):
                        if act[1] not in acts:
                            acts.append(act[1])
                    self.exp_sits.append(next_pm)
                    self.exp_maps.append(active_map)
                    subplan = self.hierarchical_exp_search(active_pm, active_map, next_pm, None, iteration, prev_state, acts)
                if not subplan:
                    plan.append((active_pm, name, script, ag_mask, None, (None, self.clarification_lv)))
                else:
                    plan.extend(subplan[0])
                    logging.info(
                        'action {0} was changed to {1}'.format(script.sign.name, [part[1] for part in subplan[0]]))

                next_map = None
                prev_state.append(active_pm)

            if self.logic == 'spatial':
                if next_pm.includes('meaning', check_pm):
                    if next_map.includes('meaning', check_map):
                        final_plans.append(plan)
                        plan_actions = [x.sign.name for _, _, x, _, _, _ in plan]
                        logging.info("len of detected plan is: {0}".format(len(plan)))
                        logging.info(plan_actions)
                    else:
                        # Expanding logic
                        self._logic_expand(self.LogicalSearch)
                        recursive_plans = self._map_iteration(next_pm, next_map, iteration + 1, plan, prev_state,
                                                              Ch_pm=check_pm,
                                                              Ch_m=check_map, MI=MAX_ITERATION)
                        if recursive_plans:
                            final_plans.extend(recursive_plans)
                else:
                    #Expanding logic
                    self._logic_expand(self.LogicalSearch)
                    recursive_plans = self._map_iteration(next_pm, next_map, iteration + 1, plan, prev_state, Ch_pm= check_pm, Ch_m=check_map, MI=MAX_ITERATION)
                    if recursive_plans:
                        final_plans.extend(recursive_plans)
            else:
                if next_pm.includes('meaning', check_pm):
                    final_plans.append(plan)
                    plan_actions = [x.sign.name for _, _, x, _, _, _ in plan]
                    logging.info("len of detected plan is: {0}".format(len(plan)))
                    logging.info(plan_actions)
                else:
                    #Expanding logic
                    self._logic_expand(self.LogicalSearch)
                    recursive_plans = self._map_iteration(next_pm, next_map, iteration + 1, plan, prev_state, Ch_pm= check_pm, Ch_m=check_map, MI=MAX_ITERATION)
                    if recursive_plans:
                        final_plans.extend(recursive_plans)

        return final_plans


    def hierarch_acts(self):
        exp_acts = {}
        for name, sign in self.world_model.items():
            if sign.meanings and sign.images:
                for index, cm in sign.meanings.items():
                    if len(cm.cause) and len(cm.effect):
                        exp_acts.setdefault(sign, {})[index] = cm

        applicable_meanings = {}
        used = {key: {} for key in exp_acts.keys()}
        for agent in self.agents:
            for conn in agent.out_meanings:
                if conn.in_sign in exp_acts and not conn.in_index in used[conn.in_sign]:
                    applicable_meanings.setdefault(conn.in_sign, []).append((agent, exp_acts[conn.in_sign][conn.in_index]))
                    used.setdefault(conn.in_sign, {})[conn.in_index] = getattr(conn.in_sign, 'meanings')[conn.in_index]

        for key1, value1 in exp_acts.items():
            for key2, value2 in value1.items():
                if not key2 in used[key1]:
                    applicable_meanings.setdefault(key1, []).append(
                        (None, value2))

        return applicable_meanings

    def hierarchical_exp_search(self, active_pm, active_map, check_pm, check_map, iteration, prev_state, acts, plan = [], subsearch = False):
        """
        create a subplan using images info
        :param script: parametrs to generate plan
        :return:plan
        """
        logging.info('Clarify experience plan')
        applicable = []
        act = acts[0].sign
        plan = []
        if not [ac for ac in self.exp_acts[act] if ac[0] is None]:
            exp_acts = copy(self.exp_acts[act])
            for agent, cm in exp_acts:
                result, checked = self._check_activity(cm, active_pm)
                if result:
                    applicable.append((agent, checked))

            if not applicable and exp_acts:
                if self.clarification_lv <= MAX_CL_LV:
                    active_pm, check_pm, active_map, check_map, iteration = self.devide_situation(active_pm, check_pm,
                                                                                                          iteration, 'agent')
                    return self.hierarchical_exp_search(active_pm, active_map, check_pm, check_map, iteration, prev_state, acts, plan)
                else:
                    return None
        else:
            exp_acts = [act[1] for act in self.exp_acts[act] if len(act[1].cause) == 1]
            for exp_act in exp_acts:
                result, checked = self._check_activity(exp_act, active_pm)
                if result:
                    applicable.append((None, checked))
        for action in applicable:
            if action[1].sign.name == 'Clarify':
                result = False
                next_pm = False
                next_map = None
                while not result:
                    if self.clarification_lv <= MAX_CL_LV:
                        next_pm, check_pm, next_map, check_map, iteration = self.devide_situation(active_pm, check_pm,
                                                                                                  iteration, 'agent')
                    else:
                        break
                    result, checked = self._check_result(action[1], next_pm)
                acts.pop(0)
                agent = action[0]
                if action[0] is None: agent = plan[-1][3]
                plan.append((active_pm, action[1].sign.name, action[1], agent, plan[-1][4], (next_map, self.clarification_lv)))

                plan = self.hierarchical_exp_search(next_pm, next_map, check_pm, check_map, iteration,
                                                        prev_state, acts, plan)
            elif action[1].sign.name == 'Abstract':
                cell_coords = active_pm.sign.images[1].spread_down_activity_view(1)
                size = [cell_coords['cell-0'][0],
                        cell_coords['cell-0'][1],
                        cell_coords['cell-8'][2],
                        cell_coords['cell-8'][3]]
                #TODO check if abstract did not only by 1 step
            elif 'subpl_' in action[1].sign.name:
                sub_sign = action[1].sign
                sub_acts = []
                for act in sub_sign.images[1].spread_down_activity('image', 2):
                    if act[1] not in sub_acts:
                        sub_acts.append(act[1])
                sub_finish = None
                for con in sub_sign.meanings[1].effect[0].coincidences:
                    sub_finish = con.out_sign.meanings[con.out_index]

                plan.extend(self.hierarchical_exp_search(active_pm, active_map, sub_finish, None, iteration,
                                                        prev_state, sub_acts, plan, True))
                if plan:
                    subsearch = False
                    acts.pop(0)
                    plan = self.hierarchical_exp_search(plan[-1][0], plan[-1][-1][0], check_pm, check_map, iteration,
                                                        prev_state, acts, plan)
            else:
                if check_map or subsearch:
                    next_pm, next_map, prev_state, direction = self._step_generating(active_pm, active_map, action[1], action[0],
                                                                                     iteration, prev_state, True)
                    ag_place = (prev_state[-1][2] - prev_state[-1][0]) // 2 + prev_state[-1][0], (
                            prev_state[-1][3] - prev_state[-1][1]) // 2 + prev_state[-1][1]
                    included_map = [map for map in self.exp_maps if map.includes('meaning', next_map)]
                    included_sit = [sit for sit in self.exp_sits if sit.includes('meaning', next_pm)]
                    if included_sit and included_map:
                        plan.append((active_pm, action[1].sign.name, action[1], action[0], (ag_place, direction),
                                     (next_map, self.clarification_lv)))
                    else:
                        continue
                else:
                    next_pm = self._time_shift_forward(active_pm, action[1])
                    included_map = True
                    next_map = None
                    included_sit = [sit for sit in self.exp_sits if sit.includes('meaning', next_pm)]
                    if included_sit and included_map:
                        plan.append(
                            (active_pm, action[1].sign.name, action[1], action[0], None, (None, self.clarification_lv)))

                acts.pop(0)

                if next_pm.includes('meaning', check_pm):
                    if check_map:
                        if next_map.includes('meaning', check_map):
                            return plan
                        else:
                            #self.exp_sits = [sit for sit in self.exp_sits if sit != included_sit[0]]
                            return self.hierarchical_exp_search(next_pm, next_map, check_pm, check_map, iteration + 1,
                                                                prev_state, acts, plan)
                    elif subsearch:
                        if len(acts):
                            return self.hierarchical_exp_search(next_pm, next_map, check_pm, check_map, iteration + 1,
                                                                prev_state, acts, plan, subsearch)
                        else:
                            return plan
                    else:
                        return plan
                else:
                    #self.exp_sits = [sit for sit in self.exp_sits if sit != included_sit[0]]
                    return self.hierarchical_exp_search(next_pm, next_map, check_pm, check_map, iteration+1, prev_state, acts, plan, subsearch)
        return plan

    def pm_parser(self, pm, agent):
        pm_events = [ev for ev in pm.cause]
        searched = self.__search_cm(pm_events, [self.world_model['orientation'], self.world_model['holding']])
        events = []

        holding = searched[self.world_model['holding']]
        direction = None
        if holding:
            holding = holding[0]
        orientation = searched[self.world_model['orientation']][0]
        for sign in orientation.get_signs():
            if sign.name != agent and sign.name != 'I':
                direction = sign
                break
        for ev in pm_events:
            if len(ev.coincidences) == 1:
                for con in ev.coincidences:
                    if con.out_sign.name == "I":
                        events.append(ev)
            elif not holding:
                if "I" in [s.name for s in ev.get_signs()]:
                    events.append(ev)

        return events, direction, holding

    def abstract_search(self, agent, active_pm, active_map, iteration, plan):
        logging.info('CHECKING AN ABILITY TO CREATE ABSTRACT MAP')
        # checking for empty situation
        first_check = True
        iteration+=1
        for cell, value in self.additions[2][iteration].items():
            if not 0 in value:
                if not agent in value:
                    first_check = False
                    logging.info('ABSTRACTING DOES NOT ALLOWED. TOO MUCH OBJECTS AROUND.')
                    break
        if first_check:
            # calculate new start situation
            objects = self.additions[0][iteration]['objects']
            map_size = self.additions[3]['map_size']
            borders = self.additions[3]['wall']
            orientation = self.additions[0][iteration]['agent-orientation']
            rmap = [0, 0]
            rmap.extend(map_size)
            region_location, region_map = locater('region-', rmap, objects, borders)
            cell_coords = active_pm.sign.images[1].spread_down_activity_view(1)
            size = [cell_coords['cell-0'][0],
                    cell_coords['cell-0'][1],
                    cell_coords['cell-8'][2],
                    cell_coords['cell-8'][3]]
            x_size = size[2]-size[0]
            y_size = size[3]-size[1]
            if x_size > map_size[0] //3 or y_size > map_size[1] //3:
                agplx = self.additions[0][iteration]['objects'][agent]['x']
                agply = self.additions[0][iteration]['objects'][agent]['y']
                for _, rsize in region_location.items():
                    if rsize[0] <= agplx <=rsize[2] and rsize[1] <= agply <=rsize[3]:
                        # x_size = rsize[2] - rsize[0]
                        # y_size = rsize[3] - rsize[1]
                        # size = [rsize[0]- x_size, rsize[1]-y_size, rsize[2]+ x_size, rsize[3] + y_size]
                        size = rsize
                        break
            cell_location, cell_map, near_loc, cell_coords, _ = cell_creater(size, objects, region_location, borders)
            front_cell = None
            for reg, val in  self.additions[1]['region-4'].items():
                if val[1] == orientation:
                    front_cell = 'cell-' + reg[-1]
                    break
            if not 0 in cell_map[front_cell]:
                if len(cell_map[front_cell]) !=1 or 'wall' not in list(cell_map[front_cell])[0]:
                    logging.info('ABSTRACTING DOES NOT ALLOWED. GOAL PATH IS NOT CLEAN.')
                    return active_pm, active_map, iteration-1, plan

            logging.info('ABSTRACTING ALLOWED. STARTING UPPER LEVEL PLANNING')
            # define new current situation
            sit_name = st.SIT_PREFIX + str(st.SIT_COUNTER)
            events, direction, holding = self.pm_parser(active_pm, agent)
            agent_state = state_prediction(self.world_model['I'], direction, holding)
            active_sit_new = define_situation(sit_name + 'sp', cell_map, events, agent_state, self.world_model)
            # define new current map
            # TODO check replace exception
            active_map = define_map(st.MAP_PREFIX + str(st.SIT_COUNTER), region_map, cell_location, near_loc,
                                    self.additions[1],
                                    self.world_model)
            st.SIT_COUNTER += 1

            state_fixation(active_sit_new, cell_coords, signs, 'cell')
            self.additions[0][iteration] = deepcopy(self.additions[0][iteration - 1])
            self.additions[2][iteration] = cell_map
            # define new action - Abstract. Adding it to the plan
            abstr_mean = self.world_model['Abstract'].add_meaning()
            connector = abstr_mean.add_feature(active_pm)
            active_pm.sign.add_out_meaning(connector)
            connector = abstr_mean.add_feature(active_sit_new, effect=True)
            active_sit_new.sign.add_out_meaning(connector)

            plan.append(
                (active_pm, 'Abstract', abstr_mean, self.world_model['I'], plan[-1][4], (plan[-1][5][0], plan[-1][5][1]-1)))

            # decrease clarification
            self.clarification_lv -=1

            return active_sit_new, active_map, iteration-1, plan

        return active_pm, active_map, iteration-1, plan


    def devide_situation(self, active_pm, check_pm, iteration, agent):
        # say that we are on the next lv of hierarchy
        self.clarification_lv+=1
        logging.info('CLARIFY THE SITUATION. CLARIFICATION LEVEL: {0}'.format(self.clarification_lv))

        #define new start situation
        var = active_pm.sign.images[1].spread_down_activity_view(1)['cell-4']
        objects = self.additions[0][iteration]['objects']
        map_size = self.additions[3]['map_size']
        borders = self.additions[3]['wall']
        x_size = (var[2] - var[0]) / 6
        y_size = (var[3] - var[1]) / 6
        size = [objects[agent]['x'] - x_size, objects[agent]['y'] - y_size, objects[agent]['x'] + x_size, objects[agent]['y'] + y_size]
        rmap = [0, 0]
        rmap.extend(map_size)
        # division into regions and cells
        region_location, region_map = locater('region-', rmap, objects, borders)
        cell_location, cell_map, near_loc, cell_coords, clar_lv = cell_creater(size, objects, region_location, borders)
        self.clarification_lv += clar_lv

        sit_name = st.SIT_PREFIX + str(st.SIT_COUNTER)
        st.SIT_COUNTER += 1
        events, direction, holding = self.pm_parser(active_pm, agent)
        agent_state = state_prediction(self.world_model['I'], direction, holding)
        active_sit_new = define_situation(sit_name + 'sp', cell_map, events, agent_state, self.world_model)
        active_map = define_map(st.MAP_PREFIX + str(st.SIT_COUNTER), region_map, cell_location, near_loc,
                                self.additions[1],
                                self.world_model)
        st.SIT_COUNTER += 1
        iteration+=1
        state_fixation(active_sit_new, cell_coords, self.world_model, 'cell')
        self.additions[0][iteration] = deepcopy(self.additions[0][iteration-1])
        self.additions[2][iteration] = cell_map

        #define new finish situation or check finish achievement
        if self.clarification_lv == self.goal_state['cl_lv']:
            logging.info('UCHIEVED THE GOAL CLARIFICATION LEVEL: {0}'.format(self.clarification_lv))
            goal_sit_new = check_pm
            goal_map = signs['*goal_map*'].meanings[1]
        else:
            goal_size = [self.goal_state['objects'][agent]['x'] - x_size, self.goal_state['objects'][agent]['y'] - y_size, self.goal_state['objects'][agent]['x'] + x_size, self.goal_state['objects'][agent]['y'] + y_size]
            region_location, region_map = locater('region-', rmap, self.goal_state['objects'], borders)
            cell_location, cell_map, near_loc, cell_coords, clar_lv = cell_creater(goal_size, self.goal_state['objects'], region_location, borders)
            events, direction, holding = self.pm_parser(check_pm, agent)
            agent_state = state_prediction(self.world_model['I'], direction, holding)
            goal_sit_new = define_situation(sit_name + 'sp', cell_map, events, agent_state, self.world_model)
            goal_map = define_map(st.MAP_PREFIX + str(st.SIT_COUNTER), region_map, cell_location, near_loc,
                                    self.additions[1],
                                    self.world_model)
            st.SIT_COUNTER += 1
            state_fixation(goal_sit_new, cell_coords, self.world_model, 'cell')

        return active_sit_new, goal_sit_new, active_map, goal_map, iteration

    def clarify_search(self, agent, active_pm, check_pm, iteration, current_plan):

        #devide sit
        active_sit_new, goal_sit_new, active_map, goal_map, iteration = self.devide_situation(active_pm, check_pm, iteration, agent)

        clarify_mean = self.world_model['Clarify'].add_meaning()
        connector = clarify_mean.add_feature(active_pm)
        active_pm.sign.add_out_meaning(connector)
        connector = clarify_mean.add_feature(active_sit_new, effect=True)
        active_sit_new.sign.add_out_meaning(connector)
        current_plan.append((active_pm, 'Clarify', clarify_mean, self.world_model['I'], current_plan[-1][4], current_plan[-1][5]))

        #start planning process
        plans = self._map_iteration(active_sit_new, active_map, iteration=iteration, current_plan=current_plan, Ch_m=goal_map, Ch_pm=goal_sit_new)

        current_plan = None
        if plans:
            current_plan = plans[0]
            active_pm = current_plan[-1][0]
            iteration += len(current_plan)

        return current_plan, active_pm, active_map, iteration

    def __get_agents(self):
        agent_back = set()
        I_sign = self.world_model['I']
        agent_back.add(I_sign)
        I_objects = [con.in_sign for con in I_sign.out_significances if con.out_sign.name == "I"]
        if I_objects:
            I_obj = I_objects[0]
        else:
            I_obj = None
        They_sign = self.world_model["They"]
        agents = They_sign.spread_up_activity_obj("significance", 1)
        for cm in agents:
            agent_back.add(cm.sign)
        return I_sign, I_obj, agent_back

    def _generate_meanings(self, chains):
        def __get_role_index(chain):
            index = 0
            rev_chain = reversed(chain)
            for el in rev_chain:
                if len(el.cause) == 0:
                    continue
                elif len(el.cause) == 1:
                    if len(el.cause[0].coincidences) ==1:
                        index = chain.index(el)
                    else:
                        return index
                else:
                    return index
            return None

        def __get_big_role_index(chain):
            index = None
            for el in chain:
                if len(el.cause) == 1:
                    if len(el.cause[0].coincidences) ==1:
                        index = chain.index(el)
                        break
                else:
                    continue
            if index:
                return index
            return None
        def __merge_predicates(predicates):
            merged = set()
            predics = copy(predicates)
            while predics:
                pred = predics.pop()
                for pr in predics:
                    if pr.name != pred.name:
                        if set(pred.signature) & set(pr.signature):
                            predics.remove(pr)
                            merged.add((pred, pr))
            return merged

        big_replace = {}

        replace_map = {}
        main_pm = None
        for chain in chains:
            role_index = __get_role_index(chain)
            if role_index:
                if not chain[role_index].sign in replace_map:
                    replace_map[chain[role_index].sign] = [chain[-1]]
                else:
                    if not chain[-1] in replace_map[chain[role_index].sign]:
                        replace_map[chain[role_index].sign].append(chain[-1])
            role_index = __get_big_role_index(chain)
            if role_index:
                if not chain[role_index].sign in big_replace:
                    big_replace[chain[role_index].sign] = [chain[role_index + 1]]
                else:
                    if not chain[role_index + 1] in big_replace[chain[role_index].sign]:
                        big_replace[chain[role_index].sign].append(chain[role_index + 1])
                main_pm = chain[0]

        connectors = [agent.out_meanings for agent in self.agents]

        main_pm_len = len(main_pm.cause) + len(main_pm.effect) + 2

        # too long! 45k connectors from pick-up!
        mapped_actions = {}
        for agent_con in connectors:
            for con in agent_con:
                if con.in_sign == main_pm.sign:
                    mapped_actions.setdefault(con.out_sign, set()).add(con.in_sign.meanings[con.in_index])

        new_map = {}
        rkeys = {el for el in replace_map.keys()}
        pms = []

        if self.constraints:
            replaced = dict()
            pms_names = []
            for ag, actions in mapped_actions.items():
                # # firstly full signed actions from experience
                for pm in actions.copy():
                    # # remove expanded actions
                    max_len = 0
                    for event in pm.cause:
                        if len(event.coincidences) > max_len:
                            max_len = len(event.coincidences)
                            if max_len > 1:
                                break
                    if max_len == 1:
                        actions.remove(pm)
                        continue
                    if len(pm.cause) + len(pm.effect) != main_pm_len:
                        continue
                    pm_signs = pm.get_signs()
                    role_signs = rkeys & pm_signs
                    if not role_signs:
                        actions.remove(pm)
                        if not pms:
                            pms.append((ag, pm))
                            pms_names.append({s.name for s in pm_signs})
                        else:
                            for _, pmd in copy(pms):
                                if pmd.resonate('meaning', pm):
                                    break
                            else:
                                pms.append((ag, pm))
                                pms_names.append({s.name for s in pm_signs})
                ## get characters from constr to replace
                agcall = ag.name
                if ag.name == 'I':
                    agcall = self.I_obj.name
                if not agcall in self.constraints:
                    continue
                else:
                    constrain = self.constraints[agcall]
                variants = []
                for constr_role, predicates in constrain.items():
                    merged = __merge_predicates(predicates)
                    for sets in merged:
                        consist = [set(), []]
                        for pred in sets:
                            for signa in pred.signature:
                                if signa[1][0].name in constr_role:
                                    if not signa[0] in consist[1]:
                                        consist[1].append(signa[0])
                                else:
                                    consist[0].add(signa[0])
                        for names in pms_names:
                            if consist[0] <= names and consist[1][0] in names:
                                break
                        else:
                            variants.append((constr_role, consist))
                for act in actions:

                    cm_sign_names = {si.name for si in act.get_signs()}
                    for var in variants:
                        if var[1][0] <= cm_sign_names:
                            cm = act.copy('meaning', 'meaning')
                            for rkey, rvalue in replace_map.items():
                                if rkey.name == var[0]:
                                    obj_pm = None
                                    for pm in rvalue:
                                        if pm.sign.name == var[1][1][0]:
                                            obj_pm = pm
                                            break
                                    obj_cm = obj_pm.copy('significance', 'meaning')
                                    cm.replace('meaning', rkey, obj_cm)
                                    replaced.setdefault(ag, []).append(cm)
                                    break
            if replaced:
                mapped_actions = replaced


        for agent, lpm in mapped_actions.items():
            for pm in lpm.copy():
                if len(pm.cause) + len(pm.effect) != main_pm_len:
                    lpm.remove(pm)
                    continue
                pm_signs = set()
                pm_mean = pm.spread_down_activity('meaning', 3)
                for pm_list in pm_mean:
                    pm_signs |= set([c.sign for c in pm_list])
                role_signs = rkeys & pm_signs
                if not role_signs:
                    lpm.remove(pm)
                    if not pms:
                        pms.append((agent, pm))
                    else:
                        for _, pmd in copy(pms):
                            if pmd.resonate('meaning', pm):
                                break
                        else:
                            pms.append((agent, pm))
            old_pms = []

            for pm in lpm:
                if len(pm.cause) + len(pm.effect) != main_pm_len:
                    continue
                pm_signs = set()
                pm_mean = pm.spread_down_activity('meaning', 3)
                for pm_list in pm_mean:
                    pm_signs |= set([c.sign for c in pm_list])
                if pm_signs not in old_pms:
                    old_pms.append(pm_signs)
                else:
                    continue
                role_signs = rkeys & pm_signs
                for role_sign in role_signs:
                    new_map[role_sign] = replace_map[role_sign]

                for chain in pm_mean:
                    if chain[-1].sign in big_replace and not chain[-1].sign in new_map :
                        for cm in big_replace.get(chain[-1].sign):
                            if self.world_model['cell?x'] in cm.get_signs() and self.world_model['cell?y'] in cm.get_signs():
                                new_map[chain[-1].sign] = [cm]


                ma_combinations = self.mix_pairs(new_map)

                for ma_combination in ma_combinations:
                    cm = pm.copy('meaning', 'meaning')
                    breakable = False
                    for role_sign, obj_pm in ma_combination.items():
                        if obj_pm.sign in pm_signs:
                            breakable = True
                            break
                        obj_cm = obj_pm.copy('significance', 'meaning')
                        cm.replace('meaning', role_sign, obj_cm)
                    if breakable:
                        continue

                    for matr in cm.spread_down_activity('meaning', 6):
                        if matr[-1].sign.name == 'cell?y' or matr[-1].sign.name == 'cell?x':
                            celly = self.world_model['cell?y']
                            cellx = self.world_model['cell?x']
                            cell_y_change = ma_combination[celly].copy('meaning', 'meaning')
                            cm.replace('meaning', celly, cell_y_change)
                            cell_x_change = ma_combination[cellx].copy('meaning', 'meaning')
                            cm.replace('meaning', cellx, cell_x_change)
                            break

                    if not pms:
                        pms.append((agent, cm))
                    else:
                        for _, pmd in copy(pms):
                            if pmd.resonate('meaning', cm):
                                break
                        else:
                            pms.append((agent, cm))
                if len(old_pms) == 64:
                    break

        return pms

    def _check_activity(self, pm, active_pm):
        if len(pm.cause) and len(pm.effect):
            result = True
        else:
            result = False
        for event in pm.cause:
            for fevent in active_pm.cause:
                if event.resonate('meaning', fevent, True, self.logic):
                    break
            else:
                result = False
                break

        if not result:
            expanded = pm.expand('meaning')
            if not len(expanded.effect) == 0:
                return self._check_activity(expanded, active_pm)
            else:
                return False, pm
        return result, pm

    def _check_result(self, pm, result_pm):
        if len(pm.effect):
            result = True
        else:
            result = False
        for event in pm.effect:
            for fevent in result_pm.cause:
                if event.resonate('meaning', fevent, True, self.logic):
                    break
            else:
                result = False
                break
        return result, pm

    def long_relations(self, plans):
        logging.info("Choosing the plan for auction")
        min = len(plans[0])
        for plan in plans:
            if len(plan) < min:
                min = len(plan)
        plans = [plan for plan in plans if len(plan) == min]

        busiest = []
        for index, plan in enumerate(plans):
            previous_agent = ""
            agents = {}
            counter = 0
            plan_agents = []
            for action in plan:
                if action[3] not in agents:
                    agents[action[3]] = 1
                    previous_agent = action[3]
                    counter = 1
                    if not action[3] is None:
                        plan_agents.append(action[3].name)
                    else:
                        plan_agents.append(str(action[3]))
                elif not previous_agent == action[3]:
                    previous_agent = action[3]
                    counter = 1
                elif previous_agent == action[3]:
                    counter += 1
                    if agents[action[3]] < counter:
                        agents[action[3]] = counter
            # max queue of acts
            longest = 0
            agent = ""
            for element in range(len(agents)):
                item = agents.popitem()
                if item[1] > longest:
                    longest = item[1]
                    agent = item[0]
            busiest.append((index, agent, longest, plan_agents))
        cheap = []
        alternative = []
        cheapest = []
        longest = 0
        min_agents = 100

        for plan in busiest:
            if plan[2] > longest:
                longest = plan[2]

        for plan in busiest:
            if plan[2] == longest:
                if len(plan[3]) < min_agents:
                    min_agents = len(plan[3])

        for plan in busiest:
            if plan[3][0]:
                if plan[2] == longest and len(plan[3]) == min_agents and "I" in plan[3]:
                    plans_copy = copy(plans)
                    cheap.append(plans_copy.pop(plan[0]))
                elif plan[2] == longest and len(plan[3]) == min_agents and not "I" in plan[3]:
                    plans_copy = copy(plans)
                    alternative.append(plans_copy.pop(plan[0]))
            else:
                plans_copy = copy(plans)
                cheap.append(plans_copy.pop(plan[0]))
        if len(cheap) >= 1:
            cheapest.extend(random.choice(cheap))
        elif len(cheap) == 0 and len(alternative):
            logging.info("There are no plans in which I figure")
            cheapest.extend(random.choice(alternative))

        return cheapest

    def _meta_check_activity(self, active_pm, scripts, prev_pms, iteration, prev_state, prev_act):
        heuristic = []
        if self.logic == 'spatial':
            for agent, script in scripts:
                if agent is None: agent = self.world_model['I']
                estimation, cell_coords_new, new_x_y, \
                cell_location, near_loc, region_map, current_direction = self._state_prediction(active_pm, script, agent, iteration)
                old_cl_lv = self.clarification_lv
                if 'task' in script.sign.name and not 'sub' in script.sign.name:
                    self.clarification_lv = self.goal_state['cl_lv']

                if not new_x_y['objects']['agent']['x'] in range(0, self.additions[3]['map_size'][0]) or \
                        not new_x_y['objects']['agent']['y'] in range(0, self.additions[3]['map_size'][1]):
                    break

                for prev in prev_pms:
                    if estimation.resonate('meaning', prev, False, False):
                        if cell_coords_new['cell-4'] in prev_state and self.clarification_lv == 0:
                            break
                else:
                    counter = 0
                    cont_region = None
                    goal_region = None
                    for reg, cellz in cell_location.items():
                        if 'cell-4' in cellz:
                            cont_region = reg
                            break
                    agent_sign = self.world_model['agent']
                    for iner in self.check_map.get_iner(self.world_model['contain'], 'meaning'):
                        iner_signs = iner.get_signs()
                        if agent_sign in iner_signs:
                            for sign in iner_signs:
                                if sign != agent_sign and 'region' in sign.name:
                                    goal_region = sign
                                    break
                        if goal_region:
                            break
                    if not 'task' in script.sign.name:
                        stright = self.get_stright(active_pm, current_direction)
                    else:
                        stright = self.get_stright(estimation, current_direction)
                    if goal_region.name != cont_region:
                        goal_dir = self.additions[1][cont_region][goal_region.name][1]
                        # do not rotate to the wall if there are no hole
                        if current_direction.name == goal_dir:
                            if stright[1] and not self.clarification_lv < self.goal_state['cl_lv']:
                                counter = 0
                            else:
                                counter += 2 # +2 if current dir is the same to goal dir
                        # for move action
                        elif cell_coords_new['cell-4'] != active_pm.sign.images[1].spread_down_activity_view(1)['cell-4']:
                            if not stright[1]:
                                counter += 1 # +1
                                if prev_act == 'rotate':
                                    counter+=2
                        # for pick-up and put-down actions
                        elif self.difference(active_pm, estimation)[0]:
                            old = self.difference(active_pm, estimation)[1]
                            for event1 in old:
                                for event2 in self.check_pm.cause:
                                    if event1.resonate('meaning', event2):
                                        break
                                else:
                                    counter+=3
                        else:
                            # check closely to goal region regions
                            closely_goal = [reg for reg, ratio in self.additions[1][goal_region.name].items() if
                                            ratio[0] == 'closely']
                            closely_dirs = set()
                            if cont_region not in closely_goal:
                                for region in closely_goal:
                                    closely_dirs.add(self.additions[1][cont_region][region][1])
                                if current_direction.name in closely_dirs:
                                    if stright[1]:
                                        counter = 0
                                    else:
                                        counter += 2 # +2 if rotate to closely to goal region
                            else:
                                if current_direction.name == goal_dir:
                                    counter += 2 # +2 if in closely reg and rotate to future_reg
                                elif not stright[1]:
                                    if self.cell_closer(cell_coords_new['cell-4'],cell_coords_new[stright[0].name], 'agent'):
                                        counter+=1

                        if self.linear_cell(cell_coords_new['cell-4'],cell_coords_new[stright[0].name], 'agent'):
                            if not stright[1]:
                                counter +=2 # +2 if agent go back to the stright goal way #TODO rework when go from far

                    else:
                        if self.clarification_lv <= self.goal_state['cl_lv']:
                            est_events = [event for event in estimation.cause if "I" not in event.get_signs_names()]
                            ce_events = [event for event in self.check_pm.cause if "I" not in event.get_signs_names()]
                            for event in est_events:
                                for ce in ce_events:
                                    if event.resonate('meaning', ce):
                                        counter += 1
                                        break
                        elif self.clarification_lv > self.goal_state['cl_lv']:
                            if stright[1] is None:
                            # choose direction closely to  goal direction
                                closely_to_stright = ['cell'+el[-2:] for el,desc in
                                                  self.additions[1]['region'+stright[0].name[-2:]].items() if desc[0] == 'closely']
                                closely_to_stright.remove('cell-4')
                                for cell in closely_to_stright:
                                    if 0 not in self.additions[2][iteration][cell]:
                                        break
                                else:
                                    counter+=3
                                directions = []
                                for reg, tup in self.additions[1]['region-4'].items():
                                    if tup[1] == self.goal_state['agent-orientation']:
                                        regs_to_goal = [reg for reg, tup2 in self.additions[1][reg].items() if tup2[0] == 'closely']
                                        directions = [tup[1] for reg, tup in self.additions[1]['region-4'].items() if reg in regs_to_goal]
                                        break
                                if current_direction.name in directions:
                                    counter+=2
                                if prev_act == 'rotate' and script.sign.name == 'move':
                                    counter+=2
                                elif prev_act == 'rotate' and script.sign.name == 'rotate':
                                    counter = 0

                        if 'task' in script.sign.name:
                            counter +=10

                        if 'task' in script.sign.name and not 'sub' in script.sign.name:
                            self.clarification_lv = old_cl_lv
                    heuristic.append((counter, script.sign.name, script, agent))
        elif self.logic == 'classic':
            for agent, script in scripts:
                estimation = self._time_shift_forward(active_pm, script)
                for prev in prev_pms:
                    if estimation.resonate('meaning', prev, False, False):
                        break
                else:
                    counter = 0
                    for event in self._applicable_events(estimation):
                        for ce in self._applicable_events(self.check_pm):
                            if event.resonate('meaning', ce):
                                counter += 1
                                break
                    heuristic.append((counter, script.sign.name, script, agent))
        if heuristic:
            best_heuristics = max(heuristic, key=lambda x: x[0])
            return list(filter(lambda x: x[0] == best_heuristics[0], heuristic))
        else:
            return None

    def difference(self, active, estim):
        old = active - estim
        new = estim - active
        eq = False
        if len(old) != len(new):
            eq = True
        return eq, old, new

    def cell_closer(self, curcell, fcell, agent):
        ag_plce = self.goal_state['objects'][agent]['x'], self.goal_state['objects'][agent]['y']
        cur_mid = curcell[0]+(curcell[2] - curcell[0])/2 , curcell[1] + (curcell[3]-curcell[1])/2
        fcell_mid = fcell[0]+(fcell[2] - fcell[0])/2 , fcell[1] + (fcell[3]-fcell[1])/2
        if (((fcell_mid[0] - ag_plce[0]) ** 2 + (fcell_mid[1] - ag_plce[1]) ** 2) ** (0.5)) < \
                (((cur_mid[0] - ag_plce[0]) ** 2 + ((cur_mid[1] - ag_plce[1]) ** 2)) ** (0.5)):
            return True
        return False

    def linear_cell(self, curcell, fcell, agent):
        delta = 3
        cur_mid = curcell[0]+(curcell[2] - curcell[0])/2 , curcell[1] + (curcell[3]-curcell[1])/2
        fcell_mid = fcell[0]+(fcell[2] - fcell[0])/2 , fcell[1] + (fcell[3]-fcell[1])/2
        ag_plce = self.goal_state['objects'][agent]['x'], self.goal_state['objects'][agent]['y']
        if fcell_mid[0]-delta <= ag_plce[0] <= fcell_mid[0]+ delta or fcell_mid[1]-delta <= ag_plce[1] <= fcell_mid[1]+ delta:
            if (((fcell_mid[0] - ag_plce[0])**2 + (fcell_mid[1] - ag_plce[1])**2)**(0.5)) < \
                    (((cur_mid[0] - ag_plce[0])**2 + ((cur_mid[1] - ag_plce[1])**2))**(0.5)):
                return True

        return False

    def _applicable_events(self, pm, effect = False):
        applicable = []
        if effect:
            search_in_part = pm.effect
        else:
            search_in_part = pm.cause
        for event in search_in_part:
            if len(event.coincidences) == 1:
                flag = False
                for connector in event.coincidences:
                    if connector.out_sign in self.agents:
                        flag = True
                if flag:
                    continue
            applicable.append(event)
        return applicable

    def recursive_files(self, direct, ext):
        import os
        extfiles = []
        for root, subfolder, files in os.walk(direct):
            for file in files:
                if file.endswith(ext):
                    extfiles.append(os.path.join(root, file))
            for sub in subfolder:
                extfiles.extend(self.recursive_files(os.path.join(root, sub), ext))
            return extfiles

    def scale_history_situation(self, history_benchmark, iteration):
        new_objects = {}

        for stobj, scoords in history_benchmark['start']['objects'].items():
            for curobj, curcoords in self.additions[0][iteration]['objects'].items():
                if stobj == curobj:
                    koef_x = curcoords['x'] - scoords['x']
                    koef_y = curcoords['y'] - scoords['y']
                    new_objects[curobj] = {'x': history_benchmark['finish']['objects'][stobj]['x']+koef_x,
                                           'y': history_benchmark['finish']['objects'][stobj]['y']+koef_y,
                                           'r': history_benchmark['finish']['objects'][stobj]['r']}

        return {'objects': new_objects}, {'map_size': self.additions[3]['map_size'], 'wall': self.additions[3]['wall']}


    def history_action(self, active_pm, script, agent, iteration):
        import os
        import pkg_resources
        import json
        benchmark = None
        history_benchmark = None
        paths = []
        delim = '/'
        for name in os.listdir('.'):
            if 'benchmark' in name.lower():
                paths.append('.' + delim +name + delim)
        if not paths:
            if not benchmark:
                paths.append(pkg_resources.resource_filename('mapplanner', 'benchmarks'))
        for direct in paths:
            files = self.recursive_files(direct, '.json')
            for file in files:
                with open(file) as data:
                    jfile = json.load(data)
                    if 'task-name' in jfile:
                        if jfile['task-name'] in script.sign.name:
                            history_benchmark = jfile
                            break
                        else:
                            continue
                    else:
                        continue

        parsed, static = self.scale_history_situation(history_benchmark, iteration)

        region_map, cell_map, cell_location, near_loc, cell_coords, _, _ = signs_markup(parsed, static, 'agent')
        events = []
        for ev in active_pm.cause:
            if len(ev.coincidences) == 1:
                for con in ev.coincidences:
                    if con.out_sign.name == "I":
                        events.append(ev)

        orientation = history_benchmark['finish']['agent-orientation']
        direction = self.world_model[orientation]

        history_benchmark['finish']['objects'].update(parsed['objects'])
        new_x_y = history_benchmark['finish']
        new_x_y['map_size'] = self.additions[3]['map_size']
        # new_x_y['wall'] = self.additions[3]['wall']

        agent_state = state_prediction(agent, history_benchmark['finish'])

        sit_name = st.SIT_PREFIX + str(st.SIT_COUNTER)
        st.SIT_COUNTER+=1
        estimation = define_situation(sit_name + 'sp', cell_map, events, agent_state, self.world_model)
        state_fixation(estimation, cell_coords, signs, 'cell')

        return cell_map, direction, estimation, cell_coords, new_x_y, cell_location, \
            near_loc, region_map

    def __search_cm(self, events_list, signs):
        searched = {}
        for event in events_list:
            for conn in event.coincidences:
                if conn.out_sign in signs:
                    searched.setdefault(conn.out_sign, []).append(conn.get_out_cm('meaning'))
        for s in signs:
            if not s in searched:
                searched[s] = None
        return searched

    def new_action(self, active_pm, script, agent, iteration):
        direction = None
        cell = None
        events = []

        fast_estimation = self._time_shift_forward_spat(active_pm, script)
        searched = self.__search_cm(fast_estimation, [self.world_model['orientation'], self.world_model['holding'], self.world_model['employment']] )

        employment = searched[self.world_model['employment']][0]
        holding = searched[self.world_model['holding']]
        if holding:
            holding = holding[0]
        orientation = searched[self.world_model['orientation']][0]
        for sign in orientation.get_signs():
            if sign != agent and sign != self.world_model['I']:
                direction = sign
                break
        for sign in employment.get_signs():
            if sign != agent:
                cell = sign
                break
        for ev in fast_estimation:
            if len(ev.coincidences) == 1:
                for con in ev.coincidences:
                    if con.out_sign.name == "I":
                        events.append(ev)
            elif not holding:
                if "I" in [s.name for s in ev.get_signs()]:
                    events.append(ev)
        agent_state = state_prediction(agent, direction, holding)

        cell_coords = active_pm.sign.images[1].spread_down_activity_view(depth = 1)[cell.name]

        new_x_y = deepcopy(self.additions[0][iteration])
        new_x_y['objects']['agent']['x'] = (cell_coords[2] - cell_coords[0]) // 2 + cell_coords[0]
        new_x_y['objects']['agent']['y'] = (cell_coords[3] - cell_coords[1]) // 2 + cell_coords[1]
        # for pick-up script
        if holding:
            block_name = [sign.name for sign in holding.get_signs() if 'block' in sign.name][0]
            if block_name in new_x_y['objects'].keys():
                new_x_y['objects'][block_name]['y'] = new_x_y['objects']['agent']['y']
                new_x_y['objects'][block_name]['x'] = new_x_y['objects']['agent']['x']
            else:
                block = {}
                block[block_name] = {'x': new_x_y['objects']['agent']['x'], 'y': new_x_y['objects']['agent']['y'], 'r': 5}
                new_x_y['objects'].update(block)

        # for put-down script
        if script.sign.name == 'put-down':
            block_name = [sign.name for sign in script.get_iner(self.world_model['holding'], 'meaning')[0].get_signs() if
                          'block' in sign.name][0]
            table_name = [sign.name for sign in script.get_iner(self.world_model['ontable'], 'meaning')[0].get_signs() if
                          sign.name != block_name][0]
            new_x_y['objects'][block_name]['y'] = new_x_y['objects'][table_name]['y']
            new_x_y['objects'][block_name]['x'] = new_x_y['objects'][table_name]['x']
        region_map, cell_map, cell_location, near_loc, cell_coords_new, _,_ = signs_markup(new_x_y, self.additions[3], 'agent', cell_coords)
        sit_name = st.SIT_PREFIX + str(st.SIT_COUNTER)
        st.SIT_COUNTER+=1
        estimation = define_situation(sit_name + 'sp', cell_map, events, agent_state, self.world_model)
        estimation = update_situation(estimation, cell_map, self.world_model, fast_estimation)
        state_fixation(estimation, cell_coords_new, signs, 'cell')

        return cell_map, direction, estimation, cell_coords_new, new_x_y, cell_location, near_loc, region_map

    def sub_action(self, active_pm, script, agent, iteration):
        applicable = []
        direction = None
        for sit in self.exp_sits:
            result, checked = self._check_result(script, sit)
            if result:
                applicable.append(sit)
        for estimation in applicable:
            #TODO check all sits by map comparison
            #cell_coords = sit.sign.images[1].spread_down_activity_view(depth=1)
            searched = self.__search_cm(estimation.cause, [self.world_model['orientation'], self.world_model['holding'],
                                                          self.world_model['employment']])

            orientation = searched[self.world_model['orientation']][0]
            for sign in orientation.get_signs():
                if sign != agent and sign != self.world_model['I']:
                    direction = sign
                    break
            cell_coords = estimation.sign.images[1].spread_down_activity_view(depth=1)
            new_x_y = deepcopy(self.additions[0][iteration])
            new_x_y['objects']['agent']['x'] = (cell_coords['cell-4'][2] - cell_coords['cell-4'][0]) // 2 + cell_coords['cell-4'][0]
            new_x_y['objects']['agent']['y'] = (cell_coords['cell-4'][3] - cell_coords['cell-4'][1]) // 2 + cell_coords['cell-4'][1]
            new_x_y['agent-orientation'] = direction.name
            region_map, cell_map, cell_location, near_loc, _, _, _ = signs_markup(new_x_y,self.additions[3],
                                                                                                'agent', cell_coords['cell-4'])
            state_fixation(estimation, cell_coords, signs, 'cell')

            return cell_map, direction, estimation, cell_coords, new_x_y, cell_location, \
            near_loc, region_map



    def _state_prediction(self, active_pm, script, agent, iteration, flag=False):
        if script.sign.images and 'task' in script.sign.name and not 'sub' in script.sign.name:
            cell_map, direction, estimation, cell_coords_new, new_x_y, cell_location, \
            near_loc, region_map = self.history_action(active_pm, script, agent, iteration)
        elif script.sign.images and 'sub' in script.sign.name:
            cell_map, direction, estimation, cell_coords_new, new_x_y, cell_location, \
            near_loc, region_map = self.sub_action(active_pm, script, agent, iteration)
        else:
            cell_map, direction, estimation, cell_coords_new, new_x_y, cell_location, \
            near_loc, region_map = self.new_action(active_pm, script, agent, iteration)

        if flag:
            region = None
            for reg, cellz in cell_location.items():
                if 'cell-4' in cellz:
                    region = reg
                    break
            self.additions[2][iteration+1] = cell_map
            print("act: {0}, cell: {1}, dir: {2}, reg: {3}".format(script.sign.name, cell_coords_new['cell-4'],
                                                                   direction.name, region))
            return estimation, cell_coords_new, new_x_y, cell_location, near_loc, region_map, direction.name

        return estimation, cell_coords_new, new_x_y, cell_location, near_loc, region_map, direction

    def _step_generating(self, active_pm, active_map, script, agent, iteration, prev_state, param):
        next_pm, cell_coords, parsed_map, cell_location, \
            near_loc, region_map, direction = self._state_prediction(active_pm, script, agent, iteration, param)
        prev_state.append(cell_coords['cell-4'])
        state_fixation(next_pm, cell_coords, signs, 'cell')
        self.additions[0][iteration + 1] = parsed_map
        if self.change_map(active_map, cell_location):
            active_map = define_map(st.MAP_PREFIX + str(st.SIT_COUNTER), region_map, cell_location, near_loc, self.additions[1],
                                 self.world_model)
            print('map has been changed!')
        elif iteration > 0:
            if list(self.additions[2][iteration].values()) != list(self.additions[2][iteration - 1].values()):
                active_map = define_map(st.MAP_PREFIX + str(st.SIT_COUNTER), region_map, cell_location, near_loc,
                                     self.additions[1], self.world_model)
            elif self.clarification_lv > 0:
                active_map = define_map(st.MAP_PREFIX + str(st.SIT_COUNTER), region_map, cell_location, near_loc,
                                        self.additions[1], self.world_model)

        return next_pm, active_map, prev_state, direction

    def _time_shift_backward(self, active_pm, script):
        next_pm = Sign(st.SIT_PREFIX + str(st.SIT_COUNTER))
        self.world_model[next_pm.name] = next_pm
        pm = next_pm.add_meaning()
        st.SIT_COUNTER += 1
        copied = {}
        for event in active_pm.cause:
            for es in script.effect:
                if event.resonate('meaning', es):
                    break
            else:
                pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))
        for event in script.cause:
            pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))
        return pm

    def _time_shift_forward(self, active_pm, script):
        next_pm = Sign(st.SIT_PREFIX + str(st.SIT_COUNTER))
        self.world_model[next_pm.name] = next_pm
        pm = next_pm.add_meaning()
        st.SIT_COUNTER += 1
        copied = {}
        for event in active_pm.cause:
            for es in script.cause:
                if event.resonate('meaning', es):
                    break
            else:
                pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))
        for event in script.effect:
            pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))
        return pm

    def _time_shift_forward_spat(self, active_pm, script):
        pm_events = []
        for event in active_pm.cause:
            for es in script.cause:
                if event.resonate('meaning', es):
                    break
            else:
                pm_events.append(event)
        for event in script.effect:
            pm_events.append(event)
        return pm_events

    def change_map(self, active_map, cell_location):
        pms = active_map.spread_down_activity('meaning', 4)
        pm_list = []
        contain_reg = None
        for location, cells in cell_location.items():
            if 'cell-4' in cells:
                contain_reg = location
        for iner in pms:
            iner_names = [s.sign.name for s in iner]
            if 'include' in iner_names:
                pm_list.append(iner[-1])
        for pm in pm_list:
            if pm.sign.name != 'cell-4':
                if pm.sign.name == contain_reg:
                    return False
        return True

    def get_stright(self, estimation, dir_sign):
        es = estimation.spread_down_activity('meaning', 4)
        grouped = {}
        for key, group in itertools.groupby(es, lambda x: x[1]):
            for pred in group:
                grouped.setdefault(key, []).append(pred[-1])
        stright_cell = None
        used_key = None
        for key, item in grouped.items():
            it_signs = {am.sign for am in item}
            if dir_sign in it_signs:
                stright_cell = [sign for sign in it_signs if
                                sign.name != 'cell-4' and sign != dir_sign and sign.name != "I"]
                if stright_cell:
                    stright_cell = stright_cell[0]
                    used_key = key
                    break
        for key, item in grouped.items():
            if key != used_key:
                it_signs_names = {am.sign.name for am in item}
                if stright_cell.name in it_signs_names:
                    if 'nothing' in it_signs_names:
                        return stright_cell, None
                    else:
                        items = [it for it in item if it.sign != stright_cell and it.sign.name != 'cell-4']
                        if items: return stright_cell, items

    @staticmethod
    def mix_pairs(replace_map):
        new_chain = {}
        elements = []
        merged_chains = []
        used_roles = []
        replace_map = list(replace_map.items())

        def get_role(obj, roles):
            for role in roles:
                if obj in role[1]:
                    return role

        for item in replace_map:
            elements.append(item[1])
        elements = list(itertools.product(*elements))
        clean_el = copy(elements)
        for element in clean_el:
            if not len(set(element)) == len(element):
                elements.remove(element)
        for element in elements:
            for obj in element:
                avalaible_roles = [x for x in replace_map if x not in used_roles]
                role = get_role(obj, avalaible_roles)
                if role:
                    used_roles.append(role)
                    new_chain[role[0]] = obj
            merged_chains.append(new_chain)
            new_chain = {}
            used_roles = []
        return merged_chains















