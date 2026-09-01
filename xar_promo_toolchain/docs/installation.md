# Installation and cross-machine delivery

This guide installs `xar-promo-toolchain` 0.1.0 into an isolated Python
environment on Windows, Linux, or macOS. Python 3.11 or later is required. The
core package has no mandatory third-party Python dependency; media, visual, and
live speech capabilities are opt-in.

The machine-readable version of this contract is installed as
`xar_promo/schemas/install-contract-v1.json`. It is part of both the wheel and
sdist and can be read through `importlib.resources` without a source checkout.

Version 0.1.0 is published as a signed-by-tag GitHub Release, but is **not
published to PyPI or another public Python index**. A command such as
`pip install xar-promo-toolchain` is therefore not an available distribution
path. Install the release wheel directly, install a downloaded local artifact,
or build from a reviewed trusted source checkout:

```text
python -m pip install https://github.com/XenoAmess/ck3_eternal_recurrence/releases/download/xar-promo-v0.1.0/xar_promo_toolchain-0.1.0-py3-none-any.whl
```

The repository workflow
[`promo-toolchain-release.yml`](../../.github/workflows/promo-toolchain-release.yml)
is a package release for the `xar-promo-v<version>` tag namespace (or an
artifact-only explicit manual run). It runs the package tests in normal and optimized
mode, builds the wheel and sdist, checks their metadata with `twine check`,
installs the wheel in a fresh environment, verifies the installed contract, and
uploads the two files plus `SHA256SUMS` as a GitHub Actions artifact. A tag run
also publishes those exact checked bytes as a GitHub Release; the workflow does
not publish to PyPI, upload a video, or launch CK3/FFmpeg. The workflow also checks the sdist member allowlist and
installs both artifacts in fresh environments before uploading them. The sdist
smoke installs a `setuptools>=77` wheel into its fresh environment and then uses
`--no-index --no-build-isolation`, proving that the checked source archive can
be installed without reaching a package index once its declared build backend
has been supplied.

The wheel can be byte-reproducible when the workflow's
`SOURCE_DATE_EPOCH` is held to the reviewed commit timestamp. With the current
setuptools backend, an sdist may still retain source-tree mtimes in tar members,
so its SHA-256 is an exact per-run record rather than a cross-run reproducibility
claim. The sdist content, metadata, and fresh-install gates above are the
release checks; do not reject an otherwise valid handoff solely because two
sdist runs have different digests.

The dependency-free core wheel is tagged `py3-none-any`: its Python code is
architecture-independent and supports Windows, Linux, and macOS when Python
3.11 or newer is available. That portability does not extend automatically to
optional dependency wheels or native tools. Obtain Pillow/other optional wheels
for the target OS, CPU architecture, and Python version, and obtain matching
FFmpeg/ffprobe executables for that target.

## 1. Create an isolated environment

Check the interpreter before creating the environment:

```powershell
# Windows PowerShell
py -0p
py -3 --version
py -3 -c "import sys; assert sys.version_info >= (3, 11), sys.version"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

`py -3` selects an installed Python 3 interpreter; the assertion prevents an
older one from being used. If several suitable versions are installed, an
explicit launcher tag such as `py -3.12` or `py -3.13` is equally valid.

If the PowerShell execution policy blocks activation, activation is optional:
run `.\.venv\Scripts\python.exe -m pip ...` and
`.\.venv\Scripts\xar-promo.exe ...` directly. In `cmd.exe`, activation is
`.venv\Scripts\activate.bat`.

```sh
# Linux or macOS
python3 --version
python3 -c "import sys; assert sys.version_info >= (3, 11), sys.version"
python3 -m venv .venv
. .venv/bin/activate
```

After activation, `python -c "import sys; assert sys.version_info >= (3, 11)"`
must exit zero. Keep one virtual environment per consumer project or deployment
so upgrades cannot silently alter another project's toolchain.

Upgrading pip is optional, not an installation prerequisite. On a connected
machine it may be done explicitly with `python -m pip install --upgrade pip`;
that command may contact a configured index and must not be run as part of an
offline procedure.

## 2. Choose an installation artifact

Prefer a local wheel whose SHA-256 was supplied independently by the trusted
artifact source. Check the received bytes before installation:

```powershell
# Windows PowerShell; compare the printed Hash with the independently supplied value
Get-FileHash -Algorithm SHA256 .\dist\xar_promo_toolchain-0.1.0-py3-none-any.whl
```

```sh
# Linux
sha256sum ./dist/xar_promo_toolchain-0.1.0-py3-none-any.whl

# macOS
shasum -a 256 ./dist/xar_promo_toolchain-0.1.0-py3-none-any.whl
```

Stop if the values differ. A digest detects changed transfer bytes; it does not
make an untrusted source trusted. If no independently delivered wheel digest is
available, review the trusted source revision, build locally, and record the
resulting digest before transferring the artifact.

### Wheel (recommended for transfer and offline use)

```powershell
python -m pip install .\dist\xar_promo_toolchain-0.1.0-py3-none-any.whl
```

```sh
python -m pip install ./dist/xar_promo_toolchain-0.1.0-py3-none-any.whl
```

The wheel contains the Python package, the console entry point, the two native
manifest schemas, the ZhongGuo phase-two capture-contract schema, and the
installation contract. It does not bundle FFmpeg,
ffprobe, a CK3 capture runner, a project composer, or a project integration
plugin.

### Source distribution

```powershell
python -m pip install .\dist\xar_promo_toolchain-0.1.0.tar.gz
```

```sh
python -m pip install ./dist/xar_promo_toolchain-0.1.0.tar.gz
```

Installing an sdist builds a wheel locally and therefore needs its declared
build dependency, `setuptools>=77`. On an offline target, prefer the prebuilt
wheel or include build requirements in the wheelhouse.

### Source checkout

Run these commands from the `xar_promo_toolchain` directory:

```sh
python -m pip install .
```

For toolchain development, use an editable install:

```sh
python -m pip install -e .
```

Editable installs execute the current checkout, so they are useful for tests
but are not immutable deployment artifacts. Build distributable artifacts with:

```sh
python -m pip install build
python -m build
```

Installing `build` may contact a configured package index. For an offline build,
obtain its wheel and all build requirements through the trusted wheelhouse
process instead; installing the already-built toolchain wheel needs no build
frontend.

The expected 0.1.0 outputs are
`dist/xar_promo_toolchain-0.1.0-py3-none-any.whl` and
`dist/xar_promo_toolchain-0.1.0.tar.gz`.

## 3. Install only the optional capabilities you need

The declared extras are:

| Extra | Python requirement | Enables | Runtime boundary |
| --- | --- | --- | --- |
| `tts` | `edge-tts==7.2.8` | Live Microsoft Edge TTS provider | Live synthesis may require network access |
| `visual` | `Pillow==12.3.0` | Raster visual-source operations | Local file and memory operations |
| `render` | `Pillow==12.3.0` | Raster rendering/layout operations | Local file and memory operations |

For a source checkout:

```sh
python -m pip install ".[tts,visual,render]"
```

For a local wheel or sdist, install the artifact first and then install the
exact optional requirements needed by that deployment:

```sh
python -m pip install ./dist/xar_promo_toolchain-0.1.0-py3-none-any.whl
python -m pip install "edge-tts==7.2.8" "Pillow==12.3.0"
```

This second command may contact the configured dependency index. It installs
the same pinned requirements declared by the `tts`, `visual`, and `render`
extras; it does not fetch the toolchain itself from a public index. Use the
wheelhouse procedure below when that network behavior is not allowed.

FFmpeg and ffprobe are native executables, not Python extras. Obtain binaries
for the target operating system from a trusted system/package distributor and
verify both commands:

```sh
ffmpeg -version
ffprobe -version
```

The `review` command takes the FFmpeg executable explicitly through `--ffmpeg`.
Create a review probe with the public `probe_and_write_bound_media` API and an
explicit ffprobe path. Project composers likewise own the exact executable
selection. Merely installing the Python package does not launch either program.

## 4. Prepare an offline wheelhouse

Build the wheel once, then prepare the wheelhouse on a connected machine with
the same target OS, CPU architecture, and Python minor version. This matters
because Pillow wheels are platform-specific.

Start from a trusted source checkout or a local wheel whose SHA-256 has already
been checked as described above. There is no public-index copy of version 0.1.0
for pip to download.

```powershell
New-Item -ItemType Directory -Force wheelhouse | Out-Null
Copy-Item .\dist\xar_promo_toolchain-0.1.0-py3-none-any.whl wheelhouse\
python -m pip download --dest wheelhouse "edge-tts==7.2.8" "Pillow==12.3.0"
```

```sh
mkdir -p wheelhouse
cp ./dist/xar_promo_toolchain-0.1.0-py3-none-any.whl wheelhouse/
python -m pip download --dest wheelhouse "edge-tts==7.2.8" "Pillow==12.3.0"
```

Transfer the whole directory, then install without index access:

```sh
python -m pip install --no-index --find-links ./wheelhouse \
  "xar-promo-toolchain[tts,visual,render]==0.1.0"
```

The distribution requirement in this command is resolved only from the local
wheelhouse because `--no-index` is mandatory. Verify the transferred wheel's
SHA-256 again on the target before running it.

If only the dependency-free core is needed, the toolchain wheel alone is
sufficient. If an sdist must be built offline, also place wheels satisfying
`setuptools>=77` in the wheelhouse and use
`--no-index --find-links ./wheelhouse`; the prebuilt wheel remains the simpler
and more reproducible offline path. FFmpeg/ffprobe must be transferred and
installed separately according to the target operating system's policy.

## 5. Verify the installed contract

First verify both public launch paths and the installed resources:

```sh
xar-promo --version
python -m xar_promo --version
python -c "from importlib.resources import files; root=files('xar_promo').joinpath('schemas'); names=('install-contract-v1.json','promo-project-config-v1.schema.json','promo-run-manifest-v1.schema.json','phase2-capture-contract-v1.schema.json'); missing=[name for name in names if not root.joinpath(name).is_file()]; raise SystemExit('missing installed resources: '+','.join(missing) if missing else 0)"
```

Both version commands must print `xar-promo 0.1.0`. Verify all ten commands on
Windows PowerShell:

```powershell
$commands = 'init','start-run','validate','preserve','signoff','plan','build','audit','review','export'
foreach ($command in $commands) {
    & xar-promo $command --help
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
```

On Linux or macOS:

```sh
for command in init start-run validate preserve signoff plan build audit review export; do
  xar-promo "$command" --help || exit 1
done
```

These checks do not create or mutate a promo project, contact a network, or
launch media processes. Python may create its normal bytecode cache. To inspect
the exact machine contract installed in the environment:

```sh
python -c "from importlib.resources import files; print(files('xar_promo').joinpath('schemas/install-contract-v1.json').read_text(encoding='utf-8'))"
```

The JSON contract carries the canonical command list, dependency/extras map,
artifact names, verification argv, and side-effect boundaries. Automation
should parse that resource instead of scraping this Markdown file.

## 6. CK3 adapter and project preset boundaries

The installed package contains reusable CK3 capture-verification code. That
adapter is read-only: it validates an already-produced capture bundle and does
not launch CK3, record the desktop, drive input, repair evidence, or interpret
OCR. A CK3 acceptance/capture runner remains an upstream producer.

Project policy is a separate layer. A project preset may define chapter order,
voice, subtitles, visual identity, duration, real-character requirements, and
release gates. A project composer wires the adapter, preset, TTS provider, and
media executables into a concrete pipeline. Those project components are not
created by installing the generic package.

`xar-promo init` writes neutral scaffold IDs, `adapter=generic` and
`preset=default`. They are not bundled production components. Before running
`plan`, `build`, or `audit`, install the project's integration plugin, replace
those IDs with the plugin's actual IDs, and provide its documented
`--composer MODULE:ATTRIBUTE`. Integration packages register callables in the
`xar_promo.adapters` and `xar_promo.presets` Python entry-point groups. A
successful ten-command help check proves the generic installation, not that a
particular CK3/project integration is installed or release-ready.

## 7. Upgrade, pin, and uninstall

Upgrade from a new wheel while keeping the environment isolated:

```sh
python -m pip install --upgrade ./dist/xar_promo_toolchain-NEW_VERSION-py3-none-any.whl
xar-promo --version
```

Verify the new wheel against the independently supplied SHA-256 before this
command. Do not substitute a package-name-only public-index install unless a
future release explicitly documents an authenticated index publication.

For an editable checkout, switch to the intended reviewed revision and rerun
`python -m pip install -e .`. For reproducible deployments, record the wheel's
SHA-256 outside the wheelhouse and pin the toolchain plus all selected extras.
Re-run every verification command after an upgrade; a version bump may also
introduce a new machine-contract version.

Uninstall the distribution from the active environment:

```sh
python -m pip uninstall xar-promo-toolchain
```

Uninstalling removes installed package files and the console shim. It does not
delete promo projects, run manifests, retained artifacts, review packages,
FFmpeg/ffprobe, pip caches, or a separately installed integration plugin. Remove
those only under their own retention and uninstall policies.

## Common errors

### `Python 3.11 or later is required`

The shell selected an older interpreter. Recreate the virtual environment with
an installed `py -3.11`, `py -3.12`, or newer launcher tag on Windows, or an
explicit Python 3.11/newer executable on POSIX, then run pip through that
environment's `python -m pip`.

### `xar-promo` is not recognized or `command not found`

Activate the intended virtual environment, or invoke its console script by
absolute path. `python -m xar_promo --help` is the portable fallback and also
helps detect a PATH problem rather than a missing package.

### `No module named xar_promo`

The active interpreter is not the one where pip installed the wheel. Compare
`python -c "import sys; print(sys.executable)"` with
`python -m pip --version`, then reinstall through that exact interpreter.

### `No matching distribution found` during offline installation

The wheelhouse is incomplete or contains a dependency wheel for another OS,
CPU, or Python version. Rebuild it for the target and keep `--no-index` so the
offline boundary is explicit. Core-only installation needs only the universal
toolchain wheel.

### `ffmpeg` or `ffprobe` cannot be executed

They are not installed by pip. Verify the native executable directly, then pass
its absolute path to the review command or project composer. On Windows, quote
paths containing spaces.

### Adapter or preset ID is not found

The generic package is installed but the project integration entry point is
not. Install the integration plugin in the same virtual environment and inspect
the available `xar_promo.adapters` and `xar_promo.presets` entry points. Do not
use the neutral `generic/default` scaffold IDs for a production build.

### Live Edge TTS fails while offline

The `tts` extra installs the provider but cannot make a network-dependent live
service offline. Use a project-supported cache/offline mode with already
retained audio, or run live synthesis on a connected machine and preserve its
outputs. Do not treat installation success as provider availability.

### Schema or version verification fails after an upgrade

The console shim and imported package may come from different environments, or
old files may remain in an editable checkout. Run `python -m xar_promo --version`,
inspect `python -m pip show xar-promo-toolchain`, reinstall the intended
artifact, and repeat the resource check before using an existing project.
