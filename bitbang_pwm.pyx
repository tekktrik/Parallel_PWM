import threading
#from libc.time import time
cdef extern from "time.h":
	ctypedef int time_t
	time_t time(time_t*)

cdef class PWM:

	cdef object _port
	cdef object _pin
	cdef long double _duty_cycle
	cdef long double cycle_time
	
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
			
	def start(self):
		self._port.writePin(self._pin, False)
		self._pwm_thread = PWMCycle(self._port, self._pin, self._duty_cycle, self.cycle_time)
		
	def stop(self):
		self._pwm_thread.stopCycle()
		
	def pause(self):
		self._pwm_thread.pauseCycle()
		
	def resume(self):
		self._pwm_thread.unpauseCycle()
		
	def isStopped(self) -> bint:
		return self._end_cycle.is_set()
        
	def isPaused(self) -> bint:
		return self._pause_cycle.is_set()
		
cdef class PWMCycle:

	cdef object _port
	cdef object _pin
	cdef long double _duty_cycle
	cdef long double cycle_time
	cdef object _pwm_thread
	cdef object _end_cycle
	cdef object _pause_cycle 
	
	def __init__(self, object gpio_port, object pwm_pin, long double duty_cycle, long double cycle_time):
		self._port = gpio_port
		self._pin = pwm_pin
		self._duty_cycle = duty_cycle
		self.cycle_time = cycle_time
		self._end_cycle = threading.Event()
		self._pause_cycle = threading.Event()
		self._pwm_thread = threading.Thread(target=self.runCycle, args=(self))
		self._pwm_thread.daemon = True
		self._pwm_thread.start()
		
	cdef runCycle(self):
	
		cdef long double ondelay
		cdef long double offdelay
		
		cdef unsigned int portregister = self.gpiopin.register
		cdef unsigned char bitindex = self.gpiopin.bit_index
            
		cdef long double ontime = self.cycletime*self.dutycycle
		cdef long double offtime = self.cycletime - ontime
		
		cdef unsigned char portregisterbyte = self.gpioport.DlPortReadPortUchar(portregister)
		cdef unsigned char bitmask = 1 << bitindex
		cdef unsigned char byteresult = (bitmask ^ portregisterbyte)
		
		while not self._end_cycle.is_set():
			if not self._pause_cycle.is_set():
				self._port.DlPortWritePortUchar(portregister, byteresult)
				ondelay = time(NULL) + ontime
				while time(NULL) < ondelay:
					pass
				self._port.DlPortWritePortUchar(portregister, portregisterbyte)
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