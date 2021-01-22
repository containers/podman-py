FROM registry.fedoraproject.org/fedora:33

RUN dnf -y install golang \
			make \
			git \
			golang \
			python3-coverage \
			python3-pylint \
			python3-fixtures && \
			dnf -y clean all
