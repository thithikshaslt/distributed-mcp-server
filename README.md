# Distributed MCP Server

This is a MongoDB-backed distributed server system using the Model Context Protocol (MCP), built with FastAPI. It simulates a modular architecture for a shopping platform with separate services for authentication, buyers, and sellers.

## Project Structure

- auth_server.py          - Handles user registration, login
- buyer_server.py         - Manages buyer operations like viewing products, managing cart, placing orders
- seller_server.py        - Manages seller operations like
- adding and viewing products
- Dockerfile              - Dockerfile for building service containers
- docker-compose.yml      - Defines and runs all three services (auth:8002, buyer:8001, seller:8000)

## Notes

- MongoDB connection settings should be configured via `.env`.
- Each service runs on its own port and exposes tools via MCP.