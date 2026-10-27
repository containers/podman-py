%global pypi_name podman
%global desc %{pypi_name} is a library of bindings to use the RESTful API for Podman.

%global pypi_dist 4

Name: python-%{pypi_name}
%if %{defined copr_username}
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
BuildRequires: pyproject-rpm-macros
Provides: %{pypi_name}-py = %{epoch}:%{version}-%{release}
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

%generate_buildrequires
%pyproject_buildrequires %{?with_tests:-t}

%build
export PBR_VERSION="0.0.0"
%pyproject_wheel

%install
export PBR_VERSION="0.0.0"
%pyproject_install
%pyproject_save_files %{pypi_name}

%check

%pyproject_extras_subpkg -n python%{python3_pkgversion}-%{pypi_name} progress_bar
%files -n python%{python3_pkgversion}-%{pypi_name} -f %{pyproject_files}
%license LICENSE
%doc README.md

%changelog
%autochangelog
