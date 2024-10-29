import cv2
import time
import base64
import requests
from pymongo import MongoClient
from datetime import datetime, timezone

# Roboflow API configuration
API_KEY = "g9kJSyGxktaT5q60WScF"
URL = "https://detect.roboflow.com"
MODEL_OBJECT_DETECTION = "fruit-m35fp"
MODEL_OBJECT_DETECTION_VERSION = 1
#MONGO_PASSWORD="Hugoiscool1!"

#url = f"{URL}/{MODEL_OBJECT_DETECTION}/{MODEL_OBJECT_DETECTION_VERSION}?api_key={API_KEY}"


client = MongoClient("mongodb+srv://hjf6888:Hugoiscool1@fruitdetection.e1nd5.mongodb.net/?retryWrites=true&w=majority&appName=FruitDetection")

#ObjectDetectionDB
db = client["ObjectDetectionDB"]
collection = db["ObjectElementsCollection"]
#ObjectElementsCollection

# Function to get predictions from the Roboflow API
def roboflow(image):
    # Convert the image to bytes
    _, img_encoded = cv2.imencode('.jpg', image)
    img_bytes = img_encoded.tobytes()

    # Encode the image bytes to Base64
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # Construct the URL for the request
    url = f"{URL}/{MODEL_OBJECT_DETECTION}/{MODEL_OBJECT_DETECTION_VERSION}?api_key={API_KEY}"

    try:
        # Send POST request to the API
        response = requests.post(url, data=img_base64, headers={"Content-Type": "application/x-www-form-urlencoded"})
        
        # Check if the request was successful
        response.raise_for_status()  # Raises an error for bad responses (4xx or 5xx)
        
        # Return the JSON response
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Open the default camera
cam = cv2.VideoCapture(0)

frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

while True:
    ret, frame = cam.read()

    if not ret:
        print("Failed to grab frame")
        break

    # Get predictions from the Roboflow API
    response = roboflow(frame)
    predictions = response.get("predictions", [])

    # Draw bounding boxes and prepare MongoDB data
    for prediction in predictions:
        if prediction['confidence'] > 0.80:  # Adjust threshold as necessary
            # Get coordinates for the bounding box
            x1 = int(prediction['x'] - prediction['width'] / 2)
            y1 = int(prediction['y'] - prediction['height'] / 2)
            x2 = int(prediction['x'] + prediction['width'] / 2)
            y2 = int(prediction['y'] + prediction['height'] / 2)

            # Ensure coordinates are within image bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame_width, x2)
            y2 = min(frame_height, y2)

            # Draw the bounding box on the frame
            thickness = 2
            color = (0, 255, 0)
            frame = cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

            # Prepare combined data for MongoDB
            current_time = time.time()
            DataFromCamera = {
                "Time": current_time,
                "DateTime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time)),
                "Class": prediction['class'],  
                "Confidence": prediction['confidence'],
                "Bounding Box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "Object Width": prediction['width'],
                "Object Height": prediction['height'],
                "Location": {"lat": 32.733372, "lon": -97.106638}
            }

            # Insert data into MongoDB
            collection.insert_one(DataFromCamera)
            print("Data inserted into MongoDB:", DataFromCamera)

            # Print the prediction details
            print(f"Class: {prediction['class']}, Confidence: {prediction['confidence']}")

    # Display the frame with bounding boxes
    cv2.imshow('Camera with Bounding Boxes', frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) == ord('q'):
        break

# Release the camera and destroy windows
cam.release()
cv2.destroyAllWindows()
