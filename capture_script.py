#!/usr/bin/env python3
import requests
import schedule
import time
import datetime
from datetime import date
import pymongo
import os
import logging
import json
import uuid
import cv2
from PIL import Image
import io
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("capture.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TabSense-Scheduler")

# MongoDB connection
try:
    mongocreds = os.getenv("mongocred", "username:password")  # Default credentials for testing
    client = pymongo.MongoClient(f"mongodb://{mongocreds}@localhost:27017")
    db = client["tablesense"]
    logger.info("Connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    sys.exit(1)

# API URL
API_URL = "http://localhost:8000"

def get_clients():
    """Get list of all clients from MongoDB collections"""
    collections = db.list_collection_names()
    clients = set()
    
    for collection in collections:
        if "-schedule" in collection:
            clients.add(collection.split("-")[0])
    
    return list(clients)

def capture_image(camera_link, output_path):
    """Capture image from camera and save to file"""
    try:
        # For real implementation, use requests or opencv to capture from camera
        # This is a simplified placeholder implementation
        
        # Approach 1: Using requests for IP cameras with HTTP access
        if camera_link.startswith(('http://', 'https://')):
            response = requests.get(camera_link, stream=True, timeout=10)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                logger.info(f"Image saved to {output_path}")
                return True
        
        # Approach 2: Using OpenCV for local cameras or RTSP streams
        else:
            # Convert string like "0" to integer for local camera
            try:
                if camera_link.isdigit():
                    camera_link = int(camera_link)
            except:
                pass
                
            cap = cv2.VideoCapture(camera_link)
            if not cap.isOpened():
                logger.error(f"Failed to open camera: {camera_link}")
                return False
                
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(output_path, frame)
                cap.release()
                logger.info(f"Image saved to {output_path}")
                return True
            else:
                cap.release()
                logger.error("Failed to capture image")
                return False
                
    except Exception as e:
        logger.error(f"Error capturing image: {str(e)}")
        return False

def create_capture_job(client, entry):
    """Create a job to capture images based on schedule entry"""
    
    def job():
        current_time = datetime.datetime.now().time()
        current_day = datetime.datetime.now().strftime("%A")
        current_date = datetime.datetime.now().date()
        holidays = requests.request("POST",
                                    f"{API_URL}/holiday/get",
                                    params = {
                                                "rooms": entry["room"]
                                             },
                                    )
        for i in holidays:
            print(i)
            if date.fromisoformat(i["start"]) <= current_date <= i["end"]:
                logger.info(f"Skipping job for {entry['label']} - currently in holiday [{i["label"]}]")
                return

        # Check if today is in the scheduled days
        if current_day not in entry.get('days', []):
            logger.info(f"Skipping job for {entry['label']} - not scheduled for {current_day}")
            return
        
        
            
        # Generate UUIDs for this capture session
        control_uuid = str(uuid.uuid4())
        current_uuid = str(uuid.uuid4())
        
        # Create directories if they don't exist
        os.makedirs("imagedata/control", exist_ok=True)
        os.makedirs("imagedata/captures", exist_ok=True)
        
        # Process each sector
        for sector in entry.get('sectors', []):
            try:
                # Get camera information
                camera_response = requests.get(
                    f"{API_URL}/cam",
                    params={
                        "client": client,
                        "room": entry['room'],
                        "sector": sector
                    }
                )
                
                if camera_response.status_code != 200:
                    logger.error(f"Failed to get camera info for room {entry['room']}, sector {sector}")
                    continue
                
                camera_info = camera_response.json()
                camera_link = camera_info['link']
                
                # If we're in the control time window, capture control image
                if datetime.time.fromisoformat(entry['start']) <= current_time <= datetime.time.fromisoformat(entry['end']):
                    control_path = f"imagedata/control/{control_uuid}-{sector}.png"
                    if capture_image(camera_link, control_path):
                        logger.info(f"Captured control image for {entry['room']}, sector {sector}")
                    else:
                        logger.error(f"Failed to capture control image for {entry['room']}, sector {sector}")
                
                # Always capture current image
                current_path = f"imagedata/captures/{current_uuid}-{sector}.png"
                if capture_image(camera_link, current_path):
                    logger.info(f"Captured current image for {entry['room']}, sector {sector}")
                else:
                    logger.error(f"Failed to capture current image for {entry['room']}, sector {sector}")
                
                # Run detection if we have both images
                if os.path.exists(f"imagedata/control/{control_uuid}-{sector}.png") and \
                   os.path.exists(f"imagedata/captures/{current_uuid}-{sector}.png"):
                    try:
                        # Prepare parameters for detection
                        detect_params = {
                            "control": control_uuid,
                            "current": current_uuid,
                            "sectors": entry.get('sectors', []),
                            "client": client,
                            "room": entry['room'],
                            "crop": True,
                            "color": "blue",
                            "shape": "auto",
                            "format": "png"
                        }
                        
                        # Make detection request
                        detect_response = requests.get(f"{API_URL}/detect", params=detect_params)
                        
                        if detect_response.status_code == 200:
                            result = detect_response.json()
                            if result:
                                logger.info(f"Detection successful for {entry['room']}! Found stains in {len(result)} sectors.")
                            else:
                                logger.info(f"No stains detected in {entry['room']}")
                        else:
                            logger.error(f"Detection API error: {detect_response.status_code} - {detect_response.text}")
                    except Exception as e:
                        logger.error(f"Error in detection process: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error processing sector {sector} for room {entry['room']}: {str(e)}")
    
    return job

def setup_schedules():
    """Set up schedules for all clients and rooms"""
    # Clear existing jobs
    schedule.clear()
    
    # Get all clients
    clients = get_clients()
    logger.info(f"Found {len(clients)} clients: {clients}")
    
    for client in clients:
        try:
            # Get all schedule entries for this client
            collection_name = f"{client}-schedule"
            schedule_entries = list(db[collection_name].find({}))
            
            logger.info(f"Found {len(schedule_entries)} schedule entries for client {client}")
            
            # Create a job for each entry and schedule it to run every minute
            # In a real implementation, you might want to schedule less frequently
            for entry in schedule_entries:
                job = create_capture_job(client, entry)
                schedule.every(5).minutes.do(job)
                logger.info(f"Scheduled job for {entry.get('label', 'Unnamed')} in room {entry.get('room', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"Error setting up schedules for client {client}: {str(e)}")

def main():
    """Main function to run the scheduler"""
    logger.info("Starting TabSense Scheduler")
    
    # Set up initial schedules
    setup_schedules()
    
    # Add a job to refresh schedules every hour
    schedule.every(1).hour.do(setup_schedules)
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)
        # try:
        #     schedule.run_pending()
        #     time.sleep(1)
        # except KeyboardInterrupt:
        #     logger.info("Scheduler stopped by user")
        #     break
        # except Exception as e:
        #     logger.error(f"Error in scheduler loop: {str(e)}\n{str(e.__traceback__)}")
        #     time.sleep(5)  # Wait a bit before retrying

if __name__ == "__main__":
    main()
