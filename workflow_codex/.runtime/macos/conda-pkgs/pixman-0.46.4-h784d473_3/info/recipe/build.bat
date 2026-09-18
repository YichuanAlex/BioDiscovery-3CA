@ECHO ON

:: win-arm64 needs two workarounds:
:: - the vs2022_win-arm64 activation points cl.exe at arm64 via vcvarsamd64_arm64.bat
::   but puts no --cross-file in %MESON_ARGS%, so meson calls it a native build and
::   dies running its arm64 sanity-check exe on the x86_64 host.
:: - pixman enables mmx for any msvc compiler regardless of target arch
::   (meson.build:104), and mmintrin.h then rejects arm64.
set "MESON_EXTRA_ARGS="
if "%target_platform%"=="win-arm64" (
  echo [host_machine]>cross_file.txt
  echo system = 'windows'>>cross_file.txt
  echo cpu_family = 'aarch64'>>cross_file.txt
  echo cpu = 'aarch64'>>cross_file.txt
  echo endian = 'little'>>cross_file.txt
  set "MESON_EXTRA_ARGS=--cross-file cross_file.txt -Dmmx=disabled"
)

%BUILD_PREFIX%\Scripts\meson setup builddir ^
  %MESON_ARGS% ^
  %MESON_EXTRA_ARGS% ^
  --default-library=shared ^
  --wrap-mode=nofallback ^
  --backend=ninja
if errorlevel 1 exit 1

ninja -v -C builddir -j %CPU_COUNT%
if errorlevel 1 exit 1

ninja -C builddir install -j %CPU_COUNT%
if errorlevel 1 exit 1
