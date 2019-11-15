#!/usr/bin/python
# coding=utf-8
from __future__ import division, print_function
from webthing import (Action, Event, MultipleThings, Property, Thing, Value,
                      WebThingServer)
import logging
import random
import time
import tornado.ioloop
import uuid
import os, sys

device_id_list = []
things_list = []

class TemperatureSensors(Thing):
    """A Temperature sensor which updates its measurement every few seconds."""

    def __init__(self, device, number):
        Thing.__init__(
            self,
            'urn:dev:ops:'+str(device),
            'Temperature Sensor '+str(number),
            ['TemperatureSensor'],
            'a web connected temperature sensor'
        )
        self.device = device
        self.level = Value(0.0)
        self.add_property(
            Property(self,
                     'level',
                     self.level,
                     metadata={
                         '@type': 'TemperatureProperty',
                         'title': 'Temperature',
                         'type': 'number',
                         'description': 'The current temperature in °C',
                         'unit': 'degree celsius',
                         'readOnly': True,
                     }))

        logging.debug('starting the sensor update looping task for: '+str(self.device))
        self.timer = tornado.ioloop.PeriodicCallback(
            self.update_level,
            30000
        )
        self.timer.start()

    def update_level(self):
        new_level = read_one(self.device)
        logging.debug('setting new temperature level: %s of %s', new_level, device)
        self.level.notify_of_external_update(new_level)


    def cancel_update_level_task(self):
        self.timer.stop()

#********************** for multiple_ds18b20 ********************
"""Sensor initializeing, get the ammount of devices connected to the bus."""
def get_devices():
    try:
        for x in os.listdir("/sys/bus/w1/devices"):
            if "master" in x:
                continue
            device_id_list.append(x)
    except:
        logging.debug('no devices found')

    logging.debug('list of devices found: %s ', device_id_list)
    return device_id_list
def read_one(temp_sensor_id):
    try:
        """ read 1-wire slave file from a specific device """
        file_name = "/sys/bus/w1/devices/" + temp_sensor_id + "/w1_slave"
        file = open(file_name)
        filecontent = file.read()
        file.close()
        """ read temperature values and convert to readable float """
        stringvalue = filecontent.split("\n")[1].split(" ")[9]
        sensorvalue = float(stringvalue[2:]) / 1000
        temperature = '%6.2f' % sensorvalue
        return temperature
    except:
        logging.debug("not able to read from: ",temp_sensor_id)


devices = get_devices()
num = 0
for device in devices:
    num += 1
    sensor = TemperatureSensors(device,num)
    things_list.append(sensor)
#********************** for multiple_ds18b20 ********************


def run_server():
    """
    If adding more than one thing, use MultipleThings() with a name.
    In the single thing case, the thing's name will be broadcast.
    """
    server = WebThingServer(MultipleThings(things_list,
                                           'TemperatureDevice'),
                            port=8888)
    try:
        logging.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        logging.debug('canceling the sensor update looping task')
        for sensor in things_list:
            sensor.cancel_update_level_task()
        logging.info('stopping the server')
        server.stop()
        logging.info('done')


if __name__ == '__main__':
    logging.basicConfig(
        level=10,
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
    )
    run_server()
