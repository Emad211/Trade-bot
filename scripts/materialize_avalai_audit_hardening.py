from __future__ import annotations

from pathlib import Path

PATH = Path("src/hybrid_trader/avalai.py")


def replace_once(text: str, before: str, after: str, *, label: str) -> str:
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    return text.replace(before, after, 1)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
''',
        '''def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def _call_id(payload: Mapping[str, Any]) -> str:
    identity = {
        key: value
        for key, value in payload.items()
        if key not in {"call_id", "previous_record_sha256"}
    }
    return hashlib.sha256(_canonical_json_bytes(identity)).hexdigest()


def _failed_call_record(
    record: AvalAICallRecord,
    *,
    error_code: str,
    error_message: str,
) -> AvalAICallRecord:
    payload = record.model_dump(
        mode="python",
        exclude={"call_id", "previous_record_sha256"},
    )
    payload.update(
        status="failed",
        error_code=error_code,
        error_message=error_message,
    )
    return AvalAICallRecord(call_id=_call_id(payload), **payload)
''',
        label="canonical JSON helper",
    )
    text = replace_once(
        text,
        '''        if self.status == "failed" and not self.error_code:
            raise ValueError("Failed AvalAI calls must contain an error_code")
        return self
''',
        '''        if self.status == "failed" and not self.error_code:
            raise ValueError("Failed AvalAI calls must contain an error_code")
        expected_call_id = _call_id(
            self.model_dump(
                mode="json",
                exclude={"call_id", "previous_record_sha256"},
            )
        )
        if self.call_id != expected_call_id:
            raise ValueError("AvalAI call_id does not match call metadata")
        return self
''',
        label="call validator",
    )
    before_record = '''        identity = {
            "extraction_key": extraction_key,
            "status": status,
            "client_request_id": client_request_id,
            "provider_request_id": provider_request_id,
            "request_body_sha256": request_sha256,
            "response_body_sha256": response_sha,
            "attempts": attempts,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
        }
        call_id = hashlib.sha256(_canonical_json_bytes(identity)).hexdigest()
        return AvalAICallRecord(
            call_id=call_id,
            extraction_key=extraction_key,
            status=status,
            route=self.settings.route,
            endpoint=self.settings.endpoint,
            model=self.settings.model,
            model_revision=self.settings.model_revision,
            client_request_id=client_request_id,
            provider_request_id=provider_request_id,
            response_id=response_id if isinstance(response_id, str) else None,
            response_model=response_model if isinstance(response_model, str) else None,
            request_body_sha256=request_sha256,
            response_body_sha256=response_sha,
            attempts=attempts,
            started_at=started_at,
            completed_at=completed_at,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            error_code=error_code,
            error_message=error_message,
        )
'''
    after_record = '''        record_payload: dict[str, Any] = {
            "schema_version": "1.0",
            "extraction_key": extraction_key,
            "status": status,
            "route": self.settings.route,
            "endpoint": self.settings.endpoint,
            "model": self.settings.model,
            "model_revision": self.settings.model_revision,
            "client_request_id": client_request_id,
            "provider_request_id": provider_request_id,
            "response_id": response_id if isinstance(response_id, str) else None,
            "response_model": response_model if isinstance(response_model, str) else None,
            "request_body_sha256": request_sha256,
            "response_body_sha256": response_sha,
            "attempts": attempts,
            "started_at": started_at,
            "completed_at": completed_at,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "error_code": error_code,
            "error_message": error_message,
        }
        return AvalAICallRecord(call_id=_call_id(record_payload), **record_payload)
'''
    text = replace_once(text, before_record, after_record, label="call record construction")
    text = replace_once(
        text,
        '''        self.call_records.append(call_record)
        signal = payload.to_event_signal(envelope)
        return make_semantic_record(
''',
        '''        try:
            signal = payload.to_event_signal(envelope)
        except Exception as exc:
            failed_record = _failed_call_record(
                call_record,
                error_code="semantic_contract_violation",
                error_message=_redact(str(exc), self._client._api_key),
            )
            self.call_records.append(failed_record)
            raise AvalAIRequestError(str(exc), call_record=failed_record) from exc
        self.call_records.append(call_record)
        return make_semantic_record(
''',
        label="semantic contract classification",
    )
    text = replace_once(
        text,
        '''            if record.previous_record_sha256 != previous_sha:
                raise ValueError(f"AvalAI call ledger hash chain breaks at line {line_number}")
''',
        '''            expected_call_id = _call_id(
                record.model_dump(
                    mode="json",
                    exclude={"call_id", "previous_record_sha256"},
                )
            )
            if record.call_id != expected_call_id:
                raise ValueError(f"AvalAI call_id mismatch at line {line_number}")
            if record.previous_record_sha256 != previous_sha:
                raise ValueError(f"AvalAI call ledger hash chain breaks at line {line_number}")
''',
        label="call ledger identity verification",
    )
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
