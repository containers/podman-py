export GO111MODULE=off
export GOPROXY=https://proxy.golang.org


PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python || which python3)
DESTDIR ?= /
DESTDIR ?=
EPOCH_TEST_COMMIT ?= $(shell git merge-base $${DEST_BRANCH:-main} HEAD)
HEAD ?= HEAD

export PODMAN_VERSION ?= "5.2.0"

.PHONY: podman
podman:
	rm dist/* || :
	$(PYTHON) -m pip install --user -r requirements.txt
	PODMAN_VERSION=$(PODMAN_VERSION) \
	$(PYTHON) setup.py sdist bdist bdist_wheel

.PHONY: lint
lint: tox
	$(PYTHON) -m tox -e black,pylint

.PHONY: tests
tests: tox
	# see tox.ini for environment variable settings
	$(PYTHON) -m tox -e coverage,py39,py310,py311,py312,py313

.PHONY: unittest
unittest:
	coverage run -m unittest discover -s podman/tests/unit
	coverage report -m --skip-covered --fail-under=80 --omit=./podman/tests/* --omit=.tox/* --omit=/usr/lib/*

.PHONY: integration
integration:
	coverage run -m unittest discover -s podman/tests/integration
	coverage report -m --skip-covered --fail-under=80 --omit=./podman/tests/* --omit=.tox/* --omit=/usr/lib/*

.PHONY: tox
tox:
ifeq (, $(shell which dnf))
	brew install python@3.9 python@3.10 python@3.11 python@3.12 python@3.13
else
	-dnf install -y python3 python3.9 python3.10 python3.11 python3.12 python3.13
endif
	# ensure tox is available. It will take care of other testing requirements
	$(PYTHON) -m pip install --user tox

.PHONY: test-release
test-release: SOURCE = $(shell find dist -regex '.*/podman-[0-9][0-9\.]*.tar.gz' -print)
test-release:
	twine upload --verbose -r testpypi dist/*whl $(SOURCE)
	# pip install -i https://test.pypi.org/simple/ podman

.PHONY: release
release: SOURCE = $(shell find dist -regex '.*/podman-[0-9][0-9\.]*.tar.gz' -print)
release:
	twine upload --verbose dist/*whl $(SOURCE)
	# pip install podman

.PHONY: docs
docs:
	sphinx-apidoc --separate --no-toc --force --templatedir docs/source/_templates/apidoc \
		-o docs/source/ podman podman/tests

	# HARD CODED COMMAND from readthedocs! We must conform!
	# -T : traceback
	# -E : do not use saved environment, always read all files
	# -W : warnings reported as errors then --keep-going when getting warnings
	# -b html : build html
	# -d : path for cached environment and doctree files
	# -D language=en : define language as en
	# . : source directory
	# _build/html : target
	cd docs/source && python3 -m sphinx -T -E -W --keep-going -b html -d _build/doctrees -D language=en . _build/html

.PHONY: rpm
rpm: ## Build rpm packages
	rpkg local

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
	rm -rf podman_py.egg-info dist build/*
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
