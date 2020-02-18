from setuptools import setup

setup(
    name='nvidia-co2',
    version='0.1.0',
    description='Show gCO2eq emissions information with nvidia-smi.',
    url='https://github.com/kylemcdonald/nvidia-co2',
    download_url='https://github.com/kylemcdonald/nvidia-co2.git',
    author='Kyle McDonald',
    license='MIT',
    packages=['nvidia_co2'],
    package_data={'nvidia_co2': ['data/*.json']},
    install_requires=[
        'shapely',
        'geocoder'
    ],
    entry_points={
        'console_scripts': [
            'nvidia-co2 = nvidia_co2.__main__:main'
        ]
    },
)
