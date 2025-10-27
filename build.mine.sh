#!/usr/bin/env bash
set -euo pipefail

# 使用传入的第一个参数作为 tag，如果未提供则使用默认值
tag="${1:-mabing1027}"

docker build -f Dockerfile.mine.dev -t "release-ci.daocloud.io/demo/mgr-operator:${tag}" . --push