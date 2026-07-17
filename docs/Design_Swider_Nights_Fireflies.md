# Design Document: Swider Nights & Fireflies

## Overview
This document outlines the design concepts for the **Swider** day/night theme manager and dashboard component, focusing on performance optimizations for mobile devices (target <15 MB RAM usage).

## Objectives
- Seamless transition between day and night themes.
- Lightweight WebGL rendering for firefly effects.
- Responsive UI for various screen sizes.
- Minimal bundle size and runtime memory footprint.

## Architecture
- **React** for UI composition.
- **Three.js** (or minimal WebGL wrapper) for firefly particle system.
- CSS custom properties for theme colors.
- Lazy loading of heavy assets.

## Performance Considerations
- Limit particle count to ~200.
- Use requestAnimationFrame with throttling.
- Bundle with Vite's esbuild for tree‑shaking.
- Avoid large image assets; prefer procedural graphics.

## Next Steps
1. Implement `ThemeManager` component.
2. Build `Dashboard` UI.
3. Integrate WebGL firefly effect.
