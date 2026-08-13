from pathlib import Path

ROOT = Path(__file__).parent.parent
RATE_LIMITS_DOC = ROOT / 'docs' / 'reference' / 'rate-limits.md'

EXPECTED_PLAN_ROWS = {
    'Personal': ('5 per minute and 100 per hour', '72,000 queries', '50 per minute and 1,000 per hour'),
    'Team': ('No plan-specific rate', 'No plan-specific quota', '50 per minute and 1,000 per hour'),
    'Growth': ('No plan-specific rate', 'No plan-specific quota', '50 per minute and 1,000 per hour'),
    'Enterprise': (
        'Set by your contract and deployment',
        'Set by your contract and deployment',
        'Set by your contract and deployment',
    ),
}


def test_rate_limit_public_contract_and_discoverability() -> None:
    text = RATE_LIMITS_DOC.read_text()
    table_rows = {
        columns[0]: tuple(columns[1:])
        for line in text.splitlines()
        if line.startswith('| ')
        if (columns := [column.strip() for column in line.strip('|').split('|')])[0] in EXPECTED_PLAN_ROWS
    }

    assert table_rows == EXPECTED_PLAN_ROWS
    assert '`429 Too Many Requests` with `Retry-After`' in text
    assert '`429 Too Many Requests` without `Retry-After`' in text
    assert '`Rate limit exceeded (minute)`' in text
    assert '`Rate limit exceeded (hour)`' in text
    assert '`413 Payload Too Large`' in text
    assert '`402 Payment Required`' in text
    assert '| Query API result | 100 rows | 10,000 rows |' in text
    assert '| OpenTelemetry Protocol (OTLP) HTTP telemetry body | Not applicable | 100 MB |' in text
    assert '100 MB on Personal and 500 MB on Team' in text

    navigation = (ROOT / 'docs' / 'navigation.yml').read_text()
    assert 'path: "reference/rate-limits.md"' in navigation
    assert '../reference/rate-limits.md' in (ROOT / 'docs' / 'how-to-guides' / 'query-api.md').read_text()
    assert 'reference/rate-limits.md' in (ROOT / 'docs' / 'logfire-costs.md').read_text()
