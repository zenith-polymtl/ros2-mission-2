from setuptools import find_packages, setup

package_name = 'test_nodes'

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
    maintainer_email='colinc131@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'service_server = test_nodes.service_server:main',
            'service_client = test_nodes.service_client:main',
            'battery_monitor = test_nodes.battery_monitor:main',
            'pose_monitor = test_nodes.pose_monitor:main'
        ],
    },
)
