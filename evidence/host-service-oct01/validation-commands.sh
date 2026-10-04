set -eu
app_dir="$HOME/.local/share/entrotter"
for spec in 'sdk b0c2ba3bba411e548af44101ae06e879bd7b5dc0 sdk-python' 'cli a63a39000e03d151e80b5a9c47dd4df449281b93 cli'; do
 set -- $spec
 git init --quiet "$app_dir/$1"
 git -C "$app_dir/$1" fetch --quiet --depth=1 "https://github.com/entrotter/$3.git" "$2"
 git -C "$app_dir/$1" checkout --quiet --detach FETCH_HEAD
 test "$(git -C "$app_dir/$1" rev-parse HEAD)" = "$2"
done
cp /tmp/entrotter-host-oct01-dc5c86b/coordination/tests_host/check_service.py "$app_dir/check_service.py"
python3 "$app_dir/check_service.py" --output "$app_dir/host-proof-oct01.json"
