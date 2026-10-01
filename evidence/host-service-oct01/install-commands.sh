set -eu
coordination_checkout=/tmp/entrotter-host-oct01-dc5c86b/coordination
app_dir="$HOME/.local/share/entrotter"
config_dir="$HOME/.config/entrotter"
test ! -e "$app_dir"
test ! -e "$config_dir"
test ! -e "$HOME/.config/systemd/user/entrotter-engine.service"
mkdir -p "$app_dir" "$config_dir" "$HOME/.config/systemd/user"
chmod 700 "$app_dir" "$config_dir"
git clone https://github.com/entrotter/engine.git "$app_dir/engine"
git -C "$app_dir/engine" checkout --detach d5b30035b4a2a1c292db24f6caf81ed419a2684e
export PYTHONPATH="$app_dir/engine/src"
export ENTROTTER_DOCKER_SOCKET=/var/run/docker.sock
python3 "$app_dir/engine/scripts/build_worker.py" --output "$app_dir/worker-image.json"
image_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["image_id"])' "$app_dir/worker-image.json")
printf 'PYTHONPATH=%s\nENTROTTER_DOCKER_SOCKET=/var/run/docker.sock\nENTROTTER_WORKER_IMAGE=%s\n' \
  "$app_dir/engine/src" "$image_id" > "$config_dir/engine.env"
chmod 600 "$config_dir/engine.env"
cp "$coordination_checkout/scripts/check_host_envelope.py" "$app_dir/check_host_envelope.py"
cp "$coordination_checkout/deploy/entrotter-engine.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user start entrotter-engine.service
systemctl --user show entrotter-engine.service -p ActiveState -p ControlGroup -p MemoryMax -p TasksMax -p RuntimeMaxUSec
