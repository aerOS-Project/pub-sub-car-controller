# aerOS ORION pub/sub example

This repository is intended to illustrate a pub/sub, stateless application designed to take advantage of aerOS' data continuum and automatic redeployment features.

## Demo outline

- A robot car is following a certain pathing/route
    - The car is an IoT-enabled device, registered as an InfrastructureElement in an aerOS domain.
    - The movement is controlled by an aerOS Service running on the car that reads coordinates from the data continuum (ORION)
- The aerOS Service writes the robot's next position/angle in the data continuum
    - *key*: The Service is stateless!
- The robot reads its next order from the data continuum and executes it
- After some time, the node hosting the service goes down
- The aerOS HLO notices that the service is down
- The Services that were deployed in that node are automatically redeployed to other nodes
- The robot continues movement

## Service behaviour

The service:

1. Reads an XY coordinate from the data continuum corresponding to the robot
2. From the obtained coordinates, get the next order
3. Send the orders to the robot via the data continuum

Since the service is stateless, it should survive a redeployment regardless of the state of the robot when the service goes down

The dockerized application takes in the `ORION_BROKER_URL` environment variable to connect to a valid ORION instance in the domain, as well as a valid `AEROS_CAR_DEMO_ORION_TOKEN` Bearer token for authorization. Both are expected to be provided by the outside k8s environment