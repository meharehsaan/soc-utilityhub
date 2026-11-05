import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.core.documents import check_nodes
from app.core.errors import ToolError
from app.schemas.sigma import SigmaOptions
from app.utils import json_result


# Normalize safe YAML dates and reject non-JSON scalars before schema/error serialization.
def normalize_yaml(value: Any) -> Any:
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ToolError("Sigma mapping keys must be strings.")
        return {key: normalize_yaml(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_yaml(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        raise ToolError("Non-finite YAML numbers are not supported.")
    if value is not None and type(value) not in {str, int, float, bool}:
        raise ToolError("Unsupported YAML scalar type.")
    return value


# Validate a local structural schema without permitting executable tags or alias expansion.
def inspect_sigma(options: SigmaOptions) -> dict:
    try:
        import yaml
        from jsonschema import Draft202012Validator, FormatChecker
        from yaml.tokens import AliasToken, AnchorToken, TagToken
    except ImportError as exc:
        raise ToolError(
            "Install Sigma dependencies from requirements.txt.", "dependency_missing", 503
        ) from exc
    if len(options.text.encode("utf-8")) > 128 * 1024:
        raise ToolError("Sigma rules are limited to 128 KiB.", "work_limit", 413)
    try:
        depth, tokens = 0, 0
        for token in yaml.scan(options.text):
            tokens += 1
            if isinstance(token, (AliasToken, AnchorToken, TagToken)):
                raise ToolError("YAML aliases, anchors, and explicit tags are not supported.")
            name = type(token).__name__
            if name in {
                "BlockMappingStartToken",
                "BlockSequenceStartToken",
                "FlowMappingStartToken",
                "FlowSequenceStartToken",
            }:
                depth += 1
            elif name in {"BlockEndToken", "FlowMappingEndToken", "FlowSequenceEndToken"}:
                depth -= 1
            if depth > 64 or tokens > 20000:
                raise ToolError("YAML exceeds its token/depth budget.", "work_limit", 413)

        class UniqueLoader(yaml.SafeLoader):
            pass

        # Reject repeated mapping keys before YAML construction can overwrite evidence.
        def construct_mapping(loader: Any, node: Any) -> dict:
            loader.flatten_mapping(node)
            result = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=True)
                if not isinstance(key, str):
                    raise ToolError("Sigma mapping keys must be strings.")
                if key in result:
                    raise ToolError("Duplicate YAML mapping keys are not supported.")
                result[key] = loader.construct_object(value_node, deep=True)
            return result

        UniqueLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
        )
        document = yaml.load(options.text, Loader=UniqueLoader)
    except (yaml.YAMLError, ValueError, RecursionError) as exc:
        raise ToolError("Malformed or unsupported YAML.") from exc
    if not isinstance(document, dict):
        raise ToolError("A Sigma rule must be a mapping.")
    document = normalize_yaml(document)
    check_nodes(document)
    schema = json.loads(
        (Path(__file__).resolve().parents[1] / "data" / "sigma-schema.json").read_text()
    )
    errors = []
    for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document):
        errors.append(
            {
                "path": "/".join(str(part) for part in error.absolute_path),
                "message": error.message[:512],
            }
        )
        if len(errors) >= 100:
            break
    source = document.get("logsource", {})
    detection = document.get("detection", {})
    selections = (
        [key for key in detection if key not in {"condition", "timeframe"}]
        if isinstance(detection, dict)
        else []
    )
    if not selections:
        errors.append(
            {"path": "detection", "message": "At least one detection selection is required."}
        )
    summary = {
        "title": document.get("title"),
        "logsource": source,
        "selections": selections,
        "condition": detection.get("condition") if isinstance(detection, dict) else None,
    }
    return json_result(
        {"structural_subset_valid": not errors, "errors": errors, "summary": summary},
        {"schema": "Sigma 2.1 structural subset"},
        [
            "Local structural checks only: condition semantics, backend conversion, and detection effectiveness are not verified. No YAML was executed."
        ],
    )
