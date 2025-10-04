#!/usr/bin/env sh

copy_deploy () {

	_cdomain="$1"
	_ckey="$2"
	_ccert="$3"
	_cca="$4"
	_cfullchain="$5"

	_debug _cdomain "$_cdomain"
	_debug _ckey "$_ckey"
	_debug _ccert "$_ccert"
	_debug _cca "$_cca"
	_debug _cfullchain "$_cfullchain"

	_deploy_dir="/certs/$_cdomain"
	_debug _deploy_dir "$_deploy_dir"

	if [ ! -d "$_deploy_dir" ]; then
		_err "Deployment directory does not exist: $_deploy_dir"
		return 1
	fi

	_uid=$(stat -c '%u' "$_deploy_dir")
	_gid=$(stat -c '%g' "$_deploy_dir")
	_debug _uid "$_uid"
	_debug _gid "$_gid"

	/usr/bin/install -o "$_uid" -g "$_gid" -m 600 "$_ckey" "$_deploy_dir/key.pem"
	/usr/bin/install -o "$_uid" -g "$_gid" -m 644 "$_ccert" "$_deploy_dir/cert.pem"
	/usr/bin/install -o "$_uid" -g "$_gid" -m 644 "$_cca" "$_deploy_dir/ca.pem"
	/usr/bin/install -o "$_uid" -g "$_gid" -m 644 "$_cfullchain" "$_deploy_dir/fullchain.pem"

	_info "Certificate successfully deployed"

	return 0
}

