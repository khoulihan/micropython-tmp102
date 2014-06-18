
def _extend_class():
    from tmp102._tmp102 import Tmp102
    from tmp102._tmp102 import _set_bit_for_boolean

    Tmp102.CONVERSION_RATE_QUARTER_HZ = 0
    Tmp102.CONVERSION_RATE_1HZ = 1
    Tmp102.CONVERSION_RATE_4HZ = 2
    Tmp102.CONVERSION_RATE_8HZ = 3

    CONVERSION_RATE_BIT_0 = 0x40
    CONVERSION_RATE_BIT_1 = 0x80

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
    Tmp102._apply_conversion_rate = _apply_conversion_rate
    Tmp102.conversion_rate = property(_get_conversion_rate, _set_conversion_rate)

_extend_class()
del _extend_class
