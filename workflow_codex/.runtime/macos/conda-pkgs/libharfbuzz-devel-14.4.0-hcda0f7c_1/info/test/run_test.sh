

set -ex



test -f $PREFIX/include/harfbuzz/hb-ft.h
test -f $PREFIX/lib/girepository-1.0/HarfBuzz-0.0.typelib
test -f $PREFIX/share/gir-1.0/HarfBuzz-0.0.gir
hb-view --version
pkg-config --print-errors --exact-version "14.4.0" harfbuzz
exit 0
