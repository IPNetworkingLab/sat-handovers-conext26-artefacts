# Artefacts of the paper "Paving the Way for Link-State Routing in Satellite Networks with Fast and Seamless Ground Station Handovers"

This repository contains the artefacts of the paper ["Paving the Way for Link-State Routing in Satellite Networks with Fast and Seamless Ground Station Handovers"](https://doi.org/10.1145/3856972) to be presented at [CoNEXT'26](https://conferences.sigcomm.org/co-next/2026/#!/home).

## How to use this repository?

First, clone it from GitHub:

```console
$ git clone https://github.com/IPNetworkingLab/sat-handovers-conext26-artefacts.git
```

Second, make sure to point to the correct version and initialise the submodules:
```console
$ cd sat-handovers-conext26-artefacts
$ git checkout conext26
$ git submodule update --init --recursive
```

The repository is structured as follows:

```text
.
├── README.md
├── kepler
├── no_delay
│   ├── iris2
│   │   └── toolchain_params.toml
│   ├── leo
│   │   └── toolchain_params.toml
│   ├── scn
│   │   └── toolchain_params.toml
│   └── starlink
│       └── toolchain_params.toml
├── scripts
│   ├── main.py
│   ├── plot_utils.py
│   ├── requirements.txt
│   └── sim.py
├── toolchain
│   ├── Cargo.lock
│   ├── Cargo.toml
│   ├── LICENSE
│   ├── README.md
│   ├── constellation
│   ├── constellation-builder
│   ├── constellation-code
│   ├── convergence-simulator
│   ├── handover-filter
│   └── toolchain
│       ├── Cargo.toml
│       └── src
└── topos
    ├── iris2.yaml
    ├── leo.yaml
    ├── scn.yaml
    └── starlink.yaml
```

The [`toolchain`](toolchain) sub-module contains the toolchain as described in Section 6.1 of the paper.
Its [dedicated README](https://github.com/IPNetworkingLab/sat-handovers-conext26-toolchain/blob/328f5503c27080b061cb8f542bfeb90124d3b904/README.md) describes in detail the role and structure of the `kepler`, `no_delay` and `topos` directories.

The [`scripts`](scripts) directory contains Python plotting scripts.

To ensure reproducible results, we provide a `Dockerfile` to build the toolchain and run the plotting scripts from within a container.
To build the container, run:

```console
$ docker build --build-arg UID=$(id -u) -t sat-toolchain .
```

The container takes approximatively 5 min to build and weighs around 1.5GB.

Simulating all the handovers is quite resource-intensive, so one could prefer [producing the plots from the provided raw data](#producing-the-plots-from-provided-raw-data).
The toolchain can of course [reproduce the paper's results from scratch](#producing-the-plots-from-scratch).

## Producing the plots from provided raw data

1. The first step is fetching the compressed raw artefacts from the [dedicated Zenodo record](https://doi.org/10.5281/zenodo.23243267).

> Note: The compressed archive weighs 705MB; the download may take some time depending on the connection speed.

The `sha256` hash of the archive is `71e4dbbf508ecc401aaa5573c8e115d73bda2a573712e6143a3b2e4d519f7aa7`. 

> WARNING: Decompressing the archive produces 21752 files for a total weight of 8.3GB.

2. Now, decompress the archive with:

```console
$ tar xjf raw.tar.bz2
```

This operation may take around 2 to 3 minutes.

This step populates the directories `no_delay/<topo>/{topology,simulation}` and `kepler`.
It also produces the files `no_delay/<topo>/stats.json`.

3. Execute the plotting script with:

```console
$ docker run -v ./no_delay:/build/no_delay -it sat-toolchain:latest scripts/env/bin/python3 scripts/main.py no_delay
``` 

This command takes around 5 min to execute and should produce the following files in the `no_delay` directory:

- [`events_duration.pdf`](no_delay/events_duration.pdf), which is Figure 3 of the paper.
- [`nesting.pdf`](no_delay/nesting.pdf), which is Figure 7 of the paper.
- [`loops.pdf`](no_delay/loops.pdf), which is Figure 8 of the paper.
- [`convergence.pdf`](no_delay/convergence.pdf), which is Figure 9 of the paper.

During execution, the plotting script logs, for each handover in each constellation, the nodes that did not trigger FIB updates due the handover.
They correspond to the negative FIB overhead discussed in Section 6.2 and shown in Figure 9.

## Producing the plots from scratch

> CAUTION: It is not recommended to run the following commands on a laptop.
> Simulations are very resource intensive and should be run on servers or virtual machines with high cores/threads counts.
> For reference, the original results were produced on an Ampere Altra server featuring 160 cores.
> The RAM usage is pretty low, i.e., below 8GB; a few gigabytes is largely sufficient, except for the Starlink shell, which requires around 52GB of RAM.
>
> Researchers who do not have access to such resources may reserve servers on [Cloudlab](https://www.cloudlab.us/) or [Grid5000](https://www.grid5000.fr/w/Grid5000:Home), two initiatives that provide access to hardware resources for research purpose.
>
> For reference, the following table summarises the simulations' duration with the bare-metal toolchain for each topology on our 160-cores server.
> The runtime FIB checks were configured, as specified in the paper, according to the values in the `toolchain_params.toml` files provided with this repository.

| Topology | Kepler step | Simulations | FIB Checks |
| -------- | ----------- | ----------- | ---------- |
| scn      | 2min40      | 7min        | on         |
| iris2    | 3min        | 1h07        | on         |
| leo      | 3min40      | 2h20        | on         |
| starlink | 13min10     | 2h46        | off        |

> *Note on the containerised toolchain.*
>
> We have noted that executing the toolchain in a container impacts performance.
> For example, computing the connectivity events for SCN-288 with the containerised toolchain takes around 12 min on a server with dual Intel(R) Xeon(R) CPU E5-2687W v3 (20 cores in total), against 8 min with the bare-metal version of the toolchain.
> Similarly, simulations for SCN-288 with the bare-metal toolchain take around 15 min to complete on the same server, while they did not terminate within 2 hours with the containerised toolchain.
>
> The main dependency to build the toolchain is `cargo`, which is easily installed with [`rustup`](https://rustup.rs/), the dedicated Rust installer.
> Hence, we recommand using the toolchain directly.
> 
> If the containerised toolchain is preferred, we recommand disabling the FIB checks in the `toolchain_params.toml` configuration file.
> The following table summarises the simulations' duration with the containerised toolchain for some topologies on the 20-cores server, with the FIB checks disabled.

| Topology | Kepler step | Simulations |
| -------- | ----------- | ----------- |
| scn      | 12min31     | 8min59      |
| iris2    | 12min6      | 2h17        |
| leo      | 17min40     | 2h30        |

Each topology can be simulated independently with:

```console
$ docker run -v ./topos:/build/topos -v ./kepler:/build/kepler -v ./no_delay:/build/no_delay -it sat-toolchain:latest ./toolchain -c no_delay/<topo>/toolchain_params.toml --no-cache -s
```

For example, for SCN-288:

```console
$ docker run -v ./topos:/build/topos -v ./kepler:/build/kepler -v ./no_delay:/build/no_delay -it sat-toolchain:latest ./toolchain -c no_delay/scn/toolchain_params.toml --no-cache -s
```

That command computes every possible connectivity event for an orbital period, determines a sequence of possible (maybe not optimal) connectivity events under hardware constraints, and simulates each handover for both synchronisation method specified in the paper.
The toolchain parameters are detailed in [the toolchain README](https://github.com/IPNetworkingLab/sat-handovers-conext26-toolchain/blob/328f5503c27080b061cb8f542bfeb90124d3b904/README.md).

The first progress bar represents the computation of every possible connectivity event for one orbital period, with a time step of one second.
The second bar measures the simulation's progress but does not work as expected. Even if the bar is stuck, the simulations make progress!

An alternate way to monitor the simulations progression is launching the following command in another terminal:

```console
$ watch -n 1 'ls no_delay/<topo>/simulation | wc -l'
```

> Note:
> The previous command may indicate that the `simulation` directory does not exist if it starts before the toolchain has dumped the first simulation file.
> Indeed, the toolchain creates the `simulation` directory on-the-fly, if needed.
> This error may be safely ignored.

The total number of handovers to be simulated is indicated in the second progress bar and should match the values shown in Table 1, Appendix C of the paper.

Once the raw simulation data are generated, the plots can be produced with:
```console
$ docker run -v ./no_delay:/build/no_delay -it sat-toolchain:latest scripts/env/bin/python3 scripts/main.py no_delay
```
