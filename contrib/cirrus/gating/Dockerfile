FROM registry.fedoraproject.org/fedora:31

RUN dnf -y install golang \
			make \
			git \
			golang \
			python3-coverage \
			python3-pylint && \
			dnf -y clean all
