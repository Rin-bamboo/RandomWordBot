#!/usr/bin/env bash
set -euo pipefail

compose() {
    docker compose --env-file .env.linux -f docker-compose.linux.yml "$@"
}

bind_address="$(compose config --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["services"]["db"]["ports"][0]["host_ip"])')"

# Dockerの自動起動がDHCPによるIP割当より早い場合、失敗したDBのネットワークも作り直す。
for attempt in $(seq 1 60); do
    if ip -o -4 addr show | awk '{print $4}' | cut -d/ -f1 | grep -Fxq "$bind_address"; then
        compose up -d --force-recreate --no-deps --wait --wait-timeout 120 db
        compose up -d --no-build --wait --wait-timeout 60 discord-bot
        exit 0
    fi
    sleep 2
done

echo "MySQLの公開用IPが割り当てられず、起動を中止しました" >&2
exit 1
