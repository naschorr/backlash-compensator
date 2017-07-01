# backlash-compensator
Modifies G-Code to compensate for backlash in the Z axis

### Installation
- Make sure you've got Python 3 installed and `python` is in your `PATH`
- Clone/download and unzip the repo into the desired location
- Adjust the `BACKLASH` variable at the top of the script as necessary (it's in millimeters)
- In Slic3r, place the absolute path to `backlash_compensator.py` in the "Post-processing Scripts" box inside the "Output options" panel inside the "Print Settings" tab. Cura and Simplify3D should work similarly.

### Theory
The script loops through the generated g-code looking for every instange of a G0 or G1 command with a Z component to it. Whenever a Z movement is found, it's pushed into a queue of Z moves (which also stores the g-code line number and z height of the movement). Once the queue has three movements, it can be checked for an inflection point in the middle point. If the inflection point...
- Is above the two outer points, then we need to soak up the backlash for the impending downwards movement. Insert a `G1 Z{z_move.height - BACKLASH}` after the middle point in the g-code to reel in the slack, then insert a `G92 Z{z_move.height}` afterwards to update the system with the actual coordinates.
- Is below the two outer points, then we need to soak up the backlash for the impending upwards movement. Insert a `G1 Z{z_move.height + BACKLASH}` after the middle point in the g-code to reel in the slack, then insert a `G92 Z{z_move.height}` afterwards to update the system with the actual coordinates.

However, if the inflection point doesn't exist, then don't do anything as there isn't a direction change that'll need the backlash to be dealt with.

### Why?
I've been working on a [low-cost CNC project](https://github.com/naschorr/vectron) that uses a [28byj-48 geared stepper](https://www.adafruit.com/product/858) to control the Z axis. Unfortunately it has a TON of slop in the gearing which made it impossible to get anything even remotely accurate out of it, hence this script.
