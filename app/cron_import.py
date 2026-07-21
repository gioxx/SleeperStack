import re

CRON_FIELDS_RE = re.compile(
    r"^\s*(\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+(.*docker\s+run.*)$"
)
ENV_VAR_RE = re.compile(r"-e\s+([A-Z_]+)=(\S+)")


class ParsedCronLine:
    def __init__(self, raw_line, cron_expression=None, action=None, target_label=None,
                 portainer_url=None, endpoint_id=None, error=None):
        self.raw_line = raw_line
        self.cron_expression = cron_expression
        self.action = action
        self.target_label = target_label
        self.portainer_url = portainer_url
        self.endpoint_id = endpoint_id
        self.error = error

    @property
    def is_valid(self):
        return self.error is None


def parse_crontab_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    match = CRON_FIELDS_RE.match(line)
    if not match:
        return ParsedCronLine(raw_line=line, error="Line does not look like a cron + docker run command")

    cron_expression, command = match.group(1), match.group(2)
    env_vars = dict(ENV_VAR_RE.findall(command))

    action = env_vars.get("ACTION")
    target_label = env_vars.get("TARGET_LABEL")
    portainer_url = env_vars.get("PORTAINER_URL")
    endpoint_id = env_vars.get("PORTAINER_ENDPOINT_ID")

    missing = [
        name
        for name, value in [
            ("ACTION", action),
            ("TARGET_LABEL", target_label),
            ("PORTAINER_URL", portainer_url),
            ("PORTAINER_ENDPOINT_ID", endpoint_id),
        ]
        if not value
    ]
    if missing:
        return ParsedCronLine(
            raw_line=line, error=f"Missing environment variable(s): {', '.join(missing)}"
        )

    return ParsedCronLine(
        raw_line=line,
        cron_expression=cron_expression,
        action=action,
        target_label=target_label,
        portainer_url=portainer_url.rstrip("/"),
        endpoint_id=endpoint_id,
    )


def parse_crontab_text(text):
    results = []
    for line in text.splitlines():
        parsed = parse_crontab_line(line)
        if parsed is not None:
            results.append(parsed)
    return results
