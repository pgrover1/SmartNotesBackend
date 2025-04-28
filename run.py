#!/usr/bin/env python3
import argparse
import os
import uvicorn

def main():
    """Run the API server"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Notes API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--init-db", action="store_true", help="Initialize MongoDB database before starting")
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        print("Initializing MongoDB database...")
        from app.db.init_mongodb import init_mongodb
        init_mongodb()
        print("Database initialization complete.")
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()