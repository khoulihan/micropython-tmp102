
def _extend_class():
    from tmp102._tmp102 import Tmp102
    from tmp102._tmp102 import _set_bit_for_boolean

    SHUTDOWN_BIT = 0x01

    def _apply_shutdown(self, config, shutdown_set):
        config[0] = _set_bit_for_boolean(
            config[0],
            SHUTDOWN_BIT,
            shutdown_set
        )
        return config
    def _get_shutdown(self):
        current_config = self._get_config()
        return (current_config[0] & SHUTDOWN_BIT) == SHUTDOWN_BIT
    def _set_shutdown(self, val):
        self._set_config(
            self._apply_shutdown(
                bytearray(self._get_config()),
                val
            )
        )
    Tmp102._apply_shutdown = _apply_shutdown
    Tmp102.shutdown = property(_get_shutdown, _set_shutdown)

_extend_class()
del _extend_class
