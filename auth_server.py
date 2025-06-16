from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from utils.db_utils import get_mongo_client
from utils.constants import DEFAULT_DATABASE, PROFILE_COLLECTION

app = FastAPI()

@app.get("/check_user", operation_id="checkUser", summary="Check if the given user name exists")
def check_user(name: str):
    client = None
    try:
        client = get_mongo_client()
        db = client[DEFAULT_DATABASE]
        prof = db[PROFILE_COLLECTION]
        count = prof.count_documents({"name": {"$regex": f"^{name.strip()}$", "$options": "i"}})

        if count > 0:
            return {
                "result": f"There {'is' if count == 1 else 'are'} {count} account{'s' if count > 1 else ''} with '{name.strip()}' as the name."
            }
        else:
            return {"result": f"There are no accounts with '{name.strip()}' as the name."}
    except Exception as e:
        return {"error": f"Error checking user: {str(e)}"}
    finally:
        if client:
            client.close()

@app.post("/login_user", operation_id="loginUser", summary="Login with email and password")
def login_user(email: str, password: str):
    client = get_mongo_client()
    db = client[DEFAULT_DATABASE]
    prof = db[PROFILE_COLLECTION]
    user_ls = list(prof.find({"email": email, "pwd": password}, {"_id": 0}))
    if user_ls:
        return {"role": user_ls[0]["role"]}
    else:
        return {"error": "no user of that email or password"}

@app.post("/register_user", operation_id="registerUser", summary="Register a new user")
def register_user(
    name: str,
    password: str,
    role: str,
    email: str,
    phno: int = None,
    addr: str = None,
):
    dict_order = {
        "name": name,
        "email": email,
        "pwd": password,
        "phno": phno,
        "addr": addr,
        "role": role.lower(),
        "balance": 100.0,
        "cart": [],
    }
    client = get_mongo_client()
    db = client[DEFAULT_DATABASE]
    prof = db[PROFILE_COLLECTION]
    result = prof.insert_one(dict_order)
    if result.inserted_id:
        return {"result": "User successfully registered"}
    else:
        return {"error": "Something went wrong, try again later"}

@app.put("/update_details", operation_id="update_pers_Details", summary="Update user details")
def update_pers_details(
    email: str,
    password: str,
    name: str = None,
    phono: int = None,
    addr: str = None,
):
    client = get_mongo_client()
    db = client[DEFAULT_DATABASE]
    prof = db[PROFILE_COLLECTION]

    user_profile = list(prof.find({"email": email, "pwd": password}))
    if not user_profile:
        return {"error": "no user profile with given credentials"}

    user = user_profile[0]

    update_fields = {
        "name": name or user.get("name"),
        "phno": phono or user.get("phno"),
        "addr": addr or user.get("addr"),
    }

    search_query = {"email": email, "pwd": password}
    change_query = {"$set": update_fields}

    result = prof.update_one(search_query, change_query)

    if result.modified_count > 0:
        return {"result": "personal details updated"}
    else:
        return {"result": "no modifications done to profile"}

@app.get("/")
def root():
    return {"message": "Auth MCP server is running"}

mcp = FastApiMCP(app, name="Auth MCP", description="Authentication and user management service")
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auth_server:app", host="127.0.0.1", port=8002)