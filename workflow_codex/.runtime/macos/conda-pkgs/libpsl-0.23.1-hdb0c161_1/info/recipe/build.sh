set -ex

if [[ $(uname) == Darwin ]]; then
  export PKG_CONFIG=$BUILD_PREFIX/bin/pkg-config
fi

if [ -z "$MESON_ARGS" ]; then
  # for some reason this is not set on Linux
  MESON_ARGS="--buildtype=release --prefix=${PREFIX} --libdir=lib"
fi

if [[ "$target_platform" == "osx-arm64" && "$CONDA_BUILD_CROSS_COMPILATION" == "1" ]]; then
  unset _CONDA_PYTHON_SYSCONFIGDATA_NAME
fi


if [[ $PKG_NAME == "libpsl" ]]; then 
  meson setup builddir \
	   ${MESON_ARGS} \
     --default-library=shared \
     -Druntime=libicu \
     -Dbuiltin=true
else
  meson setup builddir \
	   ${MESON_ARGS} \
     --default-library=static \
     -Druntime=no \
     -Dbuiltin=true
fi

ninja -v -C builddir -j ${CPU_COUNT}
ninja -C builddir install -j ${CPU_COUNT}
