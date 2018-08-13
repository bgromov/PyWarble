# from .cbindings import *
# from .cbindings import _Option
# from . import WarbleException, str_to_bytes, bytes_to_str

import pyble
from pyble.osx.IOBluetooth import CBUUID
import sys
import inspect

if sys.version_info[0] == 2:
    range = xrange

class BleScanner:
    _instance = None
    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def _handler(cls, dev_list):
        if dev_list:
            res = ScanResult(dev_list[-1])
            cls.instance().scan_handler(res)

    @classmethod
    def set_handler(cls, handler):
        """
        Sets a handler to listen for BLE scan results
        @params:
            handler     - Required  : `(ScanResult): void` function that is executed when a device is discovered
        """
        # cls.scan_handler = FnVoid_VoidP_WarbleScanResultP(lambda ctx, pointer: handler(ScanResult(pointer.contents)))
        # libwarble.warble_scanner_set_handler(None, cls.scan_handler)
        cls.instance().scan_handler = handler

    @classmethod
    def start(cls, **kwargs):
        """
        Start BLE scanning
        @params:
            hci         - Optional  : mac address of the hci device to use, only applicable on Linux
            scan_type   - Optional  : type of ble scan to perform, either 'passive' or 'active'
        """
        cls.instance().cman = pyble.CentralManager()
        cls.instance().cman.setBLEAvailableListCallback(cls.instance()._handler)
        cls.instance().cman.startScanAsync(allowDuplicates=False)

    @classmethod
    def stop(cls):
        """
        Stop BLE scanning
        """
        if cls.instance().cman:
            cls.instance().cman.stopScan()
            cls.instance().cman = None

class ScanResult:
    def __init__(self, peripheral):
        self.peripheral = peripheral

    @property
    def uuid(self):
        """
        UUID address of the scanned device
        """
        return self.peripheral.UUID

    @property
    def name(self):
        """
        Device's advertising name
        """
        return self.peripheral.name

    @property
    def rssi(self):
        """
        Device's current signal strength
        """
        return self.peripheral.rssi

    def has_service_uuid(self, uuid):
        """
        True if the device is advertising with the uuid
        @params:
            uuid        - Required  : 128-bit UUID string to search for
        """
        cbuuid = CBUUID.UUIDWithString_(uuid)

        for s in self.peripheral.advServiceUUIDs:
            if CBUUID.UUIDWithString_(s) == cbuuid:
                return True
        else:
            return False

    def get_manufacturer_data(self, company_id):
        """
        Additional data from the manufacturer included in the scan response, returns `None` if company_id is not found
        @params:
            company_id  - Optional  : Unsigned short value to look up
        """
        if company_id:
            if company_id in self.peripheral.advManufacturerDataByCompanyID:
                return self.peripheral.advManufacturerDataByCompanyID[company_id]
            else:
                return None
        else:
            return self.peripheral.advManufacturerData
