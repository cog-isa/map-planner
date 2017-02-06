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
    #objects for 1 matask: <a1-4: type: agent, block1-4: type: block>
    for obj in objects:
        #create a тип Sign with object name
        obj_sign = Sign(obj)
        #создает каузальную матрицу для знака(допустим а), либо находит его казуальную матрицу
        # и добавляет 1 к следующему значению
        # добавляет каузальную матрицу в словарь obj_signifs
        obj_signifs[obj] = obj_sign.add_significance()
        #add obj to sign list
        signs[obj] = obj_sign
    for tp, objects in type_map.items():
        #make Sign with type name, например знак "object"
        tp_sign = Sign(tp.name)
        for obj in objects:
            # находим каузальную матрицу для конкретного объекта в словаре матриц
            obj_signif = obj_signifs[obj]
            #  Увеличиваем следующего значения знака типа( всё еще object/block) на 1
            # Каузальная матрица отображается как имя знака матрицы: индекс матрицы; создается tp_signif - каузальная матрица
            # где индекс матрицы - число объектов данного типа (object:4)
            tp_signif = tp_sign.add_significance()
            #  Создается элемент типа коннектор для каузальной матрицы знака типов
            # отображается как выходящий знак: выходящий индек -> внутренняя очередь данного знака
            connector = tp_signif.add_feature(obj_signif, zero_out=True)
            # добавление выходящих значений
            signs[obj].add_out_significance(connector)
        signs[tp.name] = tp_sign

    for predicate in predicates:
        #создание знаков с именем предикатов
        pred_sign = Sign(predicate.name)
        # создает каузальную матрицу для предиката с пустым списком эффектов.
        # отображает имя знака предиката -> индекс матрицы.
        # добавляет 1 к следующему значению знака предиката
        significance = pred_sign.add_significance()
        if len(predicate.signature) == 2:  # on(block?x, block?y), holding(0=agent, 1=block)
            # функция вызывается для каждой из частей предиката с 2 частями
            def update_significance(fact, effect=False):
                #факт - кортеж ('?x', (block,)). fact[1][0].name - имя 2 части кортежа (блок) + fact[0] имя 1 части (?х)
                role_name = fact[1][0].name + fact[0]
                if role_name not in signs:
                    #если нет такого знака role_name - делаем знак
                    signs[role_name] = Sign(role_name)
                # выбираем только что созданный знак
                role_sign = signs[role_name]
                obj_sign = signs[fact[1][0].name]
                # add 1 to significance for sign agent or to sign block?x in *on* way
                # создаем каузальную матрицу для знака роли с индексом 1 и следующим значением 2
                role_signif = role_sign.add_significance()
                # создается коннектор между каузальными матрицами знака роли и знака объекта (block&x и block)
                conn = role_signif.add_feature(obj_sign.significances[1], zero_out=True)
                # в список выходящих значений добавляется коннектор ("block":0 -> 1)
                # это значит, что теперь кауз матр блок учавствовала в создании кауз матр блок?х
                obj_sign.add_out_significance(conn)
                #cоздается коннектор для каузальной матрицы знака on ( почему с эффектом, когда он =[]) и знака роли
                # создается коннектор кауз матрицы предикатного знака on и каузальной матрицы знака роли block&x
                conn = significance.add_feature(role_signif, effect=effect, zero_out=True)
                # теперь эта роль(блок?х) учавствовала в созда кауз матр предикатного знака on
                role_sign.add_out_significance(conn)

            update_significance(predicate.signature[0])
            update_significance(predicate.signature[1])

        signs[predicate.name] = pred_sign

    for action in actions:
        #создаются знаки с именами действий
        act_sign = Sign(action.name)
        # создается каузальная матрица для знака действия
        act_signif = act_sign.add_significance()
        # Для предикатов в предусловиях и в эффектах действия
        def update_significance(predicate, effect=False):
            # выбирается знак предиката из списка знаков
            pred_sign = signs[predicate.name]
            # создается коннектор для каузальной матрицы знака действия и каузальной матрицы предиката.
            # in_order отрицательный в случае предикатов-эффекто действий
            connector = act_signif.add_feature(pred_sign.significances[1], effect=effect)
            pred_sign.add_out_significance(connector)
            if len(predicate.signature) == 1:
                fact = predicate.signature[0]
                role_sign = signs[fact[1][0].name + fact[0]]
                # создается коннектор для каузальной матрицы действия и кауз матр роли знака(например block?x)
                conn = act_signif.add_feature(role_sign.significances[1], connector.in_order, effect=effect,
                                              zero_out=True)
                role_sign.add_out_significance(conn)
            elif not predicate.signature[0][1][0].name == predicate.signature[1][1][0].name:
                for fact in predicate.signature:
                    role_sign = signs[fact[1][0].name + fact[0]]
                    connector_new = act_signif.add_feature(role_sign.significances[1],connector.in_order, effect=effect,
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
    _expand_situation_ma_1(goal_situation, signs, pms, list_signs)  # For task
    return Task(problem.name, signs, start_situation, goal_situation)

def task_signs(problem):
    signs= []
    signs.append(problem.goal[0].signature[0][0])
    signs.append(problem.goal[len(problem.goal)-1].signature[1][0])
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
    #создается знак названия ситуации (старт/финиш)
    situation = Sign(name)
    # создается каузальная матрица личностных смыслов знака ситуации и
    # увеличивается значение следующего личностного смысла
    sit_meaning = situation.add_meaning()
    elements = {}

    def get_or_add(sign):
        if sign not in elements:
            meaning = sign.add_meaning()
            elements[sign] = meaning
        return elements.get(sign)

    for predicate in predicates:
        pred_sign = signs[predicate.name]
        # для знака предиката создается каузальная матрица личностных смыслов и
        # добавляется следующий личностный смысл (+1)
        # (clear: 4)
        pred_meaning = pred_sign.add_meaning()
        # задается коннектор между каузальной матрицей названия ситуации и каузальной матрицей предиката
        connector = sit_meaning.add_feature(pred_meaning)
        pred_sign.add_out_meaning(connector)
        if len(predicate.signature) == 1:
            sig_sign = signs[predicate.signature[0][0]]
            # для знака объекта ( знак с) создается каузальная матрица с минингами и доб в словарь элементов
            sig_meaning = get_or_add(sig_sign)
            #создается коннектор между кауз матр знака названия сит и кауз матр знаков элементов
            conn = sit_meaning.add_feature(sig_meaning, connector.in_order)
            sig_sign.add_out_meaning(conn)
        # если предикат on, то для обоих знаков, входящих в него создается мининг
        # и коннектор с каузальной матрицей предиката
        elif len(predicate.signature) > 1:
            for fact in predicate.signature:
                fact_sign = signs[fact[0]]
                fact_meaning = get_or_add(fact_sign)
                conn = pred_meaning.add_feature(fact_meaning)
                fact_sign.add_out_meaning(conn)

    return situation, elements

def _expand_situation_ma_1(goal_situation, signs, pms, list_signs):
    # создается каузальная матрица минингов у знака ontable :5
    ont_mean = signs['ontable'].add_meaning()
    # выбирается каузальная матрица мининга знака "a": 2
    a_mean = pms[signs['a']]
    # создается коннектор между км мин ситуации и км знака ontable
    connector = goal_situation.meanings[1].add_feature(ont_mean)
    # создается коннектор между км целевой минингов целевой сит и км знака-факта предиката ontable
    # в список использований знака-факта добавляется текущий коннектор ( а:2 -> 5)
    conn = goal_situation.meanings[1].add_feature(a_mean, connector.in_order)
    signs['ontable'].add_out_meaning(conn)
    signs['a'].add_out_meaning(conn)
    # создается км минигов для знака clear
    cl_mean = signs['clear'].add_meaning()
    # выбирается км минингов знака d
    d_mean = pms[signs['d']]
    # создается коннектор между км минингов целевой ситуации и км минингов знака clear
    connector = goal_situation.meanings[1].add_feature(cl_mean)
    # создается коннектор между км минингов целевой ситуации и км минингов знака-факта предиката clear (знака d)
    conn = goal_situation.meanings[1].add_feature(d_mean, connector.in_order)
    signs['clear'].add_out_meaning(conn)
    signs['d'].add_out_meaning(conn)

def _expand_situation1(goal_situation, signs, pms, list_signs):
    # создается каузальная матрица мининга для знака handempty:2
    h_mean = signs['handempty'].add_meaning()
    # создается коннектор каузальной матрицы минингов у знака ситуации и кауз матр handempty
    connector = goal_situation.meanings[1].add_feature(h_mean)
    signs['handempty'].add_out_meaning(connector)
    # создается каузальная матрица минингов у знака ontable :5
    ont_mean = signs['ontable'].add_meaning()
    # выбирается каузальная матрица мининга знака "a": 2
    a_mean = pms[signs['a']]
    # создается коннектор между км мин ситуации и км знака ontable
    connector = goal_situation.meanings[1].add_feature(ont_mean)
    # создается коннектор между км целевой минингов целевой сит и км знака-факта предиката ontable
    # в список использований знака-факта добавляется текущий коннектор ( а:2 -> 5)
    conn = goal_situation.meanings[1].add_feature(a_mean, connector.in_order)
    signs['ontable'].add_out_meaning(conn)
    signs['a'].add_out_meaning(conn)
    # создается км минигов для знака clear
    cl_mean = signs['clear'].add_meaning()
    # выбирается км минингов знака d
    d_mean = pms[signs['d']]
    # создается коннектор между км минингов целевой ситуации и км минингов знака clear
    connector = goal_situation.meanings[1].add_feature(cl_mean)
    # создается коннектор между км минингов целевой ситуации и км минингов знака-факта предиката clear (знака d)
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

