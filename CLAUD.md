# Micropolis Rust Port - AI Context

## Project Overview
This is a port of Micropolis (SimCity) to Rust using the Bevy Engine (ECS).

## Tech Stack
- **Language**: Rust
- **Engine**: Bevy
- **UI**: `bevy_egui`

## Principles
- **Data-Oriented Design**: Optimize for cache locality.
- **Concurrent Systems**: Bevy runs systems in parallel where possible.
- **Modular Plugins**: Organize code into Bevy Plugins (e.g., `SimulationPlugin`, `RenderingPlugin`).
