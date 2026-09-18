

set -ex



pcre2test --version
pcre2grep --version
pcre2-config --version
test -f ${PREFIX}/include/pcre2.h
test -f ${PREFIX}/include/pcre2posix.h
test -f ${PREFIX}/lib/libpcre2-posix${SHLIB_EXT}
test -f ${PREFIX}/lib/libpcre2-posix.3.dylib
test -f ${PREFIX}/lib/libpcre2-8${SHLIB_EXT}
test -f ${PREFIX}/lib/libpcre2-8.0.dylib
test -f ${PREFIX}/lib/libpcre2-16${SHLIB_EXT}
test -f ${PREFIX}/lib/libpcre2-16.0.dylib
test -f ${PREFIX}/lib/libpcre2-32${SHLIB_EXT}
test -f ${PREFIX}/lib/libpcre2-32.0.dylib
test -f ${PREFIX}/lib/pkgconfig/libpcre2-8.pc
test -f ${PREFIX}/lib/pkgconfig/libpcre2-16.pc
test -f ${PREFIX}/lib/pkgconfig/libpcre2-32.pc
test -f ${PREFIX}/lib/pkgconfig/libpcre2-posix.pc
test -f ${PREFIX}/lib/cmake/pcre2/pcre2-config.cmake
test -f ${PREFIX}/lib/cmake/pcre2/pcre2-config-version.cmake
test -f ${PREFIX}/lib/cmake/pcre2/pcre2-targets.cmake
test -f ${PREFIX}/lib/cmake/pcre2/pcre2-targets-release.cmake
cd maint/cmake-tests/install-interface
cmake -GNinja $CMAKE_ARGS .
cmake --build .
exit 0
