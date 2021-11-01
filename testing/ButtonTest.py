from adafruit_ads1x15 import ads1115 as adc
import board
import busio
from adafruit_ads1x15.analog_in import AnalogIn as ai
import qwiic_relay as qr
import time
i2c = busio.I2C(board.SCL, board.SDA)

adc1 = adc.ADS1115(i2c)

relay = qr.QwiicRelay(0x18)

def main():

    channel = ai(adc1, adc.P0)
    print(channel.value)
    if channel.value < 150:
        print("button is not pushed")
    else:
        print("button is pushed")

    time.sleep(7)
    relay.set_relay_off()
    time.sleep(4)
    relay.set_relay_on()

if __name__ == "__main__":
    main()



