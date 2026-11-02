import hashlib
import io
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.documents import DuplicateKey, dump_document, load_document
from app.core.errors import ToolError
from app.schemas.compare import CompareOptions
from app.schemas.hash import HashOptions
from app.schemas.json import JsonOptions
from app.schemas.logs import LogsOptions
from app.schemas.sanitize import Replacement, SanitizeOptions
from app.schemas.text import TextOptions
from app.services.compare import compare
from app.services.hash import hash_stream, hash_text
from app.services.json import inspect_json
from app.services.logs import inspect_logs, parse_syslog
from app.services.sanitize import sanitize
from app.services.text import transform_text


# Resolve overlapping email/username literals while preserving repeated aliases.
def test_longest_match_and_repeated_alias() -> None:
    result = sanitize(
        SanitizeOptions(
            text="alice@acme.test alice alice@acme.test",
            replacements=[
                Replacement(category="username", source="alice"),
                Replacement(category="email", source="alice@acme.test"),
            ],
        )
    )
    assert result["output"] == "EMAIL_001 USER_001 EMAIL_001"
    assert result["meta"]["matches"] == 3


# Never feed generated replacement strings back through the mapping engine.
def test_non_cascading() -> None:
    result = sanitize(
        SanitizeOptions(
            text="alice bob",
            replacements=[
                Replacement(category="custom", source="alice", replacement="bob"),
                Replacement(category="custom", source="bob", replacement="safe"),
            ],
        )
    )
    assert result["output"] == "bob safe"


# Reserve aliases that already appear in the original document.
def test_placeholder_collision() -> None:
    result = sanitize(
        SanitizeOptions(
            text="USER_001 alice", replacements=[Replacement(category="username", source="alice")]
        )
    )
    assert result["output"] == "USER_001 USER_002"


# Reject conflicting mappings before any replacement is performed.
def test_conflicting_casefold_mappings() -> None:
    with pytest.raises(ToolError):
        sanitize(
            SanitizeOptions(
                text="ALICE",
                case_sensitive=False,
                replacements=[
                    Replacement(category="username", source="alice"),
                    Replacement(category="company", source="ALICE"),
                ],
            )
        )


# Keep Unicode casefold replacements and code-point highlight spans aligned.
def test_unicode_and_spans() -> None:
    result = sanitize(
        SanitizeOptions(
            text="😀 Straße\n",
            case_sensitive=False,
            replacements=[Replacement(category="company", source="STRASSE")],
        )
    )
    assert result["output"] == "😀 COMPANY_001\n"
    assert result["data"]["spans"] == [[2, 13]]


# Whole-token mode must not replace a name inside a larger word.
def test_whole_token() -> None:
    result = sanitize(
        SanitizeOptions(
            text="alice malice",
            whole_token=True,
            replacements=[Replacement(category="username", source="alice")],
        )
    )
    assert result["output"] == "USER_001 malice"


# Report unmatched supplied values without modifying unrelated text.
def test_zero_matches() -> None:
    result = sanitize(
        SanitizeOptions(
            text="untouched", replacements=[Replacement(category="username", source="alice")]
        )
    )
    assert result["output"] == "untouched"
    assert result["data"]["matches"][0]["count"] == 0


# Scope mapping dictionaries to individual operations.
def test_independent_operations() -> None:
    results = []
    for user in ("alice", "bob"):
        results.append(
            sanitize(
                SanitizeOptions(
                    text=user, replacements=[Replacement(category="username", source=user)]
                )
            )["output"]
        )
    assert results == ["USER_001", "USER_001"]


# Selected pattern masking validates IP syntax instead of hiding every dotted number.
def test_selected_patterns() -> None:
    result = sanitize(
        SanitizeOptions(
            text="a@acme.test 192.0.2.1 999.999.999.999", mode="patterns", patterns=["email", "ip"]
        )
    )
    assert "EMAIL_001" in result["output"]
    assert "IP_001" in result["output"]
    assert "999.999.999.999" in result["output"]


# JSON field masking preserves exact unselected numeric values.
def test_json_field_masking() -> None:
    result = sanitize(
        SanitizeOptions(
            text='{"user":"alice","id":9007199254740993,"nested":{"user":"alice"}}',
            mode="json_fields",
            fields=["user"],
        )
    )
    value = load_document(result["output"])
    assert value["user"] == value["nested"]["user"]
    assert value["id"] == 9007199254740993


# A repeated single-character literal cannot generate unbounded output.
def test_match_budget() -> None:
    with pytest.raises(ToolError):
        sanitize(
            SanitizeOptions(
                text="a" * 10001, replacements=[Replacement(category="custom", source="a")]
            )
        )


# Natural sorting orders numeric chunks without converting arbitrarily long integers.
def test_natural_sort() -> None:
    result = transform_text(TextOptions(text="host-10\nhost-2\nhost-1\n", natural=True))
    assert result["output"] == "host-1\nhost-2\nhost-10\n"


# Keep-last deduplication preserves surviving spelling and order.
def test_keep_last_preserves_original() -> None:
    result = transform_text(
        TextOptions(
            text=" A \na\nB\n", action="deduplicate", trim=True, case_sensitive=False, keep="last"
        )
    )
    assert result["output"] == "a\nB\n"


# Grapheme mode treats joined emoji and combining characters as complete units.
def test_graphemes() -> None:
    result = transform_text(
        TextOptions(text="👨‍👩‍👧‍👦👨‍👩‍👧‍👦éé", action="deduplicate", unit="graphemes")
    )
    assert result["output"] == "👨‍👩‍👧‍👦é"


# Empty input, trailing separators, and CRLF follow the documented line contract.
@pytest.mark.parametrize(("source", "expected"), [("", ""), ("b\r\na\r\n", "a\nb\n"), ("\n", "\n")])
def test_line_boundaries(source: str, expected: str) -> None:
    assert transform_text(TextOptions(text=source))["output"] == expected


# Reapplying deduplication with the same options must be idempotent.
def test_idempotent_deduplication() -> None:
    first = transform_text(TextOptions(text="b\na\nb", action="deduplicate"))["output"]
    assert transform_text(TextOptions(text=first, action="deduplicate"))["output"] == first


# JSON numbers must round-trip beyond native browser precision.
def test_exact_numbers() -> None:
    text = '{"id":9007199254740993,"rate":0.1234567890123456789}'
    value = load_document(text)
    assert value["rate"] == Decimal("0.1234567890123456789")
    assert load_document(dump_document(value)) == value
    result = inspect_json(JsonOptions(text=text))
    assert result["data"]["tree"]["children"][0]["value"] == "9007199254740993"


# Duplicate object keys remain raw rather than silently choosing the last value.
def test_duplicate_keys_remain_raw() -> None:
    text = '{"user":"a","user":"b"}'
    assert inspect_json(JsonOptions(text=text))["output"] == text
    with pytest.raises(DuplicateKey):
        load_document(text)


# Boolean tree values use JSON spelling rather than Python representations.
def test_boolean_tree() -> None:
    result = inspect_json(JsonOptions(text='{"ok":true,"missing":null}'))
    assert result["data"]["tree"]["children"][0]["value"] == "true"


# Projection supports useful field access without constructed-output amplification.
def test_projection_subset() -> None:
    result = inspect_json(
        JsonOptions(text='{"events":[{"ip":"192.0.2.1"}]}', action="query", query="events[*].ip")
    )
    assert load_document(result["output"]) == ["192.0.2.1"]
    with pytest.raises(ToolError):
        inspect_json(JsonOptions(text="{}", action="query", query="{a:@,b:@}"))


# Reject nesting bombs, non-finite numbers, and unpaired decoded surrogates.
@pytest.mark.parametrize("source", ["[" * 65 + "0" + "]" * 65, '{"a":NaN}', '{"a":"\\ud800"}'])
def test_malformed_json_and_limits(source: str) -> None:
    with pytest.raises(ToolError):
        load_document(source)


# Strict schemas reject unknown options and literal Unicode surrogates.
def test_strict_input_schema() -> None:
    with pytest.raises(ValidationError):
        TextOptions(text="hello", accidental=True)
    with pytest.raises(ValidationError):
        TextOptions(text="\ud800")


# Set comparisons retain the spelling of the first normalized input.
def test_list_membership() -> None:
    result = compare(
        CompareOptions(
            a=" A \nb", b="a\nc", trim=True, case_sensitive=False, operation="intersection"
        )
    )
    assert result["output"] == " A "
    assert result["meta"]["union"] == 3


# Array ordering and Boolean-versus-number types remain significant in JSON diffs.
def test_json_order_and_types() -> None:
    assert (
        "No structural"
        in compare(CompareOptions(a='{"a":1,"b":2}', b='{"b":2,"a":1}', mode="json"))["output"]
    )
    assert compare(CompareOptions(a="[1,2]", b="[2,1]", mode="json"))["meta"]["changes"] > 0
    assert compare(CompareOptions(a="true", b="1", mode="json"))["meta"]["changes"] > 0


# Text comparison reports final newline differences separately.
def test_final_newline() -> None:
    assert (
        "Final line break differs"
        in compare(CompareOptions(a="line", b="line\n", mode="text"))["output"]
    )


# Verify fingerprints against independently called hashlib primitives.
@pytest.mark.parametrize("source", ["", "abc", "abc\n", "😀"])
def test_hash_vectors(source: str) -> None:
    result = hash_text(HashOptions(text=source, algorithms=["md5", "sha1", "sha256", "sha512"]))
    for name, digest in result["data"]["digests"].items():
        assert digest == hashlib.new(name, source.encode(), usedforsecurity=False).hexdigest()


# File hashing reads exact binary content and never uses supplied names as paths.
def test_binary_file_and_magic() -> None:
    result = hash_stream(io.BytesIO(b"%PDF-1.7\n\x00\xff"), ["sha256"], filename="../../sample.exe")
    assert result["meta"]["extension_mismatch"]
    assert result["meta"]["signature"] == "PDF"


# Identification remains ambiguous and unsupported algorithms fail clearly.
def test_hash_candidate_and_algorithm() -> None:
    assert "another" in hash_text(HashOptions(text="a" * 32, action="identify"))["output"]
    with pytest.raises(ToolError):
        hash_text(HashOptions(text="abc", algorithms=["arbitrary"]))


# Malformed JSONL records remain visible and exportable.
def test_jsonl_errors() -> None:
    result = inspect_logs(LogsOptions(text='{"host":"a"}\nbad\n{"host":"b"}'))
    assert result["meta"]["source_records"] == 3
    assert result["meta"]["malformed"] == 1
    assert '"_raw":"bad"' in result["output"]


# CSV quoting preserves multiline cells and safe exports neutralize formulas.
def test_multiline_csv_and_formula() -> None:
    result = inspect_logs(
        LogsOptions(text='name,note\n"=SUM(A1)","line1\nline2"\n', format="csv", export="csv")
    )
    assert result["meta"]["matching_records"] == 1
    assert "'=SUM(A1)" in result["output"]
    assert "line1\nline2" in result["output"]


# Syslog parsing respects escaped brackets inside structured parameter values.
def test_syslog_structure() -> None:
    record = parse_syslog('<34>1 2026-01-01T00:00:00Z host app 123 ID47 [meta x="a\\]b"] message')
    assert record["message"] == "message"
    assert record["severity"] == 2


# Missing-field counts use an explicit matching-record denominator.
def test_filtered_summary() -> None:
    result = inspect_logs(
        LogsOptions(
            text='{"host":"a","x":1}\n{"host":"a"}\n{"host":"b"}',
            filter_field="host",
            filter_value="a",
        )
    )
    assert result["meta"]["matching_records"] == 2
    assert result["data"]["summary"]["x"]["missing"] == 1


# Duplicate CSV headers must not overwrite evidence columns.
def test_duplicate_csv_header() -> None:
    with pytest.raises(ToolError):
        inspect_logs(LogsOptions(text="x,x\n1,2", format="csv"))
