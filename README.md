# Distributed MCP Server

This project implements a MongoDB-backed distributed server system using FastAPI and the Model Context Protocol (MCP). It simulates a modular shopping platform with separate services for authentication, buyers, and sellers. Each service exposes tools over MCP for integration with AI agents or other clients.

## What is MCP?

Model Context Protocol (MCP) is a protocol that defines how AI models (or agents) can interact with external tools, services, and APIs in a structured and secure way. MCP allows services to expose specific functions as *tools* that can be called by an AI agent. These tools describe their inputs and outputs clearly, enabling safe and contextual execution of operations.

In this project, each of the three services (auth, buyer, seller) registers its operations (e.g., `register_user`, `view_products`, `add_product`) as MCP tools. This allows AI assistants like **Claude Desktop** to dynamically discover and invoke these tools during a conversation or workflow.

## Project Structure

auth_server.py        - Handles user registration, login, updating user details  
buyer_server.py       - Manages buyer operations: view products, manage cart, place orders  
seller_server.py      - Manages seller operations: add, update, view products  
Dockerfile            - Defines container setup for each service  
docker-compose.yml    - Orchestrates running all three services together  
utils/                - Common utility functions (e.g. database connections)  
.env                  - MongoDB connection credentials and configuration  
requirements.txt      - Python dependencies  

## How It Works

- **Auth Server (8002)**: Provides tools for user registration, login, and updating personal details.  
- **Buyer Server (8001)**: Exposes tools for buyers to browse products, manage their cart, and place orders.  
- **Seller Server (8000)**: Exposes tools for sellers to add and manage products in inventory.  

Each service connects to a shared MongoDB database and runs independently. AI assistants like Claude can interact with these services by calling their exposed tools through the MCP interface.

## Running the Project


- Docker and Docker Compose installed  
- MongoDB connection string configured in the `.env` file  

### Steps

1. Clone the repository  
   git clone https://github.com/thithikshaslt/distributed-mcp-server.git  
   cd distributed-mcp-server  

2. Build and start all services  
   docker compose up --build -d  

3. The services will be available at:  
   - Seller MCP: http://<your-ec2-ip>:8000/mcp  
   - Buyer MCP: http://<your-ec2-ip>:8001/mcp  
   - Auth MCP: http://<your-ec2-ip>:8002/mcp  

4. Stop the services  
   docker compose down  

## Notes

- Ensure that ports 8000, 8001, and 8002 are open in your EC2 security group.  
- All MongoDB connection info should be placed in the `.env` file.  
- This setup enables direct interaction between AI assistants like Claude Desktop and your backend services using MCP tools.
