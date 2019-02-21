from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='multiMAP',
    version='1.0.0',
    packages=['mapplanner', 'mapplanner.grounding', 'mapplanner.pddl', 'mapplanner.search', 'mapplanner.agent'],
    package_dir={'mapplanner': 'src'},
    url='http://cog-isa.github.io/mapplanner/',
    license='',
    author='KiselevGA',
    author_email='kiselev@isa.ru',
    long_description=open('README.md').read(),
    install_requires=required,
    include_package_data=True
)