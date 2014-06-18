
def _extend_class():
    from tmp102._tmp102 import Tmp102
    from tmp102._tmp102 import _set_bit_for_boolean
    import tmp102.shutdown

    SHUTDOWN_BIT = 0x01
    ONE_SHOT_BIT = 0x80

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
    Tmp102.initiate_conversion = initiate_conversion

    def _conversion_ready(self):
        current_config = self._get_config()
        return (current_config[0] & ONE_SHOT_BIT) == ONE_SHOT_BIT
    Tmp102.conversion_ready = property(_conversion_ready)

_extend_class()
del _extend_class
