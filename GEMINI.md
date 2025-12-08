# Micropolis Rust Port - AI Context

## Project Overview
This is a port of Micropolis (SimCity) to Rust using the Bevy Engine (ECS).
The goal is to achieve high-performance simulation (256x256+ maps) using Data-Oriented Design.

## Tech Stack
- **Language**: Rust (2021 edition)
- **Engine**: Bevy 0.15+
- **UI**: `bevy_egui`
- **Serialization**: `serde`
- **Random**: `rand` / `bevy_rand`

## Development Guidelines
- **ECS Architecture**: Split logic into `Components` (Pure Data), `Systems` (Logic), and `Resources` (Global State).
- **No Global Mutable State**: Use Bevy Resources.
- **Error Handling**: Use `Result` and `Option`. Unwrap only when safe or during prototyping.
- **Formatting**: Run `cargo fmt` regularly.
- **Linting**: Run `cargo clippy`.
