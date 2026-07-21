from app.cron_import import parse_crontab_line, parse_crontab_text

SAMPLE_LINE = (
    "0 22 * * * docker run --rm -e PORTAINER_URL=http://dockerlab.local:9002/api "
    "-e PORTAINER_API_KEY=abc123 -e PORTAINER_ENDPOINT_ID=2 "
    "-e TARGET_LABEL=autoshutdown=night -e ACTION=stop gfsolone/sleeperstack"
)


def test_parse_valid_line_extracts_all_fields():
    parsed = parse_crontab_line(SAMPLE_LINE)

    assert parsed.is_valid
    assert parsed.cron_expression == "0 22 * * *"
    assert parsed.action == "stop"
    assert parsed.target_label == "autoshutdown=night"
    assert parsed.portainer_url == "http://dockerlab.local:9002/api"
    assert parsed.endpoint_id == "2"


def test_parse_line_missing_action_returns_error():
    line = SAMPLE_LINE.replace("-e ACTION=stop ", "")
    parsed = parse_crontab_line(line)

    assert not parsed.is_valid
    assert "ACTION" in parsed.error


def test_parse_non_cron_line_returns_error():
    parsed = parse_crontab_line("this is not a cron line")

    assert not parsed.is_valid


def test_parse_blank_and_comment_lines_are_skipped():
    assert parse_crontab_line("") is None
    assert parse_crontab_line("   ") is None
    assert parse_crontab_line("# a comment") is None


def test_parse_crontab_text_handles_multiple_lines():
    text = f"# comment\n{SAMPLE_LINE}\n\nnot a cron line"

    results = parse_crontab_text(text)

    assert len(results) == 2
    assert results[0].is_valid
    assert not results[1].is_valid
