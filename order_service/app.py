from flask import Flask, jsonify, request
import requests
import pika
import json

app = Flask(__name__)


@app.route("/order", methods=["POST"])
def create_order():
    data = request.json
    user = requests.get(
        f"http://user_service:5001/user/{data['user_id']}").json()
    product = requests.get(
        f"http://product_service:5002/product/{data['product_id']}").json()

    order = {
        "user": user.get("name"),
        "product_id": product.get("id"),
        "product_name": product.get("name"),
        "price": product.get("price")
    }

    # Надсилка події у RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='orders')
    channel.basic_publish(
        exchange='', routing_key='orders', body=json.dumps(order))
    connection.close()

    print(f"📦 Order created for {order['product_name']} by {order['user']}")
    return jsonify(order)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
