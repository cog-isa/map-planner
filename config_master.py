import configparser
import os
import pkg_resources

def create_config(task_num = '1', is_load = 'True', refinement_lv = '1', benchmark_type = 'simple', benchmark = None, LogicType = 'classic', delim = '/'):
    """
    Create a config file
    """

    #delim = '/'


    if not benchmark:
        if benchmark_type == 'mapddl':
            path_bench = 'benchmarks' +delim+benchmark_type +delim+'blocksworld' +delim
            LogicType = 'classic'
        elif benchmark_type == 'spatial':
            path_bench = 'benchmarks'+delim+benchmark_type+delim
            LogicType = 'spatial'
        else:
            path_bench = 'benchmarks' +delim+'simple' +delim+ 'blocks'+delim
            LogicType = 'classic'
        if not isinstance(task_num, str):
            task_num = str(task_num)
        p_FILE = pkg_resources.resource_filename('mapplanner', path_bench+'task'+task_num+'.pddl')
        domain_load = pkg_resources.resource_filename('mapplanner', path_bench+'domain'+'.pddl')
        path = "".join([p.strip() + delim for p in p_FILE.split(delim)[:-1]])
    else:
        splited = benchmark.split(delim)
        task_num = "".join([s for s in splited[-1] if s.isdigit()])
        path = "".join([p.strip() + delim for p in splited[:-1]])
    path_to_write = path+'config_'+task_num+'.ini'

    config = configparser.ConfigParser()
    config.add_section("Settings")
    config.set("Settings", "path", path)
    config.set("Settings", "task", task_num)
    config.set("Settings", "is_load", is_load)
    config.set("Settings", "LogicType", LogicType)
    config.set("Settings", "agpath", "mapplanner.agent.agent_search")
    config.set("Settings", "agtype", "Agent")
    config.set("Settings", "gazebo", "False")
    config.set("Settings", "LogicalSearch", "")
    config.set("Settings", "refinement_lv", refinement_lv)

    with open(path_to_write, "w") as config_file:
        config.write(config_file)
    return path_to_write


def get_config(path):
    """
    Returns the config object
    """
    if not os.path.exists(path):
        create_config()

    config = configparser.ConfigParser()
    config.read(path)
    return config


def get_setting(path, setting, section = "Settings"):
    """
    Print out a setting
    """
    config = get_config(path)
    value = config.get(section, setting)
    return value


def update_setting(path, setting, value, section= "Settings"):
    """
    Update a setting
    """
    config = get_config(path)
    config.set(section, setting, value)
    with open(path, "w") as config_file:
        config.write(config_file)


def delete_setting(path, setting, section= "Settings"):
    """
    Delete a setting
    """
    config = get_config(path)
    config.remove_option(section, setting)
    with open(path, "w") as config_file:
        config.write(config_file)

