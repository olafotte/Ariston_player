# Ariston Player Workstation

A computer vision application that reads Ariston vinyl record images and plays the music encoded in them.

## Overview

Ariston records are vinyl records with a unique encoding system where music is represented by holes punched in a spiral pattern on the disc. This application uses image processing to detect these patterns and synthesize the corresponding audio.

## Features

- **Disc Image Selection**: Browse and select from available disc images in the folder
- **Pattern Detection**: Uses computer vision (OpenCV) to detect music patterns on the disc
- **Audio Synthesis**: Generates audio from detected notes using numpy/scipy
- **Synchronized Playback**: Visual playback synchronized with audio output
- **Interactive Configuration**: Click and drag control points to adjust detection parameters
- **Configuration Save**: Settings are automatically saved to JSON files

## Requirements

```
opencv-python
numpy
scipy
pygame
```

Install dependencies:

```bash
pip install opencv-python numpy scipy pygame
```

## Usage

1. Place your disc image files (.jpg, .jpeg, .png, .bmp, .tiff) in the same folder as the script
2. Run the program:

```bash
python Ariston_player.py
```

3. Select a disc image from the list
4. Use the following controls:

| Key | Action |
|-----|--------|
| ENTER | Play detected music |
| Z/X | Rotate pattern counter-clockwise/clockwise |
| +/- | Increase/decrease detection sensitivity |
| ESC | Exit |

### Mouse Controls

- **Left Click + Drag**: Move control points (green for outer, yellow for inner)
- **Right Click + Drag**: Draw exclusion mask (ignore areas)

## Configuration

The application saves configuration to a JSON file with the same name as your disc image (e.g., `disc.json` for `disc.jpg`). This file contains:

- `pontos_ext`: Outer control points coordinates
- `pontos_int`: Inner control points coordinates

## How It Works

1. **Image Loading**: Reads the selected disc image
2. **Threshold Detection**: Applies binary threshold to detect holes in the disc
3. **Ellipse Mapping**: Maps 24 concentric ellipses representing musical notes
4. **Note Detection**: Scans each ellipse for valid note patterns
5. **Audio Synthesis**: Converts detected notes to audio using sine wave synthesis
6. **Playback**: Plays audio with synchronized visual needle movement

## Project Structure

```
Ariston_player/
├── Ariston_player.py    # Main application
├── .gitignore          # Git ignore rules
├── README.md           # This file
├── disc.json           # Sample configuration
└── disc*.jpg           # Sample disc images
```

## License

MIT License