%global mingw_build_ucrt64 1
%global mingw_build_ucrtarm64 1
# win32/win64 build with the clang supplement drivers: the qemu-ga MSI ships
# DLLs from clang/compiler-rt toolchain sysroots, where the GNU runtime DLLs
# do not exist, so nothing shipped there may import them.
%global mingw_toolchain_win32 clang
%global mingw_toolchain_win64 clang
%{?mingw_package_header}

Name:           mingw-zlib
Version:        1.3.2
Release:        2.2%{?dist}
Summary:        MinGW Windows zlib compression library

License:        Zlib
URL:            https://www.zlib.net/
Source0:        https://www.zlib.net/zlib-%{version}.tar.xz
# Use UNIX naming convention for libraries
Patch0:         mingw-zlib-cmake.patch

BuildArch:      noarch

BuildRequires:  cmake
BuildRequires:  make

# The win32/win64 clang columns dispatch to the supplement drivers only from
# 152-1.9 on.  Headers, CRT and binutils must be named; the GCC targets get
# them through gcc.  compiler-rt and libunwind: the drivers always link
# -rtlib=compiler-rt -unwindlib=libunwind, and mock installs no weak
# dependencies.
BuildRequires:  mingw32-filesystem >= 152-1.9
BuildRequires:  mingw32-clang
BuildRequires:  mingw32-binutils
BuildRequires:  mingw32-headers
BuildRequires:  mingw32-crt
BuildRequires:  mingw32-compiler-rt >= 22.1.8
BuildRequires:  mingw32-libunwind >= 22.1.8

BuildRequires:  mingw64-filesystem >= 152-1.9
BuildRequires:  mingw64-clang
BuildRequires:  mingw64-binutils
BuildRequires:  mingw64-headers
BuildRequires:  mingw64-crt
BuildRequires:  mingw64-compiler-rt >= 22.1.8
BuildRequires:  mingw64-libunwind >= 22.1.8
# llvm-windres, standing in for GNU windres on the clang columns (GNU windres
# preprocesses by invoking <triplet>-gcc, which is not installed).
BuildRequires:  llvm

BuildRequires:  ucrt64-filesystem
BuildRequires:  ucrt64-gcc

# No gcc for this target: the toolchain is clang, lld and the llvm-* tools.
# Headers and CRT must be named; the other targets get them through gcc.
BuildRequires:  ucrtarm64-filesystem >= 152
BuildRequires:  ucrtarm64-clang
BuildRequires:  ucrtarm64-llvm-tools
BuildRequires:  ucrtarm64-headers
BuildRequires:  ucrtarm64-crt
# The drivers always link -rtlib=compiler-rt (__chkstk lives there) and
# -unwindlib=libunwind; libunwind only arrives through ucrtarm64-clang's
# Recommends chain, and mock installs no weak dependencies.
BuildRequires:  ucrtarm64-compiler-rt >= 22.1.8
BuildRequires:  ucrtarm64-libunwind >= 22.1.8


%description
MinGW Windows zlib compression library.


# Win32
%package -n mingw32-zlib
Summary:        MinGW Windows zlib compression library for the win32 target

%description -n mingw32-zlib
MinGW Windows zlib compression library for the win32 target.


%package -n mingw32-zlib-static
Summary:        Static libraries for mingw32-zlib development.
Requires:       mingw32-zlib = %{version}-%{release}

%description -n mingw32-zlib-static
The mingw32-zlib-static package contains static library for mingw32-zlib development.


# Win64
%package -n mingw64-zlib
Summary:        MinGW Windows zlib compression library for the win64 target

%description -n mingw64-zlib
MinGW Windows zlib compression library for the win64 target.

%package -n mingw64-zlib-static
Summary:        Static libraries for mingw64-zlib development
Requires:       mingw64-zlib = %{version}-%{release}

%description -n mingw64-zlib-static
The mingw64-zlib-static package contains static library for mingw64-zlib development.


# UCRT64
%package -n ucrt64-zlib
Summary:        MinGW Windows zlib compression library for the ucrt64 target

%description -n ucrt64-zlib
MinGW Windows zlib compression library for the ucrt64 target.

%package -n ucrt64-zlib-static
Summary:        Static libraries for ucrt64-zlib development
Requires:       ucrt64-zlib = %{version}-%{release}

%description -n ucrt64-zlib-static
The ucrt64-zlib-static package contains static library for ucrt64-zlib development.


# Windows on ARM64
%package -n ucrtarm64-zlib
Summary:        MinGW Windows zlib compression library for the Windows on ARM64 target

%description -n ucrtarm64-zlib
MinGW Windows zlib compression library for the Windows on ARM64 target.

%package -n ucrtarm64-zlib-static
Summary:        Static libraries for ucrtarm64-zlib development
Requires:       ucrtarm64-zlib = %{version}-%{release}

%description -n ucrtarm64-zlib-static
The ucrtarm64-zlib-static package contains static library for ucrtarm64-zlib development.


%{?mingw_debug_package}


%prep
%autosetup -p1 -n zlib-%{version}


%build
# ZLIB_BUILD_TESTING=OFF for every clang target: the tests build with
# -coverage, which links libclang_rt.profile.a, and only the builtins are
# packaged.  %%check links a real zlib consumer instead.
#
# llvm-windres compiles zlib1.rc for the clang targets: GNU windres
# preprocesses .rc files by invoking <triplet>-gcc, which is not installed.
# It must reach cmake from a toolchain file: a -DCMAKE_RC_COMPILER on the
# command line makes cmake discard its cache mid-configure and lose the
# cross context.  The overlay includes the stock file and overrides only
# the resource compiler; the later -DCMAKE_TOOLCHAIN_FILE wins.  One-word
# wrapper scripts carry the --target, as CMAKE_RC_COMPILER takes no flags.
for t in i686-w64-mingw32 x86_64-w64-mingw32 ; do
    printf '#!/bin/sh\nexec llvm-windres --target=%%s "$@"\n' $t \
        > %{_builddir}/$t-windres-clang
    chmod +x %{_builddir}/$t-windres-clang
done
cat > %{_builddir}/toolchain-win32-clang-rc.cmake <<'EOF'
include(/usr/share/mingw/toolchain-mingw32.cmake)
SET(CMAKE_RC_COMPILER %{_builddir}/i686-w64-mingw32-windres-clang)
EOF
cat > %{_builddir}/toolchain-win64-clang-rc.cmake <<'EOF'
include(/usr/share/mingw/toolchain-mingw64.cmake)
SET(CMAKE_RC_COMPILER %{_builddir}/x86_64-w64-mingw32-windres-clang)
EOF

MINGW32_CMAKE_ARGS="-DINSTALL_PKGCONFIG_DIR=%{mingw32_libdir}/pkgconfig -DCMAKE_TOOLCHAIN_FILE=%{_builddir}/toolchain-win32-clang-rc.cmake -DZLIB_BUILD_TESTING=OFF" \
MINGW64_CMAKE_ARGS="-DINSTALL_PKGCONFIG_DIR=%{mingw64_libdir}/pkgconfig -DCMAKE_TOOLCHAIN_FILE=%{_builddir}/toolchain-win64-clang-rc.cmake -DZLIB_BUILD_TESTING=OFF" \
UCRT64_CMAKE_ARGS=-DINSTALL_PKGCONFIG_DIR=%{ucrt64_libdir}/pkgconfig \
UCRTARM64_CMAKE_ARGS="-DINSTALL_PKGCONFIG_DIR=%{ucrtarm64_libdir}/pkgconfig -DZLIB_BUILD_TESTING=OFF" \
%mingw_cmake
%mingw_make_build


%install
%mingw_make_install

# Drop the man pages
rm -rf %{buildroot}%{mingw32_mandir}
rm -rf %{buildroot}%{mingw64_mandir}
rm -rf %{buildroot}%{ucrt64_mandir}
rm -rf %{buildroot}%{ucrtarm64_mandir}
rm -rf %{buildroot}%{mingw32_docdir}
rm -rf %{buildroot}%{mingw64_docdir}
rm -rf %{buildroot}%{ucrt64_docdir}
rm -rf %{buildroot}%{ucrtarm64_docdir}


%check
# Verify the ucrtarm64 output with the llvm-* tools only: GNU nm/ar/objdump
# silently mis-read AArch64 PE/COFF.  %%check runs after the BRP passes, on
# exactly the bytes that end up in the rpms.

# 1. zlib1.dll really is a Windows ARM64 PE.
%{ucrtarm64_objdump} -f %{buildroot}%{ucrtarm64_bindir}/zlib1.dll
%{ucrtarm64_objdump} -f %{buildroot}%{ucrtarm64_bindir}/zlib1.dll \
    | grep -q 'file format coff-arm64'

# 1b. The DLL is stripped, with its debuginfo split out; if
#     %%mingw_debug_package went missing it would ship unstripped, silently.
%{ucrtarm64_objdump} -h %{buildroot}%{ucrtarm64_bindir}/zlib1.dll \
    | grep -q '\.gnu_debuglink'
test -f %{buildroot}%{_prefix}/lib/debug%{ucrtarm64_bindir}/zlib1.dll.debug

# 2. Every shipped archive still carries its ar symbol index.
for a in %{buildroot}%{ucrtarm64_libdir}/libz.a \
         %{buildroot}%{ucrtarm64_libdir}/libz.dll.a ; do
    magic=$(od -A n -t x1 -N 10 "$a" | tr -d ' \n')
    echo "archive $a: header $magic"
    test "$magic" = "213c617263683e0a2f20"
    %{ucrtarm64_nm} --print-armap "$a" \
        | awk '$1 == "inflate" && $2 == "in" { found = 1 } END { exit !found }'
done

# 3. The members of both archives are ARM64 COFF as well, and nothing else
#    leaked in from the host or from one of the other three targets.
for a in %{buildroot}%{ucrtarm64_libdir}/libz.a \
         %{buildroot}%{ucrtarm64_libdir}/libz.dll.a ; do
    %{ucrtarm64_objdump} -f "$a" | grep -q 'file format coff-arm64'
    ! %{ucrtarm64_objdump} -f "$a" | grep -E 'file format (coff-i386|coff-x86-64|elf)'
done

# 4. Link test: a zlib consumer has to compile and link against exactly what is
#    about to be packaged, both against the import library and statically.  Only
#    the link and the resulting file format can be checked here.
armcheck=%{_builddir}/ucrtarm64-zlib-check
rm -rf $armcheck
mkdir -p $armcheck
cat > $armcheck/t.c <<'EOF'
#include <stdio.h>
#include <string.h>
#include <zlib.h>

int main (void)
{
  static const char msg[] = "the quick brown fox jumps over the lazy dog";
  unsigned char comp[256];
  unsigned char plain[256];
  z_stream s;
  uLong clen;

  memset (&s, 0, sizeof s);
  if (deflateInit (&s, Z_DEFAULT_COMPRESSION) != Z_OK)
    return 1;
  s.next_in = (Bytef *) msg;
  s.avail_in = sizeof msg;
  s.next_out = comp;
  s.avail_out = sizeof comp;
  if (deflate (&s, Z_FINISH) != Z_STREAM_END)
    return 1;
  clen = s.total_out;
  deflateEnd (&s);

  memset (&s, 0, sizeof s);
  if (inflateInit (&s) != Z_OK)
    return 1;
  s.next_in = comp;
  s.avail_in = clen;
  s.next_out = plain;
  s.avail_out = sizeof plain;
  if (inflate (&s, Z_FINISH) != Z_STREAM_END)
    return 1;
  inflateEnd (&s);

  printf ("zlib %%s: %%s\n", zlibVersion (), (const char *) plain);
  return memcmp (msg, plain, sizeof msg) == 0 ? 0 : 1;
}
EOF

# Shared: -lz resolves to libz.dll.a -> zlib1.dll.
%{ucrtarm64_cc} -isystem %{buildroot}%{ucrtarm64_includedir} $armcheck/t.c \
    -L%{buildroot}%{ucrtarm64_libdir} -lz -o $armcheck/t.exe
%{ucrtarm64_objdump} -f $armcheck/t.exe
%{ucrtarm64_objdump} -f $armcheck/t.exe | grep -q 'file format coff-arm64'
%{ucrtarm64_objdump} -p $armcheck/t.exe | grep -i 'zlib1.dll'

# Static: the same program against ucrtarm64-zlib-static, which must not end
# up importing the DLL.  Capture the imports first: under "!" a crashed
# objdump would count as "pattern absent" and pass.
%{ucrtarm64_cc} -isystem %{buildroot}%{ucrtarm64_includedir} $armcheck/t.c \
    -L%{buildroot}%{ucrtarm64_libdir} -Wl,-Bstatic -lz -Wl,-Bdynamic \
    -o $armcheck/t-static.exe
%{ucrtarm64_objdump} -f $armcheck/t-static.exe
%{ucrtarm64_objdump} -f $armcheck/t-static.exe | grep -q 'file format coff-arm64'
imports=$(%{ucrtarm64_objdump} -p $armcheck/t-static.exe)
if echo "$imports" | grep -qi 'zlib1.dll'; then
    echo "ERROR: the static link imports zlib1.dll" >&2
    exit 1
fi

rm -rf "$armcheck"

# 5. The pkg-config file is what every later consumer finds this library
#    with.  The file is still under %%{buildroot}, so point PKG_CONFIG_LIBDIR
#    at that copy.
cat %{buildroot}%{ucrtarm64_libdir}/pkgconfig/zlib.pc
grep -q '^prefix=%{ucrtarm64_prefix}$' %{buildroot}%{ucrtarm64_libdir}/pkgconfig/zlib.pc
export PKG_CONFIG_LIBDIR=%{buildroot}%{ucrtarm64_libdir}/pkgconfig
ucrtarm64-pkg-config --exists zlib
# One invocation per mode: pkgconf answers --modversion and nothing else when it
# is asked for, so a combined "--modversion --cflags --libs" would print the
# version and silently test neither of the other two.
ucrtarm64-pkg-config --modversion zlib
ucrtarm64-pkg-config --cflags zlib
ucrtarm64-pkg-config --libs zlib
ucrtarm64-pkg-config --libs zlib | grep -q -- '-lz'
unset PKG_CONFIG_LIBDIR

# 6. The win32/win64 DLLs are now linked with the clang supplement drivers,
#    and the qemu-ga MSI ships them from sysroots where the GNU runtime DLLs
#    do not exist: no libgcc, libssp or libunwind import may appear.  A zlib
#    consumer must still link through the same drivers.
wincheck=%{_builddir}/win-zlib-check
rm -rf $wincheck
mkdir -p $wincheck
cat > $wincheck/t.c <<'EOF'
#include <string.h>
#include <zlib.h>

int main (void)
{
  static const char msg[] = "the quick brown fox jumps over the lazy dog";
  unsigned char comp[256];
  unsigned char plain[256];
  uLongf clen = sizeof comp;
  uLongf plen = sizeof plain;

  if (compress2 (comp, &clen, (const Bytef *) msg, sizeof msg, 6) != Z_OK)
    return 1;
  if (uncompress (plain, &plen, comp, clen) != Z_OK)
    return 1;
  return memcmp (msg, plain, sizeof msg) == 0 ? 0 : 1;
}
EOF

for t in i686-w64-mingw32 x86_64-w64-mingw32 ; do
  case $t in
    i686-*)
      wbin_rel=%{mingw32_bindir}
      wlibdir=%{buildroot}%{mingw32_libdir}
      wincdir=%{buildroot}%{mingw32_includedir}
      peformat=pei-i386
      ;;
    x86_64-*)
      wbin_rel=%{mingw64_bindir}
      wlibdir=%{buildroot}%{mingw64_libdir}
      wincdir=%{buildroot}%{mingw64_includedir}
      peformat=pei-x86-64
      ;;
  esac
  wbindir=%{buildroot}$wbin_rel

  # PE format, split debuginfo, and no GNU runtime or unwinder imports.
  # Capture first: under "if" a crashed objdump counts as pattern-absent.
  $t-objdump -f $wbindir/zlib1.dll | grep -q "file format $peformat"
  $t-objdump -h $wbindir/zlib1.dll | grep -q '\.gnu_debuglink'
  test -f %{buildroot}%{_prefix}/lib/debug$wbin_rel/zlib1.dll.debug
  imports=$($t-objdump -p $wbindir/zlib1.dll | grep 'DLL Name' || :)
  echo "$t zlib1.dll imports: $imports"
  if echo "$imports" | grep -qiE 'libgcc|libssp|libunwind'; then
    echo "ERROR: $t zlib1.dll imports a GNU runtime or unwinder DLL" >&2
    exit 1
  fi

  # Shared and static links through the supplement drivers.
  $t-clang -isystem $wincdir $wincheck/t.c -L$wlibdir -lz -o $wincheck/t-$t.exe
  $t-objdump -f $wincheck/t-$t.exe | grep -q "file format $peformat"
  $t-objdump -p $wincheck/t-$t.exe | grep -i 'zlib1.dll'

  $t-clang -isystem $wincdir $wincheck/t.c -L$wlibdir \
      -Wl,-Bstatic -lz -Wl,-Bdynamic -o $wincheck/t-static-$t.exe
  imports=$($t-objdump -p $wincheck/t-static-$t.exe)
  if echo "$imports" | grep -qi 'zlib1.dll'; then
    echo "ERROR: the $t static link imports zlib1.dll" >&2
    exit 1
  fi
done
rm -rf "$wincheck"


# Win32
%files -n mingw32-zlib
%{mingw32_includedir}/zconf.h
%{mingw32_includedir}/zlib.h
%{mingw32_libdir}/libz.dll.a
%{mingw32_bindir}/zlib1.dll
%{mingw32_libdir}/pkgconfig/zlib.pc
%{mingw32_libdir}/cmake/zlib/

%files -n mingw32-zlib-static
%{mingw32_libdir}/libz.a

# Win64
%files -n mingw64-zlib
%{mingw64_includedir}/zconf.h
%{mingw64_includedir}/zlib.h
%{mingw64_libdir}/libz.dll.a
%{mingw64_bindir}/zlib1.dll
%{mingw64_libdir}/pkgconfig/zlib.pc
%{mingw64_libdir}/cmake/zlib/

%files -n mingw64-zlib-static
%{mingw64_libdir}/libz.a

# UCRT64
%files -n ucrt64-zlib
%{ucrt64_includedir}/zconf.h
%{ucrt64_includedir}/zlib.h
%{ucrt64_libdir}/libz.dll.a
%{ucrt64_bindir}/zlib1.dll
%{ucrt64_libdir}/pkgconfig/zlib.pc
%{ucrt64_libdir}/cmake/zlib/

%files -n ucrt64-zlib-static
%{ucrt64_libdir}/libz.a

# Windows on ARM64
%files -n ucrtarm64-zlib
%{ucrtarm64_includedir}/zconf.h
%{ucrtarm64_includedir}/zlib.h
%{ucrtarm64_libdir}/libz.dll.a
%{ucrtarm64_bindir}/zlib1.dll
%{ucrtarm64_libdir}/pkgconfig/zlib.pc
%{ucrtarm64_libdir}/cmake/zlib/

%files -n ucrtarm64-zlib-static
%{ucrtarm64_libdir}/libz.a


%changelog
* Mon Aug 24 2026 Erik Berg <fedora@slipsprogrammor.no> - 1.3.2-2.2
- Build the win32 and win64 targets with the clang supplement drivers:
  the qemu-ga MSI ships DLLs from clang/compiler-rt toolchain sysroots,
  where the GNU runtime DLLs do not exist
- New checks assert the x86 DLLs import no libgcc, libssp or libunwind,
  and link a zlib consumer through the same drivers

* Thu Aug 06 2026 Erik Berg <fedora@slipsprogrammor.no> - 1.3.2-2.1
- Add zlib for the Windows on ARM64 target

* Thu Jul 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Sun Mar 01 2026 Sandro Mani <manisandro@gmail.com> - 1.3.2-1
- Update to 1.3.2

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.1-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Thu Jul 24 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Fri Jan 17 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Thu Jul 18 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Fri Mar 29 2024 Jonathan Schleifer <js@nil.im> - 1.3.1-2
- Build UCRT64 package

* Wed Jan 31 2024 Sandro Mani <manisandro@gmail.com> - 1.3.1-1
- Update to 1.3.1

* Thu Jan 25 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.13-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sun Jan 21 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.13-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Thu Jul 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.13-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.13-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Tue Dec 13 2022 Sandro Mani <manisandro@gmail.com> - 1.2.13-1
- Update to 1.2.13

* Thu Jul 21 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.12-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Thu Jun 30 2022 Sandro Mani <manisandro@gmail.com> - 1.2.12-1
- Update to 1.2.12

* Fri Mar 25 2022 Sandro Mani <manisandro@gmail.com> - 1.2.11-8
- Rebuild with mingw-gcc-12

* Thu Jan 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.11-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Thu Jul 22 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.11-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.11-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Thu Nov 12 2020 Sandro Mani <manisandro@gmail.com> - 1.2.11-4
- Drop minizip subpackages, it's a separate package now

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.11-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Tue Aug 13 2019 Marc-André Lureau <marcandre.lureau@redhat.com> - 1.2.11-1
- Update to 1.2.11

* Tue Aug 06 2019 Thomas Sailer <t.sailer@alumni.ethz.ch> - 1.2.8-12
- update pkgconf file version to 1.2.8

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.8-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Fri Feb 01 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.8-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.8-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Thu Feb 08 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.8-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.8-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.8-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.8-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.8-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat Jul 13 2013 Erik van Pienbroek <epienbro@fedoraproject.org> - 1.2.8-1
- Update to 1.2.8

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Nov 22 2012 Erik van Pienbroek <epienbro@fedoraproject.org> - 1.2.7-1
- Update to 1.2.7

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.5-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat Mar 10 2012 Erik van Pienbroek <epienbro@fedoraproject.org> - 1.2.5-10
- Added win64 support
- Simplified the build process by using autotools and a hacked version of libtool
- Made the package compliant with the new MinGW packaging guidelines

* Tue Mar 06 2012 Kalev Lember <kalevlember@gmail.com> - 1.2.5-9
- Renamed the source package to mingw-zlib (#800415)
- Use mingw macros without leading underscore

* Mon Feb 27 2012 Kalev Lember <kalevlember@gmail.com> - 1.2.5-8
- Remove the .la files
- Spec clean up

* Mon Feb 27 2012 Erik van Pienbroek <epienbro@fedoraproject.org> - 1.2.5-7
- Rebuild against the mingw-w64 toolchain
- Use the correct RPM macros
- Fix FTBFS against the latest binutils caused by the use of an invalid .def file

* Fri Feb 17 2012 David Tardon <dtardon@redhat.com> - 1.2.5-6
- fix dlname in libz.la

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.5-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue May 10 2011 Kalev Lember <kalev@smartlink.ee> - 1.2.5-4
- Use the built .pc file instead of manually generating it

* Tue Apr 26 2011 Kalev Lember <kalev@smartlink.ee> - 1.2.5-3
- Install zlib pkgconfig file

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sun Sep 12 2010 Erik van Pienbroek <epienbro@fedoraproject.org> - 1.2.5-1
- Update to 1.2.5
- Use %%global instead of %%define
- Automatically generate debuginfo subpackage
- Use correct %%defattr tag
- Merged the changes from the native Fedora package

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.3-19
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Fri Jun 12 2009 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-18
- Cannot copy current directory into itself, so fix the copy command
  which creates 'x' subdirectory.

* Fri May  1 2009 Thomas Sailer <t.sailer@alumni.ethz.ch> - 1.2.3-17
- BR autoconf, automake, libtool

* Thu Apr 30 2009 Thomas Sailer <t.sailer@alumni.ethz.ch> - 1.2.3-16
- use autotools build system from native package

* Tue Mar  3 2009 W. Pilorz <wpilorz at gmail.com> - 1.2.3-15
- Add static subpackage.

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.3-14
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Fri Feb 20 2009 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-13
- Rebuild for mingw32-gcc 4.4

* Mon Jan 19 2009 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-12
- Force rebuild to test maintenance account.

* Thu Dec 18 2008 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-11
- Pass correct CFLAGS to build.

* Thu Oct 16 2008 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-10
- Consider native patches.

* Wed Sep 24 2008 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-9
- Rename mingw -> mingw32.

* Sun Sep 21 2008 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-8
- Remove manpage.

* Wed Sep 10 2008 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-7
- Remove static library.

* Fri Sep  5 2008 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-5
- Fix misnamed file: zlibdll.a -> zlib.dll.a
- Explicitly provide mingw(zlib1.dll).

* Thu Sep  4 2008 Richard W.M. Jones <rjones@redhat.com> - 1.2.3-3
- Initial RPM release, largely based on earlier work from several sources.
