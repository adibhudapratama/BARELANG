#!/usr/bin/env bash
set -euo pipefail
. /etc/os-release
if [[ "${ID:-}" != ubuntu || "${VERSION_ID:-}" != 24.04 ]]; then
 echo 'Target paket ini Ubuntu 24.04. Gunakan Dockerfile untuk lingkungan lain.'; exit 2
fi
if [[ "$(id -u)" != 0 ]]; then echo 'Jalankan: sudo bash install_dependencies.sh'; exit 2; fi
apt-get update
apt-get install -y curl gnupg ca-certificates
curl -fsSL https://packages.osrfoundation.org/gazebo.gpg -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
arch="$(dpkg --print-architecture)"
echo "deb [arch=$arch signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main" > /etc/apt/sources.list.d/gazebo-stable.list
apt-get update
apt-get install -y --no-install-recommends gz-harmonic libgz-sim8-dev libgz-plugin2-dev libgz-transport13-dev cppzmq-dev cmake g++ python3
