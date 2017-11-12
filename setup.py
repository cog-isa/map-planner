from distutils.core import setup

setup(
    name='map-planner',
    version='2.0.0',
    packages=['mapplanner', 'mapplanner.grounding', 'mapplanner.pddl', 'mapplanner.search', 'mapplanner.visual'],
    package_dir={'mapplanner': 'src'},
    url='http://cog-isa.github.io/map-planner/',
    license='',
    author='GraffT',
    author_email='pan@isa.ru',
    description=''
)
