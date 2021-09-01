from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Cython PWM function',
    ext_modules=cythonize([
        "bitbang_pwm.py",
        "bitbang_i2c.py"
    ], annotate=True, compiler_directives={'language_level' : "3"}),
    zip_safe=False,
)