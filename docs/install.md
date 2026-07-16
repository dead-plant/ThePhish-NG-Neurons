# Installation guide

This guide will help you set up the analyzers and responders in this repository.

## Table of Contents

- [Requirements](#requirements)
- [Build your own](#build-your-own)
  - [Notes](#notes)
  - [Download Release](#download-release)
  - [Build Docker Image](#build-docker-image)
  - [Configure Cortex](#configure-cortex)
- [Deploy using my hosted index file](#deploy-using-remote-index-file)
  - [Add index to Cortex](#add-index-to-cortex)

## Requirements

- A working Docker installation: https://docs.docker.com/engine/install/
- A working Cortex installation: https://docs.strangebee.com/cortex/installation-and-configuration/
- Basic knowledge of Linux, Docker and Cortex

## Build your own

You can deploy these neurons by building container images from the Dockerfile, storing them in a local registry, and configuring Cortex to use a local index file.

### Notes

- If you deploy Neurons this way, you have to update them manually. You can do this by following this guide: [How to Update](how-to-update.md).

### Download Release

Coming soon...

### Build Docker Image

Coming soon...

### Configure Cortex

Coming soon...

## Deploy using remote index file

You can easily deploy the Neurons by adding a reference to my pre-built index file in the Cortex application config.
My index file and the pre-built container images are hosted using GitHub Pages (https://pages.github.com/) and the GitHub Container Registry (https://ghcr.io/).

### Add index to Cortex

Coming soon...
