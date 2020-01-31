#  ------------------------------------------------------------------------------------------------------------i----------
#  *  Activate your Tensorflow virtualenv before running this script.
#  *  This script assumes gcc version >=5. If you have an older version, remove the -D_GLIBCXX_USE_CXX11_ABI=0 flag below.
#  *  On Mac OS X, the additional flag "-undefined dynamic_lookup" is required.
#  *  If this script fails, please refer to https://www.tensorflow.org/extend/adding_an_op#build_the_op_library for help.
#  -----------------------------------------------------------------------------------------------------------------------

TF_CFLAGS=$(python -c 'import tensorflow as tf; print(" ".join(tf.sysconfig.get_compile_flags()))')
TF_LFLAGS=$(python -c 'import tensorflow as tf; print(" ".join(tf.sysconfig.get_link_flags()))')

g++ -std=c++11 high_dim_filter.cc modified_permutohedral.cc -o high_dim_filter.so $TF_CFLAGS $TF_LFLAGS -shared -fPIC -O2
