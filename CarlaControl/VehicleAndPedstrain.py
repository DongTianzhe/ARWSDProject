import carla
import random
import numpy as np
import cv2 as cv
import time

def cameraCallBack(image, dataDict):
    dataDict['image'] = np.reshape(np.copy(image.raw_data), (image.height, image.width, 4))

client = carla.Client('localhost', 2000)
world = client.get_world()

bpLib = world.get_blueprint_library()
spawnPoints = world.get_map().get_spawn_points()
settings = world.get_settings()
# print(settings.synchronous_mode)

vehicleList = []
numVehicles = 5
vehicleSpawnPointList = []
vehicleBP = bpLib.find('vehicle.seat.leon')
for i in range(numVehicles):
    location = random.choice(spawnPoints)
    while location in vehicleSpawnPointList:
        location = random.choice(spawnPoints)
    # try_spawn_actor returns None on collision instead of raising and aborting setup.
    vehicle = world.try_spawn_actor(vehicleBP, location)
    if vehicle is not None:
        vehicleSpawnPointList.append(location)
        vehicleList.append(vehicle)

# Retry the ego vehicle until it spawns; it is required by everything downstream.
mainVehicle = None
for _ in range(len(spawnPoints)):
    location = random.choice(spawnPoints)
    if location in vehicleSpawnPointList:
        continue
    mainVehicle = world.try_spawn_actor(vehicleBP, location)
    if mainVehicle is not None:
        vehicleSpawnPointList.append(location)
        break
if mainVehicle is None:
    raise RuntimeError('Could not spawn the main (ego) vehicle after several attempts.')

spectator = world.get_spectator()
transform = carla.Transform(mainVehicle.get_transform().transform(carla.Location(x=-4, z=2.5)), carla.Rotation())
spectator.set_transform(transform)

cameraBP = bpLib.find('sensor.camera.rgb')
cameraBP.set_attribute('image_size_x', '1920')
cameraBP.set_attribute('image_size_y', '1080')
cameraInitTrans = carla.Transform(carla.Location(x=0.4, z=1.6))
camera = world.spawn_actor(cameraBP, cameraInitTrans, attach_to=mainVehicle)

walkerList = []
walkerControllerList = []
numWalkers = 5
walkerSpawnPointList = []

walkerBP = bpLib.find('walker.pedestrian.0002')
walkerControllerBP = bpLib.find('controller.ai.walker')
for i in range(numWalkers):
    location = world.get_random_location_from_navigation()
    if location is None:
        continue
    spawnPoint = carla.Transform()
    spawnPoint.location = location
    walker = world.try_spawn_actor(walkerBP, spawnPoint)
    if walker is not None:
        walkerSpawnPointList.append(location)
        walkerList.append(walker)

for walker in walkerList:
    controller = world.spawn_actor(walkerControllerBP, carla.Transform(), walker)
    walkerControllerList.append(controller)

world.wait_for_tick()
print(len(walkerList))
print(len(walkerControllerList))
for i in range(len(walkerControllerList)):
    print(i, walkerControllerList[i].is_alive, walkerControllerList[i].parent)

imageW = cameraBP.get_attribute('image_size_x').as_int()
imageH = cameraBP.get_attribute('image_size_y').as_int()

cameraData = {'image': np.zeros((imageH, imageW, 4), dtype=np.uint8)}

camera.listen(lambda image: cameraCallBack(image, cameraData))

for vehicle in vehicleList:
    vehicle.set_autopilot(True)
mainVehicle.set_autopilot(True)

for i in range(len(walkerControllerList)):
    walkerControllerList[i].start()
    walkerControllerList[i].go_to_location(world.get_random_location_from_navigation())
    walkerControllerList[i].set_max_speed(float(walkerBP.get_attribute('speed').recommended_values[1]))

cv.namedWindow('RGB Camera', cv.WINDOW_AUTOSIZE)
cv.imshow('RGB Camera', cameraData['image'])
cv.waitKey(1)
t = time.time()
autolist = []
currentLocation = []
for vehicle in vehicleList:
    currentLocation.append([round(vehicle.get_location().x, 3), round(vehicle.get_location().y, 3), round(vehicle.get_location().z, 3)])
    autolist.append(True)
mainVehicleLocation = [round(mainVehicle.get_location().x, 3), round(mainVehicle.get_location().y, 3), round(mainVehicle.get_location().z, 3)]
mainVehicleAuto = True
print(currentLocation)

while True:
    world.wait_for_tick()
    for i in range(len(vehicleList)):
        if not autolist[i]:
            autolist[i] = True
            vehicleList[i].set_autopilot(True)
            print(f'Enable autonomous driving in vehicle {i}')
    if not mainVehicleAuto:
        mainVehicleAuto = True
        mainVehicle.set_autopilot(True)
        print('Enable autonomous driving in main vehicle')

    if time.time() - t > 5:
        t = time.time()
        for i in range(len(vehicleList)):
            loc = [round(vehicleList[i].get_location().x, 3), round(vehicleList[i].get_location().y, 3), round(vehicleList[i].get_location().z, 3)]
            # print(loc)
            if loc == currentLocation[i]:
                vehicleList[i].set_autopilot(False)
                autolist[i] = False
                print(f'Disable autonomous driving in vehicle {i}')

            currentLocation[i] = loc
        mainLoc = [round(mainVehicle.get_location().x, 3), round(mainVehicle.get_location().y, 3), round(mainVehicle.get_location().z, 3)]
        if mainLoc == mainVehicleLocation:
            mainVehicle.set_autopilot(False)
            mainVehicleAuto = False
        mainVehicleLocation = mainLoc


    cv.imshow('RGB Camera', cameraData['image'])

    # print(vehicle.is_alive, vehicle.get_location())

    if cv.waitKey(1) == ord('q'):
        camera.stop()
        camera.destroy()
        for i in range(len(walkerControllerList)):
            walkerControllerList[i].stop()
            walkerControllerList[i].destroy()
        for walker in walkerList:
            walker.destroy()
        for vehicle in vehicleList:
            vehicle.set_autopilot(False)
            vehicle.destroy()
        mainVehicle.destroy()
        break

cv.destroyAllWindows()
