# Copyright 2022 Docker Packaging authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

include ../../common/vars.mk

# https://github.com/opencontainers/runc/blob/main/Dockerfile#L1
export GO_VERSION = 1.19

DESTDIR ?= $(BASEDIR)/bin
BAKE_DEFINITIONS ?= -f docker-bake.hcl -f ../../common/packages.hcl

export RUNC_REPO := $(if $(RUNC_REPO),$(RUNC_REPO),https://github.com/opencontainers/runc.git)
export RUNC_REF := $(if $(RUNC_REF),$(RUNC_REF),main)

export PKG_DEB_REVISION = 1

PKG_LIST ?= deb rpm static
# supported platforms: https://github.com/opencontainers/runc/blob/main/Makefile#L71
# FIXME: add linux/ppc64le when a remote PowerPC instance is available (too slow with QEMU)
PKG_PLATFORMS ?= linux/amd64 linux/arm/v6 linux/arm/v7 linux/arm64 linux/s390x

.PHONY: default
default: pkg ;

.PHONY: metadata
metadata:
	docker buildx bake metadata

include ../../common/packages.mk
include ../../common/build.mk
