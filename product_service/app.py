import time
import pika
import json
import threading
from flask import Flask, jsonify

app = Flask(__name__)

products = {
    "101": {"id": "101", "name": "3D Model Pack", "price": 10.0, "available": 5},
    "102": {"id": "102", "name": "Game Texture", "price": 5.0, "available": 10}
}


@app.route("/product/<product_id>")
def get_product(product_id):
    return jsonify(products.get(product_id, {"error": "Not found"}))


def start_consumer():
    connection = None
    for i in range(10):  # 10 спроб
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('rabbitmq'))
            print("✅ Connected to RabbitMQ!")
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"⏳ RabbitMQ not ready, retrying ({i+1}/10)...")
            time.sleep(5)

    if not connection:
        print("❌ Could not connect to RabbitMQ after 10 attempts.")
        return
    # restart on failure
    channel = connection.channel()
    channel.queue_declare(queue='orders')

    def callback(ch, method, properties, body):
        message = json.loads(body)
        if "product_id" in message:
            pid = message["product_id"]
            if pid in products:
                products[pid]["available"] -= 1
                print(
                    f"🔔 Product {pid} sold! Remaining: {products[pid]['available']}")

    channel.basic_consume(
        queue='orders', on_message_callback=callback, auto_ack=True)
    print("🐇 Product-Service listening for order events...")
    channel.start_consuming()


threading.Thread(target=start_consumer, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
