# McFenlight Repository

Kodi addon repository for **McFenlight** — a video addon for accessing your content from Easynews and Debrid clouds.

## Setup Guide

### 1. Install Kodi

Download and install Kodi 21 (Omega) or newer from [kodi.tv/download](https://kodi.tv/download).

Available for Windows, Mac, Android, Fire TV, Linux, and more.

### 2. Install Confluence Skin (Recommended)

The default Kodi skin works fine, but Confluence gives a cleaner experience:

1. Open Kodi
2. Go to **Settings** (gear icon) > **Interface** > **Skin**
3. Click **Skin** > **Get more...**
4. Select **Confluence** and install it
5. When prompted, switch to the new skin

### 3. Enable Unknown Sources

Kodi blocks third-party addons by default. You need to allow them:

1. Go to **Settings** > **System** > **Add-ons**
2. Enable **Unknown sources**
3. Confirm the warning dialog

### 4. Add the McFenlight Repository

1. Go to **Settings** > **File manager** > **Add source**
2. Click `<None>` and enter: `https://mcmoobud.github.io/mcfenrepo/`
3. Name it `McFenlight` (or whatever you like) and click **OK**

### 5. Install the McFenlight Setup

1. Go to **Add-ons** > **Install from zip file**
2. Select the **McFenlight** source you just added
3. Select `script.mcfenlight.setup/script.mcfenlight.setup-1.0.4.zip`
4. Wait for the "Add-on installed" notification

### 6. Run the Setup

1. Go to **Add-ons** > **Program add-ons** > **McFenlight Setup**
2. It will guide you through everything automatically

> **Note:** Don't install McFenlight directly from Video Add-ons — that only installs the bare addon and skips the scraper setup below. Always run McFenlight Setup first; it installs McFenlight for you as part of the process.

## What Setup Does

McFenlight Setup handles the full install in one go:

- **Installs repositories** — McFenlight repo and CocoScrapers repo (for scraper sources)
- **Installs McFenlight** — the main video addon, plus its dependencies (requests, PIL)
- **Installs CocoScrapers** — the scraper module, and enables it in McFenlight settings automatically
- **TorBox** — pre-configured out of the box, no account or setup needed
- **Trakt authorisation** (optional) — walks you through device auth on your phone (trakt.tv/activate)
- **Kodi language defaults** — sets audio and subtitle language to match your UI language
- **Home screen shortcut** — adds McFenlight to the Confluence skin's video addon shortcuts

After setup completes, restart Kodi and you're good to go.

## Optional: Emby for Kodi

If you use Emby, install it separately after the main setup:

1. Go to **Add-ons** > **Install from zip file** > **McFenlight** source
2. Select `script.mcfenlight.emby/script.mcfenlight.emby-1.0.1.zip`
3. Restart Kodi, then add Emby manually from Add-ons > Install from repository > Emby Repository

## Requirements

- Kodi 21 (Omega) or newer
- A Trakt account ([trakt.tv](https://trakt.tv)) — free, optional

## Troubleshooting

**"Failed to install add-on from zip file"** — Make sure you enabled Unknown sources in Settings > System > Add-ons.

**McFenlight shows errors after install** — Restart Kodi. Setup writes settings that take effect on next launch.

**Trakt not working** — You can re-authorise from within McFenlight: open the addon, go to Settings > Accounts.

**Emby crashes Kodi on install** — This is expected. Restart Kodi, then install Emby manually from Add-ons > Install from repository > Emby Repository.
