PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python)
DESTDIR ?= /
export PODMAN_VERSION ?= '1.80'

.PHONY: podman-py
podman-py:
	PODMAN_VERSION=$(PODMAN_VERSION) \
	$(PYTHON) setup.py sdist bdist

.PHONY: env
env:
	dnf install python3-coverage -y
	dnf install pylint -y
	rpm -V python3-coverage pylint
	# -- or --
	# $(PYTHON) -m pip install coverage
.PHONY: lint
lint:
	$(PYTHON) -m pylint podman || exit $$(($$? % 4))

.PHONY: unittest
unittest:
	coverage run -m unittest discover -s test/unit
	coverage report -m --skip-covered --fail-under=50 --omit=./test/*

# .PHONY: integration
# integration:
# 	test/integration/test_runner.sh -v

# .PHONY: install
# install:
# 	$(PYTHON) setup.py install --root ${DESTDIR}

# .PHONY: upload
# upload: clean
# 	PODMAN_VERSION=$(PODMAN_VERSION) $(PYTHON) setup.py sdist bdist_wheel
# 	twine check dist/*
# 	twine upload --verbose dist/*
# 	twine upload --verbose dist/*

.PHONY: clobber
clobber: uninstall clean

.PHONY: uninstall
uninstall:
	$(PYTHON) -m pip uninstall --yes podman ||:

.PHONY: clean
clean:
	rm -rf podman.egg-info dist
	find . -depth -name __pycache__ -exec rm -rf {} \;
	find . -depth -name \*.pyc -exec rm -f {} \;
	$(PYTHON) ./setup.py clean --all
