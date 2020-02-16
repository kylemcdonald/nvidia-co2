# from https://github.com/Breakend/experiment-impact-tracker
# modified slightly to decrease dependencies

from .constants import REGIONS_WITH_BOUNDING_BOXES, ZONE_INFO, ZONE_NAMES
from shapely.geometry import Point

def get_region_by_coords(coords):
    #TODO: automatically narrow down possibilities
    lat, lon = coords
    point = Point(lon, lat)
    zone_possibilities = []
    for zone in REGIONS_WITH_BOUNDING_BOXES:
        if zone["geometry"].contains(point):
            zone_possibilities.append(zone) 
    if len(zone_possibilities) == 0:
        raise ValueError("No possibilities found, may need to add a zone.")
    z = min(zone_possibilities, key=lambda x: x["geometry"].area)
    return z

def get_zone_information_by_coords(coords):
    region = get_region_by_coords(coords)
    return region, ZONE_INFO[region["id"]]