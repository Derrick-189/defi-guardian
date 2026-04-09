#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# DeFi Guardian - Prusti bootstrap (pinned for this project)
# -------------------------------------------------------------------
# Installs a dedicated Prusti toolchain and writes a project env file
# that matches the current app pipeline (prusti-rustc + VIPER_HOME).
# -------------------------------------------------------------------

PROJECT_DIR="${1:-$HOME/defi_guardian}"
PRUSTI_ROOT="${HOME}/.defi-guardian/prusti"
PRUSTI_TOOLCHAIN="nightly-2023-08-15-x86_64-unknown-linux-gnu"
PRUSTI_TAG="${PRUSTI_TAG:-v-2023-08-22-1715}"
PRUSTI_ZIP_URL="${PRUSTI_ZIP_URL:-https://github.com/viperproject/prusti-dev/releases/download/${PRUSTI_TAG}/prusti-release-ubuntu.zip}"

mkdir -p "${PRUSTI_ROOT}"

echo "[1/7] Ensuring rustup toolchain: ${PRUSTI_TOOLCHAIN}"
rustup toolchain install "${PRUSTI_TOOLCHAIN}" || true

echo "[2/7] Downloading pinned Prusti release (${PRUSTI_TAG})"
TMP_DL_DIR="$(mktemp -d)"
cleanup() { rm -rf "${TMP_DL_DIR}"; }
trap cleanup EXIT
ZIP_PATH="${TMP_DL_DIR}/prusti-release-ubuntu.zip"
# Always use curl for robust retries through fresh GitHub redirects.
# wget can keep retrying an expired signed asset URL and fail with 403.
curl -L --fail \
  --retry 50 \
  --retry-delay 3 \
  --retry-all-errors \
  --connect-timeout 20 \
  --max-time 0 \
  -C - \
  "${PRUSTI_ZIP_URL}" -o "${ZIP_PATH}"

echo "[3/7] Extracting release into ${PRUSTI_ROOT}"
rm -rf "${PRUSTI_ROOT}"
mkdir -p "${PRUSTI_ROOT}"
unzip -q "${ZIP_PATH}" -d "${TMP_DL_DIR}/unzipped"
# Copy everything from extracted archive (layout differs across releases)
cp -a "${TMP_DL_DIR}/unzipped/." "${PRUSTI_ROOT}/"

# Locate Prusti binaries in extracted content
PRUSTI_RUSTC_BIN="$(find "${PRUSTI_ROOT}" -type f -name prusti-rustc 2>/dev/null | head -n 1 || true)"
CARGO_PRUSTI_BIN="$(find "${PRUSTI_ROOT}" -type f -name cargo-prusti 2>/dev/null | head -n 1 || true)"

# Fallback to existing ~/.prusti install if release zip omits binaries
if [ -z "${PRUSTI_RUSTC_BIN}" ] && [ -x "${HOME}/.prusti/prusti-rustc" ]; then
  PRUSTI_RUSTC_BIN="${HOME}/.prusti/prusti-rustc"
fi
if [ -z "${CARGO_PRUSTI_BIN}" ] && [ -x "${HOME}/.prusti/cargo-prusti" ]; then
  CARGO_PRUSTI_BIN="${HOME}/.prusti/cargo-prusti"
fi

if [ -z "${PRUSTI_RUSTC_BIN}" ]; then
  echo "ERROR: Could not find prusti-rustc in release or ~/.prusti."
  exit 1
fi
chmod +x "${PRUSTI_RUSTC_BIN}" || true
[ -n "${CARGO_PRUSTI_BIN}" ] && chmod +x "${CARGO_PRUSTI_BIN}" || true

chmod +x "${PRUSTI_ROOT}"/prusti-* || true

echo "[4/7] Running Prusti setup (if supported)"
set +e
SETUP_OUTPUT="$("${PRUSTI_RUSTC_BIN}" --setup 2>&1)"
SETUP_RC=$?
set -e
if [ ${SETUP_RC} -eq 0 ]; then
  echo "Prusti setup completed."
elif echo "${SETUP_OUTPUT}" | grep -q "Unrecognized option: 'setup'"; then
  echo "Prusti release does not support --setup; continuing."
else
  echo "WARN: Prusti setup returned non-zero; continuing."
  echo "${SETUP_OUTPUT}" | sed -n '1,6p'
fi

echo "[5/7] Detecting VIPER_HOME"
# Newer setups usually place this under ~/.prusti/viper_tools
# Keep a fallback for root-local layout
if [ -d "${HOME}/.prusti/viper_tools" ]; then
  VIPER_HOME_PATH="${HOME}/.prusti/viper_tools"
elif [ -d "${PRUSTI_ROOT}/viper_tools" ]; then
  VIPER_HOME_PATH="${PRUSTI_ROOT}/viper_tools"
elif [ -d "$(dirname "${PRUSTI_RUSTC_BIN}")/viper_tools" ]; then
  VIPER_HOME_PATH="$(dirname "${PRUSTI_RUSTC_BIN}")/viper_tools"
elif [ -d "${PRUSTI_ROOT}/backends" ]; then
  # Some release zips ship backends directly without a viper_tools directory.
  VIPER_HOME_PATH="${PRUSTI_ROOT}"
else
  echo "WARN: Could not find viper_tools; relying on Prusti's default resource lookup."
  VIPER_HOME_PATH=""
fi

PRUSTI_BIN_DIR="$(dirname "${PRUSTI_RUSTC_BIN}")"
if [ -n "${VIPER_HOME_PATH}" ]; then
  VIPER_EXPORT_LINE="export VIPER_HOME=\"${VIPER_HOME_PATH}\""
else
  VIPER_EXPORT_LINE="# export VIPER_HOME=<optional>"
fi

echo "[6/7] Writing project env file: ${PROJECT_DIR}/.prusti.env"
cat > "${PROJECT_DIR}/.prusti.env" <<EOF
# Auto-generated for DeFi Guardian
export PATH="${PRUSTI_BIN_DIR}:\$PATH"
export DG_PRUSTI_TOOLCHAIN="${PRUSTI_TOOLCHAIN}"
${VIPER_EXPORT_LINE}

# Important: never export PRUSTI_* (Prusti treats these as config keys)
unset PRUSTI_HOME
unset PRUSTI_TOOLCHAIN
unset RUSTUP_TOOLCHAIN
EOF

echo "[7/7] Verifying install"
source "${PROJECT_DIR}/.prusti.env"
prusti-rustc --version

echo "[8/8] Quick smoke check"
TMP_DIR="$(mktemp -d)"
cat > "${TMP_DIR}/lib.rs" <<'EOF'
fn max(x: u64, y: u64) -> u64 { if x > y { x } else { y } }
EOF

set +e
prusti-rustc --edition=2021 --crate-type=lib "${TMP_DIR}/lib.rs" >/tmp/prusti_smoke_out.txt 2>/tmp/prusti_smoke_err.txt
RC=$?
set -e

rm -rf "${TMP_DIR}"

if grep -q "unknown configuration flag \`home\`" /tmp/prusti_smoke_err.txt; then
  echo "FAIL: PRUSTI_HOME contamination detected."
  exit 1
fi

if grep -q "compiler unexpectedly panicked" /tmp/prusti_smoke_err.txt; then
  echo "WARN: Prusti ICE detected (toolchain incompatibility may remain)."
  echo "      Check /tmp/prusti_smoke_err.txt for details."
else
  echo "OK: Prusti smoke check passed or failed without ICE."
fi

echo
echo "Done."
echo "Next run your app with:"
echo "  source \"${PROJECT_DIR}/.prusti.env\""
echo "  python3 \"${PROJECT_DIR}/desktop_app.py\""
