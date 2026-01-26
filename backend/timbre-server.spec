# PyInstaller build for the packaged server.
#
# onedir rather than onefile: onefile unpacks ~280 MB to a temp directory on
# every launch, which adds seconds to startup and leaves debris when the
# process is killed. The shell ships the directory as a sidecar instead.
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = [], [], []

# These carry compiled extensions and data files that PyInstaller's static
# analysis cannot see from imports alone.
for package in ("faster_whisper", "ctranslate2", "av", "tokenizers", "onnxruntime"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden


hiddenimports += collect_submodules("uvicorn")
hiddenimports += ["app.main"]

a = Analysis(
    ["server.py"],
    pathex=["."],
    binaries=binaries,
    # The built SPA travels with the server: in a packaged run there is no
    # repository next to it to read from.
    datas=datas + [("app", "app"), ("../frontend/dist", "frontend")],
    hiddenimports=hiddenimports,
    # sympy arrives through onnxruntime and is 55 MB of symbolic maths this app
    # never evaluates. tkinter and matplotlib are pulled in the same way.
    excludes=["sympy", "tkinter", "matplotlib", "IPython", "pytest", "ruff"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="timbre-server",
    console=True,
    strip=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="timbre-server",
)
