<h2>Multiagent planner based on sign world model.</h2>
<hr>
<p><strong>To start planner</strong>:<br>

Create Python file and import this library. (You need to build and install it before - python setup.py install)
Create an object of MapPlanner class with arguments:
<ol>
<li>Path to benchmark (i.e. mapplanner/benchmarks/spatial/)
<li>Number of a task in integer format (i.e. 1,2,3…).</li>
<li>Logic type. The current implementation of the planner supports classical and spatial logic (i.e. spatial or classic)</li>
<li>Experience usability</li>
<li>Gazebo visualization</li>
<li>Path to module with agent Implementation</li>
<li>Agent name (i.e GatheboAgent or Agent)</li>
</ol>
Call searcher method
<br>
<p><strong>Requirements</strong>:<br>
python 3.5+</p>

```python
from mapplanner.mapplanner import MapPlanner

#Example 0 (abstract example - wouldn't work!):

if __name__ == '__main__':
   planner = MapPlanner(benchmark, task_number = 1, LogicType = 'spatial', is_load = False, gazebo= False, LogicalSearch = '',
					agpath = 'gazeboplanner.CrumbAgent', agtype = 'Agent')
   solution = planner.searcher()

#Example 1:

if __name__ == '__main__':
   planner = MapPlanner('src/benchmarks/spatial/', '1', gazebo = False,
        				agpath = 'mapplanner.agent.agent_search', agtype = 'Agent')
   solution = planner.searcher()

#Example 2:

if __name__ == '__main__':
   planner = MapPlanner('src/benchmarks/spatial/', '2', gazebo = True,
        				agpath = 'gazeboplanner.CrumbAgent', agtype = 'GazeboAgent')
   solution = planner.searcher()

#This lib includes a small kit of test benchmarks. Use them like following:

from mapplanner.mapplanner import MapPlanner
import pkg_resources

if __name__ == '__main__':

    task_num = '1'

    path_simple = 'benchmarks/simple/blocks/'
    path_mapddl = 'benchmarks/mapddl/blocksworld/'
    path_spatial = 'benchmarks/spatial/'

    p_FILE = pkg_resources.resource_filename('mapplanner', path_simple+'task'+task_num+'.pddl')
    domain_load = pkg_resources.resource_filename('mapplanner', path_simple+'domain'+'.pddl')
    path = ''.join([p.strip() + '/' for p in p_FILE.split('/')[:-1]])

    planner = MapPlanner(path, task_num, gazebo = False, is_load=True, LogicType='classic',
        				agpath = 'mapplanner.agent.agent_search', agtype = 'Agent')
    solution = planner.searcher()

```


