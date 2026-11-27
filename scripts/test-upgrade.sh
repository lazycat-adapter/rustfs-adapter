#!/usr/bin/env bash
# Exercise the stable LazyCat package's actual 2025 RustFS binary against the candidate.
set -euo pipefail
cd "$(dirname "$0")/.."
legacy='registry.lazycat.cloud/white/rustfs/rustfs:f136ca8506889dc1'
candidate=${1:-$(python3 -c 'import yaml;print(yaml.safe_load(open("lzc-manifest.yml"))["services"]["rustfs"]["image"])')}
work=$(mktemp -d)
name="rustfs-compat-$(basename "$work" | tr '[:upper:]' '[:lower:]')"
volume=$(docker volume create)
cleanup() {
  docker container rm --force "$name" >/dev/null 2>&1 || true
  docker volume rm "$volume" >/dev/null
  rm -r -- "$work"
}
trap cleanup EXIT
start() {
  docker run --detach --name "$name" --volume "$volume:/data" --publish 127.0.0.1::9000 "$1" >/dev/null
  port=$(docker port "$name" 9000/tcp | head -1)
  api="http://$port"
  for _ in {1..80}; do
    if s3 "$api/" >/dev/null 2>&1; then return 0; fi
    sleep 1
  done
  echo "S3 did not become ready" >&2
  return 1
}
s3() {
  curl --fail --silent --show-error --max-time 15 --aws-sigv4 aws:amz:us-east-1:s3 --user rustfsadmin:rustfsadmin "$@"
}
start "$legacy"
s3 -X PUT "$api/upgrade-check"
printf 'legacy inline object\n' > "$work/small"
dd if=/dev/urandom of="$work/large" bs=1024 count=512 status=none
for key in small large; do
  s3 --upload-file "$work/$key" "$api/upgrade-check/$key"
  s3 "$api/upgrade-check/$key" > "$work/readback"
  cmp "$work/$key" "$work/readback"
done
docker stop "$name" >/dev/null
docker container rm "$name" >/dev/null
docker run --rm --user 0 --entrypoint chown --volume "$volume:/data" "$candidate" -R 10001:10001 /data
start "$candidate"
failed=0
for key in small large; do
  if ! s3 "$api/upgrade-check/$key" > "$work/readback" || ! cmp "$work/$key" "$work/readback"; then
    echo "Candidate $candidate failed to preserve the $key object from store version 1.0.0" >&2
    failed=1
  else
    echo "Verified $key object"
  fi
done
if ((failed)); then exit 1; fi
echo "Both objects preserved after upgrade"
