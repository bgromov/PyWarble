from .cbindings import *
from . import WarbleException, bytes_to_str

import sys

if sys.version_info[0] == 2:
    range = xrange

class GattChar:
    @staticmethod
    def _to_ubyte_pointer(bytes):
        arr = (c_ubyte * len(bytes))()
        i = 0
        for b in bytes:
            arr[i] = b
            i = i + 1

        return arr

    def __init__(self, owner, pyble_char):
        """
        Creates a Python Warble GattChar object
        @params:
            owner       - Required  : Parent object this GattChar object belongs to
            warble_char  - Required  : PyBLEWrapper Characteristic object
        """
        self.pyble_char = pyble_char
        self.owner = owner

    @property
    def uuid(self):
        """
        128-bit UUID string identifying this GATT characteristic
        """
        return self.pyble_char.UUID

    @property
    def gatt(self):
        """
        Parent Gatt object that self belongs to
        """
        return self.owner

    def write_async(self, value, handler):
        """
        Writes value to the characteristic requiring an acknowledge from the remote device
        @params:
            value       - Required  : Bytes to write to the characteristic
            handler     - Required  : `(Exception) -> void` function that is executed when the write operation is done
        """
        def completed(char, data):
            handler(None)

        self.pyble_char.handler.set_on_write_handler(completed)
        # self.owner.peripheral.writeValueForCharacteristic(value, self.pyble_char.instance)
        self.pyble_char.value_async = bytearray(value)

    def write_without_resp_async(self, value, handler):
        """
        Writes value to the characteristic without requesting a response from the remove device
        @params:
            value       - Required  : Bytes to write to the characteristic
            handler     - Required  : `(Exception) -> void` function that is executed when the write operation is done
        """
        def completed():
            handler(None)

        # self.pyble_char.handler.set_on_write_handler(completed)
        # self.owner.peripheral.writeValueForCharacteristic(value, self.pyble_char.instance, withResponse=False)
        self.pyble_char.value_async_nr = bytearray(value)
        completed()

    def read_value_async(self, handler):
        """
        Reads current value from the characteristic
        @params:
            handler     - Required  : `(array, Exception) -> void` function that is executed when the read operation is done
        """
        # def completed(ctx, caller, pointer, length, msg):
        #     if (msg == None):
        #         value= cast(pointer, POINTER(c_ubyte * length))
        #         handler([value.contents[i] for i in range(0, length)], None)
        #     else:
        #         handler(None, WarbleException(bytes_to_str(msg)))

        def completed(char, data):
            handler(data, None)

        # completed(self.pyble_char, self.pyble_char.value)
        self.pyble_char.handler.set_on_read_handler(completed)
        self.pyble_char.value_async
        # self.owner.peripheral.readValueForCharacteristic(self.pyble_char.instance)

    def enable_notifications_async(self, handler):
        """
        Enables characteristic notifications
        @params:
            handler     - Required  : `(Exception) -> void` function that is executed when the enable operation is done
        """

        def completed(char, data):
            if data:
                handler(None)
            else:
                handler(WarbleException('Failed to set notifications for {}'.format(char)))

        self.pyble_char.handler.set_on_notification_state_handler(completed)
        self.pyble_char.notify_async = True

    def disable_notifications_async(self, handler):
        """
        Disables characteristic notifications
        @params:
            handler     - Required  : `(Exception) -> void` function that is executed when the disable operation is done
        """
        self.pyble_char.notify_async = False

    def on_notification_received(self, handler):
        """
        Assigns a handler for characteristic notifications
        @params:
            handler     - Required  : `(array) -> void` function that all received values is forwarded to
        """
        # def value_converter(ctx, caller, pointer, length):
        #     value= cast(pointer, POINTER(c_ubyte * length))
        #     handler([value.contents[i] for i in range(0, length)])
        # self.value_changed_wrapper = FnVoid_VoidP_WarbleGattCharP_UbyteP_Ubyte(value_converter)

        # libwarble.warble_gattchar_on_notification_received(self.warble_char, None, self.value_changed_wrapper)

        def value_recieved(char, data):
            handler(data)

        # completed(self.pyble_char, self.pyble_char.value)
        self.pyble_char.handler.set_on_notify_handler(value_recieved)



