@ECHO ON


:: set pkg-config path so that host deps can be found
:: (set as env var so it's used by both meson and during build with g-ir-scanner)
set "PKG_CONFIG_PATH=%LIBRARY_LIB%\pkgconfig;%LIBRARY_PREFIX%\share\pkgconfig"

:: get mixed path (forward slash) form of prefix so host prefix replacement works
set "LIBRARY_PREFIX_M=%LIBRARY_PREFIX:\=/%"

:: Preserve MESON_ARGS from the compiler activation. For win-arm64 cross builds
:: that includes --cross-file (needs_exe_wrapper), without which meson treats the
:: build as native and fails the sanity check with WinError 216 on the x64 host.
if "%MESON_ARGS%"=="" (
    set "MESON_ARGS=--buildtype=release --prefix=%LIBRARY_PREFIX_M% --libdir=lib"
)

:: win-arm64: no ICU (builtin PSL only). Same runtime=no as the static build.
if "%PKG_NAME%"=="libpsl-static" (
    set "PSL_RUNTIME=no"
    set "PSL_LIBRARY=static"
) else if "%target_platform%"=="win-arm64" (
    set "PSL_RUNTIME=no"
    set "PSL_LIBRARY=shared"
) else (
    set "PSL_RUNTIME=libicu"
    set "PSL_LIBRARY=shared"
)

%BUILD_PREFIX%\Scripts\meson.exe setup builddir %MESON_ARGS% --wrap-mode=nofallback --backend=ninja -Dbuiltin=true -Druntime=%PSL_RUNTIME% --default-library=%PSL_LIBRARY%
if errorlevel 1 exit 1

ninja -v -C builddir -j %CPU_COUNT%
if errorlevel 1 exit 1

ninja -C builddir install -j %CPU_COUNT%
if errorlevel 1 exit 1

del %LIBRARY_PREFIX%\bin\*.pdb
