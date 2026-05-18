# BCH Solo Node Umbrel App

This app is packaged as its own Umbrel app and no longer depends on the reference app's code or image names:

- `init` seeds and repairs BCHN + ckpool config
- `bchn` builds and runs Bitcoin Cash Node from upstream source
- `ckpool` builds and runs ckpool from upstream source
- `app` serves the BCH Solo Node dashboard and API
- `app_proxy` exposes the app inside Umbrel

## Current capabilities

- Node settings are written into `bitcoin.conf`
- Pool settings are written into `ckpool.conf`
- Pruning, txindex, payout address, `mindiff`, `startdiff`, and `maxdiff` are configurable
- Worker visibility, sync widgets, basic pool status, solved-block scanning, and round-luck endpoints are provided by the local app service
- Miner endpoint is exposed on `stratum+tcp://<your-host-ip>:4633`

## Notes

- BCHN and ckpool are still upstream open-source projects, but they are now built through local Dockerfiles in this repository rather than pulled from third-party packaged images
- Support and telemetry endpoints are disabled by default

## App structure

- [umbrel-app.yml](<D:\BCH Umbrel App\umbrel-app.yml:1>)
- [docker-compose.yml](<D:\BCH Umbrel App\docker-compose.yml:1>)
- [web/server.py](<D:\BCH Umbrel App\web\server.py:1>)
- [web/index.html](<D:\BCH Umbrel App\web\index.html:1>)
- [data/templates/bitcoin.conf.template](<D:\BCH Umbrel App\data\templates\bitcoin.conf.template:1>)
- [data/templates/ckpool.conf.template](<D:\BCH Umbrel App\data\templates\ckpool.conf.template:1>)
