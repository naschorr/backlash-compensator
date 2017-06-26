import sys
import os
import re

## Config
BACKLASH = 0.8
NEW_LINE_COMMENT = "\t; Compensate for Z backlash of {0}".format(BACKLASH)

## Structures

class Z_Index:
    def __init__(self, index, height):
        self.index = index
        self.height = height

    ## Properties

    @property
    def index(self):
        return self._index


    @index.setter
    def index(self, value):
        self._index = value


    @property
    def height(self):
        return self._height


    @height.setter
    def height(self, value):
        self._height = value

    ## Methods

    def incrementIndex(self, amount=1):
        self.index += amount


class Z_Queue:
    MAX_INDICES = 3

    def __init__(self, size=None, initial=None):
        if(size):
            self.max_indices = size
        else:
            self.max_indices = self.MAX_INDICES

        if(initial):
            self.indices = initial
        else:
            self.indices = [initial] * self.max_indices

    ## Properties

    @property
    def max_indices(self):
        return self._max_indices


    @max_indices.setter
    def max_indices(self, value):
        ## Suppress warning on init
        if(hasattr(self, "_max_indices")):
            print("Warning - max_indices should really be {0}.".format(self.MAX_INDICES))

        self._max_indices = value


    @property
    def indices(self):
        return self._indices


    @indices.setter
    def indices(self, value):
        if(len(value) <= self.max_indices):
            self._indices = value

    ## Methods

    def push(self, z_index):
        del self.indices[0]
        self.indices.append(z_index)


    def isPopulated(self):
        index = 0
        populated = True
        while(index < self.max_indices and populated):
            if(not self.indices[index]):
                populated = False
            index += 1

        return populated


    def getInflection(self):
        ## Assumes max_indices == 3
        try:
            left = self.indices[0].height
            center = self.indices[1].height
            right = self.indices[2].height
        except TypeError as e:
            ## Error usually from an index in self.indices not having a Z_Index
            ## object in it.
            return 0

        ## Maxima, pitch downwards. /^\
        if(left < center and right < center):
            return -1

        ## Minima, pitch upwards. \_/
        elif(left > center and right > center):
            return 1

        ## Linear, continue in same direction. / or \
        else:
            return 0


    def incrementAfterInflectionPoint(self, amount=1):
        ## Assumes max_indices == 3
        self.indices[2].incrementIndex(amount)

## Functions

def load_gcode(gcode_path):
    ## Check for valid filepath
    if(not os.path.isfile(gcode_path)):
        return []

    ## Return gcode as a list of commands
    with open(gcode_path, 'r') as fd:
        return fd.readlines()


def save_gcode(gcode_path, gcode):
    with open(gcode_path, 'w') as fd:
        for command in gcode:
            fd.write(command)


def get_z_height(command):
    result = re.match(r"^G[01]{1}.*Z\s?(-?\d*\.\d+).*$", command)
    if(result):
        return float(result.group(1))
    else:
        return 0


def compensate(gcode_list, direction, inflection_index):
    def insert_g1_z(index, position):
        command = "G1 Z{0} {1}\n".format(position, NEW_LINE_COMMENT)
        gcode_list.insert(index, command)

    def insert_g92_z(index, position):
        command = "G92 Z{0} {1}\n".format(position, NEW_LINE_COMMENT)
        gcode_list.insert(index, command)

    height = inflection_index.height
    index = inflection_index.index

    if(direction > 0):  # Pitch upwards
        insert_g1_z(index + 1, height + BACKLASH)
        insert_g92_z(index + 2, height)

    elif(direction < 0):    # Pitch downwards
        insert_g1_z(index + 1, height - BACKLASH)
        insert_g92_z(index + 2, height)

    return gcode_list


def main(gcode_path):
    gcode = load_gcode(gcode_path)

    index = 0
    z_indices = Z_Queue()
    while(index < len(gcode)):
        command = gcode[index]
        height = get_z_height(command)

        if(height):
            z_indices.push(Z_Index(index, height))

            ## Don't bother with compensation unless the z_indices psuedo-queue is filled
            if(z_indices.isPopulated()):
                gcode = compensate(gcode, z_indices.getInflection(), z_indices.indices[1])
                ## Increment by 2 since 2 new lines have been added to the
                ## gcode list
                z_indices.incrementAfterInflectionPoint(2)
                index += 2

        index += 1

    save_gcode(gcode_path, gcode)


if(__name__ == "__main__"):
    try:
        main(sys.argv[1])   ## Path to gcode to process
    except IndexError as e:
        print("Needs a path to a file containing valid G-Code")
