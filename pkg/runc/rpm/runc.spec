%global debug_package %{nil}

Name: runc
Version: %{_version}
Release: %{_release}%{?dist}
Source0: runc.tgz
Summary: CLI for running Open Containers
License: ASL 2.0
URL: https://github.com/opencontainers/runc
Vendor: Docker
Packager: Docker <support@docker.com>

# container-selinux isn't a thing in suse flavors
%if %{undefined suse_version}
# amazonlinux2 doesn't have container-selinux either
%if "%{?dist}" != ".amzn2"
Requires: container-selinux >= 2:2.74
%endif
Requires: libseccomp
%else
# SUSE flavors do not have container-selinux,
# and libseccomp is named libseccomp2
Requires: libseccomp2
%endif
BuildRequires: make
BuildRequires: gcc
BuildRequires: libtool-ltdl-devel
BuildRequires: libseccomp-devel

%description
Open Container Project - runtime
"runc" is a command line client for running applications packaged according
to the Open Container Format (OCF) and is a compliant implementation of
the Open Container Project specification.

%prep
%setup -q -c -n src -a 0

%build
mkdir -p /go/src/github.com/opencontainers
rm -f /go/src/github.com/opencontainers/runc
ln -snf ${RPM_BUILD_DIR}/src/runc /go/src/github.com/opencontainers/runc
pushd /go/src/github.com/opencontainers/runc
GO111MODULE=auto make BINDIR="bin" VERSION=%{_origversion} COMMIT=%{_commit} runc install
GO111MODULE=auto make man
popd

%install
# install binary
install -d ${RPM_BUILD_ROOT}%{_bindir}
install -p -m 755 runc/bin/runc ${RPM_BUILD_ROOT}%{_bindir}/runc

# add bash, zsh, and fish completions
install -d ${RPM_BUILD_ROOT}%{_datadir}/bash-completion/completions
install -p -m 644 runc/contrib/completions/bash/runc ${RPM_BUILD_ROOT}%{_datadir}/bash-completion/completions/runc

# install manpages
install -d ${RPM_BUILD_ROOT}%{_mandir}/man8
install -p -m 644 runc/man/man8/*.8 ${RPM_BUILD_ROOT}%{_mandir}/man8

mkdir -p build-docs
for runc_file in LICENSE MAINTAINERS NOTICE README.md; do
    cp "runc/$runc_file" "build-docs/$runc_file"
done

%files
%doc build-docs/LICENSE build-docs/MAINTAINERS build-docs/NOTICE build-docs/README.md
%{_bindir}/runc
%{_datadir}/bash-completion/completions/runc
%doc
%{_mandir}/man8/*

%changelog
