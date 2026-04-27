import cv2
import numpy as np
from scipy.io import wavfile
import pygame
import time
import threading
import json
import os

# --- FILE SELECTION SYSTEM ---
def select_file():
    # Supported image extensions
    extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    current_folder = os.path.dirname(os.path.abspath(__file__))
    
    # List files in folder
    files = [f for f in os.listdir(current_folder) if f.lower().endswith(extensions)]
    
    if not files:
        print("Error: No images found in script folder.")
        exit()
        
    print("\n--- AVAILABLE DISCS IN FOLDER ---")
    for i, name in enumerate(files):
        print(f"[{i}] {name}")
    
    while True:
        try:
            choice = int(input("\nChoose the file number to load: "))
            if 0 <= choice < len(files):
                return files[choice]
            else:
                print("Invalid number. Try again.")
        except ValueError:
            print("Please enter only numbers.")

# --- DYNAMIC INITIALIZATION ---
IMAGE_NAME = select_file()
# JSON will always have the same name as the selected image
CONFIG_FILE = os.path.splitext(IMAGE_NAME)[0] + ".json"

# --- GLOBAL PARAMETERS ---
ROTATION_DURATION = 30 
FS = 22050        
# A Major scale as per the provided photo
MIDI_SCALE = [45, 47, 50, 52, 57, 59, 61, 62, 64, 66, 68, 69, 71, 73, 74, 75, 76, 78, 79, 80, 81, 83, 85, 86]
K_SIZE = 10 

outer_points = [[500, 150], [500, 850], [850, 500], [150, 500]] 
inner_points = [[500, 350], [500, 700], [700, 500], [300, 500]]
selected_point = None
exclusion_mask = None
config = {"sens": 105, "ang_off": 180, "min_dur": 0.1, "playing": False}

def load_config():
    global outer_points, inner_points
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            outer_points = data.get("outer_points", outer_points)
            inner_points = data.get("inner_points", inner_points)
            print(f"Configuration loaded for {IMAGE_NAME}!")

def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"outer_points": outer_points, "inner_points": inner_points}, f, indent=4)
    print(f"Configuration saved to {CONFIG_FILE}")

def mouse_handler(event, x, y, flags, param):
    global selected_point, exclusion_mask
    if event == cv2.EVENT_LBUTTONDOWN:
        for i, p in enumerate(outer_points):
            if np.hypot(x - p[0], y - p[1]) < 25: selected_point = [outer_points, i]; return
        for i, p in enumerate(inner_points):
            if np.hypot(x - p[0], y - p[1]) < 25: selected_point = [inner_points, i]; return
    elif event == cv2.EVENT_MOUSEMOVE and selected_point:
        selected_point[0][selected_point[1]] = [x, y]
    elif event == cv2.EVENT_LBUTTONUP:
        selected_point = None
    if flags & cv2.EVENT_FLAG_RBUTTON:
        cv2.circle(exclusion_mask, (x, y), 20, 255, -1)

def play_audio_synchronized(file, cx, cy, ro, img_base):
    config["playing"] = True
    pygame.mixer.init(frequency=FS)
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()
    t0 = time.time()
    cv2.namedWindow("Player", cv2.WINDOW_NORMAL)
    while pygame.mixer.music.get_busy():
        dt = time.time() - t0
        if dt > ROTATION_DURATION: break
        p_disp = img_base.copy()
        rad = np.radians(config["ang_off"] - (dt/ROTATION_DURATION * 360))
        px, py = int(cx + ro * np.cos(rad)), int(cy + ro * np.sin(rad))
        cv2.line(p_disp, (int(cx), int(cy)), (px, py), (0,0,255), 3)
        cv2.circle(p_disp, (px, py), 10, (0,0,255), -1)
        cv2.imshow("Player", p_disp)
        if cv2.waitKey(30) == 27: break
    pygame.mixer.quit()
    cv2.destroyWindow("Player")
    config["playing"] = False

def main():
    global exclusion_mask
    load_config()
    img = cv2.imread(IMAGE_NAME)
    h_orig, w_orig = img.shape[:2]
    exclusion_mask = np.zeros((h_orig, w_orig), dtype=np.uint8)
    
    cv2.namedWindow("Ariston Workstation", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Ariston Workstation", mouse_handler)

    while True:
        if not config["playing"]:
            display = img.copy()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blurred, config["sens"], 255, cv2.THRESH_BINARY_INV)
            thresh = cv2.subtract(thresh, exclusion_mask)
            
            valid_notes = []
            offset_k = K_SIZE // 2

            for i in range(24):
                p_ext, p_int = i / 23.0, 1.0 - i / 23.0
                n = np.array(inner_points[0]) * p_int + np.array(outer_points[0]) * p_ext
                s = np.array(inner_points[1]) * p_int + np.array(outer_points[1]) * p_ext
                l = np.array(inner_points[2]) * p_int + np.array(outer_points[2]) * p_ext
                o = np.array(inner_points[3]) * p_int + np.array(outer_points[3]) * p_ext
                cx, cy = (l[0]+o[0])/2, (n[1]+s[1])/2
                rx, ry = abs(l[0]-o[0])/2, abs(n[1]-s[1])/2
                
                cv2.ellipse(display, (int(cx), int(cy)), (int(rx), int(ry)), 0, 0, 360, (255, 120, 0), 1)

                in_hole, start_p = False, 0
                for a in range(0, 3600, 4):
                    rad = np.radians(config["ang_off"] - (a / 10.0))
                    px, py = int(cx + rx * np.cos(rad)), int(cy + ry * np.sin(rad))
                    if offset_k <= px < w_orig - offset_k and offset_k <= py < h_orig - offset_k:
                        sample = thresh[py-offset_k:py+offset_k, px-offset_k:px+offset_k]
                        if np.mean(sample) > 115: 
                            cv2.circle(display, (px, py), 1, (0, 255, 0), -1)
                            if not in_hole: in_hole, start_p = True, a
                        elif in_hole:
                            in_hole, dur = False, a - start_p
                            if dur > config["min_dur"]:
                                valid_notes.append({'note': MIDI_SCALE[i], 'start': start_p/3600.0, 'dur': dur/3600.0})

            for p in outer_points: cv2.circle(display, tuple(p), 10, (0, 255, 0), -1)
            for p in inner_points: cv2.circle(display, tuple(p), 10, (255, 255, 0), -1)
            
            display[exclusion_mask > 0] = display[exclusion_mask > 0] * 0.5 + np.array([0,0,100], dtype=np.uint8)
            cv2.putText(display, f"File: {IMAGE_NAME} | ENTER: Play | Right-click: Add Exclusion", (15, 40), 1, 1.4, (0,255,255), 2)
            cv2.imshow("Ariston Workstation", display)
            
            key = cv2.waitKey(20) & 0xFF
            if key == 13: # ENTER
                save_config()
                audio = np.zeros(int(FS * (ROTATION_DURATION + 1)))
                for n in valid_notes:
                    freq = 440.0 * (2.0 ** ((n['note'] - 69) / 12.0))
                    t = np.arange(int(n['dur'] * ROTATION_DURATION * FS)) / FS
                    wave = (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(4 * np.pi * freq * t)) * 0.2 * np.sin(np.pi * np.arange(len(t))/len(t))
                    start = int(n['start'] * ROTATION_DURATION * FS)
                    if start + len(wave) < len(audio): audio[start:start+len(wave)] += wave
                wavfile.write("ariston_loop.wav", FS, (audio/np.max(np.abs(audio)+1e-6)*32767).astype(np.int16))
                c_x, c_y = (outer_points[2][0]+outer_points[3][0])/2, (outer_points[0][1]+outer_points[1][1])/2
                threading.Thread(target=play_audio_synchronized, args=("ariston_loop.wav", c_x, c_y, abs(outer_points[2][0]-outer_points[3][0])/2, display)).start()
            elif key == 27: break
            elif key == ord('z'): config["ang_off"] -= 1
            elif key == ord('x'): config["ang_off"] += 1
            elif key == ord('='): config["sens"] += 2
            elif key == ord('-'): config["sens"] -= 2

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()