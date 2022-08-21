# Goat

## Getting started

To reproduce the experiments, a Linux system with Make and Docker CLI (latest version) installed is required.

Running machine must have 32GB RAM (minimum)/64GB RAM (recommended) and 4 cores.

## Reproducing experimental results

For a complete run of Goat on all benchmarks:
```bash
make benchmark
```

To reproduce the `etcd` blocking error presented in the paper:
```bash
make etcd-bug
```

Experimental results can be found [here](https://docs.google.com/spreadsheets/d/1_0yMuIeBI74ZfFfMeClED_extz-FjSUFU9vE-Z5ifWw/edit?usp=sharing "Experimental result sheet").

## Interactive Goat

The interactive Goat client is a containerized application that allows running Goat on individual packages in benchmarks.

To run the interactive Goat:
```bash
make interactive
```

### Example interactive session

When the prompt shows, list packages in the `etcd` repository:
```bash
>: list etcd
```

All `etcd` packages that may be analyzed are listed line by line:
```bash
...
go.etcd.io/etcd/pkg/v3/pbutil
go.etcd.io/etcd/pkg/v3/proxy # Package with etcd bug presented in the paper
go.etcd.io/etcd/pkg/v3/report
go.etcd.io/etcd/pkg/v3/schedule
...
```

Run it:
```bash
>: run go.etcd.io/etcd/pkg/v3/proxy
```
Progress will be monitored and displayed in the console.

The results will be:
```bash
Bugs found:
etcd/pkg/proxy/server_test.go:120:10
etcd/pkg/proxy/server_test.go:193:2
etcd/pkg/proxy/server_test.go:242:2
etcd/pkg/proxy/server_test.go:252:9
etcd/pkg/proxy/server_test.go:288:2
etcd/pkg/proxy/server_test.go:323:2
etcd/pkg/proxy/server_test.go:359:2
etcd/pkg/proxy/server_test.go:369:9
etcd/pkg/proxy/server_test.go:409:2
etcd/pkg/proxy/server_test.go:439:2
etcd/pkg/proxy/server_test.go:516:2
etcd/pkg/proxy/server_test.go:84:2
```

Close interactive Goat:
```bash
>: exit
```