import cython
import threading
import time

@cython.cclass
class PWMCycle:
    
    portregister: cython.long
    bitindex: cython.uint
    onstate: cython.uint
    cycletime: cython.longdouble
    dutycycle: cython.longdouble
    ontime: cython.longdouble
    offtime: cython.longdouble
    ondelay: cython.longdouble
    offdelay: cython.longdouble
    bitmask: cython.uint
    byteresult: cython.uint
    portregisterbyte: cython.uint
    __dict__: cython.dict
    
    def __init__(self, gpioport, portregister, bitindex, onstate, dutycycle, cycletime):
        self.portregister = portregister
        self.bitindex = bitindex
        self.onstate = onstate
        self.gpioport = gpioport
        self._end_cycle = threading.Event()
        self._pause_cycle = threading.Event()
        self._pwm_thread = threading.Thread(target=self.runCycle, args=())
        self._pwm_thread.daemon = True
        self._pwm_thread.start()
            
    @cython.cfunc
    def runCycle(self):
            
        ontime = self.cycletime*self.dutycycle
        offtime = self.cycletime - ontime
        
        portregisterbyte = self.gpioport.DlPortReadPortUchar(self.portregister)
        bitmask = self.onstate << self.bitindex
        byteresult = (bitmask ^ portregisterbyte)
            
        while not self._end_cycle.is_set():
            if not self._pause_cycle.is_set():
                self.gpioport.DlPortWritePortUchar(self.portregister, byteresult)
                ondelay = time.time() + ontime
                while time.time() < ondelay:
                    pass
                #portregisterbyte = self.gpioport.DlPortReadPortUchar(self.portregister)
                #bitmask = self.onstate << self.bitindex
                #byteresult = (bitmask ^ portregisterbyte)
                self.gpioport.DlPortWritePortUchar(self.portregister, portregisterbyte)
                offdelay = time.time() + offtime
                while time.time() < offdelay:
                    pass
                    
    def stopCycle(self):
        self._end_cycle.set()
        
    def pauseCycle(self):
        self._pause_cycle.set()
    
    def unpauseCycle(self):
        self._pause_cycle.clear()
            
    def isStopped(self):
        return self._end_cycle.is_set()
        
    def isPaused(self):
        return self._pause_cycle.is_set()