# Voxel Engine

A work-in-progress Minecraft-style voxel engine built with `pygame`, `moderngl`, and `PyGLM`.

## Overview

This project renders procedural voxel terrain in real time using OpenGL 3.3. The world is split into chunks, mesh geometry is built from visible faces only, and you can walk around, break blocks, and see Minecraft-style block coloring with face shading and ambient occlusion.

## Preview

![Voxel terrain preview](assets/preview-new.png)

## Features

- **Rendering** — OpenGL 3.3 core profile via `pygame` and `moderngl`
- **Terrain** — Procedural heightmap world with grass, dirt, and stone layers
- **Chunks** — 32×32×32 voxel chunks with hidden-face culling and cross-chunk neighbor checks
- **Meshing** — Numba-accelerated mesh builder with ambient occlusion and packed vertex data
- **Shading** — Per-block colors, Minecraft-style face brightness, texture tinting, and gamma correction
- **Player** — First-person walk/run with gravity, jumping, and voxel collision
- **Interaction** — Raycast block selection with a Minecraft-style outline; left-click to remove blocks
- **Live updates** — Modified chunks and neighbors rebuild their meshes after block changes

## Requirements

- Python 3.10+
- GPU with OpenGL 3.3 support

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Controls

| Input | Action |
|-------|--------|
| `W` `A` `S` `D` | Walk |
| `Shift` | Run |
| `Space` | Jump |
| Mouse | Look around |
| Left click | Break block |
| `Esc` | Exit |

## Project Structure

```
main.py                  Entry point, window, and game loop
scene.py                 Scene wrapper around the world
world.py                 Chunk storage, voxel read/write, collision
world_objects/chunk.py     Per-chunk terrain generation and mesh ownership
blocks.py                Block type IDs (grass, dirt, stone)
player.py                Movement, physics, and camera input
camera.py                View/projection math
voxel_handler.py         Raycast, block selection, and removal
meshes/
  chunk_mesh_builder.py  Face culling, AO, and mesh generation (Numba)
  chunk_mesh.py          GPU upload for chunk meshes
  selection_outline.py   Minecraft-style block highlight wireframe
  base_mesh.py           Shared VAO/VBO handling
shader_program.py        Shader loading and uniforms
textures.py              Texture loading and binding
shaders/                 GLSL vertex and fragment shaders
assets/                  Textures and preview images
settings.py              World, player, and rendering constants
```

## How It Works

**Terrain generation** — Each chunk column uses simplex noise to pick a height, then fills blocks from the bottom up as stone, dirt, and grass.

**Meshing** — Only exposed faces are emitted. Ambient occlusion is computed per corner and packed into a single `uint32` per vertex alongside position, block type, and face direction.

**Block colors** — The vertex shader assigns grass, dirt, or stone tints per face. The fragment shader multiplies by a texture sample, applies face shading and AO, then gamma-corrects the result.

**Breaking blocks** — A DDA raycast from the camera finds the targeted block. Removing it sets the voxel to air and rebuilds the affected chunk meshes (including neighbors on shared faces).

## Notes

- Empty chunks are skipped to avoid uploading empty GPU buffers.
- The player spawns on the ground at world center.
- Player settings (speed, gravity, sensitivity, resolution) live in `settings.py`.

## Status

Under active development. Possible next steps include block placement, texture atlases, chunk streaming, and step-up movement on slopes.
