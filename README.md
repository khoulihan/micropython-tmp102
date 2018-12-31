micropython-tmp102
==================

Implements support for the Texas Instruments tmp102 temperature sensor.

Copyright (c) 2014 by Kevin Houlihan

License: MIT, see LICENSE for more details.


Usage
=====

The main functionality of this package is contained in the Tmp102 class, which
wraps an I2C object from the pyb or machine modules to configure and read from a
tmp102 device at a specific address.

At it's most basic, the class can be can be initialized with an I2C bus object and
an address, and then the temperature can be read periodically from the temperature
property:

    from pyb import I2C
    from tmp102 import Tmp102
    bus = I2C(1, I2C.MASTER)
    sensor = Tmp102(bus, 0x48)
    print(sensor.temperature)

Or for the I2C class in the machine module:

    from machine import I2C
    from tmp102 import Tmp102
    bus = I2C(1)
    sensor = Tmp102(bus, 0x48)
    print(sensor.temperature)

The temperature will be in celsius by default.


Conversion Rate
===============

By default, the temperature will be updated at 4Hz. The rate of updates can be
set to one of four frequencies by setting the conversion_rate property, or by
passing a conversion_rate named argument to the constructor. The *conversionrate*
module must be imported to enable this functionality:
    
    from tmp102 import Tmp102
    import tmp102.conversionrate
    sensor = Tmp102(
        bus,
        0x48,
        conversion_rate=Tmp102.CONVERSION_RATE_1HZ
    )
    sensor.conversion_rate = Tmp102.CONVERSION_RATE_QUARTER_HZ  # 0.25Hz

The available rates are:

    Tmp102.CONVERSION_RATE_QUARTER_HZ
    Tmp102.CONVERSION_RATE_1HZ
    Tmp102.CONVERSION_RATE_4HZ
    Tmp102.CONVERSION_RATE_8HZ


Extended Mode
=============

By default, the temperature value is stored as 12 bits, for a maximum reading of
128C. Extended mode uses 13 bits instead, allowing a reading up to 150C. Extended
mode can be enabled by setting the extended_mode property or passing an extended_mode
named argument to the constructor. The *extendedmode* module must be imported to enable
this functionality.

    from tmp102 import Tmp102
    import tmp102.extendedmode
    sensor = Tmp102(
        bus,
        0x48,
        extended_mode=True
    )
    sensor.extended_mode = True


Shutdown and One-Shot Conversions
=================================

When temperature readings are not required for an extended period, the device can
be shut down to save power. Only the serial interface is kept awake to allow the
device to be woken up again. The device can be shut down and awoken by setting the
shutdown property appropriately. The *shutdown* module must be imported to enable
this functionality.

    sensor.shutdown = True
    # sensor.temperature will not be updated again until the device is awoken.
    pyb.delay(60000)
    sensor.shutdown = False
    # sensor.temperature will again be updated at the previously configured frequency.

Note that there is a delay between when the device receives the instruction to wake
up and when the first reading becomes available.

If the device is shut down and only a single reading is required, it is not
necessary to toggle the shutdown and make the device fully active again in order
to get a reading. A "one-shot" conversion can be initiated by calling the
initiate_conversion method. The progress of the conversion can be monitored through
the conversion_ready property. The *oneshot* module must be imported to enable this
functionality.

    sensor.initiate_conversion()
    while not sensor.conversion_ready:
        pyb.delay(10)
    temp = sensor.temperature

The device remains shutdown after this process.

One-shot conversions allow the temperature to be polled at frequencies much
longer than the four pre-set conversion rates without wasting power. To facilitate
this mode of operation, the device can be intitialized in shutdown mode by passing
a shutdown named argument to the constructor:

    sensor = Tmp102(bus, 0x48, shutdown=True)


Thermostat Mode and Alerts
==========================

The sensor has a feature to set and unset a flag based on high and low temperatures
being reached. It can also generate an SMBus interrupt when operating in a
certain mode. I'm not sure if this interrupt could be handled by the hardware,
but it is definitely not supported by this module.

The alert flag can be read on the alert property, and can take the values
Tmp102.ALERT_HIGH or Tmp102.ALERT_LOW. The various configuration flags and values
supported by the device can all be set through properties of the object or
arguments to the constructor, but their semantics are best described by the
datasheet of the sensor: http://www.ti.com/lit/ds/symlink/tmp102.pdf

The alert module must be imported to use any of these features.

    from tmp102 import Tmp102
    import tmp102.alert
    sensor = Tmp102(
        bus,
        0x48,
        alert_polarity=Tmp102.ALERT_HIGH,
        thermostat_mode=Tmp102.COMPARATOR_MODE,
        fault_queue_length=Tmp102.FAULT_QUEUE_4,
        thermostat_high_temperature=35.0,
        thermostat_low_temperature=34.0
    )

    sensor.alert_polarity = Tmp102.ALERT_LOW  #Default
    sensor.alert_polarity = Tmp102.ALERT_HIGH

    sensor.thermostat_mode = Tmp102.COMPARATOR_MODE  # Default
    sensor.thermostat_mode = Tmp102.INTERRUPT_MODE

    sensor.fault_queue_length = Tmp102.FAULT_QUEUE_1  # Default
    sensor.fault_queue_length = Tmp102.FAULT_QUEUE_2
    sensor.fault_queue_length = Tmp102.FAULT_QUEUE_4
    sensor.fault_queue_length = Tmp102.FAULT_QUEUE_6


Temperature Scales/Units
========================

By default, all temperatures are in celsius. If another scale/unit is preferred,
a convertor can be provided to the constructor. Fahrenheit and Kelvin convertor
classes are included in the *convertors* module.

    sensor = Tmp102(
        bus, 
        0x48, 
        temperature_convertor=Fahrenheit()
    )

A custom convertor can be provided as an object with this signature:

    class ScaleUnit(object):
        def convert_from(self, temperature):
            '''
            Convert FROM the custom unit TO celsius.
            '''
            ...
            return new_temp

        def convert_to(self, temperature):
            '''
            Convert TO the custom unit FROM celsius.
            '''
            ...
            return new_temp
