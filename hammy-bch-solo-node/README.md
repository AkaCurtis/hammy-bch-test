# BCH Solo Node Umbrel App

This app is packaged as its own Umbrel app and no longer depends on the reference app's code or image names:

- `bchn` runs Bitcoin Cash Node from a prebuilt GHCR image
- `ckpool` runs ckpool from a prebuilt GHCR image
- `app` serves the BCH Solo Node dashboard and API
- `app_proxy` exposes the app inside Umbrel

## Current capabilities

- Node settings are written into `bitcoin.conf`
- Pool settings are written into `ckpool.conf`
- Pruning, txindex, payout address, `mindiff`, `startdiff`, and `maxdiff` are configurable
- Worker visibility, sync widgets, basic pool status, solved-block scanning, and round-luck endpoints are provided by the local app service
- Miner endpoint is exposed on `stratum+tcp://<your-host-ip>:4633`

## Notes

- Images are published to GitHub Container Registry through `.github/workflows/publish-ghcr-images.yml`
- Umbrel installs should pull prebuilt images instead of compiling BCHN and ckpool on-device
- Support and telemetry endpoints are disabled by default

## Releasing images

1. Update `hammy-bch-solo-node/umbrel-app.yml`, `hammy-bch-solo-node/docker-compose.yml`, and `hammy-bch-solo-node/web/server.py` to the new version.
2. Push the commit to GitHub.
3. Publish the images either by:
   - creating a Git tag like `v0.3.0`, or
   - running the `Publish GHCR Images` workflow manually with a version input
4. After the GHCR publish completes, Umbrel can install the app by pulling:
   - `ghcr.io/akacurtis/hammy-bch-solo-node-bchn:<version>`
   - `ghcr.io/akacurtis/hammy-bch-solo-node-ckpool:<version>`
   - `ghcr.io/akacurtis/hammy-bch-solo-node-web:<version>`

## App structure

- [umbrel-app.yml](<D:\BCH Umbrel App\umbrel-app.yml:1>)
- [docker-compose.yml](<D:\BCH Umbrel App\docker-compose.yml:1>)
- [web/server.py](<D:\BCH Umbrel App\web\server.py:1>)
- [web/index.html](<D:\BCH Umbrel App\web\index.html:1>)
- [data/templates/bitcoin.conf.template](<D:\BCH Umbrel App\data\templates\bitcoin.conf.template:1>)
- [data/templates/ckpool.conf.template](<D:\BCH Umbrel App\data\templates\ckpool.conf.template:1>)
