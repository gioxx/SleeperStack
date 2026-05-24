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
- ✅ Optional `--dry-run` mode to simulate actions
- ✅ Designed for safe automation: non-destructive and reversible
- ✅ Easily integrates with cron, Portainer Scheduled Jobs, or CI

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

## 🚀 Usage

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

### 🐳 Docker run example

```bash
docker run --rm --env-file .env gfsolone/sleeperstack
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
0 22 * * * docker run --rm -e PORTAINER_URL=... -e PORTAINER_API_KEY=... -e PORTAINER_ENDPOINT_ID=2 -e TARGET_LABEL=autoshutdown=night -e ACTION=stop gfsolone/sleeperstack
```

### 🌅 Turn them back on in the morning (07:00)

```
0 7 * * * docker run --rm -e PORTAINER_URL=... -e PORTAINER_API_KEY=... -e PORTAINER_ENDPOINT_ID=2 -e TARGET_LABEL=autoshutdown=night -e ACTION=start gfsolone/sleeperstack
```

### 🧪 Stop weekend-only environments (Friday 19:00)

```
0 19 * * 5 docker run --rm -e PORTAINER_URL=... -e PORTAINER_API_KEY=... -e PORTAINER_ENDPOINT_ID=2 -e TARGET_LABEL=autoshutdown=weekend -e ACTION=stop gfsolone/sleeperstack
```

### 🗓️ Restart them on Monday morning (08:30)

```
30 8 * * 1 docker run --rm -e PORTAINER_URL=... -e PORTAINER_API_KEY=... -e PORTAINER_ENDPOINT_ID=2 -e TARGET_LABEL=autoshutdown=weekend -e ACTION=start gfsolone/sleeperstack
```

📌 Tip: You can extract shared env vars into a `.env` file and reuse with `--env-file`.

---

## 🐳 Docker Compose example

You can use `docker-compose` to schedule SleeperStack with different labels and time-based logic using cron syntax inside the container or with external tools like [docker-cron](https://hub.docker.com/r/aptible/docker-cron).

### 🧠 Basic example (manual run)

```yaml
services:
  sleeperstack-night:
    image: gfsolone/sleeperstack
    restart: "no"
    environment:
      PORTAINER_URL: http://dockerlab.local:9002/api
      PORTAINER_API_KEY: your_api_key
      PORTAINER_ENDPOINT_ID: "2"
      TARGET_LABEL: autoshutdown=night
      ACTION: stop
```

Run it manually:

```bash
docker-compose run --rm sleeperstack-night
```

---

### ⏱️ With docker-cron

```yaml
services:
  sleeperstack-nightly:
    image: gfsolone/sleeperstack
    environment:
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
      CRON_COMMAND: "docker-compose run --rm sleeperstack-nightly"
```

📌 Note: docker-cron triggers commands in its environment, so keep `docker.sock` mounted and `docker-compose` installed if required.

---

## 📄 License

MIT — free to use, modify and distribute.

---

## 🤝 Contributions

Pull requests welcome!  
SleeperStack is built for responsible automation in all environments, including Community users.
