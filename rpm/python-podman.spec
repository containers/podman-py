# copr_username is only set on copr environments, not on others like koji
# This is used to set custom epoch value for builds on coprs owned by
# rhcontainerbot.
%if "%{?copr_username}" != "rhcontainerbot"
%bcond_with copr
%else
%bcond_without copr
%endif

# RHEL 8 envs can't use autochangelog yet,
# has slightly different python deps
# and also doesn't support generate_buildrequires.
%if !0%{?fedora} && 0%{?rhel} <= 8
%bcond_without changelog
%bcond_without rhel8_py
%else
%bcond_with changelog
%bcond_with rhel8_py
%endif

%global pypi_name podman
%global desc %{pypi_name} is a library of bindings to use the RESTful API for Podman.

%global pypi_dist 4

Name: python-%{pypi_name}
%if %{with copr}
Epoch: 102
%else
Epoch: 3
%endif
# DO NOT TOUCH the Version string!
# The TRUE source of this specfile is:
# https://github.com/containers/podman/blob/main/rpm/python-podman.spec
# If that's what you're reading, Version must be 0, and will be updated by Packit for
# copr and koji builds.
# If you're reading this on dist-git, the version is automatically filled in by Packit.
Version: 0
License: Apache-2.0
Release: %autorelease
Summary: RESTful API for Podman
URL: https://github.com/containers/%{pypi_name}-py
# Tarball fetched from upstream
Source0: %{url}/archive/v%{version}.tar.gz
BuildArch: noarch

%description
%desc

%package -n python%{python3_pkgversion}-%{pypi_name}
BuildRequires: git-core
BuildRequires: python%{python3_pkgversion}-devel
BuildRequires: python%{python3_pkgversion}-requests
%if %{with rhel8_py}
BuildRequires: python%{python3_pkgversion}-devel
BuildRequires: python%{python3_pkgversion}-rpm-macros
BuildRequires: python%{python3_pkgversion}-pytoml
Requires: python%{python3_pkgversion}-pytoml
%else
BuildRequires: pyproject-rpm-macros
BuildRequires: python%{python3_pkgversion}-toml
Requires: python%{python3_pkgversion}-toml
%endif
Requires: python%{python3_pkgversion}-requests
Provides: %{pypi_name}-py = %{version}-%{release}
Provides: python%{python3_pkgversion}dist(%{pypi_name}) = %{pypi_dist}
Provides: python%{python3_version}dist(%{pypi_name}) = %{pypi_dist}
Obsoletes: python%{python3_pkgversion}-%{pypi_name}-api <= 0.0.0-1
Provides: python%{python3_pkgversion}-%{pypi_name}-api = %{epoch}:%{version}-%{release}
Summary: %{summary}
%{?python_provide:%python_provide python%{python3_pkgversion}-%{pypi_name}}

%description -n python%{python3_pkgversion}-%{pypi_name}
%desc

%prep
%autosetup -Sgit -n %{pypi_name}-py-%{version}

%if %{without rhel8_py}
%generate_buildrequires
%pyproject_buildrequires %{?with_tests:-t}
%endif

%build
export PBR_VERSION="0.0.0"
%if %{with rhel8_py}
%py3_build
%else
%pyproject_wheel
%endif

%install
export PBR_VERSION="0.0.0"
%if %{with rhel8_py}
%py3_install
%else
%pyproject_install
%pyproject_save_files %{pypi_name}
%endif

%if %{with rhel8_py}
%files -n python%{python3_pkgversion}-%{pypi_name}
%dir %{python3_sitelib}/%{pypi_name}-*-py%{python3_version}.egg-info
%{python3_sitelib}/%{pypi_name}-*-py%{python3_version}.egg-info/*
%dir %{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}/*
%else
%files -n python%{python3_pkgversion}-%{pypi_name} -f %{pyproject_files}
%endif
%license LICENSE
%doc README.md

%changelog
%if %{with changelog}
* Mon May 01 2023 RH Container Bot <rhcontainerbot@fedoraproject.org>
- Placeholder changelog for envs that are not autochangelog-ready
%else
%autochangelog
%endif
