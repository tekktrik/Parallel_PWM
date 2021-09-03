import threading
#from posix.time cimport clock_gettime, timespec, CLOCK_MONOTONIC_RAW
from libc.time import clock_t, clock, CLOCKS_PER_SEC
#cdef extern from "time.h":
#ctypedef int time_t
#ctypedef long suseconds_t
#cdef struct timeval:
#time_t tv_sec
#suseconds_t tv_usec
#time_t clock_gettime(time_t*)

cdef class PWM:

	cdef object _port
	cdef object _pin
	cdef long double _duty_cycle
	cdef long double cycle_time
	cdef object _thread
	
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
		self._thread = None
			
	def start(self):
		self._port.writePin(self._pin, False)
		self._thread = PWMCycle(self._port, self._pin, self._duty_cycle, self.cycle_time)
		
	def stop(self):
		self._thread.stopCycle()
		
	def pause(self):
		self._thread.pauseCycle()
		
	def resume(self):
		self._thread.unpauseCycle()
		
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
		self._pwm_thread = threading.Thread(target=self.runCycle)
		self._pwm_thread.daemon = True
		self._pwm_thread.start()
		
	cpdef runCycle(self):
	
		cdef timespec currtime, limittime
		cdef long double time_now
		
		cdef object paraport = self._port._parallel_port
		
		cdef long double ondelay
		cdef long double offdelay
		
		cdef unsigned int portregister = self._pin.register
		cdef unsigned char bitindex = self._pin.bit_index
            
		cdef long double ontime = self.cycle_time*self._duty_cycle
		cdef long double offtime = self.cycle_time - ontime
		
		cdef unsigned char portregisterbyte = paraport.DlPortReadPortUchar(portregister)
		cdef unsigned char bitmask = 1 << bitindex
		cdef unsigned char byteresult = (bitmask ^ portregisterbyte)
		
		while not self._end_cycle.is_set():
			if not self._pause_cycle.is_set():
				paraport.DlPortWritePortUchar(portregister, byteresult)
				ondelay = (1000*clock())/CLOCKS_PER_SEC + ontime
				while ((1000*clock())/CLOCKS_PER_SEC) < ondely:
					pass
				paraport.DlPortWritePortUchar(portregister, portregisterbyte) 
				offdelay = (1000*clock())/CLOCKS_PER_SEC + offtime
				while ((1000*clock())/CLOCKS_PER_SEC) < offdely:
					pass
		self._pwm_thread.join()
					
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