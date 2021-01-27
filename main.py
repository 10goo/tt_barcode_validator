import RPi.GPIO as GPIO
from datetime import datetime
import time
from csv import reader
from inputimeout import inputimeout, TimeoutOccurred

def list_from_csv(path, col_nr):
    # returns a list of integers from the nth column (starting from 0) of a csv file
    with open(path, 'r') as csv_file:
        csv_reader = reader(csv_file)
        return [int(x[col_nr]) for x in csv_reader]

# load list of valid ean labels
ean_numbers = list_from_csv('ean_list.csv', 0)


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(2, GPIO.OUT)
    GPIO.setup(3, GPIO.OUT)
    # close relay 2 and
    GPIO.output(2, GPIO.HIGH)
    # open relay 3
    GPIO.output(3, GPIO.HIGH)

def set_relays_to_error():
    print("Setting relays to error")
    # close relay 2 and
    GPIO.output(2, GPIO.LOW)
    # open relay 3
    GPIO.output(3, GPIO.LOW)
            
def set_relays_to_normal():
    # close relay 2 and
    GPIO.output(2, GPIO.HIGH)
    # open relay 3
    GPIO.output(3, GPIO.HIGH)

def validate_code39(code):
    if (int(code) > 72000000) and (int(code) < 73000000):
        return True
    else:
        return False
    
def validate_ean13(code):
    if int(code) in ean_numbers:
        return True
    else:
        return False

def read_barcode(a=0):
    print('trying to read code')
    try:
        read_ean_13 = inputimeout(prompt='Reading EAN13 barcode', timeout=3)
        if not validate_ean13(read_ean_13):
            raise(TimeoutOccurred)
    except TimeoutOccurred:
        set_relays_to_error()
        return False
    try:
        read_code_39 = inputimeout(prompt='Reading CODE39 barcode', timeout=3)
        if not validate_code39(read_code_39):
            raise(TimeoutOccurred)
    except TimeoutOccurred:
        set_relays_to_error()
        return False
    # If correct reading does happen in 2 seconds
    print('Success')
    # write barcodes and timestamp to file
    write_to_file(read_code_39, read_ean_13)
   
    
def write_to_file(code_39, ean_13):
    timestamp = datetime.now(tz=None)
    new_line = '{},{},{}'.format(timestamp, code_39, ean_13)
    with open('barcode_log', 'a+') as fi:
        # Move read cursor to the start of the file
        fi.seek(0)
        # If file is not empty then append '\n'
        data = fi.read(100)
        if len(data) > 0:
            fi.write('\n')
            # Append new line to end
        fi.write(new_line)
        
def loop():
    while True:        
        # Wait for sensor trigger
        #GPIO.add_event_detect(1, GPIO.RISING)
        if GPIO.input(1) == 0:
            print("triggered")
            read_barcode()
        if GPIO.input(24) == 1:
            print('RESET')
            set_relays_to_normal()
        time.sleep(0.2)
        #GPIO.add_event_callback(1, test_trigger)
    


if __name__ == '__main__':
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        print("Interrupted")
        GPIO.cleanup()