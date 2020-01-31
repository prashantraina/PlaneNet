nvcc = /usr/local/cuda/bin/nvcc
TF_CFLAGS:=$(shell python -c 'import tensorflow as tf; print(" ".join(tf.sysconfig.get_compile_flags()))')
TF_LFLAGS:=$(shell python -c 'import tensorflow as tf; print(" ".join(tf.sysconfig.get_link_flags()))')

all: tf_nndistance_so.so
.PHONY : all

tf_nndistance_so.so: tf_nndistance_g.cu.o tf_nndistance.cpp
	g++ -std=c++11 tf_nndistance.cpp tf_nndistance_g.cu.o -o tf_nndistance_so.so $(TF_CFLAGS) $(TF_LFLAGS) -shared -fPIC -O2 

tf_nndistance_g.cu.o: tf_nndistance_g.cu
	$(nvcc) -std=c++11 -c -o tf_nndistance_g.cu.o tf_nndistance_g.cu $(TF_CFLAGS) $(TF_LFLAGS) -DGOOGLE_CUDA=1 -x cu -Xcompiler -fPIC -O2

.PHONY : clean
clean :
	rm -f *.so *.o