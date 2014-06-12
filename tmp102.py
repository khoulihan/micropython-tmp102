"""
tmp102.py
=========

Implements support for the Texas Instruments tmp102 temperature sensor.

Copyright (c) 2014 by Kevin Houlihan
License: MIT, see LICENSE for more details.


Usage
=====

The main functionality of this module is contained in the Tmp102 class, which
wraps an I2C object from the pyb module to configure and read from a tmp102 device
at a specific address.

At it's most basic, the class can be can be initialized with an I2C bus object and
an address, and then the temperature can be read periodically from the temperature
property:

    bus = I2C(1, I2C.MASTER)
    sensor = Tmp102(bus, 0x48)
    print(sensor.temperature)

The temperature will be in celsius by default.


Conversion Rate
===============

By default, the temperature will be updated at 4Hz. The rate of updates can be
set to one of four frequencies by setting the conversion_rate property, or by
passing a conversion_rate named argument to the constructor:
    
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
named argument to the constructor:

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
shutdown property appropriately:

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
the conversion_ready property.

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
classes are included in this module.

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

"""

__all__ = ['Tmp102', 'Celsius', 'Fahrenheit', 'Kelvin']

REGISTER_TEMP = 0
REGISTER_CONFIG = 1
REGISTER_T_LOW = 2
REGISTER_T_HIGH = 3

# First config byte
SHUTDOWN_BIT = 0x01
THERMOSTAT_MODE_BIT = 0x02
POLARITY_BIT = 0x04
FAULT_QUEUE_BIT_0 = 0x08
FAULT_QUEUE_BIT_1 = 0x10
RESOLUTION_BIT_0 = 0x20
RESOLUTION_BIT_1 = 0x40
ONE_SHOT_BIT = 0x80

# Second config byte
EXTENDED_MODE_BIT = 0x10
ALERT_BIT = 0x20
CONVERSION_RATE_BIT_0 = 0x40
CONVERSION_RATE_BIT_1 = 0x80


def _set_bit(b, mask):
    return b | mask

def _clear_bit(b, mask):
    return b & ~mask

def _set_bit_for_boolean(b, mask, val):
    if val:
        return _set_bit(b, mask)
    else:
        return _clear_bit(b, mask)


class Celsius(object):
    """
    Dummy convertor for celsius. Providing an instance of this convertor
    is the same as providing no convertor.
    """

    def convert_from(self, temperature):
        return temperature

    def convert_to(self, temperature):
        return temperature


class Fahrenheit(object):
    """
    Convertor for fahrenheit scale.
    """
    
    def convert_from(self, temperature):
        """
        Convert to celsius from the fahrenheit input.
        """
        return (temperature - 32.0) / 1.8

    def convert_to(self, temperature):
        """
        Convert celsius input to fahrenheit
        """
        return (temperature * 1.8) + 32.0


class Kelvin(object):
    """
    Convertor for the kelvin temperature scale.
    """

    def convert_from(self, temperature):
        """
        Convert to celsius from kelvin.
        """
        return temperature - 273.15

    def convert_to(self, temperature):
        """
        Convert celsius input to kelvin.
        """
        return temperature + 273.15


class Tmp102(object):
    """
    Manages interaction with a Texas Instruments tmp102 temperature sensor over
    I2C.

    See the module docstring for usage information.
    """

    CONVERSION_RATE_QUARTER_HZ = 0
    CONVERSION_RATE_1HZ = 1
    CONVERSION_RATE_4HZ = 2
    CONVERSION_RATE_8HZ = 3

    FAULT_QUEUE_1 = 0
    FAULT_QUEUE_2 = 1
    FAULT_QUEUE_4 = 2
    FAULT_QUEUE_6 = 3

    # Thermostat modes
    COMPARATOR_MODE = False
    INTERRUPT_MODE = True

    # Alert states. Including these constants because the default logic
    # is opposite of what I would expect.
    ALERT_HIGH = True
    ALERT_LOW = False

    def __init__(self, bus, address, temperature_convertor=None, **kwargs):
        """
        Create the device on the specified bus, at the specified address.

        The bus must be a pyb.I2C object in master mode, or an object implementing
        the same interface.

        A temperature convertor object can be passed which will convert to and
        from celsius as necessary if you want to work in a different scale.
        Fahrenheit and Kelvin convertors are provided, and specifying no convertor
        will use the celsius scale.
        """
        # There doesn't seem to be a way to check this at present. The first
        # send or recv should throw an error instead if the mode is incorrect.
        #if not bus.in_master_mode():
        #    raise ValueError('bus must be in master mode')
        self.bus = bus
        self.address = address
        self.temperature_convertor = temperature_convertor
        # The register defaults to the temperature.
        self._last_write_register = REGISTER_TEMP
        self._extended_mode = False
        if len(kwargs) > 0:
            # Apply the passed in settings
            config = bytearray(self._get_config())
            if 'extended_mode' in kwargs:
                config = self._apply_extended_mode(
                    config,
                    kwargs['extended_mode']
                )
            if 'shutdown' in kwargs:
                config = self._apply_shutdown(
                    config,
                    kwargs['shutdown']
                )
            if 'conversion_rate' in kwargs:
                config = self._apply_conversion_rate(
                    config,
                    kwargs['conversion_rate']
                )
            if 'alert_polarity' in kwargs:
                config = self._apply_polarity(
                    config,
                    kwargs['alert_polarity']
                )
            if 'thermostat_mode' in kwargs:
                config = self._apply_thermostat_mode(
                    config,
                    kwargs['thermostat_mode']
                )
            if 'fault_queue_length' in kwargs:
                config = self._apply_fault_queue_length(
                    config,
                    kwargs['fault_queue_length']
                )
            self._set_config(config)

            if 'thermostat_high_temperature' in kwargs:
                self.thermostat_high_temperature = kwargs['thermostat_high_temperature']
            if 'thermostat_low_temperature' in kwargs:
                self.thermostat_low_temperature = kwargs['thermostat_low_temperature']

    def _read_register(self, register):
        if register != self._last_write_register:
            # Reads come from the last register written.
            self._write_register(register)
        val = self.bus.recv(2, addr=self.address)
        return val

    def _write_register(self, register, value=None):
        bvals = bytearray()
        bvals.append(register)
        if value is not None:
            for val in value:
                bvals.append(val)
        self.bus.send(bvals, addr=self.address)
        self._last_write_register = register

    def _get_config(self):
        return self._read_register(REGISTER_CONFIG)

    def _set_config(self, config):
        self._write_register(REGISTER_CONFIG, config)
        self._extended_mode = config[1] & EXTENDED_MODE_BIT

    def _apply_extended_mode(self, config, mode_set):
        config[1] = _set_bit_for_boolean(
            config[1],
            EXTENDED_MODE_BIT,
            mode_set
        )
        return config
    def _get_extended_mode(self):
        return self._extended_mode
    def _set_extended_mode(self, val):
        self._set_config(
            self._apply_extended_mode(
                bytearray(self._get_config()),
                val
            )
        )
    extended_mode = property(_get_extended_mode, _set_extended_mode)

    def _apply_conversion_rate(self, config, rate):
        bit_0_set = (rate << 6) & CONVERSION_RATE_BIT_0
        bit_1_set = (rate << 6) & CONVERSION_RATE_BIT_1
        config[1] = _set_bit_for_boolean(
            config[1],
            CONVERSION_RATE_BIT_0,
            bit_0_set
        )
        config[1] = _set_bit_for_boolean(
            config[1],
            CONVERSION_RATE_BIT_1,
            bit_1_set
        )
        return config
    def _get_conversion_rate(self):
        current_config = self._get_config()
        return current_config[1] >> 6
    def _set_conversion_rate(self, val):
        self._set_config(
            self._apply_conversion_rate(
                bytearray(self._get_config()),
                val
            )
        )
    conversion_rate = property(_get_conversion_rate, _set_conversion_rate)

    def _apply_shutdown(self, config, shutdown_set):
        config[0] = _set_bit_for_boolean(
            config[0],
            SHUTDOWN_BIT,
            shutdown_set
        )
        return config
    def _get_shutdown(self):
        current_config = self._get_config()
        return current_config[0] & SHUTDOWN_BIT
    def _set_shutdown(self, val):
        self._set_config(
            self._apply_shutdown(
                bytearray(self._get_config()),
                val
            )
        )
    shutdown = property(_get_shutdown, _set_shutdown)

    @property
    def alert(self):
        current_config = self._get_config()
        return current_config[1] & ALERT_BIT

    def _apply_polarity(self, config, polarity_set):
        config[0] = _set_bit_for_boolean(
            config[0],
            POLARITY_BIT,
            polarity_set
        )
        return config
    def _get_polarity(self):
        current_config = self._get_config()
        return (current_config[0] & POLARITY_BIT) == POLARITY_BIT
    def _set_polarity(self, val):
        self._set_config(
            self._apply_polarity(
                bytearray(self._get_config()),
                val
            )
        )
    alert_polarity = property(_get_polarity, _set_polarity)

    def _apply_thermostat_mode(self, config, mode_set):
        config[0] = _set_bit_for_boolean(
            config[0],
            THERMOSTAT_MODE_BIT,
            mode_set
        )
        return config
    def _get_thermostat_mode(self):
        current_config = self._get_config()
        return current_config[0] & THERMOSTAT_MODE_BIT
    def _set_thermostat_mode(self, val):
        self._set_config(
            self._apply_thermostat_mode(
                bytearray(self._get_config()),
                val
            )
        )
    thermostat_mode = property(_get_thermostat_mode, _set_thermostat_mode)

    def _apply_fault_queue_length(self, config, length):
        bit_0_set = (length << 3) & FAULT_QUEUE_BIT_0
        bit_1_set = (length << 3) & FAULT_QUEUE_BIT_1
        config[0] = _set_bit_for_boolean(
            config[0],
            FAULT_QUEUE_BIT_0,
            bit_0_set
        )
        config[0] = _set_bit_for_boolean(
            config[0],
            FAULT_QUEUE_BIT_1,
            bit_1_set
        )
        return config
    def _get_fault_queue_length(self):
        current_config = self._get_config()
        return (current_config[0] & (FAULT_QUEUE_BIT_1 | FAULT_QUEUE_BIT_0)) >> 3
    def _set_fault_queue_length(self, val):
        self._set_config(
            self._apply_fault_queue_length(
                bytearray(self._get_config()),
                val
            )
        )
    fault_queue_length = property(_get_fault_queue_length, _set_fault_queue_length)

    def initiate_conversion(self):
        """
        Initiate a one-shot conversion.
        """
        current_config = self._get_config()
        if not current_config[0] & SHUTDOWN_BIT:
            raise RuntimeError("Device must be shut down to initiate one-shot conversion")
        new_config = bytearray(current_config)
        new_config[0] = _set_bit_for_boolean(
            new_config[0],
            ONE_SHOT_BIT,
            True
        )
        self._set_config(new_config)

    @property
    def conversion_ready(self):
        """
        Indicates that a one-shot conversion (i.e. temperature read) has completed.

        This property will only be meaningful if the device has been shut down and
        a one-shot conversion has been initiated by calling initiate_conversion.
        Under those circumstances, this will return False while the conversion is
        taking place, and True thereafter.
        """
        current_config = self._get_config()
        return (current_config[0] & ONE_SHOT_BIT) == ONE_SHOT_BIT

    def _read_temperature_register(self, register):
        rt = self._read_register(register)
        lo = rt[1]
        hi = rt[0]
        negative = (hi >> 7) == 1
        shift = 4
        if self._extended_mode:
            shift = 3
        if not negative:
            t = (((hi * 256) + lo) >> shift) * 0.0625
        else:
            remove_bit = 0b011111111111
            if self._extended_mode:
                remove_bit = 0b0111111111111
            ti = (((hi * 256) + lo) >> shift)
            # Complement, but remove the first bit.
            ti = ~ti & remove_bit
            t = -(ti * 0.0625)
        if self.temperature_convertor is not None:
            t = self.temperature_convertor.convert_to(t)
        return rt, t

    def _set_temperature_register(self, register, value):
        if register not in (REGISTER_T_HIGH, REGISTER_T_LOW):
            ValueError('Specified register cannot be set')
        if self.temperature_convertor is not None:
            value = self.temperature_convertor.convert_from(value)
        shift = 4
        if self._extended_mode:
            shift = 3
        if value >= 0:
            t = int(value / 0.0625) << shift
        else:
            t = int(abs(value) / 0.0625) << shift
            t = ~t
        # We actually want big-endian, but that is not currently supported
        # by micro-python.
        tb = t.to_bytes(2, 'little')
        lo = tb[0]
        hi = tb[1]
        rt = bytearray(2)
        rt[1] = lo
        rt[0] = hi
        self._write_register(register, rt)

    @property
    def temperature(self):
        """
        The most recently recorded temperature.
        """
        rt, t = self._read_temperature_register(REGISTER_TEMP)
        return t

    def _get_thermostat_high_temperature(self):
        rt, t = self._read_temperature_register(REGISTER_T_HIGH)
        return t
    def _set_thermostat_high_temperature(self, val):
        self._set_temperature_register(REGISTER_T_HIGH, val)
    thermostat_high_temperature = property(
        _get_thermostat_high_temperature,
        _set_thermostat_high_temperature
    )

    def _get_thermostat_low_temperature(self):
        rt, t = self._read_temperature_register(REGISTER_T_LOW)
        return t
    def _set_thermostat_low_temperature(self, val):
        self._set_temperature_register(REGISTER_T_LOW, val)
    thermostat_low_temperature = property(
        _get_thermostat_low_temperature,
        _set_thermostat_low_temperature
    )
