from adafruit_ads1x15 import ads1115 as adc
import board
import busio
from adafruit_ads1x15.analog_in import AnalogIn as ai
i2c = busio.I2C(board.SCL, board.SDA)

adc1 = adc.ADS1115(i2c)

def main():

    channel = ai(adc1, adc.P0)
    print(channel.value)
    #if adafruit_ads1x15.single_ended.ADS1x15_SingleEnded.read_adc(channel) < 150:
#         print("button is pushed")
#     else:
#         print("button is not pushed")

if __name__ == "__main__":
    main()



