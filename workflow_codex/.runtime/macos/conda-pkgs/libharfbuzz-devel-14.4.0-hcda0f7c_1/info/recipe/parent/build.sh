#!/bin/bash

set -ex

# necessary to ensure the gobject-introspection-1.0 pkg-config file gets found
# meson uses PKG_CONFIG_PATH to search when not cross-compiling and
# PKG_CONFIG_PATH_FOR_BUILD when cross-compiling,
export PKG_CONFIG_PATH_FOR_BUILD=$BUILD_PREFIX/lib/pkgconfig
export PKG_CONFIG=$BUILD_PREFIX/bin/pkg-config

# Make sure .gir files in $PREFIX are found
export XDG_DATA_DIRS=${XDG_DATA_DIRS}:$PREFIX/share:$BUILD_PREFIX/share

meson_config_args=(
    -Dbenchmark=disabled
    -Dcairo=enabled
    -Dcoretext=auto
    -Ddocs=disabled
    -Dfreetype=enabled
    -Dgdi=auto
    -Dglib=enabled
    -Dgobject=enabled
    -Dgraphite2=enabled
    -Dicu=enabled
    -Dtests=disabled
)

if [ -n "$OSX_ARCH" ] ; then
    # The -dead_strip_dylibs option breaks g-ir-scanner here
    export LDFLAGS="$(echo $LDFLAGS |sed -e "s/-Wl,-dead_strip_dylibs//g")"
    export LDFLAGS_LD="$(echo $LDFLAGS_LD |sed -e "s/-dead_strip_dylibs//g")"
fi

if [[ "$CONDA_BUILD_CROSS_COMPILATION" == "1" ]]; then
  unset _CONDA_PYTHON_SYSCONFIGDATA_NAME
  (
    mkdir -p native-build

    export CC=$CC_FOR_BUILD
    export CXX=$CXX_FOR_BUILD
    export OBJC=$OBJC_FOR_BUILD
    export AR="$($CC_FOR_BUILD -print-prog-name=ar)"
    export NM="$($CC_FOR_BUILD -print-prog-name=nm)"
    export LDFLAGS=${LDFLAGS//$PREFIX/$BUILD_PREFIX}
    export PKG_CONFIG_PATH=${BUILD_PREFIX}/lib/pkgconfig

    # Unset them as we're ok with builds that are either slow or non-portable
    unset CFLAGS
    unset CPPFLAGS
    unset CXXFLAGS
    export host_alias=$build_alias

    meson setup native-build \
        "${meson_config_args[@]}" \
        --buildtype=release \
        --prefix=$BUILD_PREFIX \
        -Dlibdir=lib \
        --wrap-mode=nofallback || cat $SRC_DIR/native-build/meson-logs/meson-log.txt

    # This script would generate the functions.txt and dump.xml and save them
    # This is loaded in the native build. We assume that the functions exported
    # by the package are the same for the native and cross builds
    export GI_CROSS_LAUNCHER=$BUILD_PREFIX/libexec/gi-cross-launcher-save.sh
    ninja -v -C native-build -j ${CPU_COUNT}
    ninja -C native-build install -j ${CPU_COUNT}
  )
  export GI_CROSS_LAUNCHER=$BUILD_PREFIX/libexec/gi-cross-launcher-load.sh

  # introspection is incompatible with cross-compilation with GI_CROSS_LAUNCHER
  # (at least, we couldn't get it to work for linux-64 -> linux-ppc64le so far;
  # osx-64 -> osx-arm64 used worked though before osx-arm64 went native)...
  meson_config_args+=(-Dintrospection=disabled)
  # ... files will be installed manually in install_pkg.sh;
  # store in $SRC_DIR, because $BUILD_PREFIX gets regenerated
  cp $BUILD_PREFIX/share/gir-1.0/HarfBuzz-0.0.gir $SRC_DIR/
  cp $BUILD_PREFIX/lib/girepository-1.0/HarfBuzz-0.0.typelib $SRC_DIR/
else
  meson_config_args+=(-Dintrospection=enabled)
fi

# Workaround needed starting 14.0.0 -- should be removable once
# https://github.com/conda-forge/ctng-compiler-activation-feedstock/pull/187
# is merged
export OBJCXX="${OBJC}++"
export OBJCXX_FOR_BUILD="${OBJC_FOR_BUILD}++"

if [[ $build_platform != $target_platform ]]; then
    # avoid picking up binaries from host env
    echo "[binaries]"                                                                         > cross_file.txt
    echo "g-ir-scanner = ['${BUILD_PREFIX}/bin/python', '${BUILD_PREFIX}/bin/g-ir-scanner']" >> cross_file.txt
    export MESON_ARGS="$MESON_ARGS --cross-file=cross_file.txt"
fi

# NB: $MESON_ARGS sets buildtype, prefix, and libdir.
meson setup builddir \
    ${MESON_ARGS} \
    "${meson_config_args[@]}" \
    --default-library=both \
    --wrap-mode=nofallback
ninja -v -C builddir -j ${CPU_COUNT}
