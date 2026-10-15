"""FastAPI-compatible OpenAPI output.

The frontend client (`frontend/src/client`) is generated from this schema and
must stay identical to the one generated from the original FastAPI backend.
Ninja's schema is already close; this module patches the remaining
differences after Ninja builds it:

- operation ids `{tag}-{function_name}` (SDK method names)
- `OAuth2PasswordBearer` security scheme instead of the `JWTBearer` class name
- `Successful Response` descriptions and `422` `HTTPValidationError` responses
- form bodies published as `Body_{operation_id}` components
- `Response {Operation Id}` titles for non-model responses
"""

from typing import Any

from ninja.operation import Operation

SECURITY_SCHEME = "OAuth2PasswordBearer"
FORM_CONTENT_TYPES = ("application/x-www-form-urlencoded", "multipart/form-data")
VALIDATION_ERROR_REF = {"$ref": "#/components/schemas/HTTPValidationError"}

VALIDATION_ERROR_SCHEMAS: dict[str, Any] = {
    "HTTPValidationError": {
        "properties": {
            "detail": {
                "items": {"$ref": "#/components/schemas/ValidationError"},
                "type": "array",
                "title": "Detail",
            }
        },
        "type": "object",
        "title": "HTTPValidationError",
    },
    "ValidationError": {
        "properties": {
            "loc": {
                "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                "type": "array",
                "title": "Location",
            },
            "msg": {"type": "string", "title": "Message"},
            "type": {"type": "string", "title": "Error Type"},
            "input": {"title": "Input"},
            "ctx": {"type": "object", "title": "Context"},
        },
        "type": "object",
        "required": ["loc", "msg", "type"],
        "title": "ValidationError",
    },
}


def operation_id(operation: Operation) -> str:
    tag = operation.tags[0] if operation.tags else "default"
    return f"{tag}-{operation.view_func.__name__}"


def _is_ref(node: Any) -> bool:
    return isinstance(node, dict) and "$ref" in node


def _used_refs(node: Any) -> set[str]:
    if isinstance(node, dict):
        refs = {node["$ref"]} if isinstance(node.get("$ref"), str) else set()
        for value in node.values():
            refs |= _used_refs(value)
        return refs
    if isinstance(node, list):
        return set().union(*(_used_refs(v) for v in node)) if node else set()
    return set()


def make_fastapi_compatible(schema: dict[str, Any], token_url: str) -> dict[str, Any]:
    schema.pop("servers", None)
    if not schema.get("info", {}).get("description"):
        schema.get("info", {}).pop("description", None)
    components = schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})

    # Security: one OAuth2 password flow scheme, like FastAPI's OAuth2PasswordBearer
    components["securitySchemes"] = {
        SECURITY_SCHEME: {
            "type": "oauth2",
            "flows": {"password": {"scopes": {}, "tokenUrl": token_url}},
        }
    }

    needs_validation_schemas = False
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            op_id = operation.get("operationId", "")
            if operation.get("security"):
                operation["security"] = [{SECURITY_SCHEME: []}]

            # Inline form bodies become `Body_{operation_id}` components
            body_content = operation.get("requestBody", {}).get("content", {})
            for content_type in FORM_CONTENT_TYPES:
                media = body_content.get(content_type)
                if media and not _is_ref(media.get("schema")):
                    name = f"Body_{op_id}"
                    schemas[name] = {**media["schema"], "title": name}
                    media["schema"] = {"$ref": f"#/components/schemas/{name}"}

            responses = operation.get("responses", {})
            for code, response in responses.items():
                if not str(code).startswith("2"):
                    continue
                response["description"] = "Successful Response"
                content = response.get("content", {})
                # A custom content type (e.g. text/html) replaces the JSON default
                if len(content) > 1:
                    content.pop("application/json", None)
                json_schema = content.get("application/json", {}).get("schema", {})
                if json_schema.get("title") == "Response":
                    title = op_id.replace("_", " ").title()
                    json_schema["title"] = f"Response {title}"
            if operation.get("parameters") or operation.get("requestBody"):
                responses[422] = {
                    "description": "Validation Error",
                    "content": {"application/json": {"schema": VALIDATION_ERROR_REF}},
                }
                needs_validation_schemas = True

    if needs_validation_schemas:
        schemas.update(VALIDATION_ERROR_SCHEMAS)

    # Drop component schemas nothing references any more (e.g. form schemas
    # Ninja registers but inlines)
    used = _used_refs(schema.get("paths", {}))
    used_names = {ref.rsplit("/", 1)[-1] for ref in used}
    while True:
        nested = _used_refs([schemas[n] for n in used_names if n in schemas])
        new_names = {ref.rsplit("/", 1)[-1] for ref in nested} - used_names
        if not new_names:
            break
        used_names |= new_names
    schemas = {k: v for k, v in schemas.items() if k in used_names}

    components["schemas"] = dict(sorted(schemas.items()))
    return schema
