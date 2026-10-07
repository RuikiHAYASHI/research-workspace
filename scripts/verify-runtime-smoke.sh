#!/usr/bin/env bash
set -euo pipefail

workspace_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
workbench_root="${WORKBENCH_REPO_ROOT:-${workspace_root}/../2026_09_hayashi_longvideoqa_workbench}"

if [[ ! -x "${workbench_root}/scripts/verify-runtime-smoke.sh" ]]; then
  workbench_root="${workspace_root}/.worktrees/longvideoqa-workbench-refactor"
fi

if [[ ! -x "${workbench_root}/scripts/verify-runtime-smoke.sh" ]]; then
  printf '%s\n' 'Workbench検証スクリプトが見つかりません。WORKBENCH_REPO_ROOTを設定してください。' >&2
  exit 2
fi

exec bash "${workbench_root}/scripts/verify-runtime-smoke.sh" "$@"
