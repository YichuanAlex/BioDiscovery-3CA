

set -ex



test -f $PREFIX/lib/libharfbuzz${SHLIB_EXT}
test -f $PREFIX/lib/libharfbuzz-cairo${SHLIB_EXT}
test -f $PREFIX/lib/libharfbuzz-gobject${SHLIB_EXT}
test -f $PREFIX/lib/libharfbuzz-gpu${SHLIB_EXT}
test -f $PREFIX/lib/libharfbuzz-icu${SHLIB_EXT}
test -f $PREFIX/lib/libharfbuzz-raster${SHLIB_EXT}
test -f $PREFIX/lib/libharfbuzz-subset${SHLIB_EXT}
test -f $PREFIX/lib/libharfbuzz-vector${SHLIB_EXT}
exit 0
