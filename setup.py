from distutils.core import setup, Extension

module1 = Extension('parallel_pwm',
                    sources = ['parallel_pwm.c'])

setup (name = 'ParallelPWM',
       version = '1.0',
       description = 'This is a demo package',
       ext_modules = [module1])