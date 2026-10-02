
from faker import Faker
import pandas as pd
import random
from datetime import datetime, timedelta

fake = Faker("en_IN")

def load_master_data():
    customers_df = pd.read_csv("data-generator/output/customers.csv")
    products_df = pd.read_csv("data-generator/output/products.csv")
    return customers_df, products_df

def generate_daily_orders(customers_df, products_df, order_date, n_orders=150):
    orders = []
    customer_ids = customers_df["customer_id"].tolist()
    product_ids = products_df["product_id"].tolist()
    product_prices = dict(zip(products_df["product_id"], products_df["price"]))

    for i in range(1, n_orders + 1):
        product_id = random.choice(product_ids)
        quantity = random.randint(1, 4)
        unit_price = product_prices[product_id]

        orders.append({
            "order_id": f"{order_date.strftime('%Y%m%d')}-{i:05d}",
            "customer_id": random.choice(customer_ids),
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": round(unit_price * quantity, 2),
            "order_date": order_date.strftime("%Y-%m-%d"),
            "order_status": random.choices(
                ["completed", "cancelled", "returned"],
                weights=[85, 10, 5]
            )[0],
        })
    return pd.DataFrame(orders)

def generate_daily_inventory(products_df, order_date):
    inventory = []
    for _, product in products_df.iterrows():
        inventory.append({
            "product_id": product["product_id"] ,
            "snapshot_date": order_date.strftime("%Y-%m-%d") ,
            "stock_quantity": random.randint(0, 500) , 
            "warehouse_location": random.choice(["Mumbai", "Pune", "Bangalore", "Delhi", "Chennai"]),
        })
    return pd.DataFrame(inventory)

if __name__ == "__main__":
    customers_df, products_df = load_master_data()

    order_date = datetime.today()


    orders_df = generate_daily_orders(customers_df, products_df, order_date)
    inventory_df = generate_daily_inventory(products_df, order_date)

    date_str = order_date.strftime("%Y-%m-%d")
    orders_path = f"data-generator/output/orders_{date_str}.csv"
    inventory_path = f"data-generator/output/inventory_{date_str}.csv"

    orders_df.to_csv(orders_path, index=False)
    inventory_df.to_csv(inventory_path, index=False)

    print(f"Generated {len(orders_df)} orders -> {orders_path}")
    print(f"Generated {len(inventory_df)} inventory records -> {inventory_path}")