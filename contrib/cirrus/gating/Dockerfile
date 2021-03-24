FROM registry.fedoraproject.org/fedora:33

RUN dnf -y install golang \
			make \
			git \
			golang \
			python3-requests \
			python3-requests-mock \
			python3-coverage \
			python3-pylint \
			python3-fixtures \
			podman \
			&& \
			dnf -y clean all
