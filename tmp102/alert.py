
def _extend_class():
    from tmp102._tmp102 import Tmp102
    from tmp102._tmp102 import _set_bit_for_boolean

    REGISTER_T_LOW = 2
    REGISTER_T_HIGH = 3

    THERMOSTAT_MODE_BIT = 0x02
    FAULT_QUEUE_BIT_0 = 0x08
    FAULT_QUEUE_BIT_1 = 0x10
    ALERT_BIT = 0x20
    POLARITY_BIT = 0x04

    Tmp102.FAULT_QUEUE_1 = 0
    Tmp102.FAULT_QUEUE_2 = 1
    Tmp102.FAULT_QUEUE_4 = 2
    Tmp102.FAULT_QUEUE_6 = 3

    # Thermostat modes
    Tmp102.COMPARATOR_MODE = False
    Tmp102.INTERRUPT_MODE = True

    # Alert states. Including these constants because the default logic
    # is opposite of what I would expect.
    Tmp102.ALERT_HIGH = True
    Tmp102.ALERT_LOW = False

    def _alert(self):
        current_config = self._get_config()
        return (current_config[1] & ALERT_BIT) == ALERT_BIT
    Tmp102.alert = property(_alert)

    def _apply_alert_polarity(self, config, polarity_set):
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
            self._apply_alert_polarity(
                bytearray(self._get_config()),
                val
            )
        )
    Tmp102._apply_alert_polarity = _apply_alert_polarity
    Tmp102.alert_polarity = property(_get_polarity, _set_polarity)

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
    Tmp102._apply_thermostat_mode = _apply_thermostat_mode
    Tmp102.thermostat_mode = property(_get_thermostat_mode, _set_thermostat_mode)

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
    Tmp102._apply_fault_queue_length = _apply_fault_queue_length
    Tmp102.fault_queue_length = property(_get_fault_queue_length, _set_fault_queue_length)

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
    Tmp102._set_temperature_register = _set_temperature_register

    def _get_thermostat_high_temperature(self):
        rt, t = self._read_temperature_register(REGISTER_T_HIGH)
        return t
    def _set_thermostat_high_temperature(self, val):
        self._set_temperature_register(REGISTER_T_HIGH, val)
    Tmp102.thermostat_high_temperature = property(
        _get_thermostat_high_temperature,
        _set_thermostat_high_temperature
    )

    def _get_thermostat_low_temperature(self):
        rt, t = self._read_temperature_register(REGISTER_T_LOW)
        return t
    def _set_thermostat_low_temperature(self, val):
        self._set_temperature_register(REGISTER_T_LOW, val)
    Tmp102.thermostat_low_temperature = property(
        _get_thermostat_low_temperature,
        _set_thermostat_low_temperature
    )

_extend_class()
del _extend_class
