from distutils.core import setup, Extension

module1 = Extension('gpioport_pwm',
                    sources = ['gpioport_pwm.c'])

setup (name = 'gpioport_pwm',
       version = '1.0',
       description = 'Implementation of PWM for GPIOPort in C',
       ext_modules = [module1])