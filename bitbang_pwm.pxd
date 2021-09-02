cdef extern from "time.h":
	ctypedef int time_t
	cpdef time_t time(time_t x)