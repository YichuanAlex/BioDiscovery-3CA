@echo on

ninja -C builddir install -j %CPU_COUNT%
if %ERRORLEVEL% neq 0 exit 1

del %LIBRARY_PREFIX%\bin\*.pdb
