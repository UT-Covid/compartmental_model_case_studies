PYTHON ?= python3
SRC_DIR ?= /covid-seir
PYTEST_DIR ?= $(SRC_DIR)/tests
PREF_SHELL ?= bash
GITREF=$(shell git rev-parse --short HEAD)
GITREF_FULL=$(shell git rev-parse HEAD)

####################################
# Docker image
####################################

IMAGE_ORG ?= enho
IMAGE_NAME ?= covid-seir
IMAGE_TAG ?= 1.3.0
IMAGE_DOCKER ?= $(IMAGE_ORG)/$(IMAGE_NAME):$(IMAGE_TAG)
IMAGE_DOCKER_DEV ?= $(IMAGE_ORG)/$(IMAGE_NAME):$(GITREF)
IMAGE_SIMG ?= $(IMAGE_ORG)-$(IMAGE_NAME)-$(IMAGE_TAG).simg
IMAGE_SIMG_DEV ?= $(IMAGE_ORG)-$(IMAGE_NAME)-$(GITREF).simg

####################################
# Runtime arguments
####################################

DOCKER_OPTS ?= --rm -v ${PWD}/outputs:$(SRC_DIR)/outputs \
	-v ${PWD}/inputs:$(SRC_DIR)/inputs \
	-e GITREF_FULL=$(GITREF_FULL)
SEIRCITY_CONFIG ?= src/SEIRcity/configs/example/example_simulate_one0.yaml
SEIRCITY_OUT_FP ?= outputs/example_simulate_one0.pckl
SEIRCITY_THREADS ?= 48
SEIRCITY_OPTS ?= --out-fp $(SEIRCITY_OUT_FP) \
	--config-yaml $(SEIRCITY_CONFIG) --threads $(SEIRCITY_THREADS)

####################################
# Sanity checks
####################################

PROGRAMS := git docker python poetry singularity
.PHONY: $(PROGRAMS)
.SILENT: $(PROGRAMS)

docker:
	docker info 1> /dev/null 2> /dev/null && \
	if [ ! $$? -eq 0 ]; then \
		echo "\n[ERROR] Could not communicate with docker daemon. You may need to run with sudo.\n"; \
		exit 1; \
	fi
python poetry singularity:
	$@ -h &> /dev/null; \
	if [ ! $$? -eq 0 ]; then \
		echo "[ERROR] $@ does not seem to be on your path. Please install $@"; \
		exit 1; \
	fi
git:
	$@ -h &> /dev/null; \
	if [ ! $$? -eq 129 ]; then \
		echo "[ERROR] $@ does not seem to be on your path. Please install $@"; \
		exit 1; \
	fi

####################################
# Build Docker image
####################################
.PHONY: image shell tests tests-pytest clean clean-image clean-tests
# .SILENT: image

requirements.txt: | poetry
	poetry export --without-hashes -f requirements.txt -o $@

requirements-dev.txt: | poetry
	poetry export --dev --without-hashes -f requirements.txt -o $@

image: ./Dockerfile requirements.txt | docker
	docker build --build-arg REQUIREMENTS=$(word 2,$^) \
		-t $(IMAGE_DOCKER) -f $< .

image-dev: ./Dockerfile requirements-dev.txt | docker
	docker build --build-arg REQUIREMENTS=$(word 2,$^) \
		-t $(IMAGE_DOCKER_DEV) -f $< .

deploy: image | docker
	docker push $(IMAGE_DOCKER)

deploy-dev: image-dev | docker
	docker push $(IMAGE_DOCKER_DEV)

####################################
# Tests in Docker container
####################################

shell: image | docker
	docker run --rm -it -v ${PWD}:/cwd $(IMAGE_DOCKER) bash

tests: tests-main

tests-main: image | docker
	docker run $(DOCKER_OPTS) $(IMAGE_DOCKER) \
		$(PYTHON) -m src.SEIRcity $(SEIRCITY_OPTS)

tests-fit: image | docker
	docker run $(DOCKER_OPTS) \
		$(IMAGE_DOCKER) \
		$(PYTHON) -m SEIRcity --out-fp outputs/single_scenario0.pckl \
		--config-yaml src/SEIRcity/configs/simulate_multiple/fit_to_data0.yaml \
		--threads 48

pytest: pytest-docker

pytest-docker: image-dev | docker
	docker run $(DOCKER_OPTS) \
		$(IMAGE_DOCKER_DEV) \
		$(PYTHON) -m pytest $(PYTEST_DIR) \
		-m 'not slow'

clean: clean-tests

clean-image:
	docker rmi -f $(IMAGE_DOCKER)

clean-tests:
	rm -rf .hypothesis .pytest_cache __pycache__ */__pycache__ \
		tmp.* *junit.xml local-mount *message_*_*.json logs/*.log \
		logs/*.o* logs/*.e*

####################################
# Build/test (Singularity)
####################################

$(IMAGE_SIMG): | singularity
	singularity pull $@ docker://$(IMAGE_DOCKER)

$(IMAGE_SIMG_DEV): | singularity
	singularity pull $@ docker://$(IMAGE_DOCKER_DEV)

tests-simg: | singularity
	singularity exec docker://$(IMAGE_DOCKER) \
		$(PYTHON) -m src.SEIRcity $(SEIRCITY_OPTS)

pytest-simg: | singularity
	PICKLE_RESULTS_FROM=multiple_serial \
		singularity exec docker://$(IMAGE_DOCKER_DEV) \
		$(PYTHON) -m pytest $(PYTEST_DIR)

####################################
# Jupyterhub
####################################
IMAGE_JHUB ?= $(IMAGE_ORG)/$(IMAGE_NAME):jhub

image-jhub: ./Dockerfile.jhub ./requirements-jhub.txt | docker
	docker build --build-arg REQUIREMENTS=$(word 2,$^) \
		-t $(IMAGE_JHUB) -f $< .

jhub: image-jhub | docker
	docker run -p 8888:8888 -v ${PWD}:/home/jovyan/work \
		$(IMAGE_JHUB)
