from faker import Faker
import pandas as pd
import random

fake = Faker("en_IN") 
# en_IN = India-specific locale for names, cities, etc.

# generating customers 
def generate_customers(n=1000):
    customers = []
    for i in range(1, n+1):
        customers.append({
            "customer_id": i,
            "name": fake.name(),
            "email": fake.email(),
            "signup_date": fake.date_between(start_date="-2y", end_date="today"),
            "city": fake.city() ,
            "state": fake.state(),
        })
    return pd.DataFrame(customers)

#generate products
def generate_products(n=200):
    categories = ["Electronics", "Fashion", "Home & Kitchen", "Beauty", "Sports", "Books", "Grocery"]
    brands = ["Boat", "Noise", "Mivi", "Fabindia", "Prestige", "Wonderchef", "Puma", "Wildcraft", "Nivea"]

    products = []
    for i  in range(1 , n+1):
        category = random.choice(categories)
        products.append({
            "product_id" : i,
            "product_name": f"{random.choice(brands)} {fake.word().capitalize()} {category[:4]}",
            "category": category,
            "brand": random.choice(brands),
            "price": round(random.uniform(199,25000), 2),
        })

    return pd.DataFrame(products)


if __name__ == "__main__":
    customers_df = generate_customers(1000)
    products_df = generate_products(200)

    customers_df.to_csv("data-generator/output/customers.csv" , index=False)
    products_df.to_csv("data-generator/output/products.csv", index=False)

    print(f"Generated {len(customers_df)} customers -> data-generator/output/customers.csv")
    print(f"Generated {len(products_df)} products -> data-generator/output/products.csv")