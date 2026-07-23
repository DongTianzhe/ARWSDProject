import carla
import random
import numpy as np
import cv2 as cv
import time

client = carla.Client('localhost', 2000)
world = client.get_world()

bpLib = world.get_blueprint_library()
spawnPoints = world.get_map().get_spawn_points()
settings = world.get_settings()

print(len(spawnPoints))