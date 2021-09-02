import cython
import threading
from time import time

class PWM:

    _port: object
    _pin: object
    _duty_cycle: cython.longdouble
    cycle_time: cython.longdouble
    _pwm_thread: object
    
    def __init__(self, gpio_port: object, pwm_pin: object, duty_cycle: cython.longdouble = 0, cycle_time: cython.longdouble = 0.02):
        self._port = gpio_port
        self._pin = pwm_pin
        self._duty_cycle = duty_cycle
        self.cycle_time = cycle_time
        self._pwm_thread = None
    
    @property
    def pin(self):
        return self._pin
    
    @pin.setter
    def pin(self, pwm_pin: object):
        if pwm_pin.isOutputAllowed():
            self._pin = pwm_pin
        else:
            raise Exception("PWM output is not available on this pin; please use a pin capable of output")
    
    @property
    def duty_cycle(self) -> cython.longdouble:
        return self._duty_cycle
    
    @duty_cycle.setter
    def duty_cycle(self, duty_cycle: cython.longdouble):
        if (0 <= duty_cycle) and (1 >= duty_cycle):
            self._duty_cycle = duty_cycle
        else:
            raise ValueError("Duty cycle must be between 0 and 1")    
    
    def startCycle(self):
        self._port.writePin(self._pin, False)
        self._pwm_thread = PWMCycle(self._port, self._pin, self._duty_cycle, self.cycle_time)
        
    def endCycle(self):
        self._pwm_thread.stopCycle()
        
@cython.cclass
class PWMCycle:
    
    gpioport: object
    gpiopin: object
    dutycycle: cython.longdouble
    cycletime: cython.longdouble
    _end_cycle: object
    _pause_cycle: object
    _pwm_thread: object
    __dict__: cython.dict
    
    def __init__(self, gpioport: object, gpiopin: object, dutycycle: cython.longdouble, cycletime: cython.longdouble):
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
    
        gpiopin: object
        pwm_gpioport: object
        portregister: cython.uint
        bitindex: cython.uchar
        cycletime: cython.longdouble
        dutycycle: cython.longdouble
    
        ontime: cython.longdouble
        offtime: cython.longdouble
        ondelay: cython.longdouble
        offdelay: cython.longdouble
        bitmask: cython.uchar
        byteresult: cython.uchar
        portregisterbyte: cython.uchar
    
        portregister = self.gpiopin.register
        bitindex = self.gpiopin.bit_index
            
        ontime = self.cycletime*self.dutycycle
        offtime = self.cycletime - ontime
        
        portregisterbyte = self.pwm_gpioport.DlPortReadPortUchar(portregister)
        bitmask = 1 << bitindex
        byteresult = (bitmask ^ portregisterbyte)
            
        while not self._end_cycle.is_set():
            if not self._pause_cycle.is_set():
                self.pwm_gpioport.DlPortWritePortUchar(portregister, byteresult)
                ondelay = time() + ontime
                while time() < ondelay:
                    pass
                self.pwm_gpioport.DlPortWritePortUchar(portregister, portregisterbyte)
                offdelay = time() + offtime
                while time() < offdelay:
                    pass
                    
    def stopCycle(self):
        self._end_cycle.set()
        
    def pauseCycle(self):
        self._pause_cycle.set()
    
    def unpauseCycle(self):
        self._pause_cycle.clear()
            
    def isStopped(self) -> cython.bint:
        return self._end_cycle.is_set()
        
    def isPaused(self) -> cython.bint:
        return self._pause_cycle.is_set()