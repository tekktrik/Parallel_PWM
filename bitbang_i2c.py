import cython

@cython.cclass
class I2C:
    
    i2c_port: object
    sda_pin: object
    scl_pin: object
    __dict__: cython.dict
        
    def __init__(self, i2c_port, sda_pin, scl_pin):
        self.i2c_port = i2c_port
        self.portDLL = i2c_port._parallel_port
        self.sda_pin = sda_pin
        self.sda_register = sda_pin.register
        self.sda_bitindex = sda_pin.bit_index
        self.sda_isinvert = sda_pin._hw_inverted
        self.scl_pin = scl_pin
        self.scl_register = scl_pin.register
        self.scl_bitindex = scl_pin.bit_index
        self.scl_isinvert = scl_pin._hw_inverted
        
    def _setPin(self, pin_register: cython.longdouble, pin_bitindex: cython.uint, pin_isinvert: cython.uint, value: cython.uint):
        portDLL = self.portDLL
        if pin_isinvert:
            value = not value
        currentbyte = portDLL.DlReadPortReadUchar(pin_register)
        bit_mask = 1 << pin_bitindex
        rev_mask = bit_mask ^ 0xFF
        if value:
            byte_result = (bit_mask | currentbyte)
        else:
            byte_result = (rev_mask & currentbyte)
        portDLL.DlPortWritePortUchar(pin_register, byte_result)
    
    @cython.ccall
    def _setSDA(self, value: cython.uint):
        self._setPin(self.sda_register, self.sda_bitindex, self.sda_isinvert, value)
        
    @cython.ccall    
    def _setSCL(self, value: cython.uint):
        self._setPin(self.scl_register, self.scl_bitindex, self.scl_isinvert, value)
        
    @cython.ccall
    def _getSDA(self):
        currentbyte = self.portDLL.DlReadPortReadUchar(self.sda_register)
        isolated_bit = (1 << self.sda_bitindex) & currentbyte
        return isolated_bit >> self.sda_bitindex
    
    @cython.ccall
    def _startCond(self):
        self._setSDA(False)
        self._setSCL(False)
        
    @cython.ccall
    def _repStartCond(self):
        self._setSDA(True)
        self._setSCL(True)
        self._startCond()
        
    @cython.ccall
    def _endCond(self):
        self._setSCL(False)
        self._setSDA(False)
        self._setSCL(True)
        self._setSDA(True)
        
    @cython.ccall
    def _writeI2CByte(self, i2cbyte: cython.uint, numbits: cython.uint):
        self._setSDA(False)
        for bitindex in range(7, -1, -1):
            nextbit = ((1 << bitindex) | i2cbyte) >> bitindex
            self._setSDA(nextbit)
            self._setSCL(True)
            self._setSCL(False)
            return self._checkAck()
        
    @cython.ccall
    def _readI2CByte(self):
        current_byte = 0
        self._setSDA(False)
        for _ in range(8):
            nextbit = self._getSDA()
            current_byte = (current_byte << 1) | nextbit
        isAck = self._checkAck()
        return (current_byte, isAck)
            
    @cython.ccall
    def _checkAck(self):
        self._setSCL(True)
        isNak = self._getSDA()
        self._setSCL(False)
        self._setSDA(True)
        return not isNak
    
    @cython.call
    def _writeAddressFrame(self, address_byte: cython: uint, rw_type: cython.uint):
        full_byte = (address_byte << 1) | rw_type
        return self._writeI2CByte(full_byte)
    
    def write(self, i2c_address, i2c_data):
        self._startCond()
        status = self._writeAddressFrame(i2c_address, 0)
        if not status:
            return False
        for databyte in i2c_data:
            status = self._writeI2CByte(i2c_data)
            if not status:
                return False
            self._endCond()
        return True
        
    def read(self, i2c_address, num_bytes=1):
        bytelist = []
        self._startCond()
        status = self._writeAddressFrame(i2c_address, 1)
        if not status:
            return False
        for databyte in range(num_bytes):
            data_read, status = self._readI2CByte()
            if not status:
                return False
            bytelist.append(data_read)
            self._endCond()
        return data_read