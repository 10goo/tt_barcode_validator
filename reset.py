import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(1, GPIO.IN)
GPIO.setup(2, GPIO.OUT)
GPIO.setup(3, GPIO.OUT)
            
def set_relays_to_normal():
    # close relay 2 and
    GPIO.output(2, GPIO.LOW)
    # open relay 3
    GPIO.output(3, GPIO.HIGH)

GPIO.cleanup()
