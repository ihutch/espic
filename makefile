all: infMagSim_cython.so


infMagSim_cython.pyx: infMagSim_cython.py
	grep -v 'utf-8' infMagSim_cython.py | grep -v nbformat | grep -v codecell \
		| grep -v %load_ext | grep -v %cython \
		> infMagSim_cython.pyx

infMagSim_cython.c: infMagSim_cython.pyx
	cython infMagSim_cython.pyx

infMagSim_cython.so: infMagSim_cython.c
	gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing \
		-I /home/chaako/virtualenvs/IPython/include/python2.7/ \
		-I /home/chaako/virtualenvs/IPython/lib/python2.7/site-packages/numpy/core/include/ \
		-o infMagSim_cython.so infMagSim_cython.c
