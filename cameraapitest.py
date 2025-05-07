import requests
import json
import uuid
from typing import Optional, Dict, Any, List
import random

# Base URL of the API
BASE_URL = "http://localhost:8000"  # Change this to your actual API URL

class CameraAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_client = "testclient"
        self.test_cameras = []

    def generate_camera_data(self, client: Optional[str] = None, room: Optional[str] = None, 
                           sector: Optional[int] = None, id: Optional[str] = None) -> Dict[str, Any]:
        """Generate random camera data for testing."""
        return {
            "id": id or str(uuid.uuid4())[:8],
            "client": client or self.test_client,
            "room": room or f"Room-{random.randint(100, 999)}",
            "sector": sector or random.randint(1, 5),
            "link": f"https://camera-feed.example.com/{random.randint(1000, 9999)}"
        }

    def add_camera(self, camera_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test the POST /cam endpoint."""
        response = requests.post(f"{self.base_url}/cam", json=camera_data)
        print(f"\n[ADD CAMERA] Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            self.test_cameras.append(camera_data)
            return {"success": True, "data": camera_data, "response": response.text}
        return {"success": False, "error": response.text}

    def get_camera(self, client: str, room: Optional[str] = None, 
                  sector: Optional[int] = None, id: Optional[str] = None) -> Dict[str, Any]:
        """Test the GET /cam endpoint."""
        params = {"client": client}
        
        if id:
            params["id"] = id
        elif room and sector:
            params["room"] = room
            params["sector"] = sector
        
        response = requests.get(f"{self.base_url}/cam", params=params)
        print(f"\n[GET CAMERA] Status: {response.status_code}")
        print(f"Request params: {params}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return {"success": True, "data": response.json()}
        else:
            print(f"Error: {response.text}")
            return {"success": False, "error": response.text}

    def update_camera(self, client: str, id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test the POST /cam/update endpoint."""
        params = {"client": client, "id": id}
        
        response = requests.post(f"{self.base_url}/cam/update", params=params, json=update_data)
        print(f"\n[UPDATE CAMERA] Status: {response.status_code}")
        print(f"Request params: {params}")
        print(f"Update data: {update_data}")
        
        if response.status_code == 200:
            print(f"Response: {response.text}")
            return {"success": True, "response": response.text}
        else:
            print(f"Error: {response.text}")
            return {"success": False, "error": response.text}

    def delete_camera(self, client: str, room: Optional[str] = None, 
                     sector: Optional[int] = None, id: Optional[str] = None) -> Dict[str, Any]:
        """Test the POST /cam/delete endpoint."""
        params = {"client": client}
        
        if id:
            params["id"] = id
        elif room and sector:
            params["room"] = room
            params["sector"] = sector
        elif room:
            params["room"] = room
        
        response = requests.post(f"{self.base_url}/cam/delete", params=params)
        print(f"\n[DELETE CAMERA] Status: {response.status_code}")
        print(f"Request params: {params}")
        
        if response.status_code == 200:
            print(f"Response: {response.text}")
            return {"success": True, "response": response.text}
        else:
            print(f"Error: {response.text}")
            return {"success": False, "error": response.text}

    def run_basic_tests(self):
        """Run a series of basic tests for the camera API."""
        print("\n==== RUNNING BASIC CAMERA API TESTS ====")
        
        # Test 1: Add a new camera
        print("\n=== Test 1: Add a new camera ===")
        camera_data = self.generate_camera_data()
        add_result = self.add_camera(camera_data)
        
        if add_result["success"]:
            camera_id = camera_data["id"]
            client = camera_data["client"]
            room = camera_data["room"]
            sector = camera_data["sector"]
            
            # Test 2: Get camera by ID
            print("\n=== Test 2: Get camera by ID ===")
            get_result = self.get_camera(client=client, id=camera_id)
            
            # Test 3: Get camera by room and sector
            print("\n=== Test 3: Get camera by room and sector ===")
            get_result_2 = self.get_camera(client=client, room=room, sector=sector)
            
            # Test 4: Update camera
            print("\n=== Test 4: Update camera ===")
            update_data = {
                "room": f"Updated-Room-{random.randint(100, 999)}",
                "sector": random.randint(1, 5),
                "link": f"https://camera-feed.example.com/updated/{random.randint(1000, 9999)}"
            }
            update_result = self.update_camera(client=client, id=camera_id, update_data=update_data)
            
            # Test 5: Verify update by getting camera again
            print("\n=== Test 5: Verify update by getting camera again ===")
            get_updated_result = self.get_camera(client=client, id=camera_id)
            
            # Test 6: Delete camera by ID
            print("\n=== Test 6: Delete camera by ID ===")
            delete_result = self.delete_camera(client=client, id=camera_id)
            
            # Test 7: Verify deletion by trying to get the deleted camera
            print("\n=== Test 7: Verify deletion by trying to get the deleted camera ===")
            get_deleted_result = self.get_camera(client=client, id=camera_id)
            
        else:
            print("Failed to add test camera. Skipping subsequent tests.")
            
    def run_advanced_tests(self):
        """Run more complex test scenarios."""
        print("\n==== RUNNING ADVANCED CAMERA API TESTS ====")
        
        # Test 8: Add multiple cameras to the same room
        print("\n=== Test 8: Add multiple cameras to the same room ===")
        common_room = f"Room-{random.randint(100, 999)}"
        camera_data_1 = self.generate_camera_data(room=common_room, sector=1)
        camera_data_2 = self.generate_camera_data(room=common_room, sector=2)
        camera_data_3 = self.generate_camera_data(room=common_room, sector=3)
        
        add_result_1 = self.add_camera(camera_data_1)
        add_result_2 = self.add_camera(camera_data_2)
        add_result_3 = self.add_camera(camera_data_3)
        
        # Test 9: Delete all cameras in a room
        print("\n=== Test 9: Delete all cameras in a room ===")
        delete_room_result = self.delete_camera(client=self.test_client, room=common_room)
        
        # Test 10: Add camera with specific ID
        print("\n=== Test 10: Add camera with specific ID ===")
        specific_id = "test-cam-001"
        camera_data_specific = self.generate_camera_data(id=specific_id)
        add_specific_result = self.add_camera(camera_data_specific)
        
        # Test 11: Get camera with specific ID
        print("\n=== Test 11: Get camera with specific ID ===")
        get_specific_result = self.get_camera(client=self.test_client, id=specific_id)
        
        # Test 12: Delete specific camera
        print("\n=== Test 12: Delete specific camera ===")
        delete_specific_result = self.delete_camera(client=self.test_client, id=specific_id)
        
    def run_error_tests(self):
        """Test error handling scenarios."""
        print("\n==== RUNNING ERROR HANDLING TESTS ====")
        
        # Test 13: Try to get camera without required parameters
        print("\n=== Test 13: Try to get camera without required parameters ===")
        try:
            get_error_result = self.get_camera(client=self.test_client)
            print(f"Result: {get_error_result}")
        except Exception as e:
            print(f"Expected error occurred: {str(e)}")
        
        # Test 14: Try to delete camera without required parameters
        print("\n=== Test 14: Try to delete camera without required parameters ===")
        try:
            delete_error_result = self.delete_camera(client=self.test_client)
            print(f"Result: {delete_error_result}")
        except Exception as e:
            print(f"Expected error occurred: {str(e)}")
        
        # Test 15: Try to update non-existent camera
        print("\n=== Test 15: Try to update non-existent camera ===")
        update_error_result = self.update_camera(
            client=self.test_client, 
            id="non-existent-id", 
            update_data={"room": "New Room", "sector": 5}
        )
        
        # Test 16: Try to get non-existent camera
        print("\n=== Test 16: Try to get non-existent camera ===")
        get_nonexistent_result = self.get_camera(client=self.test_client, id="non-existent-id")

    def cleanup_test_data(self):
        """Clean up any test data created during testing."""
        print("\n==== CLEANING UP TEST DATA ====")
        # Delete all test cameras
        for camera in self.test_cameras:
            self.delete_camera(client=camera["client"], id=camera["id"])
        
        print(f"Removed {len(self.test_cameras)} test cameras.")
        self.test_cameras = []

def main():
    tester = CameraAPITester(BASE_URL)
    
    try:
        # Run all test suites
        tester.run_basic_tests()
        tester.run_advanced_tests()
        tester.run_error_tests()
    except Exception as e:
        print(f"An error occurred during testing: {str(e)}")
    finally:
        # Always try to clean up test data
        tester.cleanup_test_data()
        
    print("\n==== CAMERA API TESTING COMPLETE ====")

if __name__ == "__main__":
    main()