import base64
import hashlib
import importlib.util
import json
import uuid
from datetime import UTC, datetime

import pytest

from app.core.documents import dump_document, load_document
from app.core.errors import ToolError
from app.schemas.certificate import CertificateOptions
from app.schemas.email import EmailOptions
from app.schemas.events import EventsOptions
from app.schemas.ioc import IocOptions
from app.schemas.jwt import JwtOptions
from app.schemas.process_tree import ProcessTreeOptions
from app.schemas.query import QueryOptions
from app.schemas.report import ReportOptions
from app.schemas.sigma import SigmaOptions
from app.schemas.spell import SpellOptions
from app.schemas.stix import StixOptions
from app.schemas.strings import StringsOptions
from app.schemas.timeline import TimelineOptions
from app.schemas.timestamp import TimestampOptions
from app.schemas.unicode import UnicodeOptions
from app.schemas.url import UrlOptions
from app.services.certificate import inspect_certificates
from app.services.email import inspect_email
from app.services.events import inspect_events
from app.services.ioc import inspect_iocs
from app.services.jwt import inspect_jwt
from app.services.process_tree import build_process_tree
from app.services.query import build_query
from app.services.report import build_report
from app.services.sigma import inspect_sigma
from app.services.spell import check_spelling
from app.services.stix import inspect_stix
from app.services.strings import extract_strings
from app.services.timeline import build_timeline
from app.services.timestamp import convert_timestamps, parse_timestamp
from app.services.unicode import inspect_unicode
from app.services.url import inspect_urls


# Normalize explicit epoch units to the same instant without floating-point drift.
@pytest.mark.parametrize(
    ("value", "kind"),
    [
        ("1000.123456", "seconds"),
        ("1000123.456", "milliseconds"),
        ("1000123456", "microseconds"),
        ("116444746001234560", "filetime"),
    ],
)
def test_timestamp_units(value: str, kind: str) -> None:
    assert parse_timestamp(value, kind).isoformat() == "1970-01-01T00:16:40.123456+00:00"


# Detect DST folds and gaps instead of silently selecting a clock interpretation.
def test_timestamp_dst() -> None:
    with pytest.raises(ToolError):
        parse_timestamp("2025-11-02T01:30:00", "iso", "America/New_York")
    a = parse_timestamp("2025-11-02T01:30:00", "iso", "America/New_York", "earlier")
    b = parse_timestamp("2025-11-02T01:30:00", "iso", "America/New_York", "later")
    assert (b - a).total_seconds() == 3600
    with pytest.raises(ToolError):
        parse_timestamp("2025-03-09T02:30:00", "iso", "America/New_York")


# Keep invalid batch values as explicit evidence rows.
def test_timestamp_errors() -> None:
    result = convert_timestamps(TimestampOptions(text="bad\n2026-01-01T00:00:00Z"))
    assert result["meta"]["errors"] == 1
    with pytest.raises(ToolError):
        parse_timestamp("1e999999999999", "seconds")


# Preserve repeated URL parameters, userinfo flags, and offline hostname forms.
def test_url_components() -> None:
    result = load_document(
        inspect_urls(UrlOptions(text="https://u:p@xn--bcher-kva.example:443/a?x=1&x=2#part"))[
            "output"
        ]
    )[0]
    assert result["unicode_host"] == "bücher.example"
    assert len(result["query"]) == 2
    assert result["has_userinfo"]


# Invalid ports and malformed explicit decoding must remain safe per-input errors.
def test_url_errors() -> None:
    result = load_document(
        inspect_urls(UrlOptions(text="https://[broken\nhttps://example.test/%zz", decode_layers=1))[
            "output"
        ]
    )
    assert all("error" in row for row in result)


# Extract defanged observations while preserving actual source character coordinates.
def test_ioc_offsets_and_defang() -> None:
    text = "Contact https://example[.]test/path and 192[.]0[.]2[.]1."
    rows = load_document(inspect_iocs(IocOptions(text=text))["output"])
    assert any(row["value"] == "192.0.2.1" for row in rows)
    for row in rows:
        span = row["occurrences"][0]
        assert text[span["start"] : span["end"]] == row["first_source"]
    transformed = inspect_iocs(
        IocOptions(text="https://example.test/file.txt?x=a.b", mode="defang")
    )["output"]
    assert transformed == "hxxps://example[.]test/file.txt?x=a.b"


# Refanging must not visit an indicator or change unrelated paths and query text.
def test_refang_and_invalid_ip() -> None:
    result = inspect_iocs(IocOptions(text="hxxps://example[.]test/a?x=1", mode="refang"))
    assert result["output"] == "https://example.test/a?x=1"
    rows = load_document(
        inspect_iocs(IocOptions(text="999.192.0.2.1 192.0.2.1", types=["ip"]))["output"]
    )
    assert len(rows) == 1 and rows[0]["first_source"] == "192.0.2.1"


# Decode claims as unverified data and preserve large exact numeric values.
def test_jwt_unverified_exact_claims() -> None:
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
    payload = (
        base64.urlsafe_b64encode(b'{"sub":"sample","id":9007199254740993,"iat":"not-numeric"}')
        .decode()
        .rstrip("=")
    )
    data = load_document(inspect_jwt(JwtOptions(text=header + "." + payload + "."))["output"])
    assert data["verification"] == "UNVERIFIED"
    assert data["claims"]["id"] == 9007199254740993
    assert data["claim_times"]["iat"] == "Not a supported numeric calendar instant"


# Reject noncanonical or structurally invalid JWT components without interpreting them.
@pytest.mark.parametrize("token", ["one.two", "AB.e30.", "e30.W10."])
def test_jwt_invalid(token: str) -> None:
    with pytest.raises(ToolError):
        inspect_jwt(JwtOptions(text=token))


# Parse MIME metadata and attachment fingerprints without rendering remote content.
def test_email_attachment() -> None:
    text = (
        "From: a@example.test\nReply-To: b@example.test\nMIME-Version: 1.0\n"
        "Content-Type: multipart/mixed; boundary=x\n\n--x\nContent-Type: text/plain\n\n"
        "https://example.test\n--x\nContent-Type: application/octet-stream\n"
        'Content-Disposition: attachment; filename="../../payload.bin"\nContent-Transfer-Encoding: base64\n\nAAE=\n--x--\n'
    )
    data = load_document(inspect_email(EmailOptions(text=text))["output"])
    assert data["attachments"][0]["sha256"] == hashlib.sha256(b"\x00\x01").hexdigest()
    assert data["attachments"][0]["name"] == "../../payload.bin"
    assert "https://example.test" in data["candidate_links"]


# Quote KQL values independently of table and field identifiers.
def test_query_escaping_and_chunking() -> None:
    result = build_query(QueryOptions(text='a"b\nsecond'))
    assert 'a\\"b' in result["output"]
    assert result["meta"]["chunks"] == 1
    with pytest.raises(ToolError):
        build_query(QueryOptions(text="x", table="Table | take 1"))
    assert (
        build_query(QueryOptions(text="\n".join(str(i) for i in range(201))))["meta"]["chunks"] == 3
    )


# Reveal invisible characters without modifying the source unless normalization is explicit.
def test_unicode_modes() -> None:
    data = load_document(inspect_unicode(UnicodeOptions(text="a\u200bb"))["output"])
    assert data["characters"][0]["codepoint"] == "U+200B"
    assert (
        inspect_unicode(UnicodeOptions(text="e\u0301", action="normalize", form="NFC"))["output"]
        == "é"
    )


# Byte offsets must remain correct across invalid and multibyte UTF-8 input.
def test_strings_offsets() -> None:
    data = load_document(
        extract_strings(
            StringsOptions(text="", encoding="utf-8", minimum=2), b"ab\xffcafe\xc3\xa9\x00"
        )["output"]
    )
    assert data[0]["offset"] == 0 and data[1]["offset"] == 3
    assert data[1]["text"] == "cafeé"
    data = load_document(
        extract_strings(
            StringsOptions(text="", encoding="utf-16le", minimum=2),
            "hello\x00world".encode("utf-16le"),
        )["output"]
    )
    assert data[1]["offset"] == 12


# Reports format supplied facts without inventing missing content.
def test_report_supplied_only() -> None:
    report = build_report(ReportOptions(text="Known evidence", title="Case review"))["output"]
    assert "Known evidence" in report
    assert "Not provided." in report
    with pytest.raises(ToolError):
        build_report(ReportOptions(text="x", title="One\nTwo"))


# Timeline sorting retains invalid source records and stable provenance.
def test_timeline_order_and_errors() -> None:
    result = build_timeline(
        TimelineOptions(
            text='{"timestamp":"2026-01-01T00:01:00Z","action":"read"}\n{"timestamp":"bad"}\n{"timestamp":"2026-01-01T00:00:00Z","action":"login"}'
        )
    )
    data = load_document(result["output"])
    assert data["events"][0]["action"] == "login"
    assert data["events"][1]["gap_seconds"] == "60"
    assert len(data["unparsed"]) == 1


# Process GUIDs are scoped to hosts and PID-only relationships are not guessed.
def test_process_host_scope_and_cycles() -> None:
    source = "\n".join(
        json.dumps(row)
        for row in [
            {"Computer": "a", "ProcessGuid": "one", "ParentProcessGuid": "two", "Image": "one"},
            {"Computer": "a", "ProcessGuid": "two", "ParentProcessGuid": "one", "Image": "two"},
            {"Computer": "b", "ProcessGuid": "three", "ParentProcessGuid": "one", "Image": "three"},
        ]
    )
    data = load_document(
        build_process_tree(ProcessTreeOptions(text=source, export="json"))["output"]
    )
    assert any("Cycle" in row.get("relationship_warning", "") for row in data)
    assert "absent" in data[2]["relationship_warning"]


# Exported simple observables use the documented STIX namespace and canonical strings.
def test_stix_export_and_inspection() -> None:
    result = inspect_stix(StixOptions(text="198.51.100.3", mode="export"))
    bundle = load_document(result["output"])
    assert bundle["objects"][0]["id"] == "ipv4-addr--28bb3599-77cd-5a82-a950-b5bc3caf07c4"
    checked = load_document(inspect_stix(StixOptions(text=result["output"]))["output"])
    assert checked["supported_subset_valid"]


# Missing object types and unresolved references are validation findings, not exceptions.
def test_stix_invalid_structure() -> None:
    bundle = {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "objects": [{"id": f"file--{uuid.uuid4()}"}],
    }
    assert not load_document(inspect_stix(StixOptions(text=dump_document(bundle)))["output"])[
        "supported_subset_valid"
    ]


# Provider-qualified reference lookup does not confuse Windows and Sysmon identifiers.
def test_event_lookup() -> None:
    data = load_document(
        inspect_events(
            EventsOptions(text="", mode="lookup", provider="Microsoft-Windows-Sysmon", event_id=1)
        )["output"]
    )
    assert data["meaning"] == "Process creation"


# Safe XML rejects DTDs while preserving repeated event-data fields.
@pytest.mark.skipif(
    importlib.util.find_spec("defusedxml") is None, reason="defusedxml is not installed"
)
def test_event_xml_entities() -> None:
    with pytest.raises(ToolError):
        inspect_events(EventsOptions(text='<!DOCTYPE x [<!ENTITY a "secret">]><Event>&a;</Event>'))
    source = '<Event><System><Provider Name="Microsoft-Windows-Sysmon"/><EventID>1</EventID></System><EventData><Data Name="X">a</Data><Data Name="X">b</Data></EventData></Event>'
    rows = load_document(inspect_events(EventsOptions(text=source))["output"])
    assert rows[0]["fields"]["X"] == ["a", "b"]


# Sigma validation rejects executable tags and aliases before loading data.
@pytest.mark.skipif(
    importlib.util.find_spec("yaml") is None or importlib.util.find_spec("jsonschema") is None,
    reason="Sigma dependencies not installed",
)
def test_sigma_structural_and_unsafe_yaml() -> None:
    rule = "title: Test\nlogsource:\n  product: windows\ndetection:\n  selection:\n    EventID: 1\n  condition: selection\n"
    assert load_document(inspect_sigma(SigmaOptions(text=rule))["output"])[
        "structural_subset_valid"
    ]
    for text in ("a: &a [*a]", "!!python/object/apply:os.system [echo blocked]"):
        with pytest.raises(ToolError):
            inspect_sigma(SigmaOptions(text=text))


# Certificate metadata remains distinct from verification and never needs a private-key file.
@pytest.mark.skipif(
    importlib.util.find_spec("cryptography") is None, reason="cryptography not installed"
)
def test_certificate_metadata() -> None:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.test")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(datetime(2026, 1, 1, tzinfo=UTC))
        .not_valid_after(datetime(2027, 1, 1, tzinfo=UTC))
        .sign(key, hashes.SHA256())
    )
    pem = certificate.public_bytes(serialization.Encoding.PEM)
    data = load_document(inspect_certificates(CertificateOptions(text=pem.decode()))["output"])
    assert data[0]["self_issued"]
    assert data[0]["subject"] == "CN=example.test"


# Local spelling suggestions preserve punctuation and require an explicit apply action.
@pytest.mark.skipif(
    importlib.util.find_spec("spellchecker") is None, reason="pyspellchecker not installed"
)
def test_spelling_preserves_text() -> None:
    source = "A speling, with punctuation!"
    untouched = check_spelling(SpellOptions(text=source))
    assert untouched["output"] == source
    corrected = check_spelling(SpellOptions(text=source, corrections={"speling": "spelling"}))
    assert corrected["output"] == "A spelling, with punctuation!"


# Preserve review boundary failures as explicit rows instead of internal exceptions.
def test_review_boundary_errors() -> None:
    data = load_document(
        convert_timestamps(
            TimestampOptions(
                text="253402300799", format="seconds", output_zone="Pacific/Kiritimati"
            )
        )["output"]
    )
    assert "error" in data[0]
    data = load_document(inspect_urls(UrlOptions(text="https://example.test/?q=%ff"))["output"])
    assert "error" in data[0]
    result = inspect_iocs(IocOptions(text="https://example.test/a[.]b?q=a[:]b", mode="defang"))
    assert result["output"] == "hxxps://example[.]test/a[.]b?q=a[:]b"
    assert (
        "😀"
        in inspect_email(EmailOptions(text="Content-Type: text/plain; charset=utf-8\n\nhello 😀"))[
            "output"
        ]
    )


# Incorrectly typed STIX reference collections must fail the limited structural check.
def test_stix_reference_collection_type() -> None:
    bundle = {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "objects": [
            {
                "type": "file",
                "id": f"file--{uuid.uuid4()}",
                "name": "sample",
                "contains_refs": "bad",
            }
        ],
    }
    result = load_document(inspect_stix(StixOptions(text=dump_document(bundle)))["output"])
    assert not result["supported_subset_valid"]
