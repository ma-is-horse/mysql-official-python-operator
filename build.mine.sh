#!/usr/bin/env bash
set -euo pipefail
tag=mabing1024-1
docker build -f Dockerfile.mine.dev -t release-ci.daocloud.io/demo/mgr-operator:${tag} . --push