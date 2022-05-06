#!/bin/bash

echo "Building GOAT and reproducing etcd bug..."

go run Goat -pset 1 -fun go.etcd.io/etcd/pkg/v3/proxy.TestServer_PauseTx -gopath external/gfuzz -modulepath external/gfuzz/etcd/pkg -include-tests -metrics -task collect-primitives go.etcd.io/etcd/pkg/v3/proxy