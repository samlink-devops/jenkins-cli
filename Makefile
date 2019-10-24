VERSION := $(shell cat version)
ARTIFACT_ID := jenkins-cli
NAME := $(ARTIFACT_ID)-$(VERSION)

all:	clean libs package

clean:
	rm -rf libs
	rm -rf dist

test:
	echo "No tests implemented"

compile:	libs
	echo "Nothing to compile"

libs:
	pip install -r requirements.txt --system -t libs

package:
	rm -rf dist
	mkdir -p dist/$(NAME)
	cp -R src/* dist/$(NAME)
	cp -R libs/* dist/$(NAME)
	tar -czf dist/$(NAME).tar.gz -C dist $(NAME)
