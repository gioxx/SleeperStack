# 💤 SleeperStack

**SleeperStack** is a lightweight automation container that safely starts or stops Docker containers managed via Portainer, using labels.  
It's designed to work especially well with **Portainer Community Edition**, offering full functionality even without access to advanced stack metadata.

[![](https://img.shields.io/github/issues/gioxx/SleeperStack.svg)](https://github.com/gioxx/SleeperStack/issues)
[![](https://img.shields.io/github/issues-pr-raw/gioxx/SleeperStack.svg)](https://github.com/gioxx/SleeperStack/pulls)
[![MIT License](https://img.shields.io/github/license/gioxx/SleeperStack)](https://github.com/gioxx/SleeperStack/blob/main/LICENSE)
[![](https://img.shields.io/badge/GHCR-available-blue?logo=docker)](https://github.com/users/gioxx/packages/container/package/SleeperStack)
[![](https://img.shields.io/docker/pulls/gfsolone/sleeperstack.svg)](https://hub.docker.com/r/gfsolone/sleeperstack)
[![](https://img.shields.io/docker/image-size/gfsolone/sleeperstack/latest.svg)](https://hub.docker.com/r/gfsolone/sleeperstack)

---

## ✨ Features

- ✅ Stop or start **containers** (not stacks) based on custom labels
- ✅ 100% compatible with **Portainer Community Edition**
- ✅ Works with containers deployed via Docker Compose stacks
- ✅ Supports **multiple label values** for grouping (e.g. `night`, `weekend`)
- ✅ Reads container state: avoids redundant stop/start
- ✅ Optional dry-run mode to simulate actions
- ✅ Designed for safe automation: non-destructive and reversible
- ✅ **WebUI with internal scheduler** (default mode): manage multiple Portainer
  endpoints, schedule rules, trigger manual stop/start, browse run history and a
  full container inventory — no external cron required
- ✅ Legacy **one-shot CLI mode** still available for existing cron-based setups
- ✅ Import existing crontab lines straight into scheduled rules

---

## 🖥️ WebUI (server mode, default)

Starting the container without `MODE=oneshot` launches a small web application
(FastAPI) on port `8000`, backed by an internal scheduler (APScheduler) and a
SQLite database persisted in `/data`. A single instance manages **all** your
Portainer environments — no need to run one container per endpoint anymore.

| Page | Purpose |
|------|---------|
| `/login` | Sign in (single admin account, bootstrapped from env vars on first boot) |
| `/dashboard` | Live status of labeled containers per endpoint, manual stop/start |
| `/rules` | Create/enable/disable/delete scheduled rules (label + action + cron) |
| `/rules/import` | Paste your existing crontab lines and import them as rules |
| `/endpoints` | Manage Portainer connections (URL, API key, endpoint ID), test connectivity |
| `/history` | Log of every scheduled and manual run, with status and dry-run flag |
| `/inventory` | Full container census per endpoint — stack, image, ports, IP, uptime, labels |

### Required environment variables (server mode)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Long random string used to sign sessions and encrypt stored Portainer API keys |
| `ADMIN_USERNAME` | Username for the first admin account (default `admin`) |
| `ADMIN_PASSWORD` | Password for the first admin account, required only on first boot |
| `SLEEPERSTACK_DB_PATH` | (Optional) SQLite file path, default `/data/sleeperstack.db` |

```bash
docker run -d --name sleeperstack \
  -p 8000:8000 \
  -v sleeperstack-data:/data \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=change_me \
  gfsolone/sleeperstack
```

Then open `http://localhost:8000`, log in, add your Portainer endpoint(s) and
create rules — or use `/rules/import` to migrate the crontab lines you already
have (see below).

### Migrating from external cron

Paste your existing lines (the same ones you used with `docker run` +
host/Portainer cron) into `/rules/import`. SleeperStack parses the cron
schedule, label, action and endpoint from each line, matches it against a
configured endpoint, and lets you review before creating the equivalent rule
— nothing is imported silently.

---

## 💡 Why Community-Friendly?

Portainer Community Edition does not expose stack-level labels or tags via API.  
To ensure compatibility:

- SleeperStack works by reading labels applied to **individual containers**
- It uses `com.docker.compose.project` to associate containers with their stack name
- It avoids stack deletion or privileged operations
- It uses only officially documented API endpoints available to **API key users**

This makes it safe and accessible for all setups — even without Portainer Business features.

---

## 🚀 One-shot mode (legacy)

Set `MODE=oneshot` to keep using SleeperStack exactly like before: a single
run that stops/starts containers for one label on one Portainer endpoint,
then exits. Useful if you already have external cron jobs and don't want to
migrate yet.

### 🔧 Required Environment Variables

| Variable | Description |
|----------|-------------|
| `PORTAINER_URL` | Portainer API base URL (e.g. `http://localhost:9000/api`) |
| `PORTAINER_API_KEY` | API key from your Portainer user account |
| `PORTAINER_ENDPOINT_ID` | ID of the target Docker environment |
| `TARGET_LABEL` | Label to match containers, e.g. `autoshutdown=night` or `autoshutdown=night,weekend` |
| `ACTION` | Either `stop` or `start` |
| `DRY_RUN` | (Optional) Set to `true` to simulate actions without executing |

---

### 🧪 Example (.env + local)

```env
PORTAINER_URL=http://dockerlab.local:9002/api
PORTAINER_API_KEY=your_api_key
PORTAINER_ENDPOINT_ID=2
ACTION=stop
TARGET_LABEL=autoshutdown=night,weekend
DRY_RUN=true
```

Then run:

```bash
python3 main.py
```

---

## 📦 Docker Image Availability

SleeperStack is available on:

- **Docker Hub**: [`gfsolone/sleeperstack`](https://hub.docker.com/r/gfsolone/sleeperstack)
- **GitHub Container Registry**: [`ghcr.io/gioxx/sleeperstack`](https://github.com/gioxx/SleeperStack/pkgs/container/sleeperstack)

You can pull it with:

```bash
docker pull ghcr.io/gioxx/sleeperstack:latest
```

---

### 🐳 Docker run example (one-shot)

```bash
docker run --rm --env-file .env -e MODE=oneshot gfsolone/sleeperstack
```

---

## 🏷️ How to label your containers

In your `docker-compose.yml`, add:

```yaml
services:
  myapp:
    image: my/image
    labels:
      autoshutdown: "night"
```

You can group containers using different values:

- `autoshutdown: "night"`
- `autoshutdown: "weekend"`
- `autoshutdown: "testlab"`

Then run:

```bash
TARGET_LABEL=autoshutdown=night,weekend ACTION=stop python3 main.py
```

---

## 🚦 Dry Run Mode

To preview what would happen:

```bash
DRY_RUN=true ACTION=stop python3 main.py
```

No containers will actually be stopped or started.

---

## 📅 Scheduling

You can run this tool via:

- Portainer Scheduled Jobs
- Host-level `cron`
- CI/CD systems

Set different `TARGET_LABEL` and `ACTION` values to automate multiple groups.

---

## 🧠 Notes

- Only containers with the target label are affected.
- Stack data is untouched — **no stack removal** or modifications.
- Uses `?all=true` to support stopped container discovery.
- Designed for compatibility with Portainer Community and API Key access.

---

## 🕓 Example crontab schedules

You can automate SleeperStack with multiple cronjobs to control different groups of containers based on their labels.

### 🔌 Turn off test containers at night (22:00)

```
0 22 * * * docker run --rm -e MODE=oneshot -e PORTAINER_URL=... -e PORTAINER_API_KEY=... -e PORTAINER_ENDPOINT_ID=2 -e TARGET_LABEL=autoshutdown=night -e ACTION=stop gfsolone/sleeperstack
```

### 🌅 Turn them back on in the morning (07:00)

```
0 7 * * * docker run --rm -e MODE=oneshot -e PORTAINER_URL=... -e PORTAINER_API_KEY=... -e PORTAINER_ENDPOINT_ID=2 -e TARGET_LABEL=autoshutdown=night -e ACTION=start gfsolone/sleeperstack
```

### 🧪 Stop weekend-only environments (Friday 19:00)

```
0 19 * * 5 docker run --rm -e MODE=oneshot -e PORTAINER_URL=... -e PORTAINER_API_KEY=... -e PORTAINER_ENDPOINT_ID=2 -e TARGET_LABEL=autoshutdown=weekend -e ACTION=stop gfsolone/sleeperstack
```

### 🗓️ Restart them on Monday morning (08:30)

```
30 8 * * 1 docker run --rm -e MODE=oneshot -e PORTAINER_URL=... -e PORTAINER_API_KEY=... -e PORTAINER_ENDPOINT_ID=2 -e TARGET_LABEL=autoshutdown=weekend -e ACTION=start gfsolone/sleeperstack
```

📌 Tip: You can extract shared env vars into a `.env` file and reuse with `--env-file`.

---

## 🐳 Docker Compose example

### 🖥️ Server mode (recommended)

A ready-to-use `docker-compose.yml` is included in the repo:

```yaml
services:
  sleeperstack:
    image: gfsolone/sleeperstack:latest
    container_name: sleeperstack
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - sleeperstack-data:/data
    environment:
      SECRET_KEY: ${SECRET_KEY:?set a long random string, e.g. openssl rand -hex 32}
      ADMIN_USERNAME: ${ADMIN_USERNAME:-admin}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD:?set the initial admin password}

volumes:
  sleeperstack-data:
```

Create a `.env` file next to it with `SECRET_KEY`, `ADMIN_USERNAME` and
`ADMIN_PASSWORD`, then:

```bash
docker compose up -d
```

The scheduler, all Portainer endpoints and every rule live inside this one
long-running container — no separate cron sidecar needed anymore.

---

### 🧠 One-shot mode (legacy, manual or external cron)

```yaml
services:
  sleeperstack-night:
    image: gfsolone/sleeperstack
    restart: "no"
    environment:
      MODE: oneshot
      PORTAINER_URL: http://dockerlab.local:9002/api
      PORTAINER_API_KEY: your_api_key
      PORTAINER_ENDPOINT_ID: "2"
      TARGET_LABEL: autoshutdown=night
      ACTION: stop
```

Run it manually:

```bash
docker compose run --rm sleeperstack-night
```

### ⏱️ One-shot mode with docker-cron

```yaml
services:
  sleeperstack-nightly:
    image: gfsolone/sleeperstack
    environment:
      MODE: oneshot
      PORTAINER_URL: http://dockerlab.local:9002/api
      PORTAINER_API_KEY: your_api_key
      PORTAINER_ENDPOINT_ID: "2"
      TARGET_LABEL: autoshutdown=night
      ACTION: stop

  cron:
    image: aptible/docker-cron
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      CRON_TIME: "0 22 * * *"
      CRON_COMMAND: "docker compose run --rm sleeperstack-nightly"
```

📌 Note: docker-cron triggers commands in its environment, so keep `docker.sock` mounted and `docker compose` installed if required. This whole setup (a second container just to trigger cron) is what the built-in scheduler in server mode replaces.

---

## 📄 License

MIT — free to use, modify and distribute.

---

## 🤝 Contributions

Pull requests welcome!  
SleeperStack is built for responsible automation in all environments, including Community users.
