#
#  $Id$
#
# The version used to be passed from build.xml. It's hardcoded here
# the build system generally passes --define "version X" to rpmbuild.
%{!?version:%define version 1.3.10}
# The release number is set to 0 unless overridden
%{!?releasenumber:%define releasenumber 0}
# The install prefix becomes $SENTINEL_HOME in the finished package
%{!?sentinelinstprefix:%define sentinelinstprefix /opt/sentinel}
# The path where the repositories will live 
%{!?sentinelrepoprefix:%define sentinelrepoprefix /opt/sentinel/repositories}

# Description
%{!?_name:%define _name "opennms"}
%{!?_descr:%define _descr "OpenNMS"}
%{!?packagedir:%define packagedir %{_name}-%version-%{releasenumber}}

%{!?_java:%define _java jre-1.8.0}

%{!?extrainfo:%define extrainfo }
%{!?extrainfo2:%define extrainfo2 }
%{!?skip_compile:%define skip_compile 0}
%{!?enable_snapshots:%define enable_snapshots 1}

# keep RPM from making an empty debug package
%define debug_package %{nil}
# don't do a bunch of weird redhat post-stuff  :)
%define _use_internal_dependency_generator 0
%define __os_install_post %{nil}
%define __find_requires %{nil}
%define __perl_requires %{nil}
%global _binaries_in_noarch_packages_terminate_build 0
AutoReq: no
AutoProv: no

%define with_tests  0%{nil}

Name:          %{_name}-sentinel
Summary:       OpenNMS Sentinel
Release:       %releasenumber
Version:       %version
License:       LGPL/AGPL
Group:         Applications/System
BuildArch:     noarch

Source:        %{_name}-source-%{version}-%{releasenumber}.tar.gz
URL:           http://www.opennms.org/wiki/Sentinel
BuildRoot:     %{_tmppath}/%{name}-%{version}-root

Requires(pre): %{name}-features-default = %{version}-%{release}
Requires:      %{name}-features-default = %{version}-%{release}

Prefix:        %{sentinelinstprefix}

%description
OpenNMS Sentinel is a container for horizontally-scalable telemetry
processing.

http://www.opennms.org/wiki/Sentinel

%{extrainfo}
%{extrainfo2}

%package container
Summary:       Sentinel Container
Group:         Applications/System
Requires:      openssh
Requires(pre): %{_java}
Requires:      %{_java}
Requires(pre): /usr/bin/getent
Requires(pre): /usr/sbin/groupadd
Requires(pre): /usr/sbin/useradd
Requires(pre): /sbin/nologin
Requires:      /sbin/nologin
Requires:      /usr/bin/id
Requires:      /usr/bin/sudo

%description container
Sentinel Container

%{extrainfo}
%{extrainfo2}

%package features-core
Summary:        Sentinel Core Features
Group:          Applications/System
Requires(pre):  %{name}-container = %{version}-%{release}
Requires:       %{name}-container = %{version}-%{release}
Requires(post): util-linux
Requires:       util-linux

%description features-core
Sentinel Core Features

%{extrainfo}
%{extrainfo2}

%package features-default
Summary:       Sentinel Default Features
Group:         Applications/System
Requires(pre): %{name}-features-core = %{version}-%{release}
Requires:      %{name}-features-core = %{version}-%{release}

%description features-default
Sentinel Default Features

%{extrainfo}
%{extrainfo2}

%prep

tar zxf %{_sourcedir}/%{_name}-source-%{version}-%{release}.tar.gz -C "%{_builddir}"
%define setupdir %{packagedir}

%setup -D -T -n %setupdir

%build

rm -rf %{buildroot}

%install

export EXTRA_ARGS=""
if [ "%{enable_snapshots}" = 1 ]; then
	EXTRA_ARGS="-s"
fi

tools/packages/sentinel/create-sentinel-assembly.sh $EXTRA_ARGS

# Extract the sentinel assembly
mkdir -p %{buildroot}%{sentinelinstprefix}
tar zxf %{_builddir}/%{_name}-%{version}-%{release}/opennms-assemblies/sentinel/target/org.opennms.assemblies.sentinel-*-sentinel.tar.gz -C %{buildroot}%{sentinelinstprefix} --strip-components=1

# Remove extraneous directories that start with "d"
rm -rf %{buildroot}%{sentinelinstprefix}/{data,debian,demos}

# fix the init script for RedHat/CentOS layout
mkdir -p "%{buildroot}%{_initrddir}"
sed -e "s,^SYSCONFDIR[ \t]*=.*$,SYSCONFDIR=%{_sysconfdir}/sysconfig,g" -e "s,^SENTINEL_HOME[ \t]*=.*$,SENTINEL_HOME=%{sentinelinstprefix},g" "%{buildroot}%{sentinelinstprefix}/etc/sentinel.init" > "%{buildroot}%{_initrddir}"/sentinel
chmod 755 "%{buildroot}%{_initrddir}"/sentinel
rm -f '%{buildroot}%{sentinelinstprefix}/etc/sentinel.init'

# move sentinel.conf to the sysconfig dir
install -d -m 755 %{buildroot}%{_sysconfdir}/sysconfig
mv "%{buildroot}%{sentinelinstprefix}/etc/sentinel.conf" "%{buildroot}%{_sysconfdir}/sysconfig/sentinel"

# container package files
find %{buildroot}%{sentinelinstprefix} ! -type d | \
    grep -v %{sentinelinstprefix}/bin | \
    grep -v %{sentinelrepoprefix} | \
    grep -v %{sentinelinstprefix}/etc/featuresBoot.d | \
    sed -e "s|^%{buildroot}|%attr(644,sentinel,sentinel) |" | \
    sort > %{_tmppath}/files.container
find %{buildroot}%{sentinelinstprefix}/bin ! -type d | \
    sed -e "s|^%{buildroot}|%attr(755,sentinel,sentinel) |" | \
    sort >> %{_tmppath}/files.container
# Exclude subdirs of the repository directory
find %{buildroot}%{sentinelinstprefix} -type d | \
    grep -v %{sentinelrepoprefix}/ | \
    sed -e "s,^%{buildroot},%dir ," | \
    sort >> %{_tmppath}/files.container

%clean
rm -rf %{buildroot}

%files
%defattr(664 root root 775)

%files container -f %{_tmppath}/files.container
%defattr(664 sentinel sentinel 775)
%attr(755,sentinel,sentinel) %{_initrddir}/sentinel
%attr(644,sentinel,sentinel) %config(noreplace) %{_sysconfdir}/sysconfig/sentinel
%attr(644,sentinel,sentinel) %{sentinelinstprefix}/etc/featuresBoot.d/.readme

%pre container
ROOT_INST="${RPM_INSTALL_PREFIX0}"
[ -z "${ROOT_INST}" ] && ROOT_INST="%{sentinelinstprefix}"

getent group sentinel >/dev/null || groupadd -r sentinel
getent passwd sentinel >/dev/null || \
	useradd -r -g sentinel -d "${ROOT_INST}" -s /sbin/nologin \
	-c "OpenNMS Sentinel" sentinel
exit 0

%post container
ROOT_INST="${RPM_INSTALL_PREFIX0}"
[ -z "${ROOT_INST}" ] && ROOT_INST="%{sentinelinstprefix}"

# Clean out the data directory
rm -rf "${ROOT_INST}/data"
# Generate an SSH key if necessary
if [ ! -f "${ROOT_INST}/etc/host.key" ]; then
    /usr/bin/ssh-keygen -t rsa -N "" -b 4096 -f "${ROOT_INST}/etc/host.key"
    chown sentinel:sentinel "${ROOT_INST}/etc/"host.key*
fi

%files features-core
%defattr(644 sentinel sentinel 755)
%{sentinelrepoprefix}/core

%post features-core
ROOT_INST="${RPM_INSTALL_PREFIX0}"
[ -z "${ROOT_INST}" ] && ROOT_INST="%{sentinelinstprefix}"

# Remove the directory used as the local Maven repo cache
rm -rf "${ROOT_INST}/repositories/.local"

%files features-default
%defattr(644 sentinel sentinel 755)
%{sentinelrepoprefix}/default

%post features-default
# Remove the directory used as the local Maven repo cache
rm -rf %{sentinelrepoprefix}/.local

%preun -p /bin/bash container
ROOT_INST="${RPM_INSTALL_PREFIX0}"
[ -z "${ROOT_INST}" ] && ROOT_INST="%{sentinelinstprefix}"

if [ "$1" = 0 ] && [ -x "%{_initrddir}/sentinel" ]; then
	%{_initrddir}/sentinel stop || :
fi

%postun -p /bin/bash container
ROOT_INST="${RPM_INSTALL_PREFIX0}"
[ -z "${ROOT_INST}" ] && ROOT_INST="%{sentinelinstprefix}"

if [ "$1" = 0 ] && [ -n "${ROOT_INST}" ] && [ -d "${ROOT_INST}" ]; then
	rm -rf "${ROOT_INST}" || echo "WARNING: failed to delete ${ROOT_INST}. You may have to clean it up yourself."
fi
