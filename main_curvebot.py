from curve_bot import Bot, Sensor, CircleSensor, LineSensor, ArcSensor, LEFT, RIGHT


 # C:\Program Files\Google\Chrome\Application>chrome.exe --remote-debugging-port=9222

# board_position = {"top": 143, "left": 945, "width": 1210, "height": 1210} # 1-pixel border for Camp fullsize
board_position = {"top": 144, "left": 946, "width": 1208, "height": 1208} # 0-pixel border for Camp fullsize

# sensor = CircleSensor(direction=0, distance=75, radius=30)
# sensor = CircleSensor(direction=0, distance=100, radius=50)
sensor = LineSensor(direction=-0.5, distance=68, length=60, width=18)
# sensor = LineSensor(direction=0, distance=138, length=120, width=18)

# sensor = LineSensor(direction=0, distance=90, length=100, width=25)


# sensor = ArcSensor(start_angle=-0.5, stop_angle=0.5, distance=60, radius=50)
bot = Bot(sensor, left_key='a', right_key='z', board_position=None)

bot.run(framerate=120)