# Installation Guide

This guide explains how to set up the analyzers and responders in this repository.

## Table of Contents

- [Requirements](#requirements)
- [Build your own](#build-your-own)
  - [Clone the Git repository](#clone-the-git-repository)
  - [Build the container images and catalog](#build-the-container-images-and-catalog)
  - [Mount the local catalogs into Cortex](#mount-the-local-catalogs-into-cortex)
  - [Add the catalog to Cortex](#add-the-catalog-to-cortex)
- [Deploy using the pre-built catalog](#deploy-using-the-pre-built-catalog)
  - [Locate `application.conf`](#locate-applicationconf)
  - [Back up the configuration](#back-up-the-configuration)
  - [Add the catalog](#add-the-catalog)
  - [Catalog URLs](#catalog-urls)
  - [Restart Cortex](#restart-cortex)
  - [Enable and configure the Neurons](#enable-and-configure-the-neurons)
- [Update outdated images](#update-outdated-images)

## Requirements

- A working [Docker installation](https://docs.docker.com/engine/install/)
- A working Cortex installation, either [installed natively](https://docs.strangebee.com/cortex/installation-and-configuration/) or deployed using [Docker Compose](https://github.com/StrangeBeeCorp/docker/tree/main/prod1-cortex)
- Basic knowledge of Linux, Docker, and Cortex
- Local builds require the sudo, git, bash, and jq commands.

## Build your own

Instead of using the pre-built version, you can optionally build the Docker images yourself and configure Cortex with a local catalog.

**Note:** Locally built images must be rebuilt manually. See [Update outdated images](#update-outdated-images)

### Clone the Git repository

First, create a user-owned directory under `/opt` and clone the Git repository:

```bash
sudo install -d -o "$USER" -g "$(id -gn)" /opt/thephish-ng-neurons
cd /opt/thephish-ng-neurons

git clone https://github.com/dead-plant/ThePhish-NG-Neurons.git .
```

### Build the container images and catalog

Then you can run the build script.

```bash
bash ./utils/build.sh
```

The script should automatically create the Docker images and the catalog files at `./analyzers/analyzers.json` and `./responders/responders.json`.

### Mount the local catalogs into Cortex

If Cortex is deployed using Docker Compose, you have to mount the local catalogs into the Cortex container. Add the following volumes to the `cortex` service in your Compose file. Make sure not to change or remove the existing volumes:

```yaml
services:
  cortex:
    volumes:
      # Keep the existing volumes here.
      - /opt/thephish-ng-neurons/analyzers/analyzers.json:/opt/thephish-ng-neurons/analyzers/analyzers.json:ro
      - /opt/thephish-ng-neurons/responders/responders.json:/opt/thephish-ng-neurons/responders/responders.json:ro
```

If you cloned the repository somewhere else, replace the path before the first colon with that host path. The second path is the location that Cortex can access; use it when configuring the catalog URLs:

```text
/opt/thephish-ng-neurons/analyzers/analyzers.json
/opt/thephish-ng-neurons/responders/responders.json
```

Recreate the Cortex service after changing the volume configuration:

```bash
docker compose up -d --force-recreate cortex
```

### Add the catalog to Cortex

After building the local catalog, follow the [pre-built catalog deployment steps](#deploy-using-the-pre-built-catalog). Use the path to the local catalog file instead of a public catalog URL.

## Deploy using the pre-built catalog

Cortex can load the pre-built catalog directly from GitHub Pages and pull the corresponding Docker images from the GitHub Container Registry.

### Locate `application.conf`

For a native Cortex installation, the configuration file is normally located at:

```text
/etc/cortex/application.conf
```

For a Docker Compose deployment, the location on the host depends on the Cortex service's volume mapping. Find the volume whose destination inside the container is `/etc/cortex`. For example:

```yaml
services:
  cortex:
    volumes:
      - ./cortex/config:/etc/cortex:ro
```

In this example, the configuration file is located at `cortex/config/application.conf`, relative to the Compose directory. The referenced StrangeBee Docker Compose deployment uses this layout, but other deployments may use a different host path.

Set `APPLICATION_CONFIG` to the appropriate host path so the following commands can be copied directly. For a native installation:

```bash
APPLICATION_CONFIG=/etc/cortex/application.conf
```

For the example Docker Compose layout:

```bash
APPLICATION_CONFIG=/path/to/cortex-compose/cortex/config/application.conf
```

### Back up the configuration

Create a backup before editing the Cortex configuration:

```bash
sudo cp -- "$APPLICATION_CONFIG" "${APPLICATION_CONFIG}.bak"
```

### Add the catalog

Open the configuration file with your preferred editor. For example:

```bash
sudo nano "$APPLICATION_CONFIG"
```

Find the existing `analyzer` and `responder` sections and add the appropriate catalog URL to each `urls` list:

```hocon
analyzer {
  urls = [
    "https://catalogs.download.strangebee.com/latest/json/analyzers.json",
    "https://dead-plant.github.io/ThePhish-NG-Neurons/analyzers.json"
  ]

  # Keep the remaining analyzer configuration unchanged.
}

responder {
  urls = [
    "https://catalogs.download.strangebee.com/latest/json/responders.json",
    "https://dead-plant.github.io/ThePhish-NG-Neurons/responders.json"
  ]

  # Keep the remaining responder configuration unchanged.
}
```

Add responder catalogs to the `responder` section and analyzer catalogs to the `analyzer` section. The example uses the pre-built catalog URLs.

### Catalog URLs

The pre-built catalogs are available at:

```text
# Analyzers
https://dead-plant.github.io/ThePhish-NG-Neurons/analyzers.json

# Responders
https://dead-plant.github.io/ThePhish-NG-Neurons/responders.json
```

For a local catalog, use paths accessible to the Cortex process. For example:

```text
# Analyzers
/opt/thephish-ng-neurons/analyzers/analyzers.json

# Responders
/opt/thephish-ng-neurons/responders/responders.json
```

When Cortex runs in Docker, local catalog files must be mounted into the Cortex container, and the paths in `application.conf` must use their locations inside the container.

### Restart Cortex

Restart Cortex to load the new catalog.

For Docker Compose, run the following command from the Compose directory:

```bash
docker compose restart cortex
```

For a native installation:

```bash
sudo systemctl restart cortex
sudo systemctl status cortex --no-pager
```

### Enable and configure the Neurons

The added Neurons should now appear in the Cortex interface. Enable and configure the Neurons you want to use, referring to their individual documentation in the repository's [list of Neurons](../README.md#list-of-neurons).

## Update outdated images

First you have to `cd` into the Git repository. If you used the default path from [Clone the Git repository](#clone-the-git-repository) this command should work:

```bash
cd /opt/thephish-ng-neurons
```

Once you have located the repository, run the following commands. The build script should automatically create the new images and update the catalog files.

```bash
git pull --ff-only

bash ./utils/build.sh
```
