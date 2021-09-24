from adafruit_ads1x15 import ads1115 as adc
import board
import busio
from adafruit_ads1x15.analog_in import AnalogIn as ai
i2c = busio.I2C(board.SCL, board.SDA)

adc1 = adc.ADS1115(i2c)

def main():

    channel = ai(adc1, adc.P0)
    print(channel.value)
    if channel.value < 150:
        print("button is not pushed")
    else:
        print("button is pushed")

    relay = QwiicRelay(0x18)
    relay.set_relay_off()


if __name__ == "__main__":
    main()



