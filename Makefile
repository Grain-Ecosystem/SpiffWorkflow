NAME=SpiffWorkflow
VERSION=`python setup.py --version`
PREFIX=/usr/local/
BIN_DIR=$(PREFIX)/bin
SITE_DIR=$(PREFIX)`python -c "import sys; from distutils.sysconfig import get_python_lib; print get_python_lib()[len(sys.prefix):]"`
SITE_DIR=build
V=`python setup.py --version`

###################################################################
# Standard targets.
###################################################################
.PHONY : clean
clean:
	find . -name "*.pyc" -o -name "*.pyo" | xargs -rn1 rm -f
	find . -name "*.egg-info" | xargs -rn1 rm -r
	rm -Rf build

.PHONY : dist-clean
dist-clean: clean
	rm -Rf dist

install:
	mkdir -p $(SITE_DIR)
	./version.sh $V
	export PYTHONPATH=$(SITE_DIR):$(PYTHONPATH); \
	python setup.py install --prefix $(PREFIX) \
		                    --install-scripts $(BIN_DIR) \
		                    --install-lib $(SITE_DIR)
	./version.sh --reset

uninstall:
	# Sorry, Python's distutils support no such action yet.

.PHONY : tests
tests:
	cd tests/$(NAME)
	PYTHONPATH=../.. python -m unittest discover -v . "*Test.py"

.PHONY : tests-cov
tests-cov:
	cd tests/$(NAME)
	coverage run --source=$(NAME) -m unittest discover -v . "*Test.py"

.PHONY : tests-ind
tests-ind:
	cd tests/$(NAME)
	@PYTHONPATH=../.. find . -name "*Test.py" -printf '%p' -exec python -m unittest {} \;

.PHONY : tests-timing
tests-timing:
	@make tests-ind 2>&1 | ./scripts/test_times.py

###################################################################
# Package builders.
###################################################################
targz: clean
	./version.sh $V
	python setup.py sdist --formats gztar
	./version.sh --reset

tarbz: clean
	./version.sh $V
	python setup.py sdist --formats bztar
	./version.sh --reset

wheel: clean
	./version.sh $V
	python setup.py bdist_wheel --universal
	./version.sh --reset

deb: clean
	./version.sh $V
	debuild -S -sa
	cd ..; sudo pbuilder build $(NAME)_$(VERSION)-0ubuntu1.dsc; cd -
	./version.sh --reset

dist: targz tarbz wheel
