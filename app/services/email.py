import hashlib
from email import policy
from email.errors import MessageError
from email.parser import BytesParser

import regex

from app.core.errors import ToolError
from app.schemas.email import EmailOptions
from app.utils import json_result


# Decode supplied email structure as inert data without loading images or running attachments.
def inspect_email(options: EmailOptions, content: bytes | None = None) -> dict:
    try:
        message = BytesParser(policy=policy.default).parsebytes(
            options.text.encode("utf-8") if content is None else content
        )
        headers = {}
        for name in (
            "From",
            "Reply-To",
            "Return-Path",
            "To",
            "Subject",
            "Date",
            "Message-ID",
            "Authentication-Results",
            "Received-SPF",
        ):
            headers[name] = [str(value) for value in message.get_all(name, [])]
        hops = [str(value) for value in message.get_all("Received", [])]
        attachments, bodies, parts = [], [], 0
        for part in message.walk():
            parts += 1
            if parts > 100:
                raise ToolError(
                    "Email inspection supports at most 100 MIME parts.", "work_limit", 413
                )
            if part.is_multipart():
                continue
            payload = part.get_payload(decode=True) or b""
            filename = part.get_filename()
            if filename or part.get_content_disposition() == "attachment":
                attachments.append(
                    {
                        "name": filename or "(unnamed)",
                        "content_type": part.get_content_type(),
                        "bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                )
            elif part.get_content_type() in {"text/plain", "text/html"}:
                charset = part.get_content_charset() or "utf-8"
                try:
                    body = payload.decode(charset, errors="replace")
                except LookupError:
                    body = payload.decode("utf-8", errors="replace")
                bodies.append(
                    {
                        "content_type": part.get_content_type(),
                        "text_preview": body[:20000],
                        "preview_truncated": len(body) > 20000,
                    }
                )
        links = []
        for body in bodies:
            for match in regex.finditer(
                r"https?://[^\s<>\"']{1,4096}", body["text_preview"], regex.IGNORECASE, timeout=1
            ):
                value = match.group().rstrip(".,;)")
                if value not in links:
                    links.append(value)
                if len(links) > 1000:
                    raise ToolError("Email has more than 1,000 candidate links.", "work_limit", 413)
    except (ValueError, MessageError, RecursionError, TimeoutError) as exc:
        raise ToolError("Malformed or excessively nested email content.") from exc
    return json_result(
        {
            "headers": headers,
            "received_hops_newest_first": hops,
            "attachments": attachments,
            "body_previews": bodies,
            "candidate_links": links,
            "parser_defects": [type(defect).__name__ for defect in message.defects],
        },
        {"mime_parts": parts, "attachments": len(attachments), "links": len(links)},
        [
            "Authentication headers and routing claims are supplied evidence, not independent SPF/DKIM/DMARC verification. HTML and attachments were not executed."
        ],
    )
