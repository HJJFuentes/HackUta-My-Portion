import cv2
import time
import os
from PIL import Image  # Import PIL for image processing
from pymongo import MongoClient
from datetime import datetime, timezone

#connect to mongodb
client = MongoClient("mongodb+srv://hjf6888:Hugoiscool1!@clusterm0.i0sv8.mongodb.net/?retryWrites=true&w=majority&appName=ClusterM0")

db = client["greenPercentageDB"]
collection = db["greenPercentageCollection"]

# Function to calculate the percentage of green pixels in the image
def percent_green(img_file):
    img = Image.open(img_file)
    pixels = img.load()
    width, height = img.size
    total_green = 0
    for x in range(width):
        for y in range(height):
            rgb = pixels[x, y]
            if rgb[1] > rgb[0] and rgb[1] > rgb[2]:  # If green is the predominant color
                total_green += 1

    percent = total_green / (width * height)
    return percent * 100

countDown = 3
cap = cv2.VideoCapture(0)
saved_images = []
img_counter = 0


while True:
    ret, img = cap.read()
    cv2.imshow('Camera', img)

    # EXIT KEY
    keyToBePressed = cv2.waitKey(1)
    if keyToBePressed == ord('q'):
        break

    if keyToBePressed == ord('s'):
        while True:
            countDown = 3
            prev = time.time()

            while countDown > 0:
                ret, img = cap.read()
                font = cv2.FONT_HERSHEY_COMPLEX
                cv2.putText(img, str(countDown), (200, 250), font, 7, (0, 255, 0), 4, cv2.LINE_AA)
                cv2.imshow('Camera', img)

                # EXIT KEY
                key = cv2.waitKey(125)
                if key == ord('q'):
                    break

                # Check if a second has passed
                cur = time.time()
                if cur - prev >= 1:
                    prev = cur
                    countDown -= 1

            # Exit countdown if 'q' was pressed
            if key == ord('q'):
                break

            # Make sure the text overlay is not displayed in the picture
            ret, img = cap.read()
            cv2.imshow('Camera', img)  # Show the camera frame without any text
            cv2.waitKey(2000)  # Display the image for 2 seconds

            # Save the frame
            img_name = f"GreenPerctPic{img_counter}.png"
            cv2.imwrite(img_name, img)
            print(f"Screenshot {img_counter} taken")

            # Add the new image filename to the list
            saved_images.append(img_name)
            img_counter += 1

            # Calculate the percentage of green pixels in the saved image
            green_percentage = percent_green(img_name)
            print(f"Percentage of green in {img_name}: {green_percentage:.2f}%")

        

            #store the data in mongoDB
            record = { 
                "imageName": img_name,
                "greenPercentage": green_percentage,
                "timeStamp": datetime.now(timezone.utc)
            }

            collection.insert_one(record)
            print(f"data inserted for {img_name}")



            # Check if there are more than 5 images in the list
            if len(saved_images) > 5:
                # Delete the oldest image
                oldest_image = saved_images.pop(0)
                if os.path.exists(oldest_image):
                    os.remove(oldest_image)
                    print(f"Deleted oldest image: {oldest_image}")

        # Exit if 'q' was pressed
        if key == ord('q'):
            break

# Close camera
cap.release()
# Close all the opened windows
cv2.destroyAllWindows()
