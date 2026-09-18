

set -ex



test -f ${PREFIX}/include/freetype2/freetype/freetype.h
test -f ${PREFIX}/lib/libfreetype.dylib
test ! -f ${PREFIX}/lib/libfreetype.a
${PREFIX}/bin/freetype-config --version
test -f ${PREFIX}/lib/pkgconfig/freetype2.pc
pkg-config --print-errors freetype2
exit 0
