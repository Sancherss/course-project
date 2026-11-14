"""Parse only documented RESULT records; never infer attacks from incidental words."""
from __future__ import annotations
import re
from .results import Status, QueryResult, ParsedResult

RECORD = re.compile(r'^RESULT\s+(.+?)\s+(is true|is false|cannot be proved)\.\s*$', re.MULTILINE)
ERROR = re.compile(r'(?im)^\s*(?:Error:|Fatal error:|Syntax error\b)')

def parse_output(stdout: str, stderr: str = '', *, exit_code: int = 0, timed_out: bool = False) -> ParsedResult:
    mapping = {'is true': Status.PROVED, 'is false': Status.ATTACK_OR_FALSE, 'cannot be proved': Status.UNKNOWN}
    queries = tuple(QueryResult(m[1], mapping[m[2]], m[0].strip()) for m in RECORD.finditer(stdout))
    warnings = tuple(x for x in (stdout+'\n'+stderr).splitlines() if 'warning' in x.lower())
    if ERROR.search(stdout+'\n'+stderr):
        return ParsedResult(Status.ERROR, queries, 'ProVerif reported an error diagnostic', warnings)
    if timed_out:
        return ParsedResult(Status.UNKNOWN, queries, 'Timeout: verification incomplete', warnings)
    if exit_code != 0:
        return ParsedResult(Status.ERROR, queries, f'Nonzero process exit code: {exit_code}', warnings)
    all_records = [x for x in stdout.splitlines() if x.startswith('RESULT ')]
    if len(all_records) != len(queries):
        return ParsedResult(Status.UNKNOWN, queries, 'Unrecognized RESULT format; raw output retained', warnings)
    if not queries:
        return ParsedResult(Status.UNKNOWN, (), 'No documented RESULT record', warnings)
    for query in {q.query for q in queries}:
        if len({q.status for q in queries if q.query == query}) > 1:
            return ParsedResult(Status.ERROR, queries, 'Conflicting RESULT records for the same query', warnings)
    statuses = {q.status for q in queries}
    if Status.ATTACK_OR_FALSE in statuses:
        return ParsedResult(Status.ATTACK_OR_FALSE, queries, 'At least one RESULT is false; interpret the specific query', warnings)
    if Status.UNKNOWN in statuses:
        return ParsedResult(Status.UNKNOWN, queries, 'At least one RESULT cannot be proved', warnings)
    return ParsedResult(Status.PROVED, queries, 'All documented RESULT records are true', warnings)
