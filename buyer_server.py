from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from bson import ObjectId
from utils.db_utils import get_mongo_client
from utils.constants import DEFAULT_DATABASE, PROFILE_COLLECTION, INVENTORY_COLLECTION
from utils.helpers import get_email_by_name
import json

app = FastAPI()

@app.get("/view_all_products", operation_id="view_all_products", summary="View all products in store")
def view_all_products():
    client = get_mongo_client()
    try:
        db = client[DEFAULT_DATABASE]
        products_cursor = db[INVENTORY_COLLECTION].find()
        products = [{
            "product_id": str(p["_id"]),
            "name": p["name"],
            "price": p["price"],
            "quantity": p["quantity"],
            "seller_email": p["seller_email"]
        } for p in products_cursor]
        return products or "No products found in the store."
    finally:
        client.close()

@app.get("/view_cart", operation_id="view_cart", summary="View contents of the buyer's cart")
def view_cart(buyer_name: str):
    client = get_mongo_client()
    try:
        db = client[DEFAULT_DATABASE]
        profile = db[PROFILE_COLLECTION].find_one({
            "name": {"$regex": f"^{buyer_name.strip()}$", "$options": "i"},
            "role": {"$regex": "^buyer$", "$options": "i"}
        })
        if not profile:
            return f"No buyer found with name: {buyer_name}"
        cart = profile.get("cart", [])
        if not cart:
            return f"{buyer_name}'s cart is empty."

        return {
            "buyer_name": profile["name"],
            "buyer_email": profile["email"],
            "cart_count": len(cart),
            "cart": [{k: str(v) if isinstance(v, ObjectId) else v for k, v in item.items()} for item in cart]
        }
    finally:
        client.close()

@app.get("/view_product_details", operation_id="view_product_details", summary="View a product's details")
def view_product_details(product_id: str):
    client = get_mongo_client()
    try:
        db = client[DEFAULT_DATABASE]
        product = db[INVENTORY_COLLECTION].find_one({"_id": ObjectId(product_id)})
        if not product:
            return "Product not found."
        return {
            "product_id": str(product["_id"]),
            "name": product["name"],
            "price": product["price"],
            "quantity": product["quantity"],
            "seller_email": product["seller_email"]
        }
    finally:
        client.close()

@app.get("/check_balance", operation_id="check_balance", summary="Check buyer balance by name")
def check_balance(name: str):
    email = get_email_by_name(name)
    if not email:
        return f"No buyer found with name: {name}"
    client = get_mongo_client()
    try:
        db = client[DEFAULT_DATABASE]
        user = db[PROFILE_COLLECTION].find_one({"email": email})
        return f"{name} has ₹{user.get('balance')} in their account."
    finally:
        client.close()

@app.post("/add_balance", operation_id="add_balance", summary="Add balance to buyer account")
def add_balance(name: str, amount: float):
    if amount <= 0:
        return "Amount must be greater than zero."
    email = get_email_by_name(name)
    if not email:
        return f"No buyer found with name: {name}"
    client = get_mongo_client()
    try:
        db = client[DEFAULT_DATABASE]
        db[PROFILE_COLLECTION].update_one({"email": email}, {"$inc": {"balance": amount}})
        user = db[PROFILE_COLLECTION].find_one({"email": email})
        return f"Balance updated. New balance: ₹{user.get('balance')}"
    finally:
        client.close()

@app.post("/add_to_cart", operation_id="add_to_cart", summary="Add item(s) to buyer's cart")
def add_to_cart(name: str, product_id: str = None, quantity: int = None, items: list = None):
    email = get_email_by_name(name)
    if not email:
        return f"No buyer found with name: {name}"
    client = get_mongo_client()
    try:
        db = client[DEFAULT_DATABASE]
        inventory = db[INVENTORY_COLLECTION]
        profile = db[PROFILE_COLLECTION]

        cart_items = []
        if items:
            for item in items:
                pid = item.get("product_id")
                qty = item.get("quantity", 0)
                if not pid or qty <= 0:
                    continue
                product = inventory.find_one({"_id": ObjectId(pid)})
                if product:
                    cart_items.append({
                        "product_id": str(product["_id"]),
                        "name": product["name"],
                        "price": product["price"],
                        "quantity": qty,
                        "seller_email": product["seller_email"]
                    })

            if not cart_items:
                return "No valid items to add."
            profile.update_one({"email": email}, {"$push": {"cart": {"$each": cart_items}}})
            return f"Added {len(cart_items)} item(s) to cart."

        elif product_id and quantity and quantity > 0:
            product = inventory.find_one({"_id": ObjectId(product_id)})
            if not product:
                return "Product not found."
            cart_item = {
                "product_id": str(product["_id"]),
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "seller_email": product["seller_email"]
            }
            profile.update_one({"email": email}, {"$push": {"cart": cart_item}})
            return f"Added {quantity} of {product['name']} to cart."

        return "Invalid input."

    finally:
        client.close()

@app.delete("/delete_from_cart", operation_id="delete_from_cart", summary="Delete an item from cart")
def delete_from_cart(name: str, product_id: str):
    email = get_email_by_name(name)
    if not email:
        return f"No buyer found with name: {name}"
    client = get_mongo_client()
    try:
        db = client[DEFAULT_DATABASE]
        result = db[PROFILE_COLLECTION].update_one(
            {"email": email},
            {"$pull": {"cart": {"product_id": product_id}}}
        )
        return "Item removed from cart." if result.modified_count > 0 else "Item not found in cart."
    finally:
        client.close()

@app.post("/place_order", operation_id="place_order", summary="Place order for all items in cart")
def place_order(name: str):
    email = get_email_by_name(name)
    if not email:
        return f"No buyer found with name: {name}"
    client = get_mongo_client()
    try:
        db = client[DEFAULT_DATABASE]
        profile = db[PROFILE_COLLECTION]
        inventory = db[INVENTORY_COLLECTION]
        orders = db["order"]
        payments = db["payment"]

        buyer = profile.find_one({"email": email})
        cart = buyer.get("cart", [])
        if not cart:
            return f"{name}'s cart is empty."
        balance = buyer.get("balance", 0.0)

        total = 0.0
        for item in cart:
            product = inventory.find_one({"_id": ObjectId(item["product_id"])})
            if not product:
                return f"Product {item['product_id']} not found."
            if item["quantity"] > product["quantity"]:
                return f"Insufficient stock for {item['name']}."
            total += item["price"] * item["quantity"]

        if total > balance:
            return f"Insufficient balance. Total: ₹{total}, Available: ₹{balance}"

        profile.update_one({"email": email}, {"$inc": {"balance": -total}})
        for item in cart:
            inventory.update_one({"_id": ObjectId(item["product_id"])}, {"$inc": {"quantity": -item["quantity"]}})
            orders.insert_one({
                "buyer_email": email,
                "prod_name": item["name"],
                "quantity": item["quantity"],
                "total_price": item["price"] * item["quantity"]
            })

        for item in cart:
            payments.insert_one({
                "buyer_email": email,
                "seller_email": item["seller_email"],
                "amount": item["price"] * item["quantity"]
            })

        profile.update_one({"email": email}, {"$set": {"cart": []}})
        return f"Order placed! Total ₹{total} deducted."

    finally:
        client.close()

mcp = FastApiMCP(app, name="Buyer Service", description="Buyer operations for Super Store")
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auth_server:app", host="127.0.0.1", port=8001)