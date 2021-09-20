import Adafruit_ADS1x15 as adc
#are you working b
def main():

    channel = 0

    if adc.read_adc(channel) < 150:
        print("button is pushed")
    else:
        print("button is not pushed")

if __name__ == "__main__":
    main()



