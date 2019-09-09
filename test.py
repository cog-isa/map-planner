from mapcore.mapplanner import MapPlanner

from config_master import create_config, get_config
import platform


if __name__ == '__main__':

    config_path = ''

    if platform.system() != 'Windows':
        delim = '/'
    else:
        delim = '\\'

    if not config_path:
        path = create_config(domen = 'blocks', task_num = '1', delim=delim, backward = 'False', task_type = 'pddl')
    else:
        path = config_path
    # after 1 time creating config simply send a path
    planner = MapPlanner(**get_config(path))
    solution = planner.search()
