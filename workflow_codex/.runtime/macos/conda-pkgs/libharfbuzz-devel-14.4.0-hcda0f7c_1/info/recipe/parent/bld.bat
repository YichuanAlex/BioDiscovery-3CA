@ECHO ON

meson setup builddir %MESON_ARGS% ^
    --backend=ninja ^
    --wrap-mode=nofallback ^
    -Dbenchmark=disabled ^
    -Dcairo=enabled ^
    -Dcoretext=auto ^
    -Dcpp_std=c++17 ^
    -Ddocs=disabled ^
    -Dfreetype=enabled ^
    -Dgdi=auto ^
    -Dglib=enabled ^
    -Dgobject=enabled ^
    -Dgraphite2=enabled ^
    -Dicu=enabled ^
    -Dintrospection=enabled ^
    -Dtests=disabled
if errorlevel 1 exit 1

ninja -v -C builddir -j %CPU_COUNT%
if errorlevel 1 exit 1
