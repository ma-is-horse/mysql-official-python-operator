#!/usr/bin/env bash
set -euo pipefail

# 使用传入的第一个参数作为 tag，如果未提供则使用默认值
tag="${1:-mabing1027}"

#docker buildx build -f Dockerfile.mine.dev -t "release-ci.daocloud.io/demo/community-operator:${tag}" . --push

docker build -f Dockerfile.mine.dev -t "release.daocloud.io/demo/community-operator:8.3.0-2.1.2-${tag}" --build-arg BASE_VERSION=8.3.0-2.1.2 . --push