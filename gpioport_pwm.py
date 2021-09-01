import cython
import threading
from time import time

@cython.cclass
class PWMCycle:
    
    gpioport: object
    gpiopin: object
    pwm_gpioport: object
    portregister: cython.long
    bitindex: cython.uint
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
    
    #def __init__(self, gpioport, portregister, bitindex, onstate, dutycycle, cycletime):
    def __init__(self, gpioport, gpiopin, dutycycle, cycletime):
        self.gpioport = gpioport._parallel_port
        self.gpiopin = gpiopin
        self.dutycycle = dutycycle
        self.cycletime = cycletime
        self._end_cycle = threading.Event()
        self._pause_cycle = threading.Event()
        self._pwm_thread = threading.Thread(target=self.runCycle, args=())
        self._pwm_thread.daemon = True
        self._pwm_thread.start()
            
    def runCycle(self):
    
        portregister = self.gpiopin.register
        bitindex = self.gpiopin.bit_index
        
        pwm_gpioport = self.gpioport
            
        ontime = self.cycletime*self.dutycycle
        offtime = self.cycletime - ontime
        
        portregisterbyte = pwm_gpioport.DlPortReadPortUchar(portregister)
        print(bin(portregisterbyte))
        bitmask = 1 << bitindex
        byteresult = (bitmask ^ portregisterbyte)
        print(bin(byteresult))
            
        while not self._end_cycle.is_set():
            if not self._pause_cycle.is_set():
                pwm_gpioport.DlPortWritePortUchar(portregister, byteresult)
                ondelay = time() + ontime
                while time() < ondelay:
                    pass
                print(time())
                pwm_gpioport.DlPortWritePortUchar(portregister, portregisterbyte)
                offdelay = time() + offtime
                while time() < offdelay:
                    pass
                print(time())
                    
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