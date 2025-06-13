# 💤 SleeperStack Launcher

A convenient wrapper script for running [SleeperStack](https://github.com/gioxx/SleeperStack) using Docker.  
This script allows you to manage Portainer stacks or containers labeled for automatic shutdown and restart based on environment and schedule.

## ✨ Features

- Run `SleeperStack` with specific labels, endpoint, and profile
- Supports multiple Portainer instances via `--profile`
- Pulls container image only if not available locally
- Dry-run support for test execution
- Option to manually update the Docker image

## 📂 Files Included

- `SleeperStack.sh`: main launcher script
- `sample.secrets`: example secrets file to define your API keys and URLs

## 🚀 Usage

Make the script executable first:

```bash
chmod +x SleeperStack.sh
```

### Run a stop/start action

```bash
./SleeperStack.sh --action stop --group night --endpoint 2 --profile lab
./SleeperStack.sh --action start --group night --endpoint 2 --profile lab
```

### Run in dry-run mode (no real action performed)

```bash
./SleeperStack.sh --action stop --group test --endpoint 1 --profile prod --dry-run
```

### Update the container image only

```bash
./SleeperStack.sh --update-image
```

## 👻 .secrets format

This file should never be committed to Git. Add entries per profile like this:

```bash
# For lab profile
PORTAINER_API_KEY_LAB="your-lab-api-key"
PORTAINER_URL_LAB="http://your-lab-host:9002/api"

# For prod profile
PORTAINER_API_KEY_PROD="your-prod-api-key"
PORTAINER_URL_PROD="http://your-prod-host:9002/api"
```

> Copy `sample.secrets` to `.secrets` and customize your values.

## ⏱️ Crontab Example

```cron
0 22 * * * /Script-Absolute-Path/SleeperStack.sh --action stop --group night --endpoint 2 --profile lab >> /var/log/sleeperstack.log 2>&1
0 7  * * * /Script-Absolute-Path/SleeperStack.sh --action start --group night --endpoint 2 --profile lab >> /var/log/sleeperstack.log 2>&1
```

## 📄 License

MIT License — see main [SleeperStack](https://github.com/gioxx/SleeperStack) repository.

## 🤝 Contributions

Pull requests welcome!  
SleeperStack is built for responsible automation in all environments, including Community users.
