from kafka import KafkaProducer
from faker import Faker
import json
import random
import time
from datetime import datetime

fake = Faker("en_IN")

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

EVENT_TYPES = ["page_view", "search", "add_to_cart", "remove_from_cart", "checkout_start", "purchase"]
PAGES = ["/home", "/product/123", "/product/456", "/cart", "/checkout", "/search", "/category/electronics"]

def generate_event():
    return {
        "event_id": fake.uuid4(),
        "session_id": fake.uuid4(),
        "customer_id": random.randint(1, 1000),  # matches customer_id range from Step 1
        "event_type": random.choices(
            EVENT_TYPES,
            weights=[50, 15, 15, 5, 10, 5]  # page_view most common, purchase rarest
        )[0],
        "page_url": random.choice(PAGES),
        "device": random.choice(["mobile", "desktop", "tablet"]),
        "timestamp": datetime.utcnow().isoformat(),
    }

if __name__ == "__main__":
    print("Starting clickstream producer... press Ctrl+C to stop.")
    try:
        while True:
            event = generate_event()
            producer.send("clickstream-events", value=event)
            print(f"Sent: {event['event_type']} | customer_id={event['customer_id']}")
            time.sleep(random.uniform(0.2, 1.0))  # simulate irregular real user activity
    except KeyboardInterrupt:
        print("\nStopped producer.")
        producer.close()