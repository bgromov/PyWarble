# from .cbindings import *
# from .cbindings import _Gatt, _Option
from .gattchar import GattChar
# from . import WarbleException, str_to_bytes, bytes_to_str
# from ctypes import cast, POINTER

import pyble
from pyble.handlers import PeripheralHandler, ProfileHandler
from pyble.osx.IOBluetooth import CBUUID

import platform
import os
import json

import traceback

class WarbleProfile(ProfileHandler):
    UUID = "*"
    _AUTOLOAD = False

    _on_read_handler = None
    _on_notify_handler = None
    _on_notification_state_handler = None
    _on_write_handler = None

    # def __init__(self):
    #     super(WarbleProfile, self).__init__()
    #     # print self
    #     # traceback.print_stack()

    def on_read(self, characteristic, data):
        # print "on_read [{}]: {}".format(characteristic, data)
        if self._on_read_handler:
            self._on_read_handler(characteristic, data)

    def on_notify(self, characteristic, data):
        # print "on_notify"
        if self._on_notify_handler:
            self._on_notify_handler(characteristic, data)

    def on_notification_state(self, characteristic, data):
        # print "on_notification_state"
        if self._on_notification_state_handler:
            self._on_notification_state_handler(characteristic, data)

    def on_write(self, characteristic, data):
        # print "on_write"
        if self._on_write_handler:
            self._on_write_handler(characteristic, data)

    def set_on_read_handler(self, value):
        self._on_read_handler = value

    def set_on_notify_handler(self, value):
        self._on_notify_handler = value

    def set_on_notification_state_handler(self, value):
        self._on_notification_state_handler = value

    def set_on_write_handler(self, value):
        self._on_write_handler = value

class WarblePeripheral(PeripheralHandler):
    _on_connect_handler = None
    _on_disconnect_handler = None
    _on_rssi_handler = None

    def initialize(self):
        # print 'WarblePeripheral initialize'
        self.addProfileHandler(WarbleProfile)

    def on_connect(self):
        if self._on_connect_handler:
            # print 'Warble on_connect'
            self._on_connect_handler()

    def on_disconnect(self):
        if self._on_disconnect_handler:
            # print 'Warble on_disconnect'
            self._on_disconnect_handler()

    def on_rssi(self, value):
        if self._on_rssi_handler:
            self._on_rssi_handler(value)

    def set_on_connect_handler(self, value):
        self._on_connect_handler = value

    def set_on_disconnect_handler(self, value):
        self._on_disconnect_handler = value

    def set_on_rssi_handler(self, value):
        self._on_rssi_handler = value

class Gatt:
    def __init__(self, mac, **kwargs):
        """
        Creates a Python Warble Gatt object
        @params:
            mac         - Required  : mac address of the board to connect to e.g. E8:C9:8F:52:7B:07
            hci         - Optional  : mac address of the hci device to use, only applicable on Linux
            addr_type   - Optional  : ble device adress type, defaults to random
        """

        self.cache_dir = kwargs['cache_path'] if ('cache_path' in kwargs) else "~/.metawear"
        self.cache_dir = os.path.expanduser(self.cache_dir)
        self.cache_file = os.path.join(self.cache_dir, "known_devices.json")

        self.cman = pyble.CentralManager()
        self.peripheral = None

        # Check the cache
        if os.path.isfile(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.known_devices = json.load(f)
        else:
            # Create dir for future use
            try:
                os.makedirs(self.cache_dir)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

        # Look up devices UUID
        mac = mac.upper()
        if not mac in self.known_devices.keys():
            raise RuntimeError("Device with this MAC [{}] is not known. Please scan for devices first"
                    .format(mac))
        else:
            # print "Found peripheral:", self.known_devices[mac]
            pass

        # Get the peripheral object
        peripherals_list = self.cman.retrievePeripheralsWithIdentifiers([self.known_devices[mac]])

        if peripherals_list:
            self.peripheral = peripherals_list[0]
            self.peripheral.delegate = WarblePeripheral

        self.characteristics = {}

    def __del__(self):
        self.peripheral = None
        self.cman = None
        self.characteristics = {}

    @property
    def peripheral(self):
        return self.peripheral

    @property
    def is_connected(self):
        return self.peripheral.isConnected

    def connect_async(self, handler):
        """
        Establishes a connection to the remote device
        @params:
            handler     - Required  : `(Exception) -> void` function that will be executed when the connect task is completed
        """
        def completed():
            handler(None)

        self.peripheral.delegate.set_on_connect_handler(completed)
        self.cman.connectPeripheralAsync(self.peripheral)

    def disconnect(self):
        """
        Closes the connection with the remote device
        """
        self.cman.disconnectPeripheral(self.peripheral)

    def on_disconnect(self, handler):
        """
        Sets a handler to listen for disconnect events
        @params:
            handler     - Required  : `(int) -> void` function that will be executed when connection is lost
        """
        def completed():
            handler(None)

        self.peripheral.delegate.set_on_disconnect_handler(completed)

    def find_characteristic(self, uuid):
        """
        Find the GATT characteristic corresponding to the uuid value
        @params:
            uuid        - Required  : 128-bit UUID string to search for
        """
        cb_uuid = CBUUID.UUIDWithString_(uuid)
        uuid = cb_uuid.UUIDString()

        import time
        if (uuid not in self.characteristics):
            self.characteristics[uuid] = None
            for s in self.peripheral.services:
                for c in s:
                    if CBUUID.UUIDWithString_(c.UUID) == cb_uuid:
                        self.characteristics[uuid] = GattChar(self, c)
                        break

        return self.characteristics[uuid]

    def service_exists(self, uuid):
        """
        Check if a GATT service with the corresponding UUID exists on the device
        @params:
            uuid        - Required  : 128-bit UUID string to search for
        """
        cbuuid = CBUUID.UUIDWithString_(uuid)

        for s in self.peripheral.services:
            if CBUUID.UUIDWithString_(s.UUID) == cbuuid:
                return True

        return False
