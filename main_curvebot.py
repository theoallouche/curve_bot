from curve_bot import Bot, Sensor, CircleSensor, LineSensor, ArcSensor, LEFT, RIGHT


 # "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# sensor = CircleSensor(direction=0, distance=75, radius=30)
# sensor = CircleSensor(direction=0, distance=100, radius=50)
sensor = LineSensor(direction=-0.5, distance=68, length=60, width=18)
# sensor = LineSensor(direction=0, distance=138, length=120, width=18)
# sensor = LineSensor(direction=0, distance=90, length=100, width=25)
# sensor = ArcSensor(start_angle=-0.5, stop_angle=0.5, distance=60, radius=50)

bot = Bot(sensor, left_key='a', right_key='z')
bot.run(framerate=120)