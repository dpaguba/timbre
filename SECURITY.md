# Security

## Reporting a vulnerability

Report privately through GitHub: open the repository's **Security** tab and
choose **Report a vulnerability**. That opens a draft advisory only the
maintainers can read. Please do not open a public issue for a security problem.

Include what you did, what happened, and which build you were running: the
desktop app and its version, or the commit you ran from source. A proof of
concept helps but is not required.

Expect a first reply within a week. If a fix is warranted it ships in the next
release and the advisory is published with credit, unless you prefer otherwise.

## What this project defends against

Timbre runs entirely on one machine. It binds to `127.0.0.1`, never opens a
port to the network, and sends nothing anywhere. The threat it is built against
is therefore not a remote attacker but **another program on the same computer,
and any web page the user happens to have open**.

Two mechanisms cover that, one per build.

**Browser build.** The API and the page share an origin, and every
state-changing request must come from it. This is not redundant with CORS:
`multipart/form-data` is a CORS-safelisted content type, so a POST from any page
on the internet reaches a local server without a preflight, and CORS alone would
only decide whether the reply is readable, not whether the upload happened. The
host header is pinned to localhost as well, so the server does not answer to a
hostname that happens to resolve to `127.0.0.1`.

**Desktop build.** The shell generates 128 bits from the OS random source at
every launch, passes it to the server, and every API call must carry it as a
bearer token. Another process on the machine cannot guess it, which is a
guarantee no header check can make. The port is chosen at random too. The
endpoint that transcribes a file already on disk exists only when a token is
configured, because that is the only mode in which a request can be trusted to
name a path.

Uploads are bounded per file and per job, so a mistake becomes a clear error
rather than a full disk, and uploaded names are stripped to a bare filename
before anything touches the filesystem.

## What it does not defend against

- **A machine that is already compromised.** Anything running as your user can
  read the token, the model cache and the transcripts.
- **Multi-user or shared hosts.** The design assumes one person on one machine.
  Do not put this behind a reverse proxy or bind it to a routable address; none
  of the above is a substitute for authentication.
- **The contents of what you transcribe.** Transcripts are written unencrypted
  under the application data directory and pruned on a schedule, not shredded.

## Downloads and signing

Release builds are not signed with a paid certificate. macOS and Windows both
warn on first launch, and the README explains the extra step. Verify you are
downloading from this repository's releases page; there is nothing else that
attests to a build's origin yet.
