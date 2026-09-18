set CMAKE_CONFIG=Release

mkdir build_shared_%CMAKE_CONFIG%
pushd build_shared_%CMAKE_CONFIG%

cmake %CMAKE_ARGS% -GNinja ^
      -DCMAKE_PREFIX_PATH="%LIBRARY_PREFIX%" ^
      -DCMAKE_INSTALL_PREFIX="%LIBRARY_PREFIX%" ^
      -DCMAKE_BUILD_TYPE:STRING=%CMAKE_CONFIG% ^
      -DBUILD_STATIC_LIBS=OFF ^
      "%SRC_DIR%"
if errorlevel 1 exit 1
ninja
if errorlevel 1 exit 1
if not "%CONDA_BUILD_SKIP_TESTS%"=="1" (
ctest -V
)
if errorlevel 1 exit 1
REM cmake --build . --target install
REM if errorlevel 1 exit 1
