from smbus2 import SMBus, i2c_msg
import time

# i2c address of the sensor
ADDRESS = 0x40 

def read_temp_hum():
    with SMBus(1) as bus:
        # Send trigger read command
        write = i2c_msg.write(ADDRESS, [0x00])
        bus.i2c_rdwr(write)
        time.sleep(0.05)

        # Read 4 bytes: temp(2) + hum(2)
        read = i2c_msg.read(ADDRESS, 4)
        bus.i2c_rdwr(read)

        data = list(read)
        raw_temp = (data[0] << 8) | data[1]
        raw_hum = (data[2] << 8) | data[3]

        temp_c = raw_temp * 165.0 / 65535.0 - 40.0
        hum_rh = raw_hum * 100.0 / 65535.0

        return temp_c, hum_rh


if __name__ == "__main__":
    while True:
        try:
            t, h = read_temp_hum()
            print(f"Temperature: {t:.2f} °C  |  Humidity: {h:.2f} %RH")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)
