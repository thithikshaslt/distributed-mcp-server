from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from bson import ObjectId
from utils.db_utils import get_mongo_client
from utils.constants import DEFAULT_DATABASE, PROFILE_COLLECTION, INVENTORY_COLLECTION
from utils.helpers import get_email_by_name, serialize_doc
import json

app = FastAPI()

@app.post("/add_product", summary="Add a single product")
def add_product(seller_email: str, product_name: str, price: float, quantity: int):
    try:
        client = get_mongo_client()
        db = client[DEFAULT_DATABASE]
        collection = db[INVENTORY_COLLECTION]

        product = {
            "name": product_name.strip(),
            "price": price,
            "quantity": quantity,
            "seller_email": seller_email.strip().lower(),
        }

        result = collection.insert_one(product)
        product["_id"] = str(result.inserted_id)

        return {"message": "Product added successfully", "product": product}

    except Exception as e:
        return {"error": str(e)}
    finally:
        client.close()

@app.post("/add_multiple_products", summary="Add multiple products")
def add_multiple_products(seller_email: str, products_json: list[dict]):
    client = None
    try:
        if not isinstance(products_json, list):
            return {"error": "Expected a list of products."}

        client = get_mongo_client()
        db = client[DEFAULT_DATABASE]
        collection = db[INVENTORY_COLLECTION]

        products = []
        for p in products_json:
            product = {
                "name": p["name"].strip(),
                "price": float(p["price"]),
                "quantity": int(p["quantity"]),
                "seller_email": seller_email.strip().lower()
            }
            products.append(product)

        result = collection.insert_many(products)

        for i, product in enumerate(products):
            product["_id"] = str(result.inserted_ids[i])

        return {
            "message": f"{len(products)} products added successfully",
            "products": products
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        if client:
            client.close()

@app.put("/update_product", summary="Update a product field")
def update_product(product_id: str, field: str, new_value: str):
    try:
        client = get_mongo_client()
        db = client[DEFAULT_DATABASE]
        collection = db[INVENTORY_COLLECTION]

        field = field.strip().lower()
        if field not in ["name", "price", "quantity"]:
            return {"error": "Invalid field. Choose from 'name', 'price', or 'quantity'."}

        if field == "price":
            new_value = float(new_value)
        elif field == "quantity":
            new_value = int(new_value)
        else:
            new_value = new_value.strip()

        result = collection.update_one({"_id": ObjectId(product_id)}, {"$set": {field: new_value}})
        if result.modified_count == 0:
            return {"message": "No changes made. Check product_id."}
        return {"message": f"Product updated: {field} set to {new_value}"}

    except Exception as e:
        return {"error": str(e)}
    finally:
        client.close()

@app.delete("/delete_product", summary="Delete a product")
def delete_product(product_id: str):
    try:
        client = get_mongo_client()
        db = client[DEFAULT_DATABASE]
        collection = db[INVENTORY_COLLECTION]

        result = collection.delete_one({"_id": ObjectId(product_id)})
        if result.deleted_count == 0:
            return {"message": "No product found with given ID."}
        return {"message": "Product deleted successfully."}

    except Exception as e:
        return {"error": str(e)}
    finally:
        client.close()

@app.get("/view_seller_products", summary="View all products by seller name")
def view_seller_products(seller_name: str):
    try:
        client = get_mongo_client()
        db = client[DEFAULT_DATABASE]
        collection = db[INVENTORY_COLLECTION]

        seller_email = get_email_by_name(seller_name.strip())
        if not seller_email:
            return {"error": f"No seller email found for name '{seller_name}'."}

        cursor = collection.find({"seller_email": seller_email.lower()})
        products = [serialize_doc(doc) for doc in cursor]

        return {
            "seller_name": seller_name,
            "seller_email": seller_email,
            "product_count": len(products),
            "products": products
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        client.close()

mcp = FastApiMCP(app, name="Seller Service", description="Seller operations for Super Store")
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auth_server:app", host="127.0.0.1", port=8000)