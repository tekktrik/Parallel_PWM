from threading Event, Thread
from libc.time import time

cdef class PWM:

	cdef object _port
	cdef object _pin
	cdef long double duty_cycle
	cdef long double cycle_time
	cdef object _pwm_thread
	cdef object _end_cycle
	cdef object _pause_cycle
	
	def __init__(self, object gpio_port, object pwm_pin, long double duty_cycle = 0, long double cycle_time = 0.02):
		self._port = gpio_port
		if pwm_pin.isOutputAllowed():
			self._pin = pwm_pin
		else:
			raise Exception("PWM output is not available on this pin; please use a pin capable of output")
		if (0 <= duty_cycle) and (1 >= duty_cycle):
			self._duty_cycle = duty_cycle
		else:
			raise ValueError("Duty cycle must be between 0 and 1") 
		self.cycle_time = cycle_time
		self._pwm_thread = None
		self._end_cycle = Event()
		self._pause_cycle = Event()
			
	def start(self):
		self._port.writePin(self._pin, False)
		self._pwm_thread = Thread(target=self.runCycle, args=())
		self._pwm_thread.daemon = True
        self._pwm_thread.start()
		
	cdef runCycle(self):
		
		unsigned int portregister
		unsigned char bitindex
		long double cycletime
		long double dutycycle
		
		long double ontime
		long double offtime
		long double ondelay
		long double offdelay
		unsigned char bitmask
		unsigned char byteresult
		unsigned char portregisterbyte
		
		portregister = self.gpiopin.register
		bitindex = self.gpiopin.bit_index
            
		ontime = self.cycletime*self.dutycycle
		offtime = self.cycletime - ontime
		
		portregisterbyte = self.gpioport.DlPortReadPortUchar(portregister)
		bitmask = 1 << bitindex
		byteresult = (bitmask ^ portregisterbyte)
		
		while not self._end_cycle.is_set():
			if not self._pause_cycle.is_set():
				self.gpioport.DlPortWritePortUchar(portregister, byteresult)
				ondelay = time(NULL) + ontime
				while time(NULL) < ondelay:
					pass
				self.gpioport.DlPortWritePortUchar(portregister, portregisterbyte)
				offdelay = time(NULL) + offtime
				while time(NULL) < offdelay:
					pass
					
	cpdef stopCycle(self):
		self._end_cycle.set()
	
	cpdef pauseCycle(self):
		self._pause_cycle.set()
	
	cpdef unpauseCycle(self):
		self._pause_cycle.clear()
		
	cpdef bint isStopped(self):
		return self._end_cycle.is_set()
        
	cpdef bint isPaused(self):
		return self._pause_cycle.is_set()