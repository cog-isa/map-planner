import datetime
import logging
import os
import pickle
import itertools

from mapplanner.grounding.semnet import Sign

DEFAULT_FILE_PREFIX = 'wmodel_'
DEFAULT_FILE_SUFFIX = '.swm'

SIT_COUNTER = 0
SIT_PREFIX = 'situation_'
PLAN_PREFIX = 'action_'
MAP_PREFIX = 'map_'


class Task:
    def __init__(self, name, signs, constraints, start_situation, goal_situation, logic, goal_map, map_precisions, additions, initial_state, goal):
        self.name = name
        self.signs = signs
        self.start_situation = start_situation
        self.goal_situation = goal_situation
        self.goal_map = goal_map
        self.constraints = constraints
        self.additions = additions
        self.map_precisions = map_precisions
        self.logic = logic
        self.init = initial_state
        self.goal = goal

    def __str__(self):
        s = 'Task {0}\n  Signs:  {1}\n  Start:  {2}\n  Goal: {3}\n'
        return s.format(self.name, '\n'.join(map(repr, self.signs)),
                        self.start_situation, self.goal_situation)

    def __repr__(self):
        return '<Task {0}, signs: {1}>'.format(self.name, len(self.signs))

    def save_signs(self, plan):
        def __is_role(pm, agents):
            chains = pm.spread_down_activity('meaning', 6)
            for chain in chains:
                if chain[-1].sign not in agents:
                    if len(chain[-1].sign.significances[1].cause) != 0:
                        break
            else:
                return False
            return True

        # I_obj = None
        logging.info('Plan preparation to save...')
        They_signs = [con.in_sign for con in self.signs["They"].out_significances]
        I_obj = [con.in_sign for con in self.signs["I"].out_significances if con.out_sign.name == "I"]
        if plan:
            logging.info('\tCleaning SWM...')

            agents = [self.signs["I"]]
            agents.extend(I_obj)
            agents.extend(They_signs)

            pms_sit = [pm[0] for pm in plan]
            pms_act = [pm[2] for pm in plan]
            pms_map = [pm[5][0] for pm in plan if pm[5][0] is not None]

            for name, s in self.signs.copy().items():
                signif=list(s.significances.items())
                if name.startswith(SIT_PREFIX):
                    for index, pm in s.meanings.copy().items():
                        if pm not in pms_sit:
                            s.remove_meaning(pm) # delete all nonplan situations
                    self.signs.pop(name)

                elif name.startswith(MAP_PREFIX):
                    for index, pm in s.meanings.copy().items():
                        if pm not in pms_map:
                            s.remove_meaning(pm) # delete all nonplan maps
                    self.signs.pop(name)

                elif len(signif):
                    if len(signif[0][1].cause) and len(signif[0][1].effect): #delete action's meanings that are not in plan
                        for index, pm in s.meanings.copy().items():
                            if __is_role(pm, agents):  # delete only fully signed actions
                                continue
                            else:
                                if pm not in pms_act:
                                    s.remove_meaning(pm)

            #saving exp_situations
            exp_signs = []
            for pm in itertools.chain(pms_sit, pms_map):
                exp_signs.append(pm.sign.rename('exp_' + pm.sign.name))

            for exp in exp_signs:
                if exp.name not in self.signs:
                    self.signs[exp.name] = exp

            # Save by parts of each size
            logging.info('\tSaving inner precedents of low lv planning... ')
            #abs_lv = max([pl[-1][1] for pl in plan])
            low_lv_plan = []
            subplans = []

            prev_act = plan[0][-1][1]
            index = 0
            low_lv_plan.append([(plan[0], index)])
            for action in plan[1:]:
                index+=1
                if action[-1][1] == prev_act:
                    low_lv_plan[-1].append((action, index))
                else:
                    low_lv_plan.append([(action, index)])
                    prev_act = action[-1][1]
            low_lv_plan = [pl for pl in low_lv_plan if len(pl) > 2]

            for smaller in low_lv_plan:
                if smaller:
                    start = [sign.meanings[1] for sign in exp_signs if smaller[0][0][0].sign.name in sign.name][0]
                    if len(plan) > smaller[-1][-1]+1:
                        finish = smaller[-1][0][0]
                    else:
                        finish = self.goal_situation.meanings[1]
                    sub = self.plan_saver(start, finish, smaller, 'subpl_'+str(low_lv_plan.index(smaller)))
                    subplans.append((sub, smaller[0][1], smaller[-1][1]))
            plan = [(el, ()) for el in plan]
            logging.info('\tSaving precedent...')
            self.start_situation.name += self.name
            self.goal_situation.name += self.name
            self.plan_saver(self.start_situation.meanings[1], self.goal_situation.meanings[1], plan, '', subplans)

        else:
            for name, sign in self.signs.copy().items():
                if name.startswith(SIT_PREFIX):
                    self.signs.pop(name)
                else:
                    sign.meanings = {}
                    sign.out_meanings = []
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

    def plan_saver(self, start, finish, plan, plan_name = '', subplans = None):
        im = start.copy('meaning', 'image')
        start.sign.add_image(im)
        im = finish.copy('meaning', 'image')
        finish.sign.add_image(im)
        if not plan_name:
            plan_name = 'plan_'+ self.name
        plan_sign = Sign(plan_name + self.name)
        plan_mean = plan_sign.add_meaning()
        connector = plan_mean.add_feature(start)
        start.sign.add_out_meaning(connector)
        conn = plan_mean.add_feature(finish, effect=True)
        finish.sign.add_out_meaning(conn)

        plan_image = plan_sign.add_image()

        iter = -1
        if not subplans:
            for act,_ in plan:
                im = act[2].sign.add_image()
                connector = plan_image.add_feature(im)
                act[2].sign.add_out_image(connector)  # add connector to plan_sign threw images to out_image
        else:
            ots = {subplans.index(it): range(it[1], it[2]+1) for it in subplans}
            for act, _ in plan:
                iter += 1
                flag = False
                for index, value in ots.items():
                    if iter == value[0]:
                        im = subplans[index][0][0].images[1]
                        connector = plan_image.add_feature(im)
                        subplans[index][0][0].add_out_image(connector)
                        flag = True
                        break
                    elif iter in value:
                        flag = True
                        break
                    # else:
                    #     im = act[2].sign.add_image()
                    #     connector = plan_image.add_feature(im)
                    #     act[2].sign.add_out_image(connector)
                if flag:
                    continue
                else:
                    im = act[2].sign.add_image()
                    connector = plan_image.add_feature(im)
                    act[2].sign.add_out_image(connector)


        self.signs[plan_sign.name] = plan_sign
        self.signs[start.sign.name] = start.sign
        self.signs[finish.sign.name] = finish.sign

        return [plan_sign, start.sign, finish.sign]


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
