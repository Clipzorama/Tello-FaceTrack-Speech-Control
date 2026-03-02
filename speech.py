import cv2  
import time 
import speech_recognition as sr  
from djitellopy import tello  
import keypress as kp  
import vosk
import json
import os  


chrision_drone = tello.Tello()

chrision_drone.connect()

print(chrision_drone.get_battery())

kp.init()


r = sr.Recognizer()


model_dir = os.path.join(os.path.dirname(os.path.realpath(
    __file__)), "vosk_models", "vosk-model-small-en-us-0.15")
vosk_model = vosk.Model(model_dir)


def recognize_audio(audio_data):
    recognizer = vosk.KaldiRecognizer(vosk_model, 16000)
    recognizer.AcceptWaveform(audio_data)
    result = json.loads(recognizer.Result())
    recognized_text = result.get("text", "")
    return recognized_text


max_retries = 3  
retry_delay = 0.5  
failed_attempts = 0


def getKeyboardInput():
    lr, fb, ud, yv = 0, 0, 0, 0
    speed = 50
    takeoff_value = 40

    if kp.getKey("LEFT"):
        lr = -speed
    elif kp.getKey("RIGHT"):
        lr = speed

    if kp.getKey("UP"):
        fb = speed
    elif kp.getKey("DOWN"):
        fb = -speed

    if kp.getKey("w"):
        ud = speed
    elif kp.getKey("s"):
        ud = -speed

    if kp.getKey("a"):
        yv = -speed
    elif kp.getKey("d"):
        yv = speed

    if kp.getKey("e"):
        chrision_drone.takeoff()

    if kp.getKey("q"):
        chrision_drone.land()

    return [lr, fb, ud, yv]


speech_recognition_successful = False


for _ in range(max_retries):
    try:
        with sr.Microphone() as source:
            print("Speak to the computer what commands you want your Tello drone to do")

            while True:
                audio_data = r.listen(source, timeout=None)
                audio_bytes = audio_data.get_raw_data(
                    convert_rate=16000, convert_width=2)
                recognized_speech = recognize_audio(audio_bytes)

                print("Recognized Speech:", recognized_speech)

                if recognized_speech:
                    if "battery level" in recognized_speech:
                        print(chrision_drone.get_battery())

                    if "take off" in recognized_speech:
                        chrision_drone.takeoff()

                    if "land" in recognized_speech:
                        chrision_drone.land()

                    if "capture" in recognized_speech:

                        chrision_drone.streamon()

                        while True:

                            audio_data = r.listen(source, timeout=None)
                            audio_bytes = audio_data.get_raw_data(
                                convert_rate=16000, convert_width=2)
                            recognized_speech = recognize_audio(audio_bytes)

                            img = chrision_drone.get_frame_read().frame

                            img = cv2.resize(img, (360, 240))

                            cv2.imshow("Image", img)
                            cv2.waitKey(1)

                            if "stop capture" in recognized_speech:
                                chrision_drone.streamoff()
                                break

                    if "control" in recognized_speech:
                        directional = getKeyboardInput()

                        while True:
                            chrision_drone.send_rc_control(
                                directional[0], directional[1], directional[2], directional[3])

                            audio_data = r.listen(source, timeout=None)
                            audio_bytes = audio_data.get_raw_data(
                                convert_rate=16000, convert_width=2)
                            recognized_speech = recognize_audio(audio_bytes)

                            if "stop control" in recognized_speech:
                                chrision_drone.send_rc_control(0, 0, 30, 0)
                                break

                    failed_attempts = 0

                speech_recognition_successful = True
                break

    except sr.RequestError:
        failed_attempts += 1
        time.sleep(retry_delay)
else:
    print("Speech recognition request failed after multiple attempts.")

cv2.destroyAllWindows()  
