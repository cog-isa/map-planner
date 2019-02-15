from mapplanner.mapplanner import MapPlanner

from config_master import create_config, get_config


if __name__ == '__main__':

    config_path = ''
    #benchmark = '/home/gleb/PycharmProjects/map-planner/TestingBenchmark/task_vertical_clar/task9.json'
    #benchmark = '/home/gleb/PycharmProjects/map-planner/src/benchmarks/simple/blocks/task1.pddl'
    benchmark = '/home/gleb/PycharmProjects/map-planner/TestingBenchmark/task_anti_walls/task11.json'
    # task_num if simple/blocks/task in other approaches -
    # benchmark_type&task_num or path to benchmark
    if not config_path:
        #path = create_config(benchmark = benchmark, refinement_lv='1')
        path = create_config(benchmark = benchmark, LogicType = 'spatial', refinement_lv='1')
    else:
        path = config_path
    # after 1 time creating config simply send a path
    planner = MapPlanner(**get_config(path))
    solution = planner.searcher()
