#!/usr/bin/env python

import time
import numpy as np
import subprocess
import shelve
import os
import argparse

def cpu_uj_total():
    fn = '/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj'
    with open(fn) as f:
        return int(f.read())
    
def cpu_watts(sample_time=0.01):
    start = cpu_uj_total()
    time.sleep(sample_time)
    stop = cpu_uj_total()
    ujps = stop - start
    watts = ujps / (10e5 * sample_time)
    return watts

def gpu_watts():
    with os.popen('nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits') as f:
        output = f.read()
    watts = sum([float(e) for e in output.splitlines()])
    return watts

def shelve_it(file_name):
    d = shelve.open(file_name)
    def decorator(func):
        def new_func(param):
            if param not in d:
                d[param] = func(param)
            return d[param]
        return new_func
    return decorator

def public_ip():
    with os.popen('dig +short myip.opendns.com @resolver1.opendns.com') as f:
        ip = f.read().strip()
    return ip

@shelve_it(os.path.expanduser('/tmp/nvidia-co2-cache'))
def get_carbon_intensity_by_ip(ip):
    import geocoder
    from .metrics import get_zone_information_by_coords
    g = geocoder.ip(ip)
    zone_name, zone_info = get_zone_information_by_coords((g.y, g.x))
    return zone_info['carbonIntensity']

def get_carbon_intensity():
    ip = public_ip()
    carbon_intensity = get_carbon_intensity_by_ip(ip)
    return carbon_intensity

def watts_to_gco2eqph(watts):
    gco2eqpkwh = get_carbon_intensity()
    return (watts / 1000) * gco2eqpkwh

def convert_watts(watts, mode):
    # all ratios in (units)/(watt)
    watts_units = {
        # https://www.consumer.ftc.gov/articles/0164-shopping-light-bulbs
        'bulb': [1/60, ' lightbulbs'],
        'cfl': [1/15, ' CFLs'],
        'watt': [1/1, 'W']
    }

    # all conversions in (units/hour)/(gCO2eq)
    gco2eq_units = {
        'gco2eqph': [1, 'gCO2eq/h'],
        # car is 404gCO2eq/mile
        # https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle
        'car-mph': [1/404, 'mph in a car'],
        'car-kph': [1/251, 'kph in a car'],
        # "0.3 square meters of September sea-ice area per metric ton of CO2 emission"
        # https://science.sciencemag.org/content/354/6313/747
        # 0.3 m^2 / tCO2eq = 300000 mm^2 / tCO2eq = 0.3 mm^2 / gCO2eq
        'ice': [0.3, 'mm^2/h sea ice'],
        # Heller and Keoleian (2014) https://meals4planet.org/science/
        # 26.45 gCO2eq/gram beef, 0.78 gCO2eq/gram tofu
        'beef': [1/26.45, ' grams of beef/h'],
        'tofu': [1/0.78, ' grams of tofu/h'],
    }

    if mode in watts_units:
        ratio, suffix = watts_units[mode]
        amount = watts * ratio
    else:
        gco2eqph = watts_to_gco2eqph(watts)
        ratio, suffix = gco2eq_units[mode]
        amount = gco2eqph * ratio
    return f'{amount:0.2f}' + suffix

def nvidia_co2(mode):
    watts = cpu_watts() + gpu_watts()
    msg = convert_watts(watts, mode)

    with os.popen('nvidia-smi') as f:
        nvidia_smi = f.read()
    nvidia_smi = nvidia_smi.replace('-SMI', '-CO2')
    lines = nvidia_smi.splitlines()
    date_time = lines[0].strip()
    cols = 79 - len(date_time)
    headline = date_time + msg.rjust(cols)

    print(headline)
    print('\n'.join(lines[1:]))

def main():
    parser = argparse.ArgumentParser(description="""Show gCO2eq emissions information with nvidia-smi. \
        Combines CPU and GPU usage. Emissions are corrected for location using IP address geolocation.""")
    parser.add_argument('--mode', '-m', type=str, default='gco2eqph',
        help="""[ice|beef|tofu|car-mph|car-kph|bulb|cfl|watt|gco2eqph] \
            `ice` shows how much sea ice is lost per hour due to your emissions. \
            `beef` and `tofu` shows how many grams of each it takes to produce the same emissions. \
            `car-mph` and `car-kph` show how fast a car would have to drive to produce the same emissions. \
            `bulb` and `cfl` show how many incandescent lightbulbs or CFLs are required to use the same power. \
            `watt` shows how many watts used, and `gco2eqph` shows gCOeq/hour used. (default: gco2eqph)""")
    args = parser.parse_args()
    nvidia_co2(args.mode)

if __name__ == "__main__":
    main()