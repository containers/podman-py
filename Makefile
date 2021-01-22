export GO111MODULE=off
export GOPROXY=https://proxy.golang.org


PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python)
DESTDIR ?= /
DESTDIR ?=
EPOCH_TEST_COMMIT ?= $(shell git merge-base $${DEST_BRANCH:-master} HEAD)
HEAD ?= HEAD

export PODMAN_VERSION ?= '1.80'

.PHONY: podman-py
podman-py: env
	PODMAN_VERSION=$(PODMAN_VERSION) \
	$(PYTHON) setup.py sdist bdist

.PHONY: env
env:
	dnf install python3-coverage python3-pylint python3-requests python3-requests-mock python3-fixtures -y
	# -- or --
	# $(PYTHON) -m pip install tox
	# -- or --
.PHONY: lint
lint:
	$(PYTHON) -m pylint podman || exit $$(($$? % 4));

.PHONY: unittest
unittest:
	coverage run -m unittest discover -s podman/tests/unit
	coverage report -m --skip-covered --fail-under=80 --omit=./podman/tests/* --omit=.tox/* --omit=/usr/lib/*

# .PHONY: integration
# integration:
# 	test/integration/test_runner.sh -v

# .PHONY: install
HEAD ?= HEAD
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

.PHONY: validate
validate: .gitvalidation lint

.PHONY: .gitvalidation
.gitvalidation:
	# I have no great ideas on how to install/check for git-validation
	@echo "Validating vs commit '$(call err_if_empty,EPOCH_TEST_COMMIT)'"
	GIT_CHECK_EXCLUDE="./vendor:docs/make.bat" git-validation -run DCO,short-subject,dangling-whitespace -range $(EPOCH_TEST_COMMIT)..$(HEAD)
