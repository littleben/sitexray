# SiteXray

An open Agent Skill for web application security checks: review source code in your agent's workspace, or call the [SiteXray website scanner](https://sitexray.net) for a passive check of an authorized public website.

[Website](https://sitexray.net) · [Install and API guide](https://sitexray.net/skill) · [Agent-readable instructions](https://sitexray.net/skill.md)

## Install

From your project directory:

```bash
npx skills add littleben/sitexray --skill sitexray
```

The installer requires Node.js 22.20+. Choose your agent during installation. The skill uses the [Agent Skills format](https://agentskills.io/specification) and can be used with compatible agents including Codex, Claude Code and Cursor. See the [skills CLI documentation](https://github.com/vercel-labs/skills) for agent selection and installation options.

You can also give an agent this URL without installing a package:

```text
Read https://sitexray.net/skill.md and use it to check my web project.
```

## Two ways to use it

### Review a local project

```text
Use $sitexray to review this web project for security issues.
Show confirmed findings, affected files and practical fixes.
```

The agent reviews authentication and authorization, data isolation, unsafe input handling, secret exposure, uploads, outbound requests, deployment settings and relevant dependency risks. It uses the project's existing tools and does not send source code to SiteXray. The instructions distinguish evidence from unverified suspicions and keep inspection separate from changes to production.

### Scan a deployed website

```text
Use $sitexray to scan https://your-site.example. I own this website.
Explain the findings and give me the report link.
```

The hosted scanner checks TLS, security headers, cookies, software banners, exposed files and secrets in public assets. No account or API key is required. Only scan websites you own, manage or have permission to test.

## Python helper

The helper requires Python 3.9+ and only uses its standard library. From this cloned repository:

```bash
python3 skills/sitexray/scripts/scan.py https://your-site.example --authorized --json
```

Replace the example URL with your authorized target. `--authorized` records permission already established by the task; the helper does not ask an interactive question. Omit `--json` for a readable summary. Add `--locale zh` for a Chinese report link.

The JSON output includes the website's report fields and `reportUrl`. If the scan completed but could not be saved, `reportUrl` is `null`. The helper reports errors and rate limits without automatically retrying them.

## Direct HTTP API

Agents with HTTP tools can call the [SiteXray scanner](https://sitexray.net) directly:

```bash
curl --max-time 90 https://sitexray.net/api/scan \
  -H 'Content-Type: application/json' \
  --data '{"url":"https://your-site.example","authorized":true}'
```

The success envelope is `{ "code": 0, "message": "ok", "data": { ...report } }`. Reports include `target`, `finalUrl`, `scannedAt`, `durationMs`, `grade`, `score`, severity `counts`, `findings` and `dataUpdated`; TLS information may also be present. Findings contain `id`, `category`, `severity`, and optional `params` and masked `evidence`.

When `data.id` is present, the report is available at `https://sitexray.net/report/REPORT_ID`, with `REPORT_ID` replaced by that value. Chinese reports use `/zh/report/REPORT_ID`. Opening a saved report does not rescan the website.

Allow up to 90 seconds per request. Calls are currently limited to one per eight seconds per client; scans of the same host may reuse a report for about five minutes. Respect HTTP 429 and `Retry-After`. A nonzero `code` is an application error; HTTP errors include 400 for invalid input or missing authorization, 422 for blocked or unreachable targets, and 429 for rate limiting.

## Scope and data

Local review does not upload source code to SiteXray. Hosted scans send the target URL and create an unlisted report that anyone with its random link can view. Report pages use `noindex`; they are shareable, not access-controlled. Do not submit URLs containing credentials or private query parameters. See the [privacy policy](https://sitexray.net/privacy-policy).

Passive checks do not test code behind a login or establish that business logic, database policies or an entire site are secure. An A grade is not a penetration-test result. The skill does not perform active exploitation.

## 中文

SiteXray 是一个开源网站安全检查 skill：可以让 agent 在工作区审查源码，也可以调用 [SiteXray 网站](https://sitexray.net/zh) 对已获授权的线上网站做被动检查，并返回可分享报告。

安装命令：`npx skills add littleben/sitexray --skill sitexray`。使用时可告诉 agent：

```text
使用 $sitexray 检查这个网站项目的安全问题，列出已确认的问题和修复建议。
```

或：

```text
使用 $sitexray 扫描 https://your-site.example，这是我自己的网站。
解释扫描结果，并给我报告链接。
```

[中文使用说明](https://sitexray.net/zh/skill) · [在线网站扫描器](https://sitexray.net/zh)

## License

MIT. This repository contains the skill, review guidance and HTTP helper; it does not contain the hosted application's source code.
