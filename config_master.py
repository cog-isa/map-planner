import configparser
import os
import pkg_resources

def create_config(task_num = '1', is_load = 'True',backward = 'True', refinement_lv = '1', benchmark_type = 'spatial', benchmark = None, task_type = 'classic', delim = '/', subsearch = 'greedy'):
    """
    Create a config file
    """
    if not benchmark:
        path_bench = 'benchmarks'+delim+benchmark_type+delim +'task'+task_num
        task_type = 'spatial'
        if not isinstance(task_num, str):
            task_num = str(task_num)
        p_FILE = pkg_resources.resource_filename('mapspatial', path_bench+'task'+task_num+'.json')
        domain_load = pkg_resources.resource_filename('mapspatial', path_bench+'domain'+'.json')
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
    config.set("Settings", "agpath", "mapspatial.agent.agent_search")
    config.set("Settings", "gazebo", "False")
    config.set("Settings", "refinement_lv", refinement_lv)
    config.set("Settings", "TaskType", task_type)
    config.set("Settings", "backward", backward)
    config.set("Settings", "subsearch", subsearch)

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

