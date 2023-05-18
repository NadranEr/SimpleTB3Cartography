#This file defines classes and functions that are used to manipulate the maps

import string
import json
import numpy as np

class map_data_class():
    def __init__(self):
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None
        self.stepx = None
        self.stepy = None
        self.width = None
        self.height = None
        self.level = None
        self.map = None

#filename: string
def get_data_from_json(filename):
    # load the JSON data from file
    with open(filename, 'r') as fileHandle:
        jsondict = json.load(fileHandle) #return a dictionnary
    #Get the values from the dictionnary
    map_obj = map_data_class #put everything into an object for convenience
    map_obj.xmin = jsondict["xmin"]
    map_obj.xmax = jsondict["xmax"]
    map_obj.ymin = jsondict["ymin"]
    map_obj.ymax = jsondict["ymax"]
    map_obj.stepx = jsondict["stepx"]
    map_obj.stepy = jsondict["stepy"]
    map_obj.level = jsondict["level"]
    map_obj.map = jsondict["data"]
    return map_obj

#map_obj: map_data_class
def compute_map(map_obj: map_data_class):
    #Compute the map and add the width and height fields
    CoordX = np.arange(map_obj.xmin-map_obj.stepx/2,map_obj.xmax+map_obj.stepx/2,map_obj.stepx)
    CoordY = np.arange(map_obj.ymin-map_obj.stepy/2,map_obj.ymax+map_obj.stepy/2,map_obj.stepy)
    width_local = CoordX.size
    height_local = CoordY.size
    map_obj.width = width_local
    map_obj.height = height_local
    map_local = np.reshape(map_obj.map,(width_local,height_local))
    map_obj.map = map_local
    return map_obj

#source_map: map_data_class, edited_map: map_data_class, fileout: string
def array_to_json(source_map, edited_map, fileout):
    print(type(edited_map))
    output = source_map
    output.map = edited_map.map.flatten()
    output.map[output.map>1] = 1
    
    output_dict = {
        "xmin": output.xmin,
        "xmax": output.xmax,
        "ymin": output.ymin,
        "ymax": output.ymax,
        "stepx": output.stepx,
        "stepy": output.stepy,
        "level": output.level,
        "data": output.map.tolist()
    }

    with open(fileout,"w") as f:
        json.dump(output_dict,f,indent=4)