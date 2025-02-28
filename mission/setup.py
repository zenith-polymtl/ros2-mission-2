from setuptools import find_packages, setup

package_name = 'mission'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='colin',
    maintainer_email='colin@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'state = mission.state_node:main',
            'approach = mission.approach:main',
            'vision = mission.machine_vision:main',
            'valve = mission.valve_control:main',
            'winch = mission.winch_control:main',
            'position_node = mission.winch_control:main'
        ],
    },
)
