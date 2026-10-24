# Free downloadable toolkit for technical and creative projects

This toolkit uses free local software and documented MCP/API/CLI interfaces.
No hosted subscription is required. The catalog records source links, model and
asset license exceptions, prerequisites and account setup. Software and bridges
are separate installations; detection does not prove that a bridge is running.

| Project work | Free software to obtain | Model-accessible interface |
|---|---|---|
| Project files, Git, web research | Python, Node, uv/uvx, Git; self-hosted SearXNG | Filesystem/Git/Fetch/Memory/Time MCPs; JSON search API |
| Browser apps and testing | Chrome/Chromium or Edge, Node | Playwright MCP; Chrome DevTools MCP for Chrome |
| 2D and 3D games | Godot, Blender, Tiled, LibreSprite | Godot MCP, Blender MCP, engine/editor CLIs and file formats |
| Browser games | Phaser, Three.js, Babylon.js, PixiJS | JavaScript SDKs plus browser MCP testing |
| 3D art, animation and rendering | Blender; local TripoSR or TRELLIS where hardware permits | Blender MCP/bpy/CLI; local model pipelines, with submodule license review for TRELLIS |
| Vector and raster graphics | Inkscape, Krita, GIMP, ImageMagick, Pillow | Inkscape/Krita community MCPs, Python plugins, SVG/CLI/image APIs |
| Music, speech and sound | LMMS, MuseScore Studio, Audacity 3.x, FluidSynth, Hydrogen; ACE-Step, Kokoro, whisper.cpp | Audacity MCP; MIDI/MusicXML/CLI; local inference; Tone.js/jsfxr/Mido for procedural audio |
| Video and recording | FFmpeg, Kdenlive, OBS Studio | FFmpeg/ffprobe CLI, project render tooling, OBS MCP/WebSocket v5 |
| Documents and spreadsheets | LibreOffice, Pandoc, python-docx, openpyxl | LibreOffice UNO/headless CLI; document SDKs; no Microsoft Office license needed |
| CAD and engineering | FreeCAD, OpenSCAD, KiCad | FreeCAD MCP/Python, OpenSCAD CLI, KiCad MCP and version-specific CLI/Python/IPC |
| Maps and scientific visualization | QGIS, ParaView, JupyterLab | QGIS MCP/PyQGIS, pvpython/pvbatch, local notebooks |
| Databases and retrieval | SQLite, PostgreSQL, MySQL Community | SQL/Python APIs and DBHub MCP with scoped database access |
| Local inference and generation | Ollama, llama.cpp, LM Studio, ComfyUI; Transformers/ONNX Runtime/PyTorch | Loopback APIs and local SDKs; select weights with suitable licenses |
| Development environments | VS Code, .NET SDK, uv, Ruff, Podman | MCP client, compiler/test CLIs, Python package tools and local containers |

Start small: use the hub, filesystem/Git/Fetch, one browser bridge and the
specific creative app needed for the project. Enable additional servers only
when their tools are useful. Multiple bridges can expose hundreds of tool
schemas, so route by capability and retrieve setup/context on demand.

```powershell
python communication_hub.py --agent codex free-tools --downloadable-only --limit 100
python communication_hub.py --agent codex free-tools --kind mcp --limit 100
python communication_hub.py --agent codex free-tool godot-app
python communication_hub.py --agent codex free-tool godot-mcp
python communication_hub.py --agent codex scan-local-tools
python communication_hub.py --agent codex free-tools --all --installed-only --limit 100
```

Use each entry's official download/repository link. This package does not ship
third-party installers, model weights or assets and does not install them.
Windows MCP clients may need an absolute executable path; exported Node recipes
use npx.cmd on Windows. Pin reviewed package releases before activation.

Unity's community MCP is free, but Unity Personal eligibility is conditional,
so it appears with `--all`. FL Studio, Microsoft Office and WolframScript
installation records do not establish free licenses. Free local alternatives
are listed above. MusicGen/AudioGen weights, Freesound API access and the hosted
Open-Meteo free endpoint have noncommercial restrictions. LinkedIn supports
approved OAuth permissions rather than unrestricted free people search.

All manual keys, OAuth and local password steps are in [CREDENTIALS.md](CREDENTIALS.md).
Detailed primary sources and restrictions are in [FREE_TOOLS.md](FREE_TOOLS.md).
