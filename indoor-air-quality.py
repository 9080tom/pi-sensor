#!/usr/bin/env python
import bme680
import time
import requests

import firebase_admin
from firebase_admin import credentials, firestore, storage, db
cred = credentials.Certificate("/home/pi/Desktop/camera-service/key.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://safespace-1bdad.firebaseio.com"})
user_id = "w9X3C5bnoXPHd4dcplSAnVwsYNs1"
print("""Estimate indoor air quality

Runs the sensor for a burn-in period, then uses a
combination of relative humidity and gas resistance
to estimate indoor air quality as a percentage.

Press Ctrl+C to exit

""")

try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except IOError:
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# These oversampling settings can be tweaked to
# change the balance between accuracy and noise in
# the data.

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# start_time and curr_time ensure that the
# burn_in_time (in seconds) is kept track of.

start_time = time.time()
curr_time = time.time()

burn_in_time = 300
reading_interval = 60

burn_in_data = []
prev_aqs_reading = 100
aqs_drop_threshold = 20

try:
    # Collect gas resistance burn-in values, then use the average
    # of the last 50 values to set the upper limit for calculating
    # gas_baseline.
    print('Collecting gas resistance burn-in data for 5 mins\n')
    while curr_time - start_time < burn_in_time:
        curr_time = time.time()
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            burn_in_data.append(gas)
            print('Gas: {0} Ohms'.format(gas))
            time.sleep(1)

    gas_baseline = sum(burn_in_data[-50:]) / 50.0

    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0

    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25

    print('Gas baseline: {0} Ohms, humidity baseline: {1:.2f} %RH\n'.format(
        gas_baseline,
        hum_baseline))

    while True:
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            gas_offset = gas_baseline - gas

            hum = sensor.data.humidity
            hum_offset = hum - hum_baseline
            temp = sensor.data.temperature
            pres = sensor.data.pressure

            # Calculate hum_score as the distance from the hum_baseline.
            if hum_offset > 0:
                hum_score = (100 - hum_baseline - hum_offset)
                hum_score /= (100 - hum_baseline)
                hum_score *= (hum_weighting * 100)

            else:
                hum_score = (hum_baseline + hum_offset)
                hum_score /= hum_baseline
                hum_score *= (hum_weighting * 100)

            # Calculate gas_score as the distance from the gas_baseline.
            if gas_offset > 0:
                gas_score = (gas / gas_baseline)
                gas_score *= (100 - (hum_weighting * 100))

            else:
                gas_score = 100 - (hum_weighting * 100)

            # Calculate air_quality_score.
            air_quality_score = hum_score + gas_score
            
            # push notification if low air quality
            if prev_aqs_reading - air_quality_score > aqs_drop_threshold:
                print "sending notification"
                push_tokens = db.reference("users/w9X3C5bnoXPHd4dcplSAnVwsYNs1/pushTokens").get().values()
    
                for token in push_tokens:
                    requests.post(url = "https://exp.host/--/api/v2/push/send", data = {"to":token.encode('ascii','ignore') , "title": "Air Quality Alert", "body": "Air quality is now {0:.2f}%".format(air_quality_score)})

            print('Temperature: {0:.2f} Air Pressure: {1:.2f} Degrees Gas: {2:.2f} Ohms,humidity: {3:.2f} %RH,air quality: {4:.2f}'.format(
                temp,
                pres,
                gas,
                hum,
                air_quality_score))
            ref = db.reference("users/{}/sensordata".format(user_id))
            ref.push({"temp": temp, "gas": gas, "hum": hum, "pres": pres, "aqs": air_quality_score, "time": time.time()})

            prev_aqs_reading = air_quality_score
            time.sleep(reading_interval)

except KeyboardInterrupt:
    pass
