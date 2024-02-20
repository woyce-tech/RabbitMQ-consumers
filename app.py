from flask import Flask
import pika
import os
from threading import Thread

app = Flask(__name__)
PORT = int(os.environ.get('PORT', 4002))
AMQP_URL = os.environ.get('AMQP_URL', 'amqp://localhost:5672')
# AMQP_URL = os.environ.get('AMQP_URL', 'amqp://guest:guest@redditmqmg.a2gkhna2h0crepaw.eastus.azurecontainer.io:5672/')


def on_message_callback(ch, method, properties, body):
    print(f'Received message from queue {method.routing_key}:', body.decode())
    ch.basic_ack(delivery_tag=method.delivery_tag)


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
