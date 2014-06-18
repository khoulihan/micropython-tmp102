
def _extend_class():
    from tmp102._tmp102 import Tmp102
    from tmp102._tmp102 import _set_bit_for_boolean, EXTENDED_MODE_BIT

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
    Tmp102._apply_extended_mode = _apply_extended_mode
    Tmp102.extended_mode = property(_get_extended_mode, _set_extended_mode)

_extend_class()
del _extend_class
