# All manual credentials and account steps

Research date: 2026-10-10 UTC. These are environment-variable NAMES, not values. Nothing here creates a key or authorizes a service.

Full-header variables (for example GROQ_AUTHORIZATION) contain the complete `Bearer <token>` value in the host secret store. Most SDKs use the raw API_KEY variable instead. The hub never interpolates one into the other. Not every client supports env header references: configure its documented secret mechanism manually.

| Service | Authentication | Variables / host action | Get access | Free eligibility |
|---|---|---|---|---|
| Cloudflare Workers AI Free allocation | manual_key | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | [Setup](https://dash.cloudflare.com/profile/api-tokens) | free-quota |
| Context7 documentation MCP | optional_key | `CONTEXT7_API_KEY` | [Setup](https://context7.com/dashboard) | free-quota |
| DBHub database MCP | local_secret | `DB_USER`, `DB_PASSWORD` | [Setup](https://github.com/bytebase/dbhub) | local |
| Discord developer API | manual_token | `DISCORD_BOT_TOKEN`, `DISCORD_AUTHORIZATION` | [Setup](https://discord.com/developers/applications) | free-quota |
| Freesound noncommercial API | manual_key_oauth | `FREESOUND_API_KEY`, `FREESOUND_AUTHORIZATION`, `FREESOUND_CLIENT_ID`, `FREESOUND_CLIENT_SECRET`, `FREESOUND_ACCESS_TOKEN` | [Setup](https://freesound.org/apiv2/apply) | noncommercial |
| Gemini API Free tier | manual_key | `GEMINI_API_KEY` | [Setup](https://aistudio.google.com/apikey) | free-quota |
| Gitea self-hosted REST API | local_secret | `GITEA_TOKEN` | [Setup](https://docs.gitea.com/) | self-hosted |
| GitHub REST API | optional_token | `GITHUB_TOKEN`, `GITHUB_AUTHORIZATION` | [Setup](https://github.com/settings/personal-access-tokens) | free-quota |
| GitHub official MCP | manual_token | `GITHUB_PERSONAL_ACCESS_TOKEN` | [Setup](https://github.com/settings/personal-access-tokens) | free-quota |
| GitLab REST API | manual_token | `GITLAB_TOKEN` | [Setup](https://gitlab.com/-/user_settings/personal_access_tokens) | free-quota |
| Gmail API | oauth | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_ACCESS_TOKEN`, `GOOGLE_REFRESH_TOKEN` | [Setup](https://console.cloud.google.com/apis/credentials) | free-quota |
| Google Calendar API | oauth | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_ACCESS_TOKEN`, `GOOGLE_REFRESH_TOKEN` | [Setup](https://console.cloud.google.com/apis/credentials) | free-quota |
| Google Drive API | oauth | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_ACCESS_TOKEN`, `GOOGLE_REFRESH_TOKEN` | [Setup](https://console.cloud.google.com/apis/credentials) | free-quota |
| Google Sheets API | oauth | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_ACCESS_TOKEN`, `GOOGLE_REFRESH_TOKEN` | [Setup](https://console.cloud.google.com/apis/credentials) | free-quota |
| Groq API | manual_key | `GROQ_API_KEY`, `GROQ_AUTHORIZATION` | [Setup](https://console.groq.com/keys) | free-quota |
| Hugging Face Hub API and downloads | optional_token | `HF_TOKEN` | [Setup](https://huggingface.co/settings/tokens) | public |
| Jina Reader keyless API | optional_key | `JINA_API_KEY`, `JINA_AUTHORIZATION` | [Setup](https://jina.ai/) | free-quota |
| LinkedIn official Open Permissions | oauth | `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN` | [Setup](https://www.linkedin.com/developers/apps) | free-quota |
| Mistral Studio Free mode | manual_key | `MISTRAL_API_KEY`, `MISTRAL_AUTHORIZATION` | [Setup](https://console.mistral.ai/) | free-quota |
| Notion data API | manual_token | `NOTION_TOKEN`, `NOTION_AUTHORIZATION` | [Setup](https://www.notion.so/profile/integrations) | free-quota |
| Notion official hosted MCP | oauth | Interactive host OAuth | [Setup](https://mcp.notion.com/mcp) | free-quota |
| OBS MCP (community) | local_secret | `OBS_PASSWORD` | [Setup](https://obsproject.com/) | local |
| OpenAlex API | optional_key | `OPENALEX_API_KEY` | [Setup](https://openalex.org/settings/api) | free-quota |
| OpenRouter free model variants | manual_key | `OPENROUTER_API_KEY`, `OPENROUTER_AUTHORIZATION` | [Setup](https://openrouter.ai/settings/keys) | free-quota |
| Semantic Scholar research API | optional_key | `SEMANTIC_SCHOLAR_API_KEY` | [Setup](https://www.semanticscholar.org/product/api#api-key-form) | noncommercial |
| Slack Web API for a Free workspace | oauth_or_token | `SLACK_BOT_TOKEN`, `SLACK_AUTHORIZATION` | [Setup](https://api.slack.com/apps) | free-quota |
| Tavily search API | manual_key | `TAVILY_API_KEY` | [Setup](https://app.tavily.com/) | free-quota |
| Tavily official MCP | oauth_or_key | `TAVILY_API_KEY`, `TAVILY_AUTHORIZATION` | [Setup](https://app.tavily.com/) | free-quota |
| Telegram Bot API | manual_token | `TELEGRAM_BOT_TOKEN` | [Setup](https://core.telegram.org/bots#botfather) | free-quota |

## Details

- **Cloudflare Workers AI Free allocation:** Create a scoped Workers AI token and obtain the account ID. These are inputs for the documented account-specific API URL.
- **Context7 documentation MCP:** A free key is recommended for a higher quota; keyless access has lower limits.
- **DBHub database MCP:** Create a scoped database account, preferably read-only. Variable names are suggested secret-store names; DBHub's documented configuration determines how they are supplied.
- **Discord developer API:** Create an application/bot and grant minimum permissions; full header is Bot followed by the token.
- **Freesound noncommercial API:** Create an API key for allowed noncommercial use. Header syntax is Token followed by the key; sound download requires OAuth.
- **Gemini API Free tier:** Create an AI Studio key in an eligible region without linking paid billing.
- **Gitea self-hosted REST API:** Create an access token on the authorized local Gitea instance.
- **GitHub REST API:** Public reads support a lower unauthenticated quota; authenticated/private access requires a scoped token.
- **GitHub official MCP:** Use a fine-grained token limited to needed repositories. Obtain the official local server binary; configure its environment.
- **GitLab REST API:** Create a narrowly scoped access token on your free or self-hosted account.
- **Gmail API:** Create a Cloud project/OAuth app, enable only this API and authorize the minimum scope on an eligible personal account. Tokens stay in host secret storage.
- **Google Calendar API:** Create a Cloud project/OAuth app, enable only this API and authorize the minimum scope on an eligible personal account. Tokens stay in host secret storage.
- **Google Drive API:** Create a Cloud project/OAuth app, enable only this API and authorize the minimum scope on an eligible personal account. Tokens stay in host secret storage.
- **Google Sheets API:** Create a Cloud project/OAuth app, enable only this API and authorize the minimum scope on an eligible personal account. Tokens stay in host secret storage.
- **Groq API:** Create a Free-tier key. For the HTTP template, set GROQ_AUTHORIZATION to the complete Bearer header in the harness secret store.
- **Hugging Face Hub API and downloads:** Public repositories support keyless access; private/gated repositories may need a free scoped token and approval.
- **Jina Reader keyless API:** Keyless Reader is free at lower limits. An optional key uses tokens from a one-time free allowance, not a recurring free allocation; do not top up or enable auto-recharge. Use keyless Reader for the ongoing free path.
- **LinkedIn official Open Permissions:** Create a developer app and complete OAuth for the approved OIDC/member-social permissions; app/Page association and product approval steps can apply.
- **Mistral Studio Free mode:** Generate a Studio API key in Free mode; full Bearer header uses MISTRAL_AUTHORIZATION.
- **Notion data API:** Create an internal connection/token and share only relevant pages with it; store complete Bearer header for the template.
- **Notion official hosted MCP:** Complete the interactive OAuth flow in a supported harness; no manually pasted key is required.
- **OBS MCP (community):** Set the local OBS WebSocket password in OBS and the harness secret environment; this is not a paid API key.
- **OpenAlex API:** Basic keyless queries work; create a free account/key for the larger daily budget. The key is also an account credential, so keep it private.
- **OpenRouter free model variants:** Create a key without buying credits; store the complete Bearer header separately for the HTTP template.
- **Semantic Scholar research API:** Request an API key for eligible use; some endpoints require a key. Commercial use requires an expanded license, not assumed free.
- **Slack Web API for a Free workspace:** Create/install an app with narrow OAuth scopes in your authorized workspace; store full Bearer header separately.
- **Tavily search API:** Create a free account/key without a card; pass the key using the documented API authentication.
- **Tavily official MCP:** Authenticate using host OAuth, or a complete Bearer header in TAVILY_AUTHORIZATION. Do not put a key in the URL.
- **Telegram Bot API:** Create a bot with BotFather. The API URL contains the token at runtime, so no credential-bearing URL template is registered.

Optional keys can be omitted for the documented keyless path; omit the optional header from its client definition. OAuth refresh/client secrets, local DB/OBS passwords and nonsecret account IDs are listed alongside API keys so setup is complete. Disabled templates neither resolve credentials nor grant access.
