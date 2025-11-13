from typing import Dict
from warnings import warn
from flask import Flask, request
import argparse
import requests
import json
from os import environ

app = Flask(__name__)

def get_host_public_ip() -> str:
    """
    Returns the host's public IP
    """
    return requests.get('https://api.ipify.org').content.decode('utf8')

def orion_write_attrs_to_entity(
        orion_endpoint: str,
        entity_id: str,
        fields: Dict[str, str | bool | int | float]
    ) -> requests.Response:
    """
    Build and execute an ORION entity write request

    Arguments:
        orion_endpoint: The endpoint of an aerOS ORION instance
        entity_id: The NGSI-LD ID of the entity to write to
        fields: The fields to write to

    Returns:
        Response of the ORION Broker
    """
    
    # Based on https://github.com/FIWARE/tutorials.NGSI-LD/blob/master/docs/ngsi-ld-operations.md#overwrite-the-value-of-an-attribute-value
    
    res = requests.patch(
        f'{orion_endpoint}ngsi-ld/v1/entities/{entity_id}/',
        headers={
            'aerOS': 'true',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {environ["AEROS_CAR_DEMO_ORION_TOKEN"]}'
        },
        data=json.dumps(fields)
    )

    if res.status_code != 204: 
        #raise Exception(f'Non-204 code returned: {res.status_code} {res.text}')
        warn(f'Non-204 code returned: {res.status_code} {res.text}')


    return res

def subscribe_to_orion(
        orion_endpoint: str, 
        entity_id: str, 
        post_uri: str
    ) -> requests.Response:
    """
    Build and send a subscription request to an ORION instance

    Arguments:
        orion_endpoint: The endpoint of an aerOS ORION instance
        entity_id: The NGSI-LD ID of the entity to write to
        post_uri: The POST URI for the ORION broker to talk to on entity updates

    Returns:
        Response of the ORION Broker
    """

    payload = {
        'id': 'urn:aeros:subscription:vehicle:controller',
        'description': 'Subscription to Vehicle entity type',
        'type': 'Subscription',
        'entities': [{
            'id': entity_id,
            'type': 'Vehicle'
        }],
        'watchedAttributes': ['location', 'direction', 'serviceStatus'],
        'notification': {
            'attributes': ['location', 'move', 'direction', 'serviceStatus', 'signalQuality', 'speed', 'heading'],
            'endpoint': {
                'uri': post_uri,
                'accept': 'application/json'
            }
        },
        'throttling': 1
    }

    res = requests.post(
        f'{orion_endpoint}/subscriptions/', 
        data=json.dumps(payload), 
        headers={
            'aerOS': 'true',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {environ["AEROS_CAR_DEMO_NCSRD_ORION_TOKEN"]}'
    })

    assert res.status_code == 201, f'Subscription failed: {res.status_code} - {res.text}'
    return res



@app.route('/car_update', methods=['POST'])
def reply_to_status_update():
    vehicle_entity = request.json['data'][0]
    print('-----------------------------------')
    print(f"Location: {vehicle_entity['location']['value']['coordinates']}")
    print(f"Move: {vehicle_entity['move']['value']}")
    print(f"Direction: {vehicle_entity['direction']['value']}")
    print(f"Service status: {vehicle_entity['serviceStatus']['value']}")
    print(f"Signal quality: {vehicle_entity['signalQuality']['value']}")
    print(f"Speed: {vehicle_entity['speed']['value']}")


    next_orders = {
        'heading': '36.0 degrees',
        'move': True
    }

    if not app.is_monitor:
        orion_write_attrs_to_entity(app.orion_endpoint, "urn:ngsi-ld:vehicle:5g-car:1", next_orders)

    return {}, 200

@app.route('/healthz', methods=['GET'])
def is_live():
    return {'is_live': True}, 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='aeros-demo-apr-4th',
        description='The Service for the aerOS Service redeployment robot demo'
    )

    parser.add_argument(
        'entity_id', 
        help='The ORION ID of the controlled entity'
    )
    parser.add_argument(
        '-m', '--monitor_only', 
        help='Do not send movement orders and instead only monitor the state of the car', 
        action='store_true'
    )

    parser.add_argument(
        '-lp', '--listen_port',
        help='The port to use for the hosted subscription listener',
        default=8080,
        type=int
    )

    args = parser.parse_args()
    app.orion_endpoint = environ['ORION_BROKER_URL']
    app.entity_id = args.entity_id
    app.is_monitor = args.monitor_only
    listen_port = args.listen_port


    post_uri = f'http://<YOUR_DOMAIN_HERE>'

    print(f'Subscribing to entity {app.entity_id} through ORION broker at {app.orion_endpoint} on {post_uri}...')
    res = subscribe_to_orion(
        app.orion_endpoint, 
        app.entity_id,
        post_uri=post_uri+'/car_update'
    )
    print(f'Subscribed on local port {listen_port}: {res.status_code} {res.text}')
    
    app.run(host='0.0.0.0', port=listen_port)