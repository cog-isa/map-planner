import itertools
import re
from copy import copy
import sys

from mapcore.grounding.sign_task import *


DEFAULT_FILE_PREFIX = 'wmodel_'
DEFAULT_FILE_SUFFIX = '.swm'

SIT_COUNTER = 0
SIT_PREFIX = 'situation_'
PLAN_PREFIX = 'action_'
MAP_PREFIX = 'map_'


class SpTask(Task):
    def __init__(self, name, signs, start_situation, goal_situation, goal_map, map_pms,
                additions, initial_state, goal_state, static_map):
        super(SpTask, self).__init__(name, signs, start_situation, goal_situation)
        self.goal_map = goal_map
        self.map_pms = map_pms
        self.additions = additions
        self.initial_state = initial_state
        self.static = static_map
        self.goal_state = goal_state

    def save_signs(self, plan):
        """
        Cleaning SWM and saving experience
        :param plan:
        :return:
        """
        def __is_role(pm, agents):
            chains = pm.spread_down_activity('meaning', 6)
            for chain in chains:
                if chain[-1].sign not in agents:
                    if len(chain[-1].sign.significances[1].cause) != 0:
                        break
            else:
                return False
            return True

        logging.info('Plan preparation to save...')

        I_obj = [con.in_sign for con in self.signs["I"].out_significances if con.out_sign.name == "I"]
        if plan:
            logging.info('\tCleaning SWM...')

            agents = [self.signs["I"]]
            agents.extend(I_obj)

            plan_sit = [pm[0].sign for pm in plan]
            plan_map = [pm[5][0].sign for pm in plan]
            if self.start_situation not in plan_sit:
                plan_sit.append(self.start_situation)
            if self.map_pms.sign not in plan_map:
                plan_map.append(self.map_pms.sign)
            if self.goal_situation not in plan_sit:
                plan_sit.append(self.goal_situation)
            if self.goal_map.sign not in plan_map:
                plan_map.append(self.goal_map.sign)
            pms_act = [pm[2] for pm in plan]


            for element in plan:
                if element[2].sign.name == 'Clarify' or element[2].sign.name == 'Abstract':
                    if len(element[2].effect) == 1:
                        start = list(element[2].cause[0].get_signs())[0]
                        finish = list(element[2].effect[0].get_signs())[0]
                    else:
                        mean = None
                        for ind, m in element[2].sign.meanings.items():
                            if len(m.effect) == 1:
                                mean = m
                                break
                        else:
                            print('Can not find matrice with link to situation from images of sign {}'.format(
                                element[1].sign.name))
                        start = list(mean.cause[0].get_signs())[0]
                        finish = list(mean.effect[0].get_signs())[0]
                    plan_sit.append(start)
                    plan_sit.append(finish)

            for name, s in self.signs.copy().items():
                signif=list(s.significances.items())
                if name.startswith(SIT_PREFIX) or name.startswith(MAP_PREFIX):
                    for index, pm in s.meanings.copy().items():
                        if s not in plan_sit and s not in plan_map:
                            s.remove_meaning(pm) # delete all meanings of situations that are not in plan
                        elif index > 1:
                            s.remove_meaning(pm) # delete double meaning from plan situations
                    if s in plan_sit or s in plan_map: # only 1 mean and 1 image per plan sit
                        for index, im in s.images.copy().items():
                            if index > 2:
                                s.remove_view(im)
                    else:
                        for index, im in s.images.copy().items():
                            if index != 2:
                                try:
                                    s.remove_image(im) # remove other
                                except AttributeError:
                                    print()
                            else:
                                s.remove_view(im) # remove view
                        self.signs.pop(name) # delete this situation

                elif len(signif):
                    if len(signif[0][1].cause) and len(signif[0][1].effect): #delete action's meanings that are not in plan
                        for index, pm in s.meanings.copy().items():
                            if __is_role(pm, agents):  # delete only fully signed actions
                                continue
                            else:
                                if pm not in pms_act:
                                    s.remove_meaning(pm)
                        for index, im in s.images.copy().items():
                            s.remove_image(im) # delete all action's images

            self.signs.pop(self.start_situation.name)
            self.signs.pop(self.goal_situation.name)
            self.start_situation.name += self.name
            self.goal_situation.name += self.name

            #saving exp_situations and maps
            exp_signs = []
            for sit in itertools.chain(plan_sit, plan_map):
                if sit.name in self.signs:
                    self.signs.pop(sit.name)
                if sit.name != "*start*" and sit.name != "*finish*":
                    sit_name = sit.name
                elif sit.name == "*start*":
                    sit_name = self.start_situation.name
                else:
                    sit_name = self.goal_situation.name

                exp_signs.append(sit.rename('exp_' + sit_name))

            for exp in exp_signs:
                if exp.name not in self.signs:
                    self.signs[exp.name] = exp

            self.start_situation = self.signs['exp_'+self.start_situation.name]
            self.goal_situation = self.signs['exp_'+ self.goal_situation.name]

            # Todo remove old connections
            self.start_situation.out_meanings = []
            self.goal_situation.out_meanings = []

            #Change situations in Clarify and Abstract actions:
            new_plan = []
            for action in plan:
                if action[2].sign.name == 'Clarify' or action[2].sign.name == 'Abstract':
                    # find exp start and finish
                    act = None
                    for ind, m in action[2].sign.meanings.items():
                        if len(m.effect) == 1:
                            act = m
                            break
                    else:
                        print('Can not find matrice with link to situation from images of sign {}'.format(
                            action[1].sign.name))
                    start = list(act.cause[0].get_signs())[0]
                    finish = list(act.effect[0].get_signs())[0]
                    new_start = [sign for sign in exp_signs if sign.name.endswith(start.name)]
                    new_finish = [sign for sign in exp_signs if sign.name.endswith(finish.name)]
                    if act.index in act.sign.meanings:
                        act.sign.meanings.pop(act.index)
                    # make new CausalMatrix
                    new_cm = act.sign.add_meaning()# check index
                    conn = new_cm.add_feature(new_start[0].meanings[1])
                    new_start[0].add_out_meaning(conn)
                    conn = new_cm.add_feature(new_finish[0].meanings[1], effect=True)
                    new_finish[0].add_out_meaning(conn)
                    new_plan.append((new_start[0].images[1], action[1], new_cm, action[3], action[4], action[5]))
                else:
                    new_start = [act for act in exp_signs if act.name.endswith(action[0].sign.name)]
                    new_plan.append((new_start[0].images[1], action[1], action[2], action[3], action[4], action[5]))
            # update plan
            plan = new_plan
            pms_act = [pm[2] for pm in plan]
            # Save by parts of each size
            logging.info('\tSaving subplans... ')

            subplans = []

            def before_change(index, pms, plan):
                # Return subplan before index
                exp_sign = None
                for con in pms[index].cause[0].coincidences:
                    exp_sign = [sign for sign in exp_signs if sign.name.endswith(con.out_sign.name)][0]
                goal_mean = exp_sign.images[1].copy('image', 'meaning')
                plan_sign, _, _ = self.PlanToAction(self.start_situation.meanings[1], goal_mean, plan[:index+1], 'subplan_'+str(index))
                return plan_sign

            def after_change(index, pms, plan):
                # Return subplan after index
                exp_sign = None
                for con in pms[index].effect[0].coincidences:
                    exp_sign = [sign for sign in exp_signs if sign.name.endswith(con.out_sign.name)][0]
                start_mean = exp_sign.images[1].copy('image', 'meaning')
                plan_sign, _, _ = self.PlanToAction(start_mean, self.goal_situation.meanings[1], plan[index:], 'subplan_'+str(index))
                return plan_sign
            def between_change(start, end, pms, plan):
                # Return subplan between indices
                exp_sign = None
                for con in pms[start].cause[0].coincidences:
                    exp_sign = [sign for sign in exp_signs if sign.name.endswith(con.out_sign.name)][0]
                if not exp_sign.meanings:
                    start_mean = exp_sign.images[1].copy('image', 'meaning')
                else:
                    start_mean = exp_sign.meanings[1]
                for con in pms[end].effect[0].coincidences:
                    exp_sign_vars = [sign for sign in exp_signs if sign.name.endswith(con.out_sign.name)]
                    if exp_sign_vars:
                        exp_sign = exp_signs[0]
                    else:
                        exp_sign = con.out_sign.rename('exp_' + con.out_sign.name)
                        exp_signs.append(exp_sign)
                if not exp_sign.meanings:
                    finish_mean = exp_sign.images[1].copy('image', 'meaning')
                else:
                    finish_mean = exp_sign.meanings[1]
                plan_sign, _, _ = self.PlanToAction(start_mean, finish_mean, plan[start:end+1], 'subplan_'+str(index))
                return plan_sign

            pms_plan = [cm.sign.name+':'+str(pms_act.index(cm)) for cm in pms_act]
            str_plan = ''.join(el+ ' ' for el in pms_plan)
            if 'Abstract' in str_plan and 'Clarify' in str_plan:
                # Save plan between abstr and clarify acts iff the refinement level is identical
                for st, end, _ in self.tree_refinement(str_plan, opendelim='Clarify', closedelim='Abstract'):
                    if not end - st +1 == len(pms_act):
                        if plan[st][-1][1] == plan[end][-1][1]+1:
                            subpl = between_change(st, end, pms_act, plan)
                            subplans.append((subpl, st, len(pms_act) - 1))
            elif 'Abstract' in str_plan and 'Clarify' not in str_plan:
                for el in pms_act:
                    if el.sign.name == 'Abstract':
                        subpl = before_change(pms_act.index(el), pms_act, plan)
                        subplans.append((subpl, 0, pms_act.index(el)))
            elif 'Abstract' not in str_plan and 'Clarify' in str_plan:
                for el in pms_act:
                    if el.sign.name == 'Clarify':
                        subpl = after_change(pms_act.index(el), pms_act, plan)
                        subplans.append((subpl, pms_act.index(el), len(pms_act) - 1))



            logging.info('\tSaving precedent...')
            self.PlanToAction(self.start_situation.meanings[1], self.goal_situation.meanings[1], plan, '',
                            subplans)


        else:
            for name, sign in self.signs.copy().items():
                if name.startswith(SIT_PREFIX) or name.startswith(MAP_PREFIX):
                    self.signs.pop(name)
                else:
                    sign.meanings = {}
                    sign.out_meanings = []
                    sign.images = {}
                    sign.out_images = []
        if I_obj:
            I_obj = "_"+I_obj[0].name
        else:
            I_obj = 'I'
        file_name = DEFAULT_FILE_PREFIX + datetime.datetime.now().strftime('%m_%d_%H_%M') + I_obj + DEFAULT_FILE_SUFFIX
        logging.info('Start saving to {0}'.format(file_name))
        logging.info('\tDumping SWM...')
        pickle.dump(self.signs, open(file_name, 'wb'))
        logging.info('\tDumping SWM finished')
        return file_name

    def tree_refinement(self, line, opendelim, closedelim):
        stack = []
        for m in re.finditer(r'[{}{}]'.format(opendelim, closedelim), line):
            pos = m.start()
            CL = line[pos:pos+len(opendelim)]
            ABS = line[pos: pos+len(closedelim)]
            if CL == opendelim:
                iter = pos + len(opendelim)+1
                curs = line[iter]
                num = ''
                while curs != ' ':
                    num+=curs
                    if iter+1 == len(line)-1:
                        break
                    else:
                        iter+=1
                        curs = line[iter]
                stack.append(eval(num))

            elif ABS == closedelim:
                iter = pos + len(closedelim)+1
                curs = line[iter]
                num = ''
                while curs != ' ' or curs != "'":
                    num+=curs
                    if iter+1 == len(line)-1:
                        break
                    else:
                        iter+=1
                        curs = line[iter]
                #stack.append(eval(num))
                if len(stack) > 0:
                    prevpos = stack.pop()
                    yield prevpos, eval(num), len(stack)
                else:
                    # error
                    print("encountered extraneous closing quote at pos {}: '{}'".format(pos, line[pos:]))
                    pass

        if len(stack) > 0:
            for pos in stack:
                print("expecting closing quote to match open quote starting at: '{}'"
                      .format(line[pos - 1:]))

    def PlanToAction(self, start, finish, PlActs, plan_name, subplans = None):
        # Creating plan action for further use
        if not plan_name:
            plan_name = 'plan_'+ self.name
        if not start.sign.meanings:
            scm = start.copy('image', 'meaning')
            start.sign.add_meaning(scm)
        if not finish.sign.meanings:
            fcm = finish.copy('image', 'meaning')
            finish.sign.add_meaning(fcm)
        plan_sign = Sign(plan_name)
        plan_mean = plan_sign.add_meaning()
        connector = plan_mean.add_feature(start.sign.meanings[1])
        start.sign.add_out_meaning(connector)
        conn = plan_mean.add_feature(finish.sign.meanings[1], effect=True)
        finish.sign.add_out_meaning(conn)
        self.signs[plan_sign.name] = plan_sign

        # Adding Sequence of actions to plan image
        plan_image = plan_sign.add_image()
        iter = -1
        if not subplans:
            for act in PlActs:
                im = act[2].sign.add_image()
                connector = plan_image.add_feature(im)
                act[2].sign.add_out_image(connector)  # add connector to plan_sign threw images to out_image
        else:
            ots = {subplans.index(it): range(it[1], it[2]+1) for it in subplans}
            for act in PlActs:
                iter += 1
                flag = False
                for index, value in ots.items():
                    if iter == value[0]:
                        if subplans[index][0].images:
                            im = subplans[index][0].images[1]
                        else:
                            im  = subplans[index][0].add_image()
                        connector = plan_image.add_feature(im)
                        subplans[index][0].add_out_image(connector)
                        flag = True
                        break
                    elif iter in value:
                        flag = True
                        break
                if flag:
                    continue
                else:
                    im = act[2].sign.add_image()
                    connector = plan_image.add_feature(im)
                    act[2].sign.add_out_image(connector)

        # Adding scenario vs partly concrete actions to the plan sign
        scenario = self.scenario_builder(start, finish, PlActs)
        plan_signif = plan_sign.add_significance()
        for act in scenario:
            connector = plan_signif.add_feature(act)
            act.sign.add_out_significance(connector)

        return [plan_sign, start.sign, finish.sign]

    def scenario_builder(self, start, goal, PlActs):
        # start_signif = start.copy('image', 'significance')
        # goal_signif = goal.copy('image', 'significance')
        # landmarks = goal_signif - start_signif
        scenario = []
        #
        # for act in PlActs:
        #     act_signif = act.copy('meaning', 'significance')
        #     for ev1 in act_signif.effect:
        #         flag = False
        #         for ev2 in landmarks.copy():
        #             if ev1.resonate('significance', ev2):
        #                 landmarks.remove(ev2)
        #                 event_pms = [con.get_out_cm('significance') for con in ev2.coincidences]
        #                 scen_act = act_signif.sign.significances[1].copy('significance', 'significance')
        #                 for pm in event_pms:
        #                     for event in scen_act.effect:
        #                         if pm.sign in event.get_signs():
        #                             event.replace('significance', pm.sign, pm, [])
        #                 scenario.append(scen_act)
        #                 flag = True
        #                 break
        #         if flag:
        #             break
        #     else:
        #         scenario.append(act.sign.significances[1])
        #     act_signif.sign.remove_significance(act_signif)
        # start.sign.remove_significance(start_signif)
        # goal.sign.remove_significance(goal_signif)

        for act in PlActs:
            if act[2].sign.significances:
                scenario.append(act[2].sign.significances[1])
            else:
                signif = act[2].sign.add_significance()
                scenario.append(signif)

        return scenario



    @staticmethod
    def load_signs(agent, file_name=None, load_all = False):
        if not file_name:
            file_name = []
            for f in os.listdir('.'):
                if f.endswith(DEFAULT_FILE_SUFFIX):
                    if f.split(".")[0].endswith(agent) or f.split(".")[0].endswith('agent'):
                        file_name.append(f)
        else:
            file_name = [file_name]
        if file_name:
            if load_all:
                pass
            else:
                newest = 0
                file_load = ''
                for file in file_name:
                    file_signature = int(''.join([i if i.isdigit() else '' for i in file]))
                    if file_signature > newest:
                        newest = file_signature
                        file_load = file
                signs = pickle.load(open(file_load, 'rb'))
        else:
            logging.info('File not found')
            return None
        return signs
