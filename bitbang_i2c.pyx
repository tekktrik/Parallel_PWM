cdef class I2C:
    
	cdef object i2c_port
	cdef object portDLL
	cdef object sda_pin
	cdef unsigned int sda_register
	cdef unsigned char sda_bitindex
	cdef bint sda_isinvert
	cdef object scl_pin
	cdef unsigned int scl_register
	cdef unsigned char scl_bitindex
	cdef bint scl_isinvert
	
	def __init__(self, object i2c_port, object sda_pin, object scl_pin, bint no_force_input = False):
		self.i2c_port = i2c_port
		self.portDLL = i2c_port._parallel_port
		if sda_pin.isOutputAllowed() and (sda_pin.isInputAllow() or no_force_input):
			self.sda_pin = sda_pin
		elif not sda_pin.isOutputAllowed():
			raise Exception("The selected SDA pin is not viable - cannot output")
		else:
			raise Exception("The selected SDA pin cannot be used as input - select input-viable pin or use no_force_input=True")
		self.sda_register = sda_pin.register
		self.sda_bitindex = sda_pin.bit_index
		self.sda_isinvert = sda_pin._hw_inverted
		if scl_pin.isOutputAllowed():
			self.scl_pin = scl_pin
		elif not scl_pin.isOutputAllowed():
			raise Exception("The selected SDA pin is not viable - cannot output")
		self.scl_register = scl_pin.register
		self.scl_bitindex = scl_pin.bit_index
		self.scl_isinvert = scl_pin._hw_inverted
		
	cdef _setPin(self, unsigned int pin_register, unsigned char pin_bitindex, bint pin_isinvert, bint value):
	
		cdef unsigned char byte_result
		
		if pin_isinvert:
			value = not value
		cdef unsigned char currentbyte = self.portDLL.DlReadPortReadUchar(pin_register)
		cdef unsigned char bit_mask = 1 << pin_bitindex
		cdef unsigned char rev_mask = bit_mask ^ 0xFF
		if value:
			byte_result = (bit_mask | currentbyte)
		else:
			byte_result = (rev_mask & currentbyte)
		self.portDLL.DlPortWritePortUchar(pin_register, byte_result)
    
	cdef _setSDA(self, bint value):
		self._setPin(self.sda_register, self.sda_bitindex, self.sda_isinvert, value)
		 
	cdef _setSCL(self, bint value):
		self._setPin(self.scl_register, self.scl_bitindex, self.scl_isinvert, value)
		
	cdef bint _getSDA(self):
		
		cdef unsigned char currentbyte = self.portDLL.DlReadPortReadUchar(self.sda_register)
		cdef unsigned char isolated_bit = (1 << self.sda_bitindex) & currentbyte
		return isolated_bit >> self.sda_bitindex
	
	cdef _startCond(self):
		self._setSDA(False)
		self._setSCL(False)
		
	cdef _repStartCond(self):
		self._setSCL(True)
		self._startCond()
		
	cdef _endCond(self):
		self._setSDA(False)
		self._setSCL(True)
		self._setSDA(True)
		
	cdef bint _writeI2CByte(self, bint i2cbyte):
	
		cdef bint nextbit
		cdef unsigned char bitindex
	
		self._setSDA(False)
		for bitindex in range(7, -1, -1):
			nextbit = ((1 << bitindex) | i2cbyte) >> bitindex
			self._setSDA(nextbit)
			self._setSCL(True)
			self._setSCL(False)
		return self._checkAck()
		
	cdef unsigned char _readI2CByte(self):
	
		cdef bint nextbit
		
		cdef unsigned char current_byte = 0
		self._setSDA(False)
		for _ in range(8):
			nextbit = self._getSDA()
			current_byte = (current_byte << 1) | nextbit
		cdef bint isAck = self._assertAck(True)
		return current_byte
		
	cdef bint _checkAck(self):
	
		self._setSCL(True)
		cdef bint isNak = self._getSDA()
		self._setSCL(False)
		self._setSDA(True)
		return not isNak
		
	cdef _assertAck(self, bint value):
		self._setSDA(not value)
		self._setSCL(True)
		self._setSCL(False)
		self._setSDA(True)
	
	cdef bint _writeAddressFrame(self, unsigned char address_byte, bint rw_type):
	
		return self._writeI2CByte((address_byte << 1) | rw_type)
	
	cpdef bint write(self, unsigned char i2c_address, list i2c_data, bint hold_device = False):
		
		
		cdef unsigned char databyte
		cdef bint status
		cdef object sdareglock = self.sda_pin.__class__.registerlock
		cdef object sclreglock = self.scl_pin.__class__.registerlock
		cdef bint samelock = False
		
		if type(self.sda_pin) == type(self.scl_pin):
			samelock = True
			sdareglock.acquire()
		else:
			sdareglock.acquire()
			sclreglock.acquire()
		
		try:
			self._startCond()
			status = self._writeAddressFrame(i2c_address, False)
			if not status:
				return False
			for databyte in i2c_data:
				status = self._writeI2CByte(databyte)
				if not status:
					return False
			if hold_device:
				self._repStartCond()
			else:
				self._endCond()
		finally:
			sdareglock.release()
			if not samelock:
				sclreglock.release()
			
		return True
		
	cpdef list read(self, unsigned char i2c_address, unsigned int num_bytes = 1, bint hold_device = False):
        
		cdef unsigned char data_read
		cdef bint status
		cdef object sdareglock = self.sda_pin.__class__.registerlock
		cdef object sclreglock = self.scl_pin.__class__.registerlock
		cdef bint samelock = False
		
		cdef list bytelist = []
		
		if type(self.sda_pin) == type(self.scl_pin):
			samelock = True
			sdareglock.acquire()
		else:
			sdareglock.acquire()
			sclreglock.acquire()
		try:
			self._startCond()
			status = self._writeAddressFrame(i2c_address, True)
			if not status:
				return False
			for _ in range(num_bytes):
				data_read, status = self._readI2CByte()
				if not status:
					return False
				bytelist.append(data_read)
			if hold_device:
				self._repStartCond()
			else:
				self._endCond()
		finally:
			sdareglock.release()
			if not samelock:
				sclreglock.release()
		
		return bytelist