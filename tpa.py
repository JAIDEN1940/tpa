import pytesseract
import pyautogui
import time
import random
import keyboard
import cv2
import numpy as np
from PIL import Image, ImageGrab
import threading
import tkinter as tk  # Import Tkinter for GUI

# Set the path for Tesseract if it's not set globally
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Paths to the font images for font identification
FONT_IMAGE_PATH_1 = 
FONT_IMAGE_PATH_2 = 

# Load the font images for template matching
font_image_1 = cv2.imread(FONT_IMAGE_PATH_1, cv2.IMREAD_GRAYSCALE)
font_image_2 = cv2.imread(FONT_IMAGE_PATH_2, cv2.IMREAD_GRAYSCALE)

if font_image_1 is None or font_image_2 is None:
    print("Error: One or both font images not found or cannot be loaded.")
else:
    print("Both font images loaded successfully.")

# Custom bounding box (for example, the center of the screen)
screen_width, screen_height = 1920, 1080  # Example screen resolution
bbox_center = (screen_width // 4, screen_height // 4, 3 * screen_width // 4, 3 * screen_height // 4)

def capture_screen(bbox=None):
    """Capture a screenshot of the specified area (bbox) or the full screen."""
    try:
        img = ImageGrab.grab(bbox)  # Capture the screenshot
        img_np = np.array(img)
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)  # Convert to OpenCV format
        return img_np
    except Exception as e:
        print(f"Error capturing screen: {e}")
        return None

def preprocess_image(image):
    """Preprocess the image for faster OCR."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def extract_text_from_image(image):
    """Use OCR to extract text from the image."""
    try:
        processed_img = preprocess_image(image)  # Preprocess image for faster OCR
        if processed_img is None:
            print("Error: Image preprocessing failed.")
            return ""
        text = pytesseract.image_to_string(processed_img)
        return text
    except Exception as e:
        print(f"Error extracting text with Tesseract: {e}")
        return ""

def find_player_name_in_text(text):
    """Find the player name from the OCR text, only if '' is next to it."""
    lines = text.split('\n')
    for line in lines:
        if '' in line:  # Look for the word "" next to the player name
            words = line.split()
            if len(words) > 1 and '' in words:
                player_name = words[words.index('feels') - 1]  # The word before "" should be the player name
                return player_name
    return None

def send_tpa_request(player_name):
    """Send the /tpa request in the game using pyautogui."""
    try:
        pyautogui.press('t')  # Open the chat by pressing 't'
        time.sleep(0.3)  # Wait for the chat window to open
        player_name = player_name[:3]  # Take the first 3 letters of the player's name
        pyautogui.write(f'/tpa {player_name}')  # Type /tpa <first 3 letters of player_name>
        pyautogui.press('enter')  # Press Enter to send the message
    except Exception as e:
        print(f"Error sending /tpa request: {e}")

def find_font_match(image):
    """Find if any of the font images match any part of the captured image using template matching."""
    try:
        result_1 = cv2.matchTemplate(image, font_image_1, cv2.TM_CCOEFF_NORMED)
        result_2 = cv2.matchTemplate(image, font_image_2, cv2.TM_CCOEFF_NORMED)
        
        threshold = 0.8  # Adjust this threshold depending on how accurate the font recognition should be
        
        locations_1 = np.where(result_1 >= threshold)
        locations_2 = np.where(result_2 >= threshold)
        
        if len(locations_1[0]) > 0 or len(locations_2[0]) > 0:
            return True
        return False
    except Exception as e:
        print(f"Error performing template matching: {e}")
        return False

# Tkinter GUI to display OCR text
def create_gui():
    """Create a simple Tkinter window to display the OCR text."""
    window = tk.Tk()
    window.title("Captured Text")

    # Create a Text widget to display OCR output
    text_widget = tk.Text(window, height=20, width=80)
    text_widget.pack()

    return window, text_widget

def update_text_widget(text_widget, text):
    """Update the text widget with the captured OCR text."""
    text_widget.delete(1.0, tk.END)  # Clear existing text
    text_widget.insert(tk.END, text)  # Insert new OCR text

def log_text(text):
    """Log the captured text to a file."""
    try:
        with open('captured_text_log.txt', 'a') as log_file:
            log_file.write(f"{text}\n")  # Append text with a new line
    except Exception as e:
        print(f"Error logging text: {e}")

def capture_and_process_screen(text_widget):
    """Capture screen and process the text using OCR."""
    last_position_time = time.time()  # Track the last time "position:" was seen
    while True:
        try:
            # Capture the chat area
            screenshot = capture_screen(bbox=(0, 0, 960, 540))  # Capture the chat box region
            if screenshot is None:
                continue  # Skip if there's an issue with the capture

            # Extract text from the captured screenshot
            text = extract_text_from_image(screenshot)
            if not text:
                continue  # Skip if no text extracted

            # Print the captured text to the console
            print("Captured Text: ", text)

            # Log the captured text to a local file
            log_text(text)

            # Update the text widget with the captured text
            update_text_widget(text_widget, text)

            # Check if the word "spam" is in the text
            if 'spam' in text.lower():  # Case insensitive check
                pyautogui.write('/kill')  # Type the "/kill" command directly
                pyautogui.press('enter')  # Press Enter to send the message
                print("Detected 'spam'. Sent '/kill' command.")  # Debugging message

            # Check if the word "position:" is in the text
            if 'position:' in text.lower():  # Case insensitive check
                last_position_time = time.time()  # Reset the timer if "position:" is detected
                print("Detected 'position:'. Resetting timer.")  # Debugging message

            # Check if more than 3 seconds have passed since "position:" was last seen
            if time.time() - last_position_time > 3:  # Changed from 5 to 3 seconds
                pyautogui.press('enter')  # Press Enter if "position:" was not detected for more than 3 seconds
                print("No 'position:' detected for 3 seconds. Pressed Enter.")  # Debugging message

            # Try to find a player's name in the text
            player_name = find_player_name_in_text(text)
            if player_name:
                # Unconditionally send two TPA requests to the player
                send_tpa_request(player_name)
                time.sleep(random.uniform(0.5, 2))  # Random delay between requests
                send_tpa_request(player_name)

            time.sleep(0.5)  # Short sleep time for faster capture
        except Exception as e:
            print(f"Error in capture and processing loop: {e}")
            time.sleep(1)  # Sleep to prevent a tight loop in case of errors

def toggle_script():
    """Start/stop the OCR capture loop based on keypress."""
    print("Press 'Q' to start/stop the script.")
    while True:
        if keyboard.is_pressed('q'):  # If 'Q' is pressed
            # Create GUI
            window, text_widget = create_gui()
            threading.Thread(target=capture_and_process_screen, args=(text_widget,)).start()  # Start capture loop
            window.mainloop()  # Start GUI event loop
            break  # Exit the loop once the script is started
        time.sleep(0.1)

if __name__ == "__main__":
    # Start the monitoring of keypresses for the main script
    toggle_script()

