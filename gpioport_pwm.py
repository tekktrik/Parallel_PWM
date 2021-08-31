import cython
import threading
import time

@cython.cclass
class PWMCycle:
    
    register: cython.long
    bitindex: cython.uint
    onstate: cython.uint
    cycletime: cython.ulongdouble
    dutycycle: cython.ulongdouble
    ontime: cython.ulongdouble
    offtime: cython.ulongdouble
    ondelay: cython.ulongdouble
    offdelay: cython.ulongdouble
    bitmask: cython.uint
    byteresult: cython.uint
    registerbyte: cython.unit
    __dict__: cython.dict
    
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
            ondelay = time.time() + ontime
            while time.time() < ondelay:
                pass
            register_byte = self.gpioport.DlPortReadPortUchar(self.register)
            bitmask = self.onstate << self.bitindex
            byteresult = (bitmask ^ register_byte)
            self.gpioport.DlPortWritePortUchar(self.register, byteresult)
            ondelay = time.time() + ontime
            offdelay = time.time() + offtime
            while time.time() < offdelay:
                pass
                    
    def stopCycle(self):
        self._end_cycle.set()
            
    def shouldStop(self):
        return self._end_cycle.is_set()