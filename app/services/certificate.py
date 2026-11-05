from app.core.errors import ToolError
from app.schemas.certificate import CertificateOptions
from app.utils import json_result


# Decode uploaded certificates as metadata without remote TLS, chain, or revocation checks.
def inspect_certificates(options: CertificateOptions, content: bytes | None = None) -> dict:
    try:
        from cryptography import x509
        from cryptography.exceptions import UnsupportedAlgorithm
        from cryptography.hazmat.primitives import hashes
    except ImportError as exc:
        raise ToolError(
            "Install the certificate dependencies from requirements.txt.", "dependency_missing", 503
        ) from exc
    data = options.text.encode("utf-8") if content is None else content
    if len(data) > 1024 * 1024 or data.count(b"-----BEGIN CERTIFICATE-----") > 10:
        raise ToolError(
            "Use at most ten certificates and 1 MiB of certificate data.", "work_limit", 413
        )
    try:
        certificates = (
            x509.load_pem_x509_certificates(data)
            if b"-----BEGIN CERTIFICATE-----" in data
            else [x509.load_der_x509_certificate(data)]
        )
        if not certificates:
            raise ValueError
        rows = []
        for certificate in certificates:
            try:
                names = certificate.extensions.get_extension_for_class(
                    x509.SubjectAlternativeName
                ).value
                alternatives = [str(name.value) for name in names]
            except x509.ExtensionNotFound:
                alternatives = []
            rows.append(
                {
                    "subject": certificate.subject.rfc4514_string(),
                    "issuer": certificate.issuer.rfc4514_string(),
                    "serial_hex": format(certificate.serial_number, "x"),
                    "version": certificate.version.name,
                    "not_before": certificate.not_valid_before_utc.isoformat(),
                    "not_after": certificate.not_valid_after_utc.isoformat(),
                    "subject_alt_names": alternatives,
                    "sha256": certificate.fingerprint(hashes.SHA256()).hex(),
                    "sha1": certificate.fingerprint(hashes.SHA1()).hex(),
                    "self_issued": certificate.subject == certificate.issuer,
                }
            )
    except (
        ValueError,
        TypeError,
        x509.DuplicateExtension,
        x509.UnsupportedGeneralNameType,
        UnsupportedAlgorithm,
    ) as exc:
        raise ToolError("Input is not a supported PEM/DER certificate.") from exc
    return json_result(
        rows,
        {"certificates": len(rows)},
        [
            "Metadata only: no trust-chain, signature, hostname, or revocation verdict. Self-issued does not prove self-signed."
        ],
    )
