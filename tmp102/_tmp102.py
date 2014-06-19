
REGISTER_TEMP = 0
REGISTER_CONFIG = 1

EXTENDED_MODE_BIT = 0x10

def _set_bit(b, mask):
    return b | mask

def _clear_bit(b, mask):
    return b & ~mask

def _set_bit_for_boolean(b, mask, val):
    if val:
        return _set_bit(b, mask)
    else:
        return _clear_bit(b, mask)


class Tmp102(object):

    def __init__(self, bus, address, temperature_convertor=None, **kwargs):
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
            for key, value in kwargs.items():
                applyfunc = '_apply_{}'.format(key)
                config = getattr(self, applyfunc)(config, value)
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

    @property
    def temperature(self):
        """
        The most recently recorded temperature.
        """
        rt, t = self._read_temperature_register(REGISTER_TEMP)
        return t
