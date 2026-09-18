

set -ex



test -f ${PREFIX}/include/lcms2.h
test ! -f ${PREFIX}/lib/liblcms2.a
test -f ${PREFIX}/lib/liblcms2${SHLIB_EXT}
jpgicc
tificc
linkicc
transicc
psicc
pkg-config --modversion lcms2
pkg-config --cflags lcms2
pkg-config --libs lcms2
exit 0
