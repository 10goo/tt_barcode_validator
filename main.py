#!/home/pi/tt_barcode_validator/venv/bin/python
import requests
import RPi.GPIO as GPIO
import os
from datetime import datetime
import time
from csv import reader
from evdev import *
from timeout import timeout, TimeoutError

dirname = os.path.dirname(__file__)
ean_csv_file_path = os.path.join(dirname, 'ean_list.csv')
validated_products_csv_path = os.path.join(dirname, 'validated_products.csv')

# Send api request to insert new validated barcodes
def api_insert(ean=0, code_39=0):
    url = 'http://192.168.2.13:8080/v1/graphql'
    query = """mutation insert_barcode{{
      insert_barcodes(
        objects: [
          {{
            ean: {}, 
            code_39: {}
          }}
    ]
    ) {{
        returning {{
          id,
          ean,
          code_39,
          created_at
    }}
    }}
    }}""".format(ean, code_39)
    print(query)
    r = requests.post(url, json={'query': query})
    print(r.text)

@timeout(3)
def read_barcode():
    dev = InputDevice('/dev/input/event0')
    x = ''

    scancodes = {2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
        10: u'9', 11: u'0'}

    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            data = categorize(event)
            # Filter out only down events
            if data.keystate == 1:
                key_lookup = u'{}'.format(scancodes.get(data.scancode)) or u'UNKNOWN:[{}]'.format(data.scancode)
                if (data.scancode == 28):
                    return(x)
                else:
                    x += key_lookup

def list_from_csv(path, col_nr):
    # returns a list of integers from the nth column (starting from 0) of a csv file
    with open(path, 'r') as csv_file:
        csv_reader = reader(csv_file)
        return [int(x[col_nr]) for x in csv_reader]

# load list of valid ean labels
ean_numbers = list_from_csv(ean_csv_file_path, 0)


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

def read_barcodes(a=0):
    print('trying to read code')
    try:
        read_ean_13 = read_barcode()
        print(read_ean_13)
        if not validate_ean13(read_ean_13):
            raise(TimeoutError)
    except TimeoutError:
        set_relays_to_error()
        return False
    try:
        read_code_39 = read_barcode()
        print(read_code_39)
        if not validate_code39(read_code_39):
            raise(TimeoutError)
    except TimeoutError:
        set_relays_to_error()
        return False
    # If correct reading does happen in 2 seconds
    if validate_ean13: # and validate_code_39:
        print('Success')
        # write barcodes and timestamp to file
        write_to_file(read_code_39, read_ean_13)
        # Send request to API
        api_insert(read_ean_13, read_code_39)    
   
    
def write_to_file(code_39=0, ean_13=0):
    timestamp = datetime.now(tz=None)
    new_line = '{},{},{}'.format(timestamp, code_39, ean_13)
    with open(validated_products_csv_path, 'a+') as fi:
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
            read_barcodes()
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
