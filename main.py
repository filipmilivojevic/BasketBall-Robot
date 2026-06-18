#Imports
from XRPLib.board import Board
import time
from machine import Pin, I2C, PWM
from XRPLib.imu import IMU
from ssd1306 import *
import math
from XRPLib.servo import Servo
from XRPLib.differential_drive import DifferentialDrive
from XRPLib.rangefinder import Rangefinder



#Hardware Vars

i2c = I2C(1, sda=Pin(38), scl=Pin(39), freq=400000)
display = SSD1306_I2C(128, 64, i2c)
board = Board.get_default_board()
ext_led = Pin(5, Pin.OUT)
ext_button_pin = Pin(4, Pin.IN, Pin.PULL_UP)
BUZZER_PIN = 15
buzzer = PWM(Pin(BUZZER_PIN, Pin.OUT))
rangefinder = Rangefinder.get_default_rangefinder()
drivetrain = DifferentialDrive.get_default_differential_drive()
imu = IMU.get_default_imu()
interPin = Pin(7, Pin.IN, Pin.PULL_UP)
imu.calibrate(1)



#Global Variables
interTrigger = False
score = 0
global timer
timeSeconds = 30
basket_notes = [1047, 1318, 1568]
high_score_melody = [(523, 0.10, 0.03),(659, 0.10, 0.03),(784, 0.10, 0.03),(1047, 0.20, 0.05),(988, 0.08, 0.02),(1047, 0.08, 0.02),(988, 0.08, 0.02),(1047, 0.35, 0.00)]
userFound = False
gameOver = False
lastTick = time.time()
servo1 = Servo.get_default_servo(1)

#functions
def scanHuman():
    print("Scanning for human torso...")
    userFound = False
    firstYaw = 0
    secondYaw = 0
    targetDistance = 0

    # spin in micro-steps to find the person
    for i in range(180):
        
        distance = rangefinder.distance()

        # detect torso within standard range
        if 20 < distance < 35:
            # get the left edge
            firstYaw = imu.get_yaw()
            
            # keep turning until the sensor clears the right edge
            while rangefinder.distance() < 35:
                drivetrain.turn(2)
                time.sleep(0.05)
                
            # get the right edge
            secondYaw = imu.get_yaw()
            userFound = True
            targetDistance = distance
            break

        # keep searching if nothing is detected
        drivetrain.turn(2)
        time.sleep(0.05)

    # if the human is found, do the positioning
    if userFound:
        print(f"Human targeted at {targetDistance}cm. Aligning...")
        
        # center the robot perfectly onto the torso
        centerYaw = (firstYaw + secondYaw) / 2
        currentYaw = imu.get_yaw()
        turnAmount = centerYaw - currentYaw
        drivetrain.turn(turnAmount)
        time.sleep(0.2)
        
        # drive forward to the person
        # sse max() to make sure we don't pass a negative distance if already too close
        drive_distance = max(0, targetDistance - 10)
        print(f"Driving forward: {drive_distance}cm")
        drivetrain.straight(drive_distance, 0.5)
        time.sleep(0.2)
        
        # turn 90 degrees 
        print("Pivoting 90 degrees for game presentation.")
        drivetrain.turn(90)
        time.sleep(0.2)
        
        # sound cue that it is ready and to stop the function
        playNote(880, 0.1, 0.02)
        playNote(1109, 0.15, 0.02)
        servo1.set_angle(180)
        drivetrain.stop()
        return True
        
    print("No human found in this sweep.")
    return False

def level2():
	while True:
		servo1.set_angle(160)
		time.sleep(0.3)
		servo1.set_angle(155)
		time.sleep(0.2)
		if gameOver == False:
			break
			
def level3():
	while True:
		drivetrain.straight(5, 0.7)
		time.sleep(0.3)
		drivetrain.straight(-5, 0.7)
		time.sleep(0.2)
		
		servo1.set_angle(160)
		time.sleep(0.3)
		servo1.set_angle(155)
		time.sleep(0.2)
		if gameOver == False:
			break

def update_oledDisplay():
    global score
    global lastTick
    global timeSeconds
    display.fill(0)
    display.text("Score: " + str(score), 0, 0)
    display.text(str(timeSeconds), 52, 28,60)                  	
    display.show()
    if time.time() - lastTick >= 1:
        if timeSeconds > 0:
            timeSeconds = timeSeconds - 1
        lastTick = time.time()
	
def handle_interrupt(pin):
	global interTrigger
	interTrigger = True

def playNote(frequency, duration, pause):
    global buzzer
    buzzer.duty_u16(5000)
    buzzer.freq(frequency)
    time.sleep(duration)
    buzzer.duty_u16(0)
    time.sleep(pause)

def checkForLevel():
	if score >= 3 and score < 6:
		level2()
	elif score >= 6:
		level3()
	elif score > 3:
		pass

def scoredPoint():
    global score
    if ext_button_pin.value() == 0:
        time.sleep(1)
        score = score + 1
        board.set_rgb_led(0,255,0)
        for note in basket_notes:
		    playNote(note, 0.08, 0.02)


def finishGame():
    global timeSeconds
    global gameOver
    if timeSeconds == 0:
        gameOver = True
        board.set_rgb_led(255,0,0)
        for freq, dur, pause in high_score_melody:
            playNote(freq, dur, pause)  



interPin.irq(trigger=Pin.IRQ_FALLING, handler=handle_interrupt)


# Main

while not gameOver:
    update_oledDisplay()
    if interTrigger:
        score = score + 1
        interTrigger = False
        board.set_rgb_led(0,255,0)
        for note in basket_notes:
            playNote(note, 0.08, 0.02)
		
    scoredPoint()
    checkForLevel()
    finishGame()
    board.set_rgb_led(0,0,0)
    time.sleep(0.01)
 
