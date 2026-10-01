# Read-only Pi evidence

Current sanitized Pi facts are in [runtime follow-up](pi-runtime-follow-up.md) and [inventory](inventory.md). The collection commands below are reserved for the Pi agent or owner terminal; the MSI does not repeat live-host work. Earlier wording about workspace access describes the initial MSI collection guide.

The Pi has not been accessed from this workspace. Run these commands in your
existing Pi terminal as your normal account. They read information; they do not
install software, change services or grant access. If a command is unavailable
or permission is denied, share its sanitized error and skip that command. Do
not add `sudo`, change Docker socket permissions or install anything for this
collection. Confirm your normal Docker CLI targets the Pi before step 2; a
Docker context can target another machine.

Keep the first results private. Review every line before sending a sanitized
copy back in the task. Do not add raw evidence to this public repository.

## 1. Host and storage

```sh
date -u '+%Y-%m-%dT%H:%M:%SZ'
sed -n '/^PRETTY_NAME=/p; /^VERSION_ID=/p' /etc/os-release
uname -smr
free -h
lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINT
findmnt -rn -o SOURCE,TARGET,FSTYPE
df -hT
```

These establish the current OS, architecture, memory, device layout, mounts and
capacity. They do not establish SSD health, mount persistence after a reboot,
the physical disk model, cooling performance or power reliability. Keep disk
paths consistently labeled so the boot disk, data disk and future backup
destination remain distinguishable.

## 2. Docker versions and container names

```sh
docker version --format 'client={{.Client.Version}} server={{.Server.Version}}'
docker compose version
docker info --format 'default_log_driver={{.LoggingDriver}}'
docker ps --all --format 'table {{.Names}}\t{{.Image}}\t{{.State}}\t{{.Status}}'
ss -lntu
```

Use a container name from that list in the next command, replacing
`CONTAINER_NAME`. Repeat for each service to review. This explicitly selects
fields and excludes environment values, labels, startup commands, health-test
commands and health-test output. Docker supports selective inspection using
[format templates](https://docs.docker.com/reference/cli/docker/inspect/).

```sh
docker inspect --type container --format '
name={{.Name}} image={{.Config.Image}} image_id={{.Image}}
state={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}not-reported{{end}}
user={{json .Config.User}} extra_groups={{json .HostConfig.GroupAdd}}
privileged={{.HostConfig.Privileged}} readonly_root={{.HostConfig.ReadonlyRootfs}}
restart={{.HostConfig.RestartPolicy.Name}} network_mode={{.HostConfig.NetworkMode}}
ports={{json .NetworkSettings.Ports}}
networks={{range $name, $settings := .NetworkSettings.Networks}}{{$name}} {{end}}
mounts={{range .Mounts}}
  type={{.Type}} source={{.Source}} destination={{.Destination}} rw={{.RW}}{{end}}
log_driver={{.HostConfig.LogConfig.Type}} max_size={{index .HostConfig.LogConfig.Config "max-size"}} max_files={{index .HostConfig.LogConfig.Config "max-file"}}
' CONTAINER_NAME
```

An empty configured `user` does not identify the effective application user:
an entrypoint can drop privileges. A running state does not prove application
health; `not-reported` means Docker supplied no health status. Keep `0.0.0.0`,
`::`, `127.0.0.1` and `::1` intact when sanitizing bind addresses because their
scope matters. Replace a specific host address with `PI_LAN_IP` or another
consistent role label. Missing port bindings do not prove isolation: host
networking shares the host network namespace and ignores published-port
options. See [Docker host networking](https://docs.docker.com/engine/network/drivers/host/).
The `ss` output lists local listening TCP/UDP sockets without process details;
it does not establish which network clients can reach them.

## 3. Permissions for the identified data paths

Replace the path below with one actual bind-mount source from step 2. Repeat
for configuration, downloads and media paths that services need to share.

```sh
stat -c 'path=%n type=%F mode=%a uid=%u gid=%g' -- /actual/source/path
namei -l -- /actual/source/path
```

Sanitize account names and personal path components consistently in `namei`
output. Keep mode bits and numeric UID/GID values. These checks reveal ordinary
ownership and parent-directory traversal permissions; they do not prove
effective access inside a container or account for every ACL, user namespace
or security policy. If ACLs or a rootless Docker setup are used, say so; a
targeted follow-up can inspect them without changing permissions.

## 4. Files and decisions to return

Send the sanitized results with the original Compose YAML or Portainer stack
source copied and sanitized, including every override in its actual load
order. State enabled profiles and whether Portainer or the CLI deploys it.
Include environment-variable **names only**, plus the names/roles of `.env`,
`env_file`, secret and config files. Do not send their contents. Redact literal
secrets in YAML, including values in URLs, `command`, labels, health checks and
default expressions such as `${TOKEN:-secret}`.

Do not send interpolated `docker compose config` output. Even
`config --no-interpolate` is not a sanitizer: literal secrets remain and service
environment files can be resolved separately. We can review and validate the
sanitized source copies first. Docker documents both `--no-interpolate` and
`--no-env-resolution` in the [Compose config reference](https://docs.docker.com/reference/cli/docker/compose/config/).

Also supply three short decisions:

- Which services should be accessible from the LAN, VPN and Internet; where
  WireGuard runs; whether the gateway has port forwards or UPnP enabled. A
  sanitized rule summary is enough initially; do not export controller backups.
- The proposed backup destination and whether it is physically separate from
  the Pi's disks; available capacity; which data matters; tolerable data loss
  and restore delay; an acceptable maintenance window. No credentials.
- Any existing backup/export schedule, retention, last successful restore
  evidence and preferred failure-notification channel. Do not send archives.

Remove passwords, API/session tokens, VPN private **and preshared** keys,
registry credentials, credential-bearing URLs, public IPs, private endpoints,
email addresses, personal host/account names, serial numbers, UUIDs and private
media/business/career details. Preserve relationships with placeholders such as
`CONFIG_ROOT`, `MEDIA_ROOT` and `PI_LAN_IP`. Never paste `env`, `printenv`, a full
`docker inspect`, Docker `config.json`, `wg showconf`, VPN configuration files,
full logs or unreviewed screenshots. If unsure, omit that field and state what
was omitted. A missing field is preferable to a leaked secret.

The smallest first response is steps 1 and 2 plus the proposed backup
destination. Remaining paths and files can then be requested precisely.
