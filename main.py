#!/usr/bin/env python3
"""
Main entry point for the apartment search application.
This file provides a simple wrapper to start the application.
"""
import asyncio
import logging
import sys
from app import ApartmentSearchApp

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point."""
    print("\n=== Wohnungssuche - Apartment Search Application ===\n")
    print("Starting application...\n")
    
    # Create and start the application
    app = ApartmentSearchApp()
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
    finally:
        # Ensure proper cleanup
        await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except Exception as e:
        print(f"\nApplication crashed: {e}", file=sys.stderr)
        sys.exit(1)
