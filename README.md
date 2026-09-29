# MegameshCLI

Standalone C++17 command-line converter from glTF 2.0 (`.gltf`/`.glb`) meshes
to versioned, range-addressable MeshLoD (`.mlod`) containers. The companion
[Babylon Lite](https://github.com/CedricGuillemet/Babylon-Lite) runtime consumes
the containers; this repository builds and tests independently of Babylon Lite.

## Install and build

Download the archive matching your OS and CPU from
[Releases](https://github.com/CedricGuillemet/MegameshCLI/releases), extract it,
and run `bin/mesh-lod-tool` (`bin/mesh-lod-tool.exe` on Windows). Releases
contain macOS x64/arm64, Linux x64/arm64, and Windows x64 archives, plus
`SHA256SUMS.txt` for verifying downloaded archives (`sha256sum -c SHA256SUMS.txt`
on systems with `sha256sum`). Pull requests expose the same archives as CI
artifacts, without publishing a release.

To build from source, install CMake 3.24+ and a C++17 compiler; the first
configure fetches pinned meshoptimizer and cgltf revisions over the network.
On Linux/macOS, use a native compiler and Ninja:

```sh
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/mesh-lod-tool --version
```

On Windows x64, with Visual Studio 2022 and its C++ desktop workload:

```powershell
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
.\build\Release\mesh-lod-tool.exe --version
```

`cmake --install build --config Release --prefix <directory>` installs the
executable to `<directory>/bin`. No Babylon Lite checkout is needed.

## Convert and validate

```sh
mesh-lod-tool --input assets/harvard-yenching_institute_statue.glb --output statue.mlod --stats-json stats.json
mesh-lod-tool --input assets/harvard-yenching_institute_statue.glb --output check.mlod --validate-only
mesh-lod-tool --help
```

For one selected primitive the specified output filename is used. For multiple
primitives, each gets a sibling file with its zero-padded source indices:
`statue.mesh000.prim000.mlod`, `statue.mesh001.prim000.mlod`, and
`statue.mesh002.prim000.mlod` for the checked-in statue. The statistics JSON
reports `primitiveCount`, per-output mesh/primitive indices, page counts,
source triangle counts, and terminal coverage. `--mesh N` optionally selects a
mesh; `--primitive N` additionally selects one primitive from that mesh.
`--validate-only` runs conversion and internal container validation but does
not write containers (a requested `--stats-json` is still written).

All selected primitives are converted and validated in memory before output
publication. Output files are staged in sibling temporary files, then renamed
**individually**, not as a multi-file transaction: a filesystem error during
publication can leave earlier files in place. Existing output files may be
replaced; choose a dedicated output directory for important conversions.
Errors identify the input/resource or failed output path and return a nonzero
exit status.

## Architecture and format

`src/input.cpp` ingests glTF/GLB and resolves local resources;
`src/normalize.cpp` and `src/hierarchy.cpp` construct meshlets and the
simplification hierarchy; `src/page_packer.cpp` packs page data;
`src/mlod_writer.cpp` and `src/validator.cpp` serialize and validate the
container. `src/cli.cpp` and `src/native_filesystem.cpp` provide the CLI and
filesystem adapter. `include/mlod_format.h` defines the authoritative binary
layout: little-endian MLOD **1.0**, magic `MESHLOD\0`, a 256-byte header,
64-byte section-directory records, provenance, hierarchy, and 64-KiB-aligned
page data. Serve `.mlod` over HTTP with byte ranges and identity encoding;
re-encoding the response breaks the stored byte offsets.

The build pins meshoptimizer at
`f843aae0b3070306bd2aeef43ffcf09509fee526` and cgltf at
`85cd62382dfea638278962690cf515023f33ed00`. `--version` reports
the tool version, MLOD format, both dependency revisions, and the native
compiler target. The build fingerprint in each container hashes the
tool/format/dependency revisions and canonical conversion settings, **not**
the compiler target, host paths, or timestamps. Cross-platform byte-for-byte
identity is not asserted by the CI matrix.

## Included asset and attribution

`assets/harvard-yenching_institute_statue.glb` is the original
**Harvard-Yenching Institute statue** by **Alexandre Tokovinine**, licensed
under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
See [asset attribution](assets/ATTRIBUTION.md) for the original model link,
hash, and how to credit `.mlod` derivatives. The root Apache 2.0 `LICENSE`
applies to converter code, **not** the statue.

## Provenance and tests

Converter `CMakeLists.txt`, `cmake/`, `include/`, `src/`, and `tests/fixtures/`
were extracted from public
[`CedricGuillemet/Babylon-Lite` commit `d7b6f54ddd57b09f1198205b3cf870ff968fed24`](https://github.com/CedricGuillemet/Babylon-Lite/tree/d7b6f54ddd57b09f1198205b3cf870ff968fed24/mesh-lod-tool).
The GLB comes from that commit's repository root. Standalone packaging,
statue-based smoke coverage, and CI were adapted here. CTest covers the CLI,
conversion core, and MLOD layout; the additional `tests/verify_statue.py`
converts the included GLB and checks all three headers, statistics, naming,
and validate-only behavior. GitHub Actions runs both on native OS/CPU runners.
