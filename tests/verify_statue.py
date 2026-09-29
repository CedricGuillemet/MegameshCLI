"""Exercise the distributed CLI against the checked-in three-mesh GLB."""

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


def run(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return result.stdout


def main() -> None:
    tool = str(Path(sys.argv[1]).resolve())
    asset = Path(sys.argv[2]).resolve()
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    assert digest == "cf7d1539ed700b05455fb7c3d2bcb62b27500189ac24e42a816ee2c99e5b6f86", digest

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        output = root / "statue.mlod"
        stats = root / "stats.json"
        stdout = run(tool, "--input", str(asset), "--output", str(output), "--stats-json", str(stats))
        metadata = json.loads(stats.read_text(encoding="utf-8"))
        assert metadata["primitiveCount"] == 3, metadata
        assert len(metadata["outputs"]) == 3, metadata
        assert not output.exists()

        expected_triangles = (98366, 119201, 93519)
        for mesh, triangles in enumerate(expected_triangles):
            item = metadata["outputs"][mesh]
            assert (item["meshIndex"], item["primitiveIndex"]) == (mesh, 0), item
            assert item["sourceTriangleCount"] == item["terminalCoverage"] == triangles, item
            assert item["pageCount"] > 0 and item["pinnedPageCount"] > 0, item
            path = root / f"statue.mesh{mesh:03d}.prim000.mlod"
            assert path.is_file() and path.stat().st_size > 256, path
            with path.open("rb") as file:
                header = file.read(256)
            assert header[:8] == b"MESHLOD\0", path
            assert struct.unpack_from("<HH", header, 8) == (1, 0), path
            assert struct.unpack_from("<Q", header, 56)[0] == path.stat().st_size, path
            assert struct.unpack_from("<I", header, 144)[0] == mesh, path
            assert struct.unpack_from("<Q", header, 152)[0] == triangles, path
            assert f"wrote {path}" in stdout, stdout

        assert len(list(root.glob("*.mlod"))) == 3
        validate = root / "validate.mlod"
        run(tool, "--input", str(asset), "--output", str(validate), "--validate-only")
        assert not list(root.glob("validate*.mlod"))
    print("Harvard statue: 3 valid MLOD 1.0 outputs, statistics, and validate-only passed")


if __name__ == "__main__":
    main()
