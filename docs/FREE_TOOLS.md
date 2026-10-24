# Free tools, APIs and MCP research

Research date: 2026-10-10 UTC (2026-10-09 America/Los_Angeles).

Default discovery includes only no-card local/self-hosted/public/recurring-free access and clearly flagged noncommercial free paths. Trials, required payment methods, retired services, paid APIs and unverified existing licenses are excluded. Free software does not include hardware/electricity, unlimited hosted quota, every model license or every asset's rights. No paid fallback, automatic signup, download, installation or external call is performed by the catalog.

The catalog is embedded in communication_hub.py and available through list_free_tools/get_free_tool, MCP resources and the dashboard. It is evidence-backed metadata and setup recipes, not a promise that external services are connected or tested on this machine. Hosted limits and licenses must be checked again when activating a service.

## Use from any project

```powershell
python communication_hub.py --agent codex free-tools --category games
python communication_hub.py --agent codex free-tools --kind mcp
python communication_hub.py --agent codex free-tools --downloadable-only
python communication_hub.py --agent codex free-tools --all --installed-only
python communication_hub.py --agent codex free-tool blender-mcp
python communication_hub.py --agent codex scan-local-tools
python communication_hub.py --agent codex local-tools
python communication_hub.py --agent codex credential-requirements --limit 100
```

Use --commercial-only for entries whose reviewed licenses allow commercial use without separate model/asset/eligibility review. Use --all to see conditional entries and exclusions. A registry/PATH match means an app is detected; it does not mean a server is installed, running or compatible.

`free-tool-template ID` prints a disabled hub connection definition. Save it to a file and have the controller register it through `connection-add`; configure the real harness separately. Templates retain environment names only, never credential values. API definitions describe a base URL, not a fabricated MCP wrapper. SDKs and asset websites have their own setup interfaces.

Before activating a third-party MCP, inspect its repository, license, dependency versions, permissions and client-specific configuration. Pin a reviewed version; @latest in an upstream example is not a supply-chain lock. Keep disabled entries disabled until setup and authorization are complete.

## Catalog

### ACE-Step 1.5 local music (`ace-step`)

Local music generation with MIT-licensed code and weights.

Type: software. Categories: music, audio, inference, games. Access: local. Strict free default: True. License: MIT code and weights; commercial: allowed.

Limits: Local compute and model downloads required. The model card permits commercial outputs; that does not guarantee every output is free of third-party rights.

Setup: Follow the repository's platform and model installation guide; run the documented local UI/API. Choose a workflow that fits available memory; inspect generated music before distributing it.

[Official download/repository](https://github.com/ace-step/ACE-Step-1.5)

Sources: [Primary source 1](https://github.com/ace-step/ACE-Step-1.5), [Primary source 2](https://huggingface.co/ACE-Step/Ace-Step1.5)

### ambientCG asset API (`ambientcg`)

Discover CC0 PBR materials and other downloadable assets.

Type: api. Categories: 3d, graphics, games. Access: public. Strict free default: True. License: CC0 assets; commercial: allowed.

Limits: Asset licenses are CC0; use polite caching and do not assume unlimited service availability.

Setup: Use the linked Public API documentation for full_json and downloadable asset metadata. Keep license/source receipts with the downloaded assets.

Sources: [Primary source 1](https://docs.ambientcg.com/api/), [Primary source 2](https://docs.ambientcg.com/license/)

### arXiv API (`arxiv`)

Use the documented Atom query API and respect the recommended request interval and batching.

Type: api. Categories: search, research. Access: public. Strict free default: True. License: Service/data-specific; see source; commercial: check-license.

Limits: No key needed for the query API. Per-paper reuse licenses differ; API results are not blanket permission to redistribute papers.

Setup: Use the documented Atom query API and respect the recommended request interval and batching.

Sources: [Primary source 1](https://info.arxiv.org/help/api/user-manual.html)

### Audacity (`audacity-app`)

For scripting and the listed bridge, use compatible Audacity 3.x and enable mod-script-pipe

Type: software. Categories: audio, music. Access: local. Strict free default: True. License: GPL-3.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. For scripting and the listed bridge, use compatible Audacity 3.x and enable mod-script-pipe; newer major versions can change this interface.

[Official download/repository](https://www.audacityteam.org/download/)

Sources: [Primary source 1](https://github.com/audacity/audacity)

### Audacity MCP (community) (`audacity-mcp`)

Edit audio through Audacity's local scripting pipe.

Type: mcp. Categories: audio, music. Access: local. Strict free default: True. License: Apache-2.0 bridge; commercial: allowed.

Limits: Audacity 4 can change/remove the 3.x pipe interface. This bridge version must be checked against your installed app.

Setup: Use compatible Audacity 3.x and enable mod-script-pipe in its settings. Install audacity-mcp-server in an isolated Python environment and use the absolute audacity-mcp executable path in the harness.

Sources: [Primary source 1](https://github.com/xDarkzx/Audacity-MCP)

### Babylon.js (`babylonjs`)

Use the JavaScript engine for browser 3D games, glTF assets, animation and rendering.

Type: sdk. Categories: 3d, games, graphics. Access: local. Strict free default: True. License: Apache-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use the JavaScript engine for browser 3D games, glTF assets, animation and rendering. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/BabylonJS/Babylon.js)

### Blender (`blender-app`)

Use Blender's bpy Python API and background CLI for modeling, animation, rendering and glTF export.

Type: software. Categories: 3d, graphics, video, games. Access: local. Strict free default: True. License: GPL-3.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use Blender's bpy Python API and background CLI for modeling, animation, rendering and glTF export.

[Official download/repository](https://www.blender.org/download/)

Sources: [Primary source 1](https://github.com/blender/blender)

### MCP for Blender (community) (`blender-mcp`)

Control Blender scenes and run Blender Python through a local addon bridge.

Type: mcp. Categories: 3d, graphics, games. Access: local. Strict free default: True. License: MIT bridge; GPL Blender; commercial: allowed.

Limits: The PyPI name changed from blender-mcp to mcp-for-blender. Local code execution is powerful; isolate projects. Compatibility with installed Blender versions still requires a live test.

Setup: Review and install the repository's Blender addon; enable its local MCP server inside Blender. New installations use uvx mcp-for-blender; keep optional paid asset-provider integrations disabled.

Sources: [Primary source 1](https://github.com/ahujasid/mcp-for-blender)

### Brave Search API — outside strict default (`brave-search`)

$5 monthly allowance is available, but a card and a refundable verification hold are required; no standalone free plan.

Type: excluded. Categories: utilities. Access: card-required. Strict free default: False. License: See primary source; commercial: not-included.

Limits: $5 monthly allowance is available, but a card and a refundable verification hold are required; no standalone free plan.

Setup: Excluded from no-payment templates. Choose one of the free alternatives in the catalog.

Sources: [Primary source 1](https://api-dashboard.search.brave.com/documentation/resources/help-feedback)

### Cerebras direct inference — excluded (`cerebras`)

Current promotional credit requires a payment method and expires after 30 days; it is not recurring free access.

Type: excluded. Categories: inference. Access: trial. Strict free default: False. License: See primary source; commercial: not-included.

Limits: Current promotional credit requires a payment method and expires after 30 days; it is not recurring free access.

Setup: Excluded from no-payment templates. Choose one of the free alternatives in the catalog.

Sources: [Primary source 1](https://www.cerebras.ai/pricing)

### Chrome DevTools MCP (`chrome-devtools-mcp`)

Inspect browser pages, performance traces, network and console output.

Type: mcp. Categories: browser, testing, development. Access: local. Strict free default: True. License: Apache-2.0; commercial: allowed.

Limits: Local MCP is free; no website access entitlement is provided. Browser debugging has significant access to that browser session.

Setup: Check the repository's current Node/Chrome requirements and configure a dedicated browser profile. Review telemetry and debugging connection settings before activation.

Sources: [Primary source 1](https://github.com/ChromeDevTools/chrome-devtools-mcp)

### Cloudflare Workers AI Free allocation (`cloudflare-workers-ai`)

Workers AI models eligible for the Workers Free allocation.

Type: api. Categories: inference, multimodal. Access: free-quota. Strict free default: True. License: See primary source; commercial: model-dependent.

Limits: 10,000 Neurons per day on Workers Free. Some newer frontier models require billing and are excluded from this route. Free-plan over-quota calls error; do not upgrade.

Setup: Use a Free account and a model explicitly supported without billing. POST to the documented /client/v4/accounts/{account_id}/ai/run/{model} endpoint. A template requires your nonsecret account ID first.

Sources: [Primary source 1](https://developers.cloudflare.com/workers-ai/platform/pricing/)

### ComfyUI local generation API (`comfyui`)

Install ComfyUI, select local workflows and licensed weights, and use /prompt plus documented WebSocket/status routes.

Type: software. Categories: inference, graphics, video. Access: local. Strict free default: True. License: GPL-3.0 runtime; model-specific weights; commercial: model-dependent.

Limits: No hosted inference subscription is required. Models, hardware and dependencies must be obtained separately; verify weight licenses and available memory.

Setup: Install ComfyUI, select local workflows and licensed weights, and use /prompt plus documented WebSocket/status routes. Exclude paid API nodes.

[Official download/repository](https://github.com/Comfy-Org/ComfyUI)

Sources: [Primary source 1](https://github.com/Comfy-Org/ComfyUI)

### Context7 documentation MCP (`context7-mcp`)

Retrieve current library documentation on demand.

Type: mcp. Categories: search, development. Access: free-quota. Strict free default: True. License: See repository and hosted service terms; commercial: allowed.

Limits: Hosted quotas and optional paid plans apply. Free access can be rate limited; do not upgrade automatically.

Setup: Use the documented hosted MCP endpoint; omit its optional key header for keyless access. Fetch only the selected library and topic instead of injecting full documentation into every agent context.

Sources: [Primary source 1](https://github.com/upstash/context7)

### Crossref REST metadata API (`crossref`)

Query /works and other documented endpoints; add a contact mailto and cache results.

Type: api. Categories: search, research. Access: public. Strict free default: True. License: Service/data-specific; see source; commercial: allowed.

Limits: Public/polite pool service limits apply. Metadata access does not grant full-text copyright permissions.

Setup: Query /works and other documented endpoints; add a contact mailto and cache results.

Sources: [Primary source 1](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)

### DBHub database MCP (`dbhub-mcp`)

Query authorized MySQL, PostgreSQL, SQLite and other databases with a small MCP surface.

Type: mcp. Categories: data, development. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: No database hosting payment is required for a local database. Existing database credentials and explicit authorization are still needed.

Setup: Install the official @bytebase/dbhub package or binary and use its documented TOML/connection configuration. Keep DSNs/passwords in a private host configuration, never command arguments or hub context. Enable read-only mode, row limits and timeouts. Generate the exact client definition after creating that private configuration; no credential-bearing DSN template is bundled.

Sources: [Primary source 1](https://github.com/bytebase/dbhub)

### Discord developer API (`discord-bot`)

Build a bot for explicitly authorized Discord servers.

Type: api. Categories: collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: Rate limits and privileged intent/verification rules apply. A free bot token is not access to arbitrary private messages.

Setup: Authorize the bot to the intended server and follow the official rate-limit/intent requirements.

Sources: [Primary source 1](https://docs.discord.com/developers/reference)

### .NET SDK (`dotnet-app`)

Build and test C# projects with dotnet CLI

Type: software. Categories: development, games. Access: local. Strict free default: True. License: Free SDK; MIT components; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Build and test C# projects with dotnet CLI; Unity has separate licensing and editor requirements.

[Official download/repository](https://dotnet.microsoft.com/download)

Sources: [Primary source 1](https://dotnet.microsoft.com/en-us/platform/free)

### Excalidraw (`excalidraw`)

Use the embeddable open-source canvas or self-host it for diagrams and visual collaboration.

Type: sdk. Categories: graphics, documents, collaboration. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use the embeddable open-source canvas or self-host it for diagrams and visual collaboration. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/excalidraw/excalidraw)

### Fetch MCP (`fetch-mcp`)

Fetch web content and convert it to readable text.

Type: mcp. Categories: development, utilities. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Reference implementation, not a production security guarantee. Configure filesystem/repository and persistence scope explicitly.

Setup: Install the documented Node or uv runtime and review the reference implementation before activation. Replace {project_root} with the explicitly permitted project directory where present; do not grant your whole filesystem.

Sources: [Primary source 1](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)

### FFmpeg (`ffmpeg-app`)

Use ffmpeg/ffprobe for audio/video conversion, game trailers, sprite/video extraction and media inspection.

Type: software. Categories: audio, video, graphics. Access: local. Strict free default: True. License: LGPL/GPL depending on build; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use ffmpeg/ffprobe for audio/video conversion, game trailers, sprite/video extraction and media inspection.

[Official download/repository](https://ffmpeg.org/download.html)

Sources: [Primary source 1](https://github.com/FFmpeg/FFmpeg)

### Filesystem MCP (`filesystem-mcp`)

Read and edit explicitly permitted project directories.

Type: mcp. Categories: development, utilities. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Reference implementation, not a production security guarantee. Configure filesystem/repository and persistence scope explicitly.

Setup: Install the documented Node or uv runtime and review the reference implementation before activation. Replace {project_root} with the explicitly permitted project directory where present; do not grant your whole filesystem.

Sources: [Primary source 1](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)

### FL Studio existing installation (`fl-studio-existing`)

Python MIDI-controller scripting is documented, but the application license is not universally free and local detection does not prove entitlement. No verified free general-control MCP is claimed.

Type: excluded. Categories: utilities. Access: existing-license. Strict free default: False. License: See primary source; commercial: not-included.

Limits: Python MIDI-controller scripting is documented, but the application license is not universally free and local detection does not prove entitlement. No verified free general-control MCP is claimed.

Setup: Excluded from no-payment templates. Choose one of the free alternatives in the catalog.

Sources: [Primary source 1](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm)

### FluidSynth (`fluidsynth-app`)

Render MIDI via FluidSynth with a separately licensed SoundFont

Type: software. Categories: music, audio, games. Access: local. Strict free default: True. License: LGPL-2.1; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Render MIDI via FluidSynth with a separately licensed SoundFont; the runtime does not license every SoundFont.

[Official download/repository](https://www.fluidsynth.org/)

Sources: [Primary source 1](https://github.com/FluidSynth/fluidsynth)

### FreeCAD (`freecad-app`)

Use FreeCAD's Python API for parametric modeling, STEP/STL exports and documented workbenches.

Type: software. Categories: cad, 3d, engineering. Access: local. Strict free default: True. License: LGPL-2.1 component terms; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use FreeCAD's Python API for parametric modeling, STEP/STL exports and documented workbenches.

[Official download/repository](https://github.com/FreeCAD/FreeCAD/releases)

Sources: [Primary source 1](https://github.com/FreeCAD/FreeCAD)

### FreeCAD MCP (community) (`freecad-mcp`)

Operate a running FreeCAD document through a local addon and MCP server.

Type: mcp. Categories: cad, 3d, engineering. Access: local. Strict free default: True. License: MIT bridge; commercial: allowed.

Limits: Addon plus server required; executing Python changes the CAD document. Optional workbench solvers have their own dependencies.

Setup: Install the repository's FreeCADMCP addon into FreeCAD, restart and start its local RPC server. Use the documented uvx freecad-mcp command and verify workbench compatibility.

Sources: [Primary source 1](https://github.com/neka-nat/freecad-mcp)

### Freesound noncommercial API (`freesound`)

Find sound metadata under the API's noncommercial free terms.

Type: api. Categories: audio, music, games. Access: noncommercial. Strict free default: True. License: Noncommercial API; per-sound CC licenses; commercial: noncommercial.

Limits: An individual CC0 sound does not override the API's noncommercial access terms.

Setup: Use only within the free API's noncommercial terms; review each sound's license independently. Commercial API access requires separate agreement and is outside the no-payment recommendation.

Sources: [Primary source 1](https://freesound.org/docs/api/terms_of_use.html), [Primary source 2](https://freesound.org/docs/api/authentication.html)

### GDevelop local engine (`gdevelop`)

Use the local open-source engine/editor and documented project format; hosted AI/build services and paid plans are optional separate products.

Type: sdk. Categories: 2d, 3d, games. Access: local. Strict free default: True. License: MIT core; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use the local open-source engine/editor and documented project format; hosted AI/build services and paid plans are optional separate products. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/4ian/GDevelop)

### Gemini API Free tier (`gemini`)

Free-tier inference for models explicitly marked free in Google's pricing table.

Type: api. Categories: inference, multimodal. Access: free-quota. Strict free default: True. License: See primary source; commercial: model-dependent.

Limits: Not every model has a Free tier. Rate limits, regional eligibility and free-tier data-use terms apply. Stop when quota is exhausted.

Setup: Check the current API pricing table for the exact model; AI Studio UI access alone is not evidence of free API access. Use POST /v1beta/models/{free-model}:generateContent with x-goog-api-key.

Sources: [Primary source 1](https://ai.google.dev/gemini-api/docs/billing), [Primary source 2](https://ai.google.dev/gemini-api/docs/pricing)

### GIMP (`gimp-app`)

Use GIMP's documented Python plug-in and batch interfaces

Type: software. Categories: graphics, 2d. Access: local. Strict free default: True. License: GPL; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use GIMP's documented Python plug-in and batch interfaces; versions 2 and 3 have different APIs.

[Official download/repository](https://www.gimp.org/downloads/)

Sources: [Primary source 1](https://www.gimp.org/about/)

### Git (`git-app`)

Use Git CLI and project-specific repositories/worktrees to coordinate concurrent agent edits.

Type: software. Categories: development, collaboration. Access: local. Strict free default: True. License: GPL-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use Git CLI and project-specific repositories/worktrees to coordinate concurrent agent edits.

[Official download/repository](https://git-scm.com/install/)

Sources: [Primary source 1](https://github.com/git/git/blob/master/COPYING)

### Git MCP (`git-mcp`)

Inspect and manage a local Git repository.

Type: mcp. Categories: development, utilities. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Reference implementation, not a production security guarantee. Configure filesystem/repository and persistence scope explicitly.

Setup: Install the documented Node or uv runtime and review the reference implementation before activation. Replace {project_root} with the explicitly permitted project directory where present; do not grant your whole filesystem.

Sources: [Primary source 1](https://github.com/modelcontextprotocol/servers/tree/main/src/git)

### Gitea self-hosted REST API (`gitea-api`)

Automate your own free Git repository host.

Type: api. Categories: development, collaboration. Access: self-hosted. Strict free default: True. License: MIT; commercial: allowed.

Limits: Hosting on your own hardware is free software; third-party hosted plans have separate terms.

Setup: Install/self-host Gitea and use the instance's documented /api/v1 endpoints.

Sources: [Primary source 1](https://docs.gitea.com/development/api-usage/)

### GitHub REST API (`github-api`)

Search public repositories and manage authorized repository data.

Type: api. Categories: development, collaboration, search. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: Public unauthenticated reads and free-account authenticated API quotas apply. Paid account features are separate.

Setup: Use the REST API version and accept headers from the current documentation. Read rate-limit response headers and stop/back off rather than creating extra identities to bypass limits.

Sources: [Primary source 1](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)

### GitHub official MCP (`github-mcp`)

Work with authorized GitHub repositories, issues and pull requests.

Type: mcp. Categories: development, collaboration. Access: free-quota. Strict free default: True. License: MIT server; GitHub service terms; commercial: allowed.

Limits: GitHub API quotas and repository permissions apply. A token does not grant access to other users' private repositories.

Setup: Download/build the official server binary and replace command with its absolute path. Use repository/API tools available to your free account; Copilot and paid-only features are outside this recipe.

Sources: [Primary source 1](https://github.com/github/github-mcp-server)

### GitHub Models — retired (`github-models`)

The playground, catalog, inference API and BYOK were retired on July 30, 2026.

Type: excluded. Categories: inference. Access: retired. Strict free default: False. License: See primary source; commercial: not-included.

Limits: The playground, catalog, inference API and BYOK were retired on July 30, 2026.

Setup: Excluded from no-payment templates. Choose one of the free alternatives in the catalog.

Sources: [Primary source 1](https://docs.github.com/en/github-models)

### GitLab REST API (`gitlab-api`)

Read and manage GitLab Free projects using the documented REST API.

Type: api. Categories: development, collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: Hosted quotas or self-hosted limits apply. GitLab Duo/AI and premium endpoints are not included.

Setup: Select documented endpoints available in the Free tier and follow instance limits.

Sources: [Primary source 1](https://docs.gitlab.com/api/rest/)

### Gmail API (`gmail`)

Read or draft authorized email through scoped OAuth.

Type: api. Categories: productivity, collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: scope-dependent.

Limits: Standard usage is currently no extra cost; documentation describes planned over-quota charges later in 2026. Remain below free quotas and recheck current terms. Sensitive scopes may need app verification.

Setup: Use an eligible free personal Google account and the documented OAuth flow. Supply a complete Authorization header in your HTTP client; a paid Workspace subscription or automatic paid quota expansion is not part of this record.

Sources: [Primary source 1](https://developers.google.com/workspace/gmail/api/reference/quota)

### Godot Engine (`godot-app`)

Use GDScript/C#, the scene format and documented headless/export CLI

Type: software. Categories: 2d, 3d, games. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use GDScript/C#, the scene format and documented headless/export CLI; an export template download may be required.

[Official download/repository](https://godotengine.org/download/)

Sources: [Primary source 1](https://godotengine.org/license/)

### Godot MCP (community) (`godot-mcp`)

Launch, inspect and debug Godot projects through MCP.

Type: mcp. Categories: 2d, 3d, games. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: App and bridge installs are separate. Some tools require newer Godot versions.

Setup: Install Godot and Node 18+; set GODOT_PATH in the harness if Godot is not on PATH. Inspect version requirements for UID/scene tools before use.

Sources: [Primary source 1](https://github.com/Coding-Solo/godot-mcp)

### Google Calendar API (`google-calendar`)

Read and manage calendars explicitly shared with your app.

Type: api. Categories: productivity, collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: scope-dependent.

Limits: Per-project/user quotas and operation limits apply; do not purchase quota increases.

Setup: Use an eligible free personal Google account and the documented OAuth flow. Supply a complete Authorization header in your HTTP client; a paid Workspace subscription or automatic paid quota expansion is not part of this record.

Sources: [Primary source 1](https://developers.google.com/workspace/calendar/api/guides/quota)

### Google Drive API (`google-drive`)

File metadata, authorized downloads and project document storage.

Type: api. Categories: productivity, collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: scope-dependent.

Limits: Standard requests have quotas; egress/over-quota billing policies are changing in 2026. Keep usage below free thresholds and recheck before activation.

Setup: Use an eligible free personal Google account and the documented OAuth flow. Supply a complete Authorization header in your HTTP client; a paid Workspace subscription or automatic paid quota expansion is not part of this record.

Sources: [Primary source 1](https://developers.google.com/workspace/drive/api/guides/limits)

### Google Sheets API (`google-sheets`)

Read/write authorized spreadsheet ranges.

Type: api. Categories: productivity, collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: scope-dependent.

Limits: Per-project and per-user read/write quotas apply; no paid Workspace subscription is needed for eligible personal-account use.

Setup: Use an eligible free personal Google account and the documented OAuth flow. Supply a complete Authorization header in your HTTP client; a paid Workspace subscription or automatic paid quota expansion is not part of this record.

Sources: [Primary source 1](https://developers.google.com/workspace/sheets/api/limits)

### Groq API (`groq`)

Hosted model inference and supported speech transcription under Free-tier limits.

Type: api. Categories: inference, speech. Access: free-quota. Strict free default: True. License: See primary source; commercial: model-dependent.

Limits: Model-specific organization quotas. Remain on Free; Developer upgrade requires a payment method. Handle 429 without paid fallback.

Setup: Use the Free-tier console and select an available model from the rate-limits page. Call POST /openai/v1/chat/completions; speech models have their own documented endpoints.

Sources: [Primary source 1](https://console.groq.com/docs/billing-faqs), [Primary source 2](https://console.groq.com/docs/rate-limits)

### Hugging Face Hub API and downloads (`hf-hub`)

Find and download public model/dataset repositories for local use.

Type: api. Categories: inference, search, research. Access: public. Strict free default: True. License: Apache-2.0 client; repository-specific content; commercial: model-dependent.

Limits: Hub rate limits, storage rules and gated-model terms apply. Free model download does not make hosted inference free.

Setup: Use the Hub client/API to inspect model cards and download permitted files. Use local inference; the separately billed Inference Providers service is excluded.

Sources: [Primary source 1](https://github.com/huggingface/huggingface_hub)

### Hugging Face Inference Providers — excluded (`hf-inference`)

Current free accounts receive no inference credits; routed inference requires credit purchase or a paid plan.

Type: excluded. Categories: inference. Access: paid. Strict free default: False. License: See primary source; commercial: not-included.

Limits: Current free accounts receive no inference credits; routed inference requires credit purchase or a paid plan.

Setup: Excluded from no-payment templates. Choose one of the free alternatives in the catalog.

Sources: [Primary source 1](https://huggingface.co/docs/inference-providers/en/pricing)

### Hydrogen drum machine (`hydrogen-app`)

Program drum patterns and export audio

Type: software. Categories: music, audio. Access: local. Strict free default: True. License: GPL-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Program drum patterns and export audio; verify drumkit/sample licenses.

[Official download/repository](https://hydrogen-music.org/)

Sources: [Primary source 1](https://github.com/hydrogen-music/hydrogen)

### ImageMagick (`imagemagick-app`)

Use magick CLI for resizing, compositing, atlas preparation and format conversion

Type: software. Categories: graphics, 2d, utilities. Access: local. Strict free default: True. License: ImageMagick License; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use magick CLI for resizing, compositing, atlas preparation and format conversion; configure resource limits for untrusted inputs.

[Official download/repository](https://imagemagick.org/)

Sources: [Primary source 1](https://github.com/ImageMagick/ImageMagick)

### Inkscape (`inkscape-app`)

Use SVG files, the Inkscape action/CLI interface and inkex extensions for vector creation and exports.

Type: software. Categories: graphics, 2d, documents. Access: local. Strict free default: True. License: GPL; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use SVG files, the Inkscape action/CLI interface and inkex extensions for vector creation and exports.

[Official download/repository](https://inkscape.org/)

Sources: [Primary source 1](https://github.com/inkscape/inkscape)

### Inkscape MCP (community) (`inkscape-mcp`)

Inspect, edit, validate and export SVG documents through MCP.

Type: mcp. Categories: graphics, 2d, documents. Access: local. Strict free default: True. License: MIT bridge; commercial: allowed.

Limits: Not published under a verified bare PyPI package name in the reviewed README. Use source instructions; no guessed executable template is shipped.

Setup: Use the documented source installation with Python 3.12+ and Inkscape 1.2+. The README's Git launch URL differs from the displayed repository name; verify the repository and pin a reviewed revision before installing. Prefer its CLI/headless mode on Windows; optional live GUI modes have platform-specific behavior.

Sources: [Primary source 1](https://github.com/jjjsood/inkscape-mcp-server)

### Jina Reader keyless API (`jina-reader`)

Convert a public page to model-readable content through Reader.

Type: api. Categories: search, research. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: Keyless Reader currently permits 20 requests/minute. Authenticated requests consume tokens and can require paid top-ups after the initial allowance. A key does not bypass website restrictions. Downloaded Reader weights are noncommercial; this record covers the hosted Reader API.

Setup: Prefix a public page URL with https://r.jina.ai/ using the documented Reader interface. Use the free/keyless Reader path only; separately billed embeddings, reranking, search and on-prem products are not included.

Sources: [Primary source 1](https://jina.ai/reader/)

### jsfxr (`jsfxr`)

Generate retro game sound effects from JSON parameters in JavaScript; export or synthesize audio locally.

Type: sdk. Categories: audio, games. Access: local. Strict free default: True. License: Unlicense; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Generate retro game sound effects from JSON parameters in JavaScript; export or synthesize audio locally. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/chr15m/jsfxr)

### JupyterLab (`jupyterlab`)

Run local notebooks and kernels with project-specific environments; authenticate its local server.

Type: sdk. Categories: science, data, development. Access: local. Strict free default: True. License: BSD-3-Clause; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Run local notebooks and kernels with project-specific environments; authenticate its local server. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/jupyterlab/jupyterlab)

### Kdenlive (`kdenlive-app`)

Edit video and render documented project files with the supported render tooling

Type: software. Categories: video, audio. Access: local. Strict free default: True. License: GPL; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Edit video and render documented project files with the supported render tooling; no hosted generative-video API is implied.

[Official download/repository](https://kdenlive.org/download/)

Sources: [Primary source 1](https://kdenlive.org/)

### Kenney free asset packs (`kenney-assets`)

Free downloadable game sprites, models, UI and sounds.

Type: asset-library. Categories: 2d, 3d, audio, games. Access: public. Strict free default: True. License: CC0 on free asset pages; commercial: allowed.

Limits: Free asset pages are CC0; paid tools/bundles are not required and are not included.

Setup: Download a free asset-page pack and retain its included license file. Use filesystem/asset tools to import the pack; there is no verified general REST API in this record.

[Official download/repository](https://kenney.nl/assets)

Sources: [Primary source 1](https://kenney.nl/support)

### KiCad (`kicad-app`)

Use kicad-cli for PCB/diagram exports and DRC

Type: software. Categories: cad, engineering. Access: local. Strict free default: True. License: GPL-3.0 and component licenses; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use kicad-cli for PCB/diagram exports and DRC; version-specific Python/IPC APIs are available for deeper automation.

[Official download/repository](https://www.kicad.org/download/)

Sources: [Primary source 1](https://www.kicad.org/about/licenses/)

### KiCad MCP (community) (`kicad-mcp`)

Assist with PCB design using the documented KiCad 9 Python/Node bridge.

Type: mcp. Categories: cad, engineering. Access: local. Strict free default: True. License: MIT bridge; commercial: allowed.

Limits: The reviewed README documents KiCad 9 compatibility. No payment is required by the bridge, but installed app/version setup is necessary.

Setup: Use the repository's source installation and Node build steps, with compatible KiCad Python modules. Use the exact built entrypoint from the documented client configuration; KiCad 10 compatibility is not established by this record.

Sources: [Primary source 1](https://github.com/miyosuda/kicad-mcp-server)

### Kokoro-82M local text to speech (`kokoro`)

Generate speech locally using Apache-licensed model weights.

Type: sdk. Categories: speech, audio, inference. Access: local. Strict free default: True. License: Apache-2.0 weights; commercial: allowed.

Limits: Model and voice/language dependencies require download. Check any additional voice assets and pronunciation dependencies.

Setup: Install the documented Kokoro pipeline and language dependencies; load the model and save generated audio locally.

Sources: [Primary source 1](https://huggingface.co/hexgrad/Kokoro-82M)

### Krita (`krita-app`)

Use Krita's Python plugin API for painting documents, layers, exports and animation workflows.

Type: software. Categories: graphics, 2d, games. Access: local. Strict free default: True. License: GPL-3.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use Krita's Python plugin API for painting documents, layers, exports and animation workflows.

[Official download/repository](https://krita.org/en/download/)

Sources: [Primary source 1](https://krita.org/en/about/license/)

### KritaMCP (community) (`krita-mcp`)

Operate Krita using a plugin and local Python MCP bridge.

Type: mcp. Categories: graphics, 2d. Access: local. Strict free default: True. License: MIT bridge; commercial: allowed.

Limits: Requires the matching Krita plugin and bridge runtime. Compatibility and plugin access must be tested locally.

Setup: Follow the repository's plugin install and source environment instructions. Generate configuration from the installed project's documented entrypoint; no generic package command is assumed.

Sources: [Primary source 1](https://github.com/halby24/KritaMCP)

### libGDX (`libgdx`)

Use the Java game framework with its documented project generation/build tooling.

Type: sdk. Categories: 2d, 3d, games. Access: local. Strict free default: True. License: Apache-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use the Java game framework with its documented project generation/build tooling. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/libgdx/libgdx)

### LibreOffice (`libreoffice-app`)

Use UNO automation and soffice --headless --convert-to for spreadsheets, documents, presentations and PDF exports.

Type: software. Categories: documents, data. Access: local. Strict free default: True. License: MPL-2.0 and component licenses; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use UNO automation and soffice --headless --convert-to for spreadsheets, documents, presentations and PDF exports.

[Official download/repository](https://www.libreoffice.org/download/download-libreoffice/)

Sources: [Primary source 1](https://www.libreoffice.org/licenses/)

### LibreSprite (`libresprite-app`)

Create pixel art and animated sprites

Type: software. Categories: graphics, 2d, games. Access: local. Strict free default: True. License: GPL-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Create pixel art and animated sprites; export sprite sheets with the app's documented batch/file interface.

[Official download/repository](https://github.com/LibreSprite/LibreSprite/releases)

Sources: [Primary source 1](https://github.com/LibreSprite/LibreSprite)

### LinkedIn official Open Permissions (`linkedin`)

OAuth sign-in and authorized member posting through LinkedIn's self-service permissions.

Type: api. Categories: collaboration, search. Access: free-quota. Strict free default: True. License: See primary source; commercial: scope-dependent.

Limits: Most LinkedIn permissions need partner approval. General people/company search is not a free self-service API; unofficial scraping MCPs are excluded.

Setup: Request only the documented Open Permissions or permissions separately approved for your app. Use the relevant versioned API and OAuth scopes. This entry provides no unrestricted people/company search, scraping or hiring-data access.

Sources: [Primary source 1](https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access), [Primary source 2](https://developer.linkedin.com/legal)

### llama.cpp local server (`llama-cpp`)

Build or download llama-server, choose licensed GGUF weights and run an OpenAI-compatible server bound to loopback.

Type: software. Categories: inference. Access: local. Strict free default: True. License: MIT runtime; model-specific weights; commercial: model-dependent.

Limits: No hosted inference subscription is required. Models, hardware and dependencies must be obtained separately; verify weight licenses and available memory.

Setup: Build or download llama-server, choose licensed GGUF weights and run an OpenAI-compatible server bound to loopback. Change the default port if Unity uses 8080.

[Official download/repository](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)

Sources: [Primary source 1](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)

### LM Studio local API (`lm-studio`)

Download the app, load licensed local weights and enable its local developer server.

Type: software. Categories: inference. Access: local. Strict free default: True. License: Free proprietary app; model-specific weights; commercial: model-dependent.

Limits: No hosted inference subscription is required. Models, hardware and dependencies must be obtained separately; verify weight licenses and available memory.

Setup: Download the app, load licensed local weights and enable its local developer server. Authentication settings can vary; follow its developer docs.

[Official download/repository](https://lmstudio.ai/blog/free-for-work)

Sources: [Primary source 1](https://lmstudio.ai/blog/free-for-work)

### LMMS (`lmms-app`)

Create music in LMMS using MIDI/project files and documented command-line export options

Type: software. Categories: music, audio, games. Access: local. Strict free default: True. License: GPL-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Create music in LMMS using MIDI/project files and documented command-line export options; inspect sample/plugin licenses.

[Official download/repository](https://lmms.io/)

Sources: [Primary source 1](https://github.com/LMMS/lmms)

### Memory MCP (`memory-mcp`)

Persist an explicit local knowledge graph.

Type: mcp. Categories: development, utilities. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Reference implementation, not a production security guarantee. Configure filesystem/repository and persistence scope explicitly.

Setup: Install the documented Node or uv runtime and review the reference implementation before activation. Replace {project_root} with the explicitly permitted project directory where present; do not grant your whole filesystem.

Sources: [Primary source 1](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)

### Mermaid (`mermaid`)

Render software/engineering diagrams from text with the library or its separate CLI.

Type: sdk. Categories: documents, development. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Render software/engineering diagrams from text with the library or its separate CLI. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/mermaid-js/mermaid)

### MET Norway weather API (`met-weather`)

Use the documented Locationforecast product and a unique User-Agent with contact information.

Type: api. Categories: data, utilities. Access: public. Strict free default: True. License: Service/data-specific; see source; commercial: allowed.

Limits: CC-BY attribution, caching and service rate requirements apply. No uptime guarantee or unlimited quota is implied.

Setup: Use the documented Locationforecast product and a unique User-Agent with contact information.

Sources: [Primary source 1](https://api.met.no/doc/TermsOfService)

### Mido MIDI (`mido`)

Read/write MIDI and create procedural compositions in Python; render with a licensed synth/SoundFont.

Type: sdk. Categories: music, audio. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Read/write MIDI and create procedural compositions in Python; render with a licensed synth/SoundFont. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/mido/mido)

### Mistral Studio Free mode (`mistral`)

Mistral API access in the no-card Free mode.

Type: api. Categories: inference, multimodal. Access: free-quota. Strict free default: True. License: See primary source; commercial: model-dependent.

Limits: Free-mode usage and rate limits apply; do not switch to Scale or enable paid fallback.

Setup: Keep Studio in Free mode and consult current model availability. Call POST /v1/chat/completions with a selected free-mode model.

Sources: [Primary source 1](https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key)

### MuseScore Studio (`musescore-app`)

Use MIDI/MusicXML and supported command-line exports for score-based music

Type: software. Categories: music, audio. Access: local. Strict free default: True. License: GPL-3.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use MIDI/MusicXML and supported command-line exports for score-based music; MuseScore.com subscriptions are a separate product.

[Official download/repository](https://musescore.org/)

Sources: [Primary source 1](https://github.com/musescore/MuseScore)

### MusicGen / AudioCraft noncommercial weights (`musicgen`)

Generate audio locally for permitted noncommercial projects.

Type: software. Categories: music, audio, inference. Access: noncommercial. Strict free default: True. License: MIT code; CC-BY-NC-4.0 weights; commercial: noncommercial.

Limits: MIT library code does not make MusicGen/AudioGen weights commercially usable.

Setup: Install the documented local stack and obtain the appropriate model weights. Use ACE-Step or procedural music with suitable licenses when commercial use is required.

[Official download/repository](https://github.com/facebookresearch/audiocraft)

Sources: [Primary source 1](https://github.com/facebookresearch/audiocraft), [Primary source 2](https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_MODEL_CARD.md)

### MySQL Community Edition (`mysql-app`)

Use the Community server and protocol/client interfaces

Type: software. Categories: data, development. Access: local. Strict free default: True. License: GPL Community Edition; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use the Community server and protocol/client interfaces; DBHub can connect with explicitly authorized local credentials.

[Official download/repository](https://dev.mysql.com/downloads/)

Sources: [Primary source 1](https://www.mysql.com/products/community/)

### Node.js (`node-app`)

Install a supported Node release for JavaScript projects and Node-based MCPs

Type: software. Categories: development, utilities. Access: local. Strict free default: True. License: MIT and component licenses; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Install a supported Node release for JavaScript projects and Node-based MCPs; on Windows, harnesses may need npx.cmd.

[Official download/repository](https://nodejs.org/en/download)

Sources: [Primary source 1](https://github.com/nodejs/node/blob/main/LICENSE)

### OpenStreetMap Nominatim (`nominatim`)

Use limited geocoding with identifying headers, cache responses and show attribution; self-host for bulk workloads.

Type: api. Categories: gis, data, search. Access: public. Strict free default: True. License: Service/data-specific; see source; commercial: allowed.

Limits: Public service has an absolute maximum of 1 request/second and prohibits client autocomplete/systematic bulk querying. ODbL applies.

Setup: Use limited geocoding with identifying headers, cache responses and show attribution; self-host for bulk workloads.

Sources: [Primary source 1](https://operations.osmfoundation.org/policies/nominatim/)

### Notion data API (`notion-api`)

Read/update explicitly connected pages and databases.

Type: api. Categories: productivity, collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: API rate and free-workspace limits apply. Paid AI functionality is not included.

Setup: Use a free workspace within its storage/collaboration limits; set the documented Notion-Version header. The Data API is separate from paid Notion AI features.

Sources: [Primary source 1](https://developers.notion.com/reference/request-limits), [Primary source 2](https://www.notion.com/pricing)

### Notion official hosted MCP (`notion-mcp`)

Authorize an MCP client to work with accessible Notion content.

Type: mcp. Categories: productivity, collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: Workspace permissions, account plan and API limits apply; paid Notion AI products are separate.

Setup: Configure the hosted MCP endpoint and complete OAuth for the selected workspace. Use the current hosted server rather than the no-longer-maintained open-source v1 server.

Sources: [Primary source 1](https://developers.notion.com/guides/mcp/overview), [Primary source 2](https://developers.notion.com/guides/mcp/get-started-with-mcp), [Primary source 3](https://www.notion.com/pricing)

### npm public registry metadata (`npm`)

Use npm view or the public registry metadata interface for public packages.

Type: api. Categories: development, search. Access: public. Strict free default: True. License: Service/data-specific; see source; commercial: allowed.

Limits: Public metadata does not require a paid npm account; private packages, publishing and optional paid products have separate access rules.

Setup: Use npm view or the public registry metadata interface for public packages.

Sources: [Primary source 1](https://docs.npmjs.com/cli/v11/commands/npm-view/)

### OBS Studio (`obs-app`)

Enable the bundled obs-websocket v5 interface for local recording and scene automation

Type: software. Categories: video, audio. Access: local. Strict free default: True. License: GPL-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Enable the bundled obs-websocket v5 interface for local recording and scene automation; set a local password.

[Official download/repository](https://obsproject.com/download)

Sources: [Primary source 1](https://github.com/obsproject/obs-websocket)

### OBS MCP (community) (`obs-mcp`)

Control OBS scenes and recording through the WebSocket v5 protocol.

Type: mcp. Categories: video, audio. Access: local. Strict free default: True. License: MIT/Apache-2.0 bridge; commercial: allowed.

Limits: Recording and streaming are side effects. The local password, app and compiled MCP binary are separate setup steps.

Setup: Install/build the documented obs-mcp binary and use its absolute path. Enable OBS WebSocket v5, retain loopback binding and set a strong local password; do not configure automatic shell-based app launch.

Sources: [Primary source 1](https://github.com/JLFN/obs-mcp)

### Microsoft Office existing installation (`office-existing`)

An installed Office component does not prove an active license. Use LibreOffice UNO, python-docx and openpyxl for the included free workflows.

Type: excluded. Categories: utilities. Access: existing-license. Strict free default: False. License: See primary source; commercial: not-included.

Limits: An installed Office component does not prove an active license. Use LibreOffice UNO, python-docx and openpyxl for the included free workflows.

Setup: Excluded from no-payment templates. Choose one of the free alternatives in the catalog.

Sources: [Primary source 1](https://www.libreoffice.org/licenses/)

### Ollama local inference (`ollama`)

Install the local runtime, download a suitable model and use /api/chat or /api/generate.

Type: software. Categories: inference. Access: local. Strict free default: True. License: MIT runtime; model-specific weights; commercial: model-dependent.

Limits: No hosted inference subscription is required. Models, hardware and dependencies must be obtained separately; verify weight licenses and available memory.

Setup: Install the local runtime, download a suitable model and use /api/chat or /api/generate. Use local models; cloud offerings are separate.

[Official download/repository](https://github.com/ollama/ollama)

Sources: [Primary source 1](https://github.com/ollama/ollama)

### ONNX Runtime (`onnxruntime`)

Local CPU/GPU inference of ONNX models.

Type: sdk. Categories: inference. Access: local. Strict free default: True. License: MIT runtime; commercial: model-dependent.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Install the CPU or hardware-compatible GPU package and load a licensed ONNX model.

Sources: [Primary source 1](https://github.com/microsoft/onnxruntime)

### Open-Meteo noncommercial hosted API (`open-meteo`)

Keyless forecasts for noncommercial prototypes.

Type: api. Categories: data, utilities. Access: noncommercial. Strict free default: True. License: Noncommercial hosted free tier; commercial: noncommercial.

Limits: Free hosted endpoint is noncommercial and limited to 10,000 calls/day; commercial hosted use requires a paid subscription.

Setup: Use the free hosted API only for qualifying noncommercial projects. For other no-payment weather work, evaluate MET Norway's attributed API or self-host compatible open data software.

Sources: [Primary source 1](https://open-meteo.com/en/pricing)

### OpenAlex API (`openalex`)

Query research metadata with a no-card daily free budget.

Type: api. Categories: search, research, data. Access: free-quota. Strict free default: True. License: CC0 data; API usage terms; commercial: allowed.

Limits: Free account currently receives $1/day usage with no payment method; keyless allowance is smaller. Rate/budget 429s should stop or back off.

Setup: Use the documented API authentication and monitor credit/rate response headers. Stay within the free allocation without adding prepaid funds.

Sources: [Primary source 1](https://help.openalex.org/access/pricing/), [Primary source 2](https://help.openalex.org/api/authentication/)

### OpenGameArt (`opengameart`)

Download community game art, sounds and music with per-asset licenses.

Type: asset-library. Categories: 2d, 3d, music, audio, games. Access: public. Strict free default: True. License: Per asset: CC0, CC-BY, CC-BY-SA, GPL and others; commercial: check-license.

Limits: No uniform license covers the whole site. Preserve license and attribution evidence for every asset.

Setup: Choose an asset and inspect its exact license, attribution and redistribution requirements. Download manually or through authorized web tooling; this entry does not claim an official asset REST API.

[Official download/repository](https://opengameart.org/)

Sources: [Primary source 1](https://opengameart.org/content/faq)

### Open Library API (`openlibrary`)

Use documented search/works/edition endpoints with identifying request headers.

Type: api. Categories: search, research. Access: public. Strict free default: True. License: Service/data-specific; see source; commercial: check-license.

Limits: Low-volume access and rate limits apply. Book borrowing/full text has separate access and copyright requirements.

Setup: Use documented search/works/edition endpoints with identifying request headers.

Sources: [Primary source 1](https://openlibrary.org/developers/api)

### openpyxl (`openpyxl`)

Read/write XLSX locally without Excel; formulas are preserved but are not calculated by openpyxl.

Type: sdk. Categories: documents, data. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Read/write XLSX locally without Excel; formulas are preserved but are not calculated by openpyxl. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://openpyxl.readthedocs.io/en/stable/)

### OpenRouter free model variants (`openrouter-free`)

Route only to explicitly free model variants.

Type: api. Categories: inference. Access: free-quota. Strict free default: True. License: See primary source; commercial: model-dependent.

Limits: Use :free models or openrouter/free only, disable paid plugins and paid fallback, and inspect /api/v1/key for your live free-model ceiling. Availability can change.

Setup: Select an explicit :free model for reproducibility; openrouter/free can select different free models. Check the model's terms and provider data policy before sending project content.

Sources: [Primary source 1](https://openrouter.ai/docs/api_reference/limits), [Primary source 2](https://openrouter.ai/pricing)

### OpenSCAD (`openscad-app`)

Generate .scad source and use the CLI to export STL and other supported formats.

Type: software. Categories: cad, 3d, engineering. Access: local. Strict free default: True. License: GPL-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Generate .scad source and use the CLI to export STL and other supported formats.

[Official download/repository](https://openscad.org/downloads.html)

Sources: [Primary source 1](https://github.com/openscad/openscad)

### Pandoc (`pandoc-app`)

Use pandoc CLI to convert document formats

Type: software. Categories: documents, utilities. Access: local. Strict free default: True. License: GPL-2.0-or-later; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use pandoc CLI to convert document formats; some PDF workflows additionally require a free TeX installation.

[Official download/repository](https://pandoc.org/installing.html)

Sources: [Primary source 1](https://pandoc.org/)

### ParaView (`paraview-app`)

Use pvpython/pvbatch for scientific data visualization and reproducible renders.

Type: software. Categories: science, 3d, data. Access: local. Strict free default: True. License: BSD-3-Clause; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use pvpython/pvbatch for scientific data visualization and reproducible renders.

[Official download/repository](https://www.paraview.org/download/)

Sources: [Primary source 1](https://github.com/Kitware/ParaView)

### Phaser (`phaser`)

Use the open-source JavaScript library for 2D browser games; separately advertised agent/cloud products are outside this record.

Type: sdk. Categories: 2d, games. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use the open-source JavaScript library for 2D browser games; separately advertised agent/cloud products are outside this record. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/phaserjs/phaser)

### Pillow (`pillow`)

Use Python image APIs for atlases, resizing, masks and image inspection; this does not require a hosted generation service.

Type: sdk. Categories: graphics, 2d, utilities. Access: local. Strict free default: True. License: HPND/Pillow license; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use Python image APIs for atlases, resizing, masks and image inspection; this does not require a hosted generation service. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/python-pillow/Pillow)

### PixiJS (`pixijs`)

Use the JavaScript rendering library for sprites, interactive 2D scenes and animation.

Type: sdk. Categories: 2d, games, graphics. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use the JavaScript rendering library for sprites, interactive 2D scenes and animation. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/pixijs/pixijs)

### Microsoft Playwright MCP (`playwright-mcp`)

Browser automation using accessibility snapshots and screenshots.

Type: mcp. Categories: browser, testing, development. Access: local. Strict free default: True. License: Apache-2.0; commercial: allowed.

Limits: Free local bridge. Website accounts and website terms are separate; actions can modify data. Installed browser detection does not verify the bridge.

Setup: Install Node and the required browser dependencies; select the browser/channel and isolated project profile. Enable only the capabilities needed for this task in the harness.

Sources: [Primary source 1](https://github.com/microsoft/playwright-mcp)

### Podman (`podman-app`)

Run local containers with Podman

Type: software. Categories: development, utilities. Access: local. Strict free default: True. License: Apache-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Run local containers with Podman; Windows requires its supported Linux VM/WSL setup.

[Official download/repository](https://podman.io/)

Sources: [Primary source 1](https://github.com/podman-container-tools/podman)

### Poly Haven asset API (`polyhaven`)

Find CC0 textures, HDRIs and 3D models through the public asset API.

Type: api. Categories: 3d, graphics, games. Access: public. Strict free default: True. License: CC0 assets; API terms; commercial: allowed.

Limits: The July 2026 API terms permit commercial API use with identification/credit requirements. CC0 asset rights and live API service terms are separate.

Setup: Use /assets and /files/{asset_id} to discover assets and download URLs. Identify requests with the required User-Agent/Referer and visibly credit Poly Haven where the live API is integrated.

Sources: [Primary source 1](https://github.com/Poly-Haven/Public-API/blob/master/ToS.md), [Primary source 2](https://polyhaven.com/license), [Primary source 3](https://github.com/Poly-Haven/Public-API/blob/master/README.md)

### PostgreSQL (`postgres-app`)

Install a local database and use SQL or DBHub with a scoped read-only account

Type: software. Categories: data, development. Access: local. Strict free default: True. License: PostgreSQL License; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Install a local database and use SQL or DBHub with a scoped read-only account; paid hosting is unnecessary.

[Official download/repository](https://www.postgresql.org/download/)

Sources: [Primary source 1](https://www.postgresql.org/about/licence/)

### pygame (`pygame`)

Install the Python package and use its display, sprite, input and mixer interfaces.

Type: sdk. Categories: 2d, games. Access: local. Strict free default: True. License: LGPL-2.1; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Install the Python package and use its display, sprite, input and mixer interfaces. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/pygame/pygame)

### PyPI metadata API (`pypi`)

Use documented JSON/Simple APIs for public package metadata; cache and respect repository policy.

Type: api. Categories: development, search. Access: public. Strict free default: True. License: Service/data-specific; see source; commercial: allowed.

Limits: Public package metadata is free to query; every downloaded package has its own license and supply-chain risk.

Setup: Use documented JSON/Simple APIs for public package metadata; cache and respect repository policy.

Sources: [Primary source 1](https://docs.pypi.org/api/)

### Python (`python-app`)

Use Python 3.11+ for the hub and create isolated environments for SDKs and MCP servers.

Type: software. Categories: development, science, utilities. Access: local. Strict free default: True. License: PSF and component licenses; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use Python 3.11+ for the hub and create isolated environments for SDKs and MCP servers.

[Official download/repository](https://www.python.org/downloads/)

Sources: [Primary source 1](https://docs.python.org/3/license.html)

### python-docx (`python-docx`)

Create/edit DOCX documents locally without Microsoft Office; rendering needs a separate compatible viewer.

Type: sdk. Categories: documents. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Create/edit DOCX documents locally without Microsoft Office; rendering needs a separate compatible viewer. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/python-openxml/python-docx)

### PyTorch (`pytorch`)

Local model inference, tensor operations and training.

Type: sdk. Categories: inference, science. Access: local. Strict free default: True. License: BSD-style runtime; commercial: model-dependent.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use the official installation selector matching your CUDA/CPU platform; model licenses remain separate.

Sources: [Primary source 1](https://github.com/pytorch/pytorch)

### QGIS (`qgis-app`)

Use PyQGIS and Processing algorithms for maps and spatial data

Type: software. Categories: gis, science, data. Access: local. Strict free default: True. License: GPL-2.0-or-later; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use PyQGIS and Processing algorithms for maps and spatial data; local bridge versions must match the app.

[Official download/repository](https://qgis.org/download/)

Sources: [Primary source 1](https://github.com/qgis/QGIS)

### QGIS MCP (community) (`qgis-mcp`)

Use typed tools and bounded context through a local QGIS Desktop plugin.

Type: mcp. Categories: gis, science, data. Access: local. Strict free default: True. License: MIT bridge; commercial: allowed.

Limits: Plugin-generated authenticated local connection. No static token or machine-specific launch path is bundled.

Setup: Install the documented QGIS plugin and use its Connect/Repair UI to generate a project-specific harness binding. Check QGIS 3.44 through 4.x compatibility in the current release notes.

Sources: [Primary source 1](https://github.com/Aaa2122/QGIS-MCP)

### Ruff (`ruff`)

Use the linter/formatter CLI in a project environment to improve generated Python code.

Type: sdk. Categories: development, testing. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use the linter/formatter CLI in a project environment to improve generated Python code. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/astral-sh/ruff)

### SearXNG self-hosted search (`searxng`)

Run a local metasearch service with a documented JSON search API.

Type: software. Categories: search, research. Access: self-hosted. Strict free default: True. License: AGPL-3.0; commercial: allowed.

Limits: No hosted API subscription is required for a self-hosted instance. Upstream engines may throttle or block requests; public instances are not a guaranteed API.

Setup: Deploy your own SearXNG instance and enable JSON in the search formats setting. Use /search?q=...&format=json; choose and configure upstream engines within their terms.

[Official download/repository](https://github.com/searxng/searxng)

Sources: [Primary source 1](https://docs.searxng.org/dev/search_api.html)

### Semantic Scholar research API (`semantic-scholar`)

Academic graph access for permitted research/evaluation use.

Type: api. Categories: search, research. Access: noncommercial. Strict free default: True. License: Dataset/API license with restricted general access; commercial: noncommercial.

Limits: The general license is limited to specified noncommercial research/education purposes; do not treat all commercial access as free.

Setup: Read the current dataset/API license and select permitted endpoints; respect rate limits.

Sources: [Primary source 1](https://api.semanticscholar.org/license/), [Primary source 2](https://api.semanticscholar.org/api-docs/)

### Slack Web API for a Free workspace (`slack-api`)

Automate authorized workspace operations available to the Free plan.

Type: api. Categories: collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: Free workspace and app limits apply. Commercially distributed non-Marketplace apps face additional history/replies rate limits.

Setup: Check the Free plan's app/history limits and the current limits for your app distribution type. Use scoped Web API calls; paid enterprise MCP features are not assumed.

Sources: [Primary source 1](https://docs.slack.dev/apis/web-api/rate-limits/)

### SQLite (`sqlite-app`)

Use Python's built-in sqlite3 API or the SQLite CLI

Type: software. Categories: data, development. Access: local. Strict free default: True. License: Public domain; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Use Python's built-in sqlite3 API or the SQLite CLI; no server or account is needed.

[Official download/repository](https://sqlite.org/download.html)

Sources: [Primary source 1](https://github.com/sqlite/sqlite)

### Tavily search API (`tavily-api`)

Web search and extraction under the recurring free credit allowance.

Type: api. Categories: search, research. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: 1,000 credits/month without a card. Basic search costs one credit; advanced search and research use more. Do not enable pay-as-you-go.

Setup: Use the documented search endpoint and prefer basic search when adequate. Track credits and stop before the free allowance is exhausted.

Sources: [Primary source 1](https://docs.tavily.com/documentation/api-credits)

### Tavily official MCP (`tavily-mcp`)

Search, extract, map and crawl using Tavily's MCP service.

Type: mcp. Categories: search, research. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: Shares the Tavily account's free credit allowance; extraction/crawl/research have different credit costs.

Setup: Configure the hosted endpoint and complete OAuth, or configure its referenced authorization header. Use the same free credit limits as the search API.

Sources: [Primary source 1](https://github.com/tavily-ai/tavily-mcp), [Primary source 2](https://docs.tavily.com/documentation/api-credits)

### Telegram Bot API (`telegram-bot`)

Integrate your own authorized bot using the HTTP Bot API.

Type: api. Categories: collaboration. Access: free-quota. Strict free default: True. License: See primary source; commercial: allowed.

Limits: Standard bot operations are free within rate limits; optional paid broadcasts are excluded.

Setup: Use the official Bot API and authorized chats; respect messaging rates. Avoid paid broadcast options; sending messages requires explicit user/task authorization.

Sources: [Primary source 1](https://core.telegram.org/bots/faq)

### Three.js (`threejs`)

Use npm three or a pinned browser module for 3D scenes, glTF loading and custom game rendering.

Type: sdk. Categories: 3d, games, graphics. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use npm three or a pinned browser module for 3D scenes, glTF loading and custom game rendering. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/mrdoob/three.js)

### Tiled Map Editor (`tiled-app`)

Generate JSON/TMX maps and use documented CLI exports

Type: software. Categories: 2d, games. Access: local. Strict free default: True. License: GPL editor; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Generate JSON/TMX maps and use documented CLI exports; free downloads are available without a mandatory donation.

[Official download/repository](https://www.mapeditor.org/)

Sources: [Primary source 1](https://www.mapeditor.org/)

### Time MCP (`time-mcp`)

Read and convert times across time zones.

Type: mcp. Categories: development, utilities. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Reference implementation, not a production security guarantee. Configure filesystem/repository and persistence scope explicitly.

Setup: Install the documented Node or uv runtime and review the reference implementation before activation. Replace {project_root} with the explicitly permitted project directory where present; do not grant your whole filesystem.

Sources: [Primary source 1](https://github.com/modelcontextprotocol/servers/tree/main/src/time)

### Tone.js (`tonejs`)

Use the Web Audio JavaScript library for procedural music, synths and scheduling.

Type: sdk. Categories: music, audio, games. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Use the Web Audio JavaScript library for procedural music, synths and scheduling. Install from the official package/repository with a reviewed version; no API key is needed.

Sources: [Primary source 1](https://github.com/Tonejs/Tone.js)

### Transformers local models (`transformers`)

Python model loading and local inference for text, images and audio.

Type: sdk. Categories: inference, multimodal. Access: local. Strict free default: True. License: Apache-2.0 runtime; commercial: model-dependent.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Install transformers and the model's supported backend in an isolated environment; choose weights with a suitable license.

Sources: [Primary source 1](https://github.com/huggingface/transformers)

### TRELLIS local 3D generation (`trellis`)

Generate local 3D assets from images with the documented TRELLIS pipeline.

Type: software. Categories: 3d, games, inference. Access: local. Strict free default: True. License: MIT models and majority of code; submodule exceptions; commercial: check-license.

Limits: Submodule licenses differ from the main MIT license. Hardware and platform requirements apply.

Setup: Use the repository's supported Linux/NVIDIA environment and licensed weights. Review the diffoctreerast and Flexicubes submodule licenses before commercial deployment.

[Official download/repository](https://github.com/microsoft/TRELLIS)

Sources: [Primary source 1](https://github.com/microsoft/TRELLIS)

### TripoSR local image to 3D (`triposr`)

Reconstruct a 3D object locally from a reference image.

Type: software. Categories: 3d, games, inference. Access: local. Strict free default: True. License: MIT code and weights; commercial: allowed.

Limits: GPU/software requirements apply. Input image rights and generated mesh quality require review.

Setup: Install the repository requirements and model weights, then use its documented run.py workflow. Clean up topology, scale and materials in Blender before using the mesh in a game.

[Official download/repository](https://github.com/VAST-AI-Research/TripoSR)

Sources: [Primary source 1](https://github.com/VAST-AI-Research/TripoSR)

### MCP for Unity (community) (`unity-mcp`)

Manage scenes, assets, scripts and tests through a local Unity bridge.

Type: mcp. Categories: 2d, 3d, games. Access: conditional. Strict free default: False. License: MIT bridge; Unity Personal eligibility; commercial: eligibility.

Limits: The bridge is free, but Unity editor eligibility is conditional. This entry is outside the strict free default; installed Unity does not prove license entitlement.

Setup: Unity 2021.3 LTS through 6.x is documented. Add the project's MCPForUnity package via Unity Package Manager. Use the package's connection UI to start its local server and generate harness configuration. Unity Personal is free only if current revenue/funding and usage eligibility are met; check before activation.

Sources: [Primary source 1](https://github.com/CoplayDev/unity-mcp), [Primary source 2](https://unity.com/products/unity-personal), [Primary source 3](https://github.com/CoplayDev/unity-mcp/blob/main/Server/README.md)

### uv and uvx (`uv-app`)

Manage Python environments and launch reviewed MCP packages with uvx

Type: software. Categories: development, utilities. Access: local. Strict free default: True. License: MIT/Apache-2.0; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. Manage Python environments and launch reviewed MCP packages with uvx; no model service subscription is bundled.

[Official download/repository](https://docs.astral.sh/uv/getting-started/installation/)

Sources: [Primary source 1](https://github.com/astral-sh/uv)

### Visual Studio Community eligibility (`visual-studio-existing`)

Use installed Visual Studio build/test tooling when Community license eligibility is satisfied.

Type: software. Categories: development. Access: conditional. Strict free default: False. License: Visual Studio Community terms; commercial: eligibility.

Limits: Community eligibility is conditional. Paid Copilot or commercial Visual Studio editions are not required by the free alternatives, and installed software does not prove entitlement.

Setup: Read the Community license for individual and organizational eligibility before use. Use compiler/build/test CLIs and project files; no verified free general-control Visual Studio MCP server is asserted. VS Code and .NET are included free alternatives.

[Official download/repository](https://visualstudio.microsoft.com/vs/community/)

Sources: [Primary source 1](https://visualstudio.microsoft.com/license-terms/vs2022-ga-community/)

### vLLM local inference (`vllm`)

Use the documented Linux/WSL or supported platform installation and launch vllm serve with licensed weights; hardware compatibility matters.

Type: software. Categories: inference. Access: local. Strict free default: True. License: Apache-2.0 runtime; model-specific weights; commercial: model-dependent.

Limits: No hosted inference subscription is required. Models, hardware and dependencies must be obtained separately; verify weight licenses and available memory.

Setup: Use the documented Linux/WSL or supported platform installation and launch vllm serve with licensed weights; hardware compatibility matters.

[Official download/repository](https://github.com/vllm-project/vllm)

Sources: [Primary source 1](https://github.com/vllm-project/vllm)

### VS Code (`vscode-app`)

VS Code is an MCP client, not a generic control server. Use a separately configured assistant and project-scoped MCP definitions.

Type: software. Categories: development. Access: local. Strict free default: True. License: Free binary; MIT source and distribution terms; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download the free application from the linked official site/release page. VS Code is an MCP client, not a generic control server. Use a separately configured assistant and project-scoped MCP definitions.

[Official download/repository](https://code.visualstudio.com/)

Sources: [Primary source 1](https://code.visualstudio.com/docs/agent-customization/mcp-servers)

### whisper.cpp (`whisper-cpp`)

Offline speech transcription with CPU/GPU support.

Type: software. Categories: speech, audio, inference. Access: local. Strict free default: True. License: MIT; commercial: allowed.

Limits: Local hardware, disk space and electricity are required; software access has no mandatory subscription.

Setup: Download or build the runtime and its documented model files; use whisper-cli or the example server.

[Official download/repository](https://github.com/ggml-org/whisper.cpp)

Sources: [Primary source 1](https://github.com/ggml-org/whisper.cpp)

### Wikidata query and data APIs (`wikidata`)

Use documented SPARQL/data access, a descriptive User-Agent and small cached queries.

Type: api. Categories: search, research, data. Access: public. Strict free default: True. License: Service/data-specific; see source; commercial: allowed.

Limits: Query timeouts and throttles apply; Wikidata structured data is CC0, but linked content has separate rights.

Setup: Use documented SPARQL/data access, a descriptive User-Agent and small cached queries.

Sources: [Primary source 1](https://www.wikidata.org/wiki/Wikidata:Data_access)

### Wikipedia / MediaWiki Action API (`wikipedia`)

Use action=query search/page endpoints with format=json and an identifying User-Agent.

Type: api. Categories: search, research. Access: public. Strict free default: True. License: Service/data-specific; see source; commercial: check-license.

Limits: Content licenses and Wikimedia rate/usage policy apply; this is encyclopedia search, not arbitrary web search.

Setup: Use action=query search/page endpoints with format=json and an identifying User-Agent.

Sources: [Primary source 1](https://www.mediawiki.org/wiki/API:Main_page)

### WolframScript existing installation (`wolfram-existing`)

Installation is not proof of free engine entitlement. Evaluate free Python/.NET/scientific tools for no-payment automation.

Type: excluded. Categories: utilities. Access: existing-license. Strict free default: False. License: See primary source; commercial: not-included.

Limits: Installation is not proof of free engine entitlement. Evaluate free Python/.NET/scientific tools for no-payment automation.

Setup: Excluded from no-payment templates. Choose one of the free alternatives in the catalog.

Sources: [Primary source 1](https://www.wolfram.com/wolframscript/)
