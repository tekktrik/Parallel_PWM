import cython
import threading
import time

@cython.cclass
class PWMCycle():
    
    register: cython.long
    bitindex: cython.uint
    onstate: cython.uint
    cycletime: cython.double
    dutycycle: cython.double
    ontime: cython.double
    offtime: cython.double
    ondelay: cython.double
    offdelay: cython.double
    bitmask: cython.uint
    byteresult: cython.uint
    registerbyte: cython.unit
    #dllstring: cython.p_char
    
    def __init__(self, gpioport, register, bitindex, onstate, dutycycle, cycletime):
        self.register = register
        self.bitindex = bitindex
        self.onstate = onstate
        self.gpioport = gpioport
        self._end_cycle = threading.Event()
        self._pwm_thread = threading.Thread(target=self.runCycle, args=())
        self._pwm_thread.daemon = True
        self._pwm_thread.start()
            
    def runCycle(self):
            
        ontime = self.cycletime*self.dutycycle
        offtime = self.cycletime - ontime
            
        while not self._end_cycle.is_set():
            register_byte = self.gpioport.DlPortReadPortUchar(self.register)
            bitmask = self.onstate << self.bitindex
            byteresult = (bitmask ^ register_byte)
            self.gpioport.DlPortWritePortUchar(self.register, byteresult)
            ondelay = time.monotonic() + ontime
            while time.monotonic() < ondelay:
                pass
            register_byte = self.gpioport.DlPortReadPortUchar(self.register)
            bitmask = self.onstate << self.bitindex
            byteresult = (bitmask ^ register_byte)
            self.gpioport.DlPortWritePortUchar(self.register, byteresult)
            ondelay = time.monotonic() + ontime
            offdelay = time.monotonic() + offtime
            while time.monotonic() < offdelay:
                pass
                    
    def stopCycle(self):
        self._end_cycle.set()
            
    def shouldStop(self):
        return self._end_cycle.is_set()