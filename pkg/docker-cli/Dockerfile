# syntax=docker/dockerfile:1

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

ARG XX_VERSION="1.6.1"
ARG DEBIAN_FRONTEND="noninteractive"

# https://github.com/docker/cli/blob/master/Dockerfile#L9
ARG GOVERSIONINFO_VERSION="v1.4.1"

ARG DISTRO_NAME="debian12"
ARG DISTRO_TYPE="deb"
ARG DISTRO_RELEASE="debian"
ARG DISTRO_ID="12"
ARG DISTRO_SUITE="bookworm"
ARG DISTRO_IMAGE="debian:bookworm"

ARG PKG_NAME="docker-ce-cli"
ARG PKG_REPO="https://github.com/docker/cli.git"
ARG PKG_REF="master"

ARG GO_IMAGE="golang"
ARG GO_VERSION="1.24.3"
ARG GO_IMAGE_VARIANT="bookworm"

# stage used as named context that mounts hack/scripts
# see pkg target in docker-bake.hcl
FROM scratch AS scripts

# cross compilation helper
FROM --platform=$BUILDPLATFORM tonistiigi/xx:${XX_VERSION} AS xx

# osxcross contains the MacOSX SDK for xx
FROM dockercore/golang-cross:xx-sdk-extras AS osxsdk

# go base image to retrieve /usr/local/go
FROM ${GO_IMAGE}:${GO_VERSION}-${GO_IMAGE_VARIANT} AS go
FROM --platform=$BUILDPLATFORM ${GO_IMAGE}:${GO_VERSION}-${GO_IMAGE_VARIANT} AS gocross

# src
FROM --platform=$BUILDPLATFORM alpine AS src-base
RUN apk add --no-cache bash curl file git zip tar

FROM src-base AS src
WORKDIR /src
ARG PKG_REPO
RUN git init . && git remote add origin "${PKG_REPO}"
ARG PKG_REF
RUN git fetch origin "${PKG_REF}" +refs/heads/*:refs/remotes/origin/* +refs/tags/*:refs/tags/* && git checkout -q FETCH_HEAD

FROM src-base AS src-tgz
RUN --mount=from=src,source=/src,target=/cli \
    mkdir /out && tar -C / -zcf /out/cli.tgz --exclude .git cli

# metadata
FROM src-base AS metadata-builder
ARG PKG_REPO
ARG PKG_REF
ARG NIGHTLY_BUILD
RUN --mount=type=bind,from=scripts,source=gen-ver.sh,target=/usr/local/bin/gen-ver \
    --mount=type=bind,from=src,source=/src,target=/src <<EOT
  set -e
  mkdir -p /out
  for l in $(gen-ver "/src"); do
    export "${l?}"
  done
  cat > "/out/metadata.env" <<-EOF
REPO=${PKG_REPO%.*}
REF=${PKG_REF}
VERSION=${GENVER_VERSION}
COMMIT=${GENVER_COMMIT}
EOF
EOT

FROM scratch AS metadata
COPY --from=metadata-builder /out /

# deb
FROM ${DISTRO_IMAGE} AS builder-deb
COPY --from=xx / /
ARG DEBIAN_FRONTEND
ENV GOPROXY="https://proxy.golang.org|direct"
ENV GOPATH="/go"
ENV GOTOOLCHAIN="local"
ENV GO111MODULE="off"
ENV PATH="$PATH:/usr/local/go/bin:$GOPATH/bin"
ARG DISTRO_NAME
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils bash ca-certificates curl devscripts equivs git
RUN <<EOT
  set -e
  case "$DISTRO_NAME" in
    ubuntu2204|ubuntu2404)
      if [ "$(dpkg-divert --truename /usr/bin/man)" = "/usr/bin/man.REAL" ]; then
        rm -f /usr/bin/man
        dpkg-divert --quiet --remove --rename /usr/bin/man
      fi
      ;;
  esac
EOT
COPY deb /root/package/debian
ARG TARGETPLATFORM
RUN mk-build-deps -t "xx-apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends -y" -i /root/package/debian/control
WORKDIR /root/package
ARG NIGHTLY_BUILD
ARG DISTRO_RELEASE
ARG DISTRO_ID
ARG DISTRO_SUITE
ARG PKG_NAME
ARG PKG_REF
ARG PKG_PACKAGER
ARG PKG_DEB_BUILDFLAGS
ARG PKG_DEB_REVISION
ARG PKG_DEB_EPOCH
ARG SOURCE_DATE_EPOCH
RUN --mount=type=bind,source=scripts/pkg-deb-build.sh,target=/usr/local/bin/pkg-deb-build \
    --mount=type=bind,from=scripts,source=gen-ver.sh,target=/usr/local/bin/gen-ver \
    --mount=type=bind,from=scripts,source=gen-deb-changelog.sh,target=/usr/local/bin/gen-deb-changelog \
    --mount=type=bind,from=scripts,source=fix-cc.sh,target=/usr/local/bin/fix-cc \
    --mount=type=bind,from=src,source=/src,target=/root/package/cli,rw \
    --mount=type=bind,from=go,source=/usr/local/go,target=/usr/local/go \
    OUTDIR=/out SRCDIR=/root/package/cli pkg-deb-build

# rpm
FROM ${DISTRO_IMAGE} AS builder-rpm
COPY --from=xx / /
ENV GOPROXY="https://proxy.golang.org|direct"
ENV GOPATH="/go"
ENV GOTOOLCHAIN="local"
ENV GO111MODULE="off"
ENV PATH="$PATH:/usr/local/go/bin:$GOPATH/bin"
ARG DISTRO_NAME
RUN --mount=type=bind,from=scripts,source=rpm-init.sh,target=/usr/local/bin/rpm-init \
    --mount=type=secret,id=RH_USER,env=RH_USER \
    --mount=type=secret,id=RH_PASS,env=RH_PASS \
    rpm-init $DISTRO_NAME
COPY rpm /root/rpmbuild/SPECS
ARG TARGETPLATFORM
RUN --mount=type=bind,from=scripts,source=rpm-builddep.sh,target=/usr/local/bin/rpm-builddep \
    rpm-builddep $(xx-info rhel-arch) /root/rpmbuild/SPECS
WORKDIR /root/rpmbuild
ARG NIGHTLY_BUILD
ARG DISTRO_RELEASE
ARG DISTRO_ID
ARG DISTRO_SUITE
ARG PKG_NAME
ARG PKG_REF
ARG PKG_PACKAGER
ARG PKG_RPM_BUILDFLAGS
ARG PKG_RPM_RELEASE
ARG SOURCE_DATE_EPOCH
RUN --mount=type=bind,source=scripts/pkg-rpm-build.sh,target=/usr/local/bin/pkg-rpm-build \
    --mount=type=bind,from=scripts,source=gen-ver.sh,target=/usr/local/bin/gen-ver \
    --mount=type=bind,from=scripts,source=fix-cc.sh,target=/usr/local/bin/fix-cc \
    --mount=type=bind,from=src-tgz,source=/out/cli.tgz,target=/root/rpmbuild/SOURCES/cli.tgz \
    --mount=type=bind,from=src,source=/src,target=/usr/local/src/cli \
    --mount=type=bind,from=go,source=/usr/local/go,target=/usr/local/go \
    OUTDIR=/out SRCDIR=/usr/local/src/cli pkg-rpm-build

# static
FROM --platform=$BUILDPLATFORM ${DISTRO_IMAGE} AS build-base-static
COPY --from=xx / /
ARG DEBIAN_FRONTEND
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates file git zip tar
ENV GOPROXY="https://proxy.golang.org|direct"
ENV GOPATH="/go"
ENV PATH="$PATH:/usr/local/go/bin:$GOPATH/bin"
ENV CGO_ENABLED="0"
ENV GOTOOLCHAIN="local"
ENV GO111MODULE="off"

FROM build-base-static AS goversioninfo
ARG GOVERSIONINFO_VERSION
RUN --mount=type=bind,from=gocross,source=/usr/local/go,target=/usr/local/go,rw \
    GOBIN=/out GO111MODULE=on go install "github.com/josephspurrier/goversioninfo/cmd/goversioninfo@${GOVERSIONINFO_VERSION}"

FROM build-base-static AS builder-static-nosdk
ARG DEBIAN_FRONTEND
RUN apt-get install -y --no-install-recommends dpkg-dev clang lld llvm make pkg-config
ARG PKG_NAME
ARG PKG_REF
ARG NIGHTLY_BUILD
WORKDIR /build
ARG TARGETPLATFORM
RUN xx-apt-get install -y gcc libc6-dev
RUN --mount=type=bind,source=scripts/pkg-static-build.sh,target=/usr/local/bin/pkg-static-build \
    --mount=type=bind,from=scripts,source=gen-ver.sh,target=/usr/local/bin/gen-ver \
    --mount=type=bind,from=scripts,source=fix-cc.sh,target=/usr/local/bin/fix-cc \
    --mount=type=bind,from=src,source=/src,target=/go/src/github.com/docker/cli,rw \
    --mount=type=bind,from=gocross,source=/usr/local/go,target=/usr/local/go,rw \
    --mount=type=bind,from=goversioninfo,source=/out/goversioninfo,target=/usr/bin/goversioninfo \
    --mount=type=tmpfs,target=/go/src/github.com/docker/cli/winresources \
    OUTDIR=/out BUILDDIR=/build SRCDIR=/go/src/github.com/docker/cli pkg-static-build
FROM builder-static-nosdk AS builder-static-linux
FROM builder-static-nosdk AS builder-static-windows

FROM build-base-static AS builder-static-darwin
ARG DEBIAN_FRONTEND
RUN apt-get install -y --no-install-recommends dpkg-dev clang lld llvm make pkg-config
ARG PKG_NAME
ARG PKG_REF
ARG NIGHTLY_BUILD
WORKDIR /build
ARG TARGETPLATFORM
RUN xx-apt-get install -y gcc libc6-dev
RUN --mount=type=bind,source=scripts/pkg-static-build.sh,target=/usr/local/bin/pkg-static-build \
    --mount=type=bind,from=scripts,source=gen-ver.sh,target=/usr/local/bin/gen-ver \
    --mount=type=bind,from=scripts,source=fix-cc.sh,target=/usr/local/bin/fix-cc \
    --mount=type=bind,from=src,source=/src,target=/go/src/github.com/docker/cli,rw \
    --mount=type=bind,from=gocross,source=/usr/local/go,target=/usr/local/go,rw \
    --mount=type=bind,from=goversioninfo,source=/out/goversioninfo,target=/usr/bin/goversioninfo \
    --mount=from=osxsdk,target=/xx-sdk,src=/xx-sdk \
    --mount=type=tmpfs,target=/go/src/github.com/docker/cli/winresources \
    OUTDIR=/out BUILDDIR=/build SRCDIR=/go/src/github.com/docker/cli pkg-static-build

FROM builder-static-$TARGETOS AS builder-static

FROM builder-${DISTRO_TYPE} AS build-pkg
ARG BUILDKIT_SBOM_SCAN_STAGE=true

FROM scratch AS pkg
COPY --from=build-pkg /out /
