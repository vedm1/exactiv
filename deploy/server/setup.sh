#!/usr/bin/env bash
# One-time, idempotent server setup for the Exaktiv deploy (EXK0b). Run as root on the Hetzner host.
#
#   setup.sh [--dry-run] <circleci-public-key-file>
#
# It changes ONLY Exaktiv files: the user exaktiv-deploy, /opt/stack/exaktiv, /etc/exaktiv/deploy.conf, two
# root-owned scripts in /opt/stack/bin (deploy-infra, exaktiv-policy.py). It never touches Caddy, bin/deploy or another project.
# Run it from a reviewed checkout of this repository: the scripts it installs are the ones next to it.
set -euo pipefail

DRY=0
if [[ "${1:-}" == "--dry-run" ]]; then DRY=1; shift; fi
PUBKEY_FILE="${1:?usage: setup.sh [--dry-run] <circleci-public-key-file>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK="${STACK_ROOT:-/opt/stack}"
USER_NAME=exaktiv-deploy
HOME_DIR="/home/$USER_NAME"
PROJECT_DIR="$STACK/exaktiv"
REPO="git@github.com:vedm1/exactiv.git"
# GitHub's published ED25519 host key fingerprint (api.github.com/meta, ssh_key_fingerprints).
GITHUB_FPR="${GITHUB_ED25519_FPR:-SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU}"
FORCED='command="/opt/stack/bin/deploy-infra",no-pty,no-port-forwarding,no-agent-forwarding,no-X11-forwarding'

say() { printf '%s\n' "$*"; }
act() { # act "<what>" cmd args...  : print it, run it unless --dry-run
  local what="$1"; shift
  if [[ $DRY -eq 1 ]]; then say "would: $what"; else say "do:    $what"; "$@"; fi
}

[[ -f "$PUBKEY_FILE" ]] || { echo "no such file: $PUBKEY_FILE" >&2; exit 1; }
[[ "$(wc -l < "$PUBKEY_FILE")" -le 1 ]] || { echo "the key file must hold exactly one line" >&2; exit 1; }
pub="$(head -n 1 "$PUBKEY_FILE")"
[[ "$pub" =~ ^ssh-ed25519\ [A-Za-z0-9+/=]+(\ [A-Za-z0-9._@-]+)?$ ]] || { echo "not an ed25519 public key" >&2; exit 1; }
[[ $EUID -eq 0 || -n "${SETUP_CHECK_ONLY:-}" ]] || { echo "run as root" >&2; exit 1; }
[[ -n "${SETUP_CHECK_ONLY:-}" ]] && { echo "key file ok"; exit 0; }
[[ -d "$STACK" && -d "$STACK/bin" ]] || { echo "$STACK/bin does not exist" >&2; exit 1; }

# 1. user
if id "$USER_NAME" >/dev/null 2>&1; then say "ok:    user $USER_NAME exists"
else act "create user $USER_NAME (docker group)" useradd -m -s /bin/bash -G docker "$USER_NAME"; fi

# 2. directories
[[ -d "$PROJECT_DIR" ]] && say "ok:    $PROJECT_DIR exists" \
  || act "create $PROJECT_DIR (owner $USER_NAME, mode 750)" install -d -m 750 -o "$USER_NAME" -g "$USER_NAME" "$PROJECT_DIR"
[[ -d "$HOME_DIR/.ssh" ]] && say "ok:    $HOME_DIR/.ssh exists" \
  || act "create $HOME_DIR/.ssh (mode 700)" install -d -m 700 -o "$USER_NAME" -g "$USER_NAME" "$HOME_DIR/.ssh"

# 3. the two scripts: root-owned, so the deploy user and a deployed repository cannot change them
act "install $STACK/bin/deploy-infra (root, 755)" install -m 755 -o root -g root "$HERE/deploy-infra" "$STACK/bin/deploy-infra"
act "install $STACK/bin/exaktiv-policy.py (root, 755)" install -m 755 -o root -g root "$HERE/policy.py" "$STACK/bin/exaktiv-policy.py"

# 4. the CircleCI key, forced to deploy-infra
auth="$HOME_DIR/.ssh/authorized_keys"
line="$FORCED $pub"
if [[ -f "$auth" ]] && grep -qxF "$line" "$auth"; then say "ok:    authorized_keys has the forced-command line"
elif [[ $DRY -eq 1 ]]; then say "would: write the forced-command line to $auth (replaces the file, mode 600)"
else
  say "do:    write the forced-command line to $auth"
  printf '%s\n' "$line" > "$auth"; chown "$USER_NAME:$USER_NAME" "$auth"; chmod 600 "$auth"
fi

# 5. read-only GitHub deploy key and the pinned GitHub host key
key="$HOME_DIR/.ssh/repo_deploy_key"
known="$HOME_DIR/.ssh/known_hosts_github"
if [[ -f "$key" ]]; then say "ok:    repository deploy key exists"
else act "create the read-only repository deploy key" \
  sudo -u "$USER_NAME" ssh-keygen -q -t ed25519 -N '' -C "deploy-exaktiv-readonly" -f "$key"; fi
if [[ -f "$known" ]]; then say "ok:    GitHub host key is pinned"
elif [[ $DRY -eq 1 ]]; then say "would: pin the GitHub host key after checking fingerprint $GITHUB_FPR"
else
  scan="$(ssh-keyscan -t ed25519 github.com 2>/dev/null)"
  fpr="$(printf '%s\n' "$scan" | ssh-keygen -lf - 2>/dev/null | awk '{print $2}')"
  [[ "$fpr" == "$GITHUB_FPR" ]] || { echo "refused: GitHub host key fingerprint is '$fpr'" >&2; exit 1; }
  say "do:    pin the GitHub host key (fingerprint checked)"
  printf '%s\n' "$scan" > "$known"; chown "$USER_NAME:$USER_NAME" "$known"; chmod 644 "$known"
fi

# 6. deploy.conf in a root-owned directory (the only keys deploy-infra accepts)
CONF_DIR="${CONF_DIR:-/etc/exaktiv}"
conf="$CONF_DIR/deploy.conf"
want="REPO=$REPO
BRANCH=main
SSH_KEY=$key
KNOWN_HOSTS=$known"
if [[ -f "$conf" ]] && [[ "$(cat "$conf")" == "$want" ]]; then say "ok:    deploy.conf is current"
elif [[ $DRY -eq 1 ]]; then say "would: write $conf (root-owned, so the deploy user cannot change it)"
else
  say "do:    write $conf (root-owned)"
  install -d -m 755 -o root -g root "$CONF_DIR"
  printf '%s\n' "$want" > "$conf"; chown root:root "$conf"; chmod 644 "$conf"
fi

say ""
say "Next, by hand (secrets stay with you):"
say "  1. Add this public key in GitHub: repository, Settings, Deploy keys, Add deploy key, write access OFF:"
if [[ -f "$key.pub" ]]; then sed 's/^/       /' "$key.pub"; else say "       (created when this script runs without --dry-run)"; fi
say "  2. Put the Doppler service token of the prd config on the server. Run this on YOUR machine, with the token in \$T:"
say "       printf %s \"\$T\" | ssh root@<host> 'install -m 600 -o $USER_NAME -g $USER_NAME /dev/stdin $PROJECT_DIR/doppler.token'"
