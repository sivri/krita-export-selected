# Krita Export Selected

A small Krita plugin for exporting selected layers or groups as trimmed transparent PNGs.

Made for game artists who draw on a large canvas and want to quickly export prototype or production assets for engines like Unreal or Unity.

## Features

- Export selected layers or groups as PNG
- Transparent background
- Auto-trim empty transparent space
- Optional padding
- Optional scaling
- Optional group merge/projection export
- Export multiple selected layers/groups
- Choose export folder in the UI
- Uses clean layer/group names as file names
- No metadata in layer names
- No automatic scale suffixes
- No forced folder structure

## Install

Download the plugin zip, then in Krita:

1. Go to `Tools > Scripts > Import Python Plugin...`
2. Select the zip file
3. Restart Krita
4. Go to `Settings > Configure Krita > Python Plugin Manager`
5. Enable `Export Selected`
6. Restart Krita again
7. Open it from `Settings > Dockers > Export Selected`

## Usage

1. Select one or more layers/groups
2. Choose an export folder
3. Set scale and padding
4. Click `Export Selected`

Example:

Layer name:

```text
Ship_Cockpit