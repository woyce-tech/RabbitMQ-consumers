from flask import Flask
import pika
import os
import requests
import json
from threading import Thread

app = Flask(__name__)
PORT = int(os.environ.get('PORT', 4002))
AMQP_URL = os.environ.get('AMQP_URL', 'amqp://localhost:5672')
# AMQP_URL = os.environ.get('AMQP_URL', 'amqp://guest:guest@redditmqmg.a2gkhna2h0crepaw.eastus.azurecontainer.io:5672/')

# Define a dictionary mapping keys to API configurations
api_configs = {
    'key3': {
        'method': 'GET',
        'url': 'https://first-api.com/data'
    },
    'key1': {
        'method': 'POST',
        'url': 'http://127.0.0.1:5000/consumer_send_notifications'
    },
    # Add more key-endpoint mappings as needed
}


def call_api(api_method, api_url, headers=None, payload=None, body=None):
    """Calls the given API URL with specified method and returns the response."""
    try:
        if api_method.upper() == 'POST':
            response = requests.post(api_url, headers=headers, data=json.dumps(body.decode()))
        elif api_method.upper() == 'GET':
            response = requests.get(api_url, headers=headers)
        else:
            raise ValueError("Unsupported API method: should be 'GET' or 'POST'")

        response.raise_for_status()
        return ('success', response.json())  # Assuming response is in JSON format
    except requests.HTTPError as http_err:
        return ('http_error', f"HTTP error occurred: {http_err}")
    except ValueError as val_err:
        return ('value_error', str(val_err))
    except Exception as err:
        return ('error', f"An error occurred: {err}")


def on_message_callback(ch, method, properties, body):
    print(f'Received message from queue {method.routing_key}:', body.decode())
    api_config = api_configs.get(method.routing_key)

    if api_config:
        headers = {'Content-Type': 'application/json'}
        status, result = call_api(api_config['method'], api_config['url'],
                                  headers=headers, body=body)

        if status == 'success':
            print(f'Successfully called API for {method.routing_key}:', result)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            print(f'Failed to call API for {method.routing_key}.', result)

    else:
        print(f"No API endpoint defined for {method.routing_key}")


def connect_queue():
    params = pika.URLParameters(AMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    # Declare queues and consume messages for Exchange One and Two
    exchange_queues = {
        'Exchange One': ['queue1', 'queue2', 'queue3'],
        'Exchange Two': ['queue6', 'queue5', 'queue4']
    }

    for exchange, queues in exchange_queues.items():
        for queue in queues:
            channel.queue_declare(queue=queue, durable=True)
            print(f'Consumer connected to queue: {queue} for {exchange}')
            channel.basic_consume(queue=queue, on_message_callback=on_message_callback)

    return connection, channel


def start_consumer():
    connection, channel = None, None
    try:
        connection, channel = connect_queue()
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Consumer stopped with KeyboardInterrupt")
    except Exception as error:
        print('An error occurred while consuming messages:', error)
    finally:
        if channel:
            channel.close()
        if connection:
            connection.close()


@app.route('/')
def index():
    return "Hello, World!"


if __name__ == '__main__':
    consumer_thread = Thread(target=start_consumer)
    consumer_thread.start()
    try:
        app.run(host="0.0.0.0", debug=True, port=PORT)
    finally:
        consumer_thread.join()
