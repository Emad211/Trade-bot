from __future__ import annotations

from pathlib import Path

PATH = Path(".github/workflows/phase3g-prospective-overlap.yml")


def replace_once(text: str, before: str, after: str, *, label: str) -> str:
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    return text.replace(before, after, 1)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''          import json
          from pathlib import Path
''',
        '''          import json
          import os
          from pathlib import Path
''',
        label="overlap verifier imports",
    )
    text = replace_once(
        text,
        '''      - name: Record source provenance
        shell: bash
        run: |
          set -euo pipefail
          root=artifacts/phase3g-overlap
          cat > "$root/run_context.json" <<EOF
          {
            "schema_version": "1.0",
            "workflow_run_id": "$GITHUB_RUN_ID",
            "source_commit_sha": "$GITHUB_SHA",
            "as_of": "$PHASE3G_AS_OF",
            "semantic_run_id": "$SEMANTIC_RUN_ID",
            "semantic_artifact_id": $SEMANTIC_ARTIFACT_ID,
            "semantic_artifact_digest": "$SEMANTIC_ARTIFACT_DIGEST",
            "previous_phase3g_run_id": ${PREVIOUS_PHASE3G_RUN_ID:-null},
            "previous_phase3g_artifact_id": ${PREVIOUS_PHASE3G_ARTIFACT_ID:-null},
            "previous_phase3g_artifact_digest": ${PREVIOUS_PHASE3G_ARTIFACT_DIGEST:+"$PREVIOUS_PHASE3G_ARTIFACT_DIGEST"},
            "trajectory_restored": $TRAJECTORY_RESTORED,
            "credentials_used": false,
            "model_fitting_executed": false,
            "prospective_decisions_created": false
          }
          EOF
          printf '%s\\n' "$GITHUB_SHA" > "$root/source_commit_sha.txt"
          printf '%s\\n' "$GITHUB_RUN_ID" > "$root/workflow_run_id.txt"
          find "$root" -type f ! -name SHA256SUMS -print0 \\
            | sort -z | xargs -0 sha256sum > "$root/SHA256SUMS"
''',
        '''      - name: Record source provenance
        shell: bash
        run: |
          set -euo pipefail
          python - <<'PY'
          import json
          import os
          from pathlib import Path

          def optional_int(name: str) -> int | None:
              value = os.environ.get(name, "")
              return int(value) if value else None

          def optional_text(name: str) -> str | None:
              value = os.environ.get(name, "")
              return value or None

          root = Path("artifacts/phase3g-overlap")
          payload = {
              "schema_version": "1.0",
              "workflow_run_id": os.environ["GITHUB_RUN_ID"],
              "source_commit_sha": os.environ["GITHUB_SHA"],
              "as_of": os.environ["PHASE3G_AS_OF"],
              "semantic_run_id": os.environ["SEMANTIC_RUN_ID"],
              "semantic_artifact_id": int(os.environ["SEMANTIC_ARTIFACT_ID"]),
              "semantic_artifact_digest": os.environ["SEMANTIC_ARTIFACT_DIGEST"],
              "previous_phase3g_run_id": optional_text("PREVIOUS_PHASE3G_RUN_ID"),
              "previous_phase3g_artifact_id": optional_int(
                  "PREVIOUS_PHASE3G_ARTIFACT_ID"
              ),
              "previous_phase3g_artifact_digest": optional_text(
                  "PREVIOUS_PHASE3G_ARTIFACT_DIGEST"
              ),
              "trajectory_restored": os.environ["TRAJECTORY_RESTORED"] == "true",
              "credentials_used": False,
              "model_fitting_executed": False,
              "prospective_decisions_created": False,
          }
          (root / "run_context.json").write_text(
              json.dumps(payload, sort_keys=True, indent=2) + "\\n",
              encoding="utf-8",
          )
          PY
          root=artifacts/phase3g-overlap
          printf '%s\\n' "$GITHUB_SHA" > "$root/source_commit_sha.txt"
          printf '%s\\n' "$GITHUB_RUN_ID" > "$root/workflow_run_id.txt"
          find "$root" -type f ! -name SHA256SUMS -print0 \\
            | sort -z | xargs -0 sha256sum > "$root/SHA256SUMS"
''',
        label="safe Phase 3G run context",
    )
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
