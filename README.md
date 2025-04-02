# mcp-gsuite MCP server

[![smithery badge](https://smithery.ai/badge/mcp-gsuite)](https://smithery.ai/server/mcp-gsuite)
MCP server to interact with Google produts.

## Example prompts

Right now, this MCP server supports Gmail and Calendar integration with the
following capabilities:

1. General

- Multiple google accounts

2. Gmail

- Get your Gmail user information
- Query emails with flexible search (e.g., unread, from specific senders, date
  ranges, with attachments)
- Retrieve complete email content by ID
- Create new draft emails with recipients, subject, body and CC options
- Delete draft emails
- Reply to existing emails (can either send immediately or save as draft)
- Retrieve multiple emails at once by their IDs.
- Save multiple attachments from emails to your local system.

3. Calendar

- Manage multiple calendars
- Get calendar events within specified time ranges
- Create calendar events with:
  - Title, start/end times
  - Optional location and description
  - Optional attendees
  - Custom timezone support
  - Notification preferences
- Delete calendar events

Example prompts you can try:

- Retrieve my latest unread messages
- Search my emails from the Scrum Master
- Retrieve all emails from accounting
- Take the email about ABC and summarize it
- Write a nice response to Alice's last email and upload a draft.
- Reply to Bob's email with a Thank you note. Store it as draft

- What do I have on my agenda tomorrow?
- Check my private account's Family agenda for next week
- I need to plan an event with Tim for 2hrs next week. Suggest some time slots.

## Quickstart

### Install

### Installing via Smithery

To install mcp-gsuite for Claude Desktop automatically via
[Smithery](https://smithery.ai/server/mcp-gsuite):

```bash
npx -y @smithery/cli install mcp-gsuite --client claude
```

#### Oauth 2

Google Workspace (G Suite) APIs require OAuth2 authorization. Follow these steps
to set up authentication:

1. Create OAuth2 Credentials:

   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API and Google Calendar API for your project
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Select "Desktop app" or "Web application" as the application type
   - Configure the OAuth consent screen with required information
   - Add authorized redirect URIs (include `http://localhost:4100/code` for
     local development)

2. Required OAuth2 Scopes:

```json
[
	"openid",
	"https://mail.google.com/",
	"https://www.googleapis.com/auth/calendar",
	"https://www.googleapis.com/auth/userinfo.email"
]
```

3. Then create a `.gauth.json` in your working directory with client

```json
{
	"web": {
		"client_id": "$your_client_id",
		"client_secret": "$your_client_secret",
		"redirect_uris": ["http://localhost:4100/code"],
		"auth_uri": "https://accounts.google.com/o/oauth2/auth",
		"token_uri": "https://oauth2.googleapis.com/token"
	}
}
```

4. Create a `.accounts.json` file with account information

```json
{
	"accounts": [
		{
			"email": "alice@bob.com",
			"account_type": "personal",
			"extra_info": "Additional info that you want to tell Claude: E.g. 'Contains Family Calendar'"
		}
	]
}
```

You can specifiy multiple accounts. Make sure they have access in your Google
Auth app. The `extra_info` field is especially interesting as you can add info
here that you want to tell the AI about the account (e.g. whether it has a
specific agenda)

Note: When you first execute one of the tools for a specific account, a browser
will open, redirect you to Google and ask for your credentials, scope, etc.
After a successful login, it stores the credentials in a local file called
`.oauth.{email}.json` . Once you are authorized, the refresh token will be used.

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>

```json
{
	"mcpServers": {
		"mcp-gsuite": {
			"command": "uv",
			"args": ["--directory", "<dir_to>/mcp-gsuite", "run", "mcp-gsuite"]
		}
	}
}
```

Note: You can also use the
`uv run mcp-gsuite --accounts-file /path/to/custom/.accounts.json` to specify a
different accounts file or `--credentials-dir /path/to/custom/credentials` to
specify a different credentials directory.

```json
{
	"mcpServers": {
		"mcp-gsuite": {
			"command": "uv",
			"args": [
				"--directory",
				"<dir_to>/mcp-gsuite",
				"run",
				"mcp-gsuite",
				"--accounts-file",
				"/path/to/custom/.accounts.json",
				"--credentials-dir",
				"/path/to/custom/credentials"
			]
		}
	}
}
```

</details>

<details>
  <summary>Published Servers Configuration</summary>

```json
{
	"mcpServers": {
		"mcp-gsuite": {
			"command": "uvx",
			"args": [
				"mcp-gsuite",
				"--accounts-file",
				"/path/to/custom/.accounts.json",
				"--credentials-dir",
				"/path/to/custom/credentials"
			]
		}
	}
}
```

</details>

### Configuration Options

The MCP server can be configured with several command-line options to specify
custom paths for authentication and account information:

- `--gauth-file`: Specifies the path to the `.gauth.json` file containing OAuth2
  client configuration. Default is `./.gauth.json`.
- `--accounts-file`: Specifies the path to the `.accounts.json` file containing
  information about the Google accounts. Default is `./.accounts.json`.
- `--credentials-dir`: Specifies the directory where OAuth credentials are
  stored after successful authentication. Default is the current working
  directory with a subdirectory for each account as `.oauth.{email}.json`.

#### Environment Variable Configuration

Alternatively, you can provide configuration directly via environment variables
instead of files:

- `GSUITE_OAUTH_CONFIG`: JSON string containing the OAuth2 client configuration
  (same structure as `.gauth.json`)
- `GSUITE_ACCOUNTS_CONFIG`: JSON array of account configurations (same structure
  as the "accounts" array in `.accounts.json`)
- `GSUITE_USE_MEMORY_STORAGE`: When set to "true", credentials will be stored in
  memory rather than on disk

Example using environment variables in your Claude Desktop configuration:

```json
{
	"mcpServers": {
		"mcp-gsuite": {
			"command": "uvx",
			"args": ["mcp-gsuite"],
			"env": {
				"GSUITE_OAUTH_CONFIG": "{\"web\":{\"client_id\":\"your-client-id\",\"project_id\":\"your-project\",\"auth_uri\":\"https://accounts.google.com/o/oauth2/auth\",\"token_uri\":\"https://oauth2.googleapis.com/token\",\"auth_provider_x509_cert_url\":\"https://www.googleapis.com/oauth2/v1/certs\",\"client_secret\":\"your-client-secret\",\"redirect_uris\":[\"http://localhost:4100/code\"],\"javascript_origins\":[\"http://localhost:3050\"]}}",
				"GSUITE_ACCOUNTS_CONFIG": "[{\"email\":\"your-email@example.com\",\"account_type\":\"work\",\"extra_info\":\"Your account description\"}]",
				"GSUITE_USE_MEMORY_STORAGE": "true"
			}
		}
	}
}
```

These options allow for flexibility in managing different environments or
multiple sets of credentials and accounts, especially useful in development and
testing scenarios.

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:

```bash
uv sync
```

2. Build package distributions:

```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:

```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command
flags:

- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and
  `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best
debugging experience, we strongly recommend using the
[MCP Inspector](https://github.com/modelcontextprotocol/inspector).

#### Using MCP Inspector with File-Based Configuration

You can launch the MCP Inspector via
[ `npm` ](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-gsuite run mcp-gsuite
```

#### Using MCP Inspector with Environment Variables

If you're using environment variables instead of configuration files, you can
pass them to the Inspector using the `-e` flag:

```bash
npx @modelcontextprotocol/inspector -e GSUITE_OAUTH_CONFIG='{...}' -e GSUITE_ACCOUNTS_CONFIG='[...]' -e GSUITE_USE_MEMORY_STORAGE=true uv --directory /path/to/mcp-gsuite run mcp-gsuite
```

For example, with the configuration from the examples above:

```bash
npx @modelcontextprotocol/inspector -e GSUITE_OAUTH_CONFIG='{"web":{"client_id":"your-client-id","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"your-client-secret","redirect_uris":["http://localhost:4100/code"],"javascript_origins":["http://localhost:3050"]}}' -e GSUITE_ACCOUNTS_CONFIG='[{"email":"your-email@example.com","account_type":"work","extra_info":"Your account description"}]' -e GSUITE_USE_MEMORY_STORAGE=true uv --directory /path/to/mcp-gsuite run mcp-gsuite
```

If needed, you can use the `--` separator to distinguish inspector flags from
server arguments:

```bash
npx @modelcontextprotocol/inspector -e GSUITE_OAUTH_CONFIG='{...}' -e GSUITE_ACCOUNTS_CONFIG='[...]' -- uv --directory /path/to/mcp-gsuite run mcp-gsuite
```

Upon launching, the Inspector will display a URL that you can access in your
browser to begin debugging.

You can also watch the server logs with this command:

```bash
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-mcp-gsuite.log
```
