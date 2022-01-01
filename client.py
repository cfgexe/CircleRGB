import websocket as websockets
import json
from threading import Thread
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor, DeviceType
import os
import subprocess
import time
import atexit

def exit_handler():
    """
    Handle Closing OpenRGB/gosumemory on program closed
    This one is also PC-Only, remove it if you're on another platform, 
    or change it to that platform's equivelant if you'd like
    """
    print("Closing OpenRGB/gosumemory")
    os.system("taskkill /im gosumemory.exe")
    os.system("taskkill /im OpenRGB.exe")

atexit.register(exit_handler)

class appClient:
    def __init__(self):
        ## Remove this line if you are distibuting the app on a non-windows platform
        self.bootup()
        self.client = None
        self.keyboard = None
        self.startOpenRGBClient() # Shit fucking crashes every time, man

        self.currentScoreType = "0"
        print("Keyboard initialized successfully")

        self.scoreMap = {
            "300": 0,
            "100": 0,
            "50": 0,
            "miss": 0
        }

        self.tempScore = {} # Temp Real Score

        ## Define our RGB values for each different hit type
        self.rgbMap = {
            "300": RGBColor(0,0,255),
            "100": RGBColor(0,255,0),
            "50": RGBColor(255,255,0),
            "miss": RGBColor(255,0,0)
        }
    
    def startOpenRGBClient(self):
        x = True
        while x:
            try:
                self.client = OpenRGBClient()
                self.client.clear() # Turns everything off
                self.keyboard = self.client.get_devices_by_type(DeviceType.KEYBOARD)[0]
                x = False
            except:
                pass
            time.sleep(0.5)
    
    def bootup(self):
        ## For Windows Dist Only. Ignore for all other platforms
        os.startfile("gosumemory.exe")
        os.startfile(os.path.join("openRGB", "OpenRGB.exe"))
        subprocess.Popen(["openRGB/openRGB.exe", '--startminimized', '--server'])

    def run(self):
        websocket = websockets.WebSocketApp("ws://localhost:24050/ws",
                                        on_message=self.on_message)
        websocket.run_forever()     
                
    
    def clearKeyboard(self):
        self.keyboard.set_color(RGBColor(0,0,0), True)
    
    def resetStats(self):
        self.scoreMap = {
            "300": 0,
            "100": 0,
            "50": 0,
            "miss": 0
        }
        self.currentScoreType = "0"
        self.clearKeyboard()


    def on_message(self, ws, message):
        try:
            msg = json.loads(message)
            hits = msg["gameplay"]["hits"]
            if self.tempScore == {} and msg["menu"]["state"] == 2:
                self.tempScore = hits
            elif msg["gameplay"]["hits"] != self.tempScore and msg["menu"]["state"] == 2:
                self.tempScore = hits
                Thread(target=self.logicThread).start()
            elif msg["menu"]["state"] == 7:
                self.clearKeyboard()
            elif msg["menu"]["state"] == 0:
                self.tempScore = hits
                self.resetStats()
            if self.tempScore != hits:
                self.tempScore = hits
                self.resetStats()
        except:
            pass

    def itemLogic(self, key, value):
        try:
            temp = ""
            match key:
                case "300":
                    temp = "300"
                case "geki":
                    temp = "300"
                case "100":
                    temp = "100"
                case "katu":
                    temp = "100"
                case "50":
                    temp = "50"
                case "0":
                    temp = "miss"
            if value > self.scoreMap[temp] and temp != self.currentScoreType:
                self.currentScoreType = temp
                self.scoreMap[temp] = value
                self.setLight(temp)
        except:
            pass

    def logicThread(self):
        for item in list(self.tempScore.keys()):
            Thread(target=self.itemLogic, args=(item,self.tempScore[item],)).start()
    
    def setLight(self, hitType):
        rgb = self.rgbMap[hitType]
        print(f"Changing light for hit type {hitType} with rgb {rgb}")
        self.keyboard.set_color(rgb, False)

a = appClient()
a.run()