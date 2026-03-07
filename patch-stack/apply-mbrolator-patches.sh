#!/usr/bin/env bash
set -euo pipefail

REVERT=0
CHECK_ONLY=0
MBROLATOR_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --revert)
      REVERT=1
      ;;
    --check)
      CHECK_ONLY=1
      ;;
    --mbrolator-root)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --mbrolator-root" >&2
        echo "Usage: $0 [--revert] [--check] [--mbrolator-root <path>]" >&2
        exit 2
      fi
      MBROLATOR_ROOT="$2"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--revert] [--check] [--mbrolator-root <path>]" >&2
      exit 2
      ;;
  esac
  shift
done

SCRIPT_PATH="${BASH_SOURCE[0]}"
if [[ "$SCRIPT_PATH" == */* ]]; then
  SCRIPT_DIR="$(cd "${SCRIPT_PATH%/*}" && pwd)"
else
  SCRIPT_DIR="$(pwd)"
fi

if [[ -n "$MBROLATOR_ROOT" ]]; then
  if [[ ! -d "$MBROLATOR_ROOT" ]]; then
    echo "MBROLATOR root not found: $MBROLATOR_ROOT" >&2
    exit 1
  fi
  MBROLATOR_ROOT="$(cd "$MBROLATOR_ROOT" && pwd)"
else
  if ! MBROLATOR_ROOT="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null)"; then
    echo "Could not detect MBROLATOR root from current directory." >&2
    echo "cd into MBROLATOR root or pass --mbrolator-root <path>." >&2
    exit 1
  fi
fi

if [[ "${MBROLATOR_ROOT##*/}" != "MBROLATOR" ]]; then
  echo "Target repository is not MBROLATOR: $MBROLATOR_ROOT" >&2
  exit 1
fi

cleanup_file() {
  local f="$1"
  if [[ -z "$f" ]]; then
    return
  fi
  if command -v rm >/dev/null 2>&1; then
    rm -f "$f"
  else
    : > "$f" 2>/dev/null || true
  fi
}

PATCHES=(
  "$SCRIPT_DIR/mbrolator/0001-resynthesis-src-resynth-windows-drand48.patch"
)

for patch in "${PATCHES[@]}"; do
  if [[ ! -f "$patch" ]]; then
    echo "Patch not found: $patch" >&2
    exit 1
  fi

  mode_label="apply"
  if [[ "$REVERT" -eq 1 ]]; then
    mode_label="revert"
  fi

  echo "[patch-stack] Checking $mode_label for: $patch"
  patch_to_apply="$patch"
  tmp_patch=""

  first_line=""
  if [[ -f "$patch" ]]; then
    IFS= read -r first_line < "$patch" || true
  fi
  if [[ "$first_line" != diff\ --git* ]]; then
    tmp_base="${TMPDIR:-/tmp}"
    tmp_patch="$tmp_base/patch-stack.$$.${RANDOM:-0}.patch"
    found=0
    : > "$tmp_patch"
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$found" -eq 1 || "$line" == diff\ --git* ]]; then
        found=1
        printf '%s\n' "$line" >> "$tmp_patch"
      fi
    done < "$patch"
    if [[ ! -s "$tmp_patch" ]]; then
      cleanup_file "$tmp_patch"
      echo "No unified diff found in patch file: $patch" >&2
      exit 1
    fi
    patch_to_apply="$tmp_patch"
  fi

  can_apply=0
  already_in_target_state=0
  patch_leaf="${patch##*/}"

  if [[ "$REVERT" -eq 1 ]]; then
    if git -C "$MBROLATOR_ROOT" apply --check -R "$patch_to_apply" >/dev/null 2>&1; then
      can_apply=1
    else
      if [[ "$patch_leaf" == "0001-resynthesis-src-resynth-windows-drand48.patch" ]]; then
        marker_file="$MBROLATOR_ROOT/Resynthesis/Src/resynth.c"
        marker_contents=""
        if [[ -f "$marker_file" ]]; then
          marker_contents="$(<"$marker_file")"
        fi
        if [[ ! -f "$marker_file" || "$marker_contents" != *mbr_drand48* ]]; then
          already_in_target_state=1
        else
          [[ -n "$tmp_patch" ]] && cleanup_file "$tmp_patch"
          echo "Patch check failed for: $patch" >&2
          exit 1
        fi
      elif git -C "$MBROLATOR_ROOT" apply --check "$patch_to_apply" >/dev/null 2>&1; then
        already_in_target_state=1
      else
        [[ -n "$tmp_patch" ]] && cleanup_file "$tmp_patch"
        echo "Patch check failed for: $patch" >&2
        exit 1
      fi
    fi
  else
    if git -C "$MBROLATOR_ROOT" apply --check "$patch_to_apply" >/dev/null 2>&1; then
      can_apply=1
    else
      if [[ "$patch_leaf" == "0001-resynthesis-src-resynth-windows-drand48.patch" ]]; then
        marker_file="$MBROLATOR_ROOT/Resynthesis/Src/resynth.c"
        marker_contents=""
        if [[ -f "$marker_file" ]]; then
          marker_contents="$(<"$marker_file")"
        fi
        if [[ -f "$marker_file" && "$marker_contents" == *mbr_drand48* ]]; then
          already_in_target_state=1
        else
          [[ -n "$tmp_patch" ]] && cleanup_file "$tmp_patch"
          echo "Patch check failed for: $patch" >&2
          exit 1
        fi
      elif git -C "$MBROLATOR_ROOT" apply --check -R "$patch_to_apply" >/dev/null 2>&1; then
        already_in_target_state=1
      else
        [[ -n "$tmp_patch" ]] && cleanup_file "$tmp_patch"
        echo "Patch check failed for: $patch" >&2
        exit 1
      fi
    fi
  fi

  if [[ "$already_in_target_state" -eq 1 ]]; then
    if [[ "$REVERT" -eq 1 ]]; then
      echo "[patch-stack] Skipping: already reverted for $patch"
    else
      echo "[patch-stack] Skipping: already applied for $patch"
    fi
    [[ -n "$tmp_patch" ]] && cleanup_file "$tmp_patch"
    continue
  fi

  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    [[ -n "$tmp_patch" ]] && cleanup_file "$tmp_patch"
    continue
  fi

  if [[ "$can_apply" -ne 1 ]]; then
    echo "Patch cannot be processed for: $patch" >&2
    exit 1
  fi

  echo "[patch-stack] Executing $mode_label for: $patch"
  if [[ "$REVERT" -eq 1 ]]; then
    git -C "$MBROLATOR_ROOT" apply -R "$patch_to_apply"
  else
    git -C "$MBROLATOR_ROOT" apply "$patch_to_apply"
  fi

  [[ -n "$tmp_patch" ]] && cleanup_file "$tmp_patch"
done

echo "[patch-stack] Done."
