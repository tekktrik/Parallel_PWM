from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Cython PWM function',
    ext_modules=cythonize([
        "bitbang_pwm.pyx",
        "bitbang_i2c.pyx"
    ], annotate=True, compiler_directives={'language_level' : "3"}),
    zip_safe=False,
)