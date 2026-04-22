# Viral Video Generator (VEO 3 & TikTok)

An end-to-end automation suite designed to interface with the **VEO 3 (Kie) API** for programmatic video creation. This project automates the entire pipeline from creative ideation to publishing transformation-style content on TikTok using **Blotato**.

## 🚀 Overview

The system follows a three-phase autonomous workflow to produce high-quality, viral-ready vertical videos:

1.  **Creative Ideation**: Generates striking BEFORE/AFTER transformation concepts for non-human subjects.
2.  **Structured Prompting**: Converts ideas into a cinematic JSON schema optimized for the VEO 3 engine.
3.  **Autonomous Production**: Handles API generation, status polling, and automated TikTok publication.

## 🛠 Workflow Detail

### Phase 1: Creative Ideation
The system generates a specific one-line prompt structure focusing on subject transformations:
`BEFORE: [phrase] → AFTER: [phrase] | TRANSITION: [style] | STYLE: [tags] | PALETTE: [colors] | CAMERA: [movement] | LIGHTING: [descriptor]`

It also handles viral metadata generation, including:
-   Punchy captions with emojis.
-   12 optimized hashtags (Topic-relevant, Popular, and Trending).
-   Sound descriptions for audio alignment.

### Phase 2: Cinematic Scripting
Concepts are transformed into a master JSON schema that controls:
-   **Camera**: Type (dolly, crane, etc.), movement, and lens.
-   **Lighting**: Natural vs. Dramatic, light sources, and FX (fog, flares).
-   **Environment**: Location, set pieces, and ambient mood.
-   **Motion**: Visual flow of the transformation (explosion, vortex, etc.).

### Phase 3: Execution & Publishing
-   **Generation**: Calls the `veo3_fast` model at `api.kie.ai` using a `9:16` aspect ratio.
-   **Polling**: Monitored via `taskId` until the render is complete (~3 minutes).
-   **Distribution**: Automatically uploads the result to **Blotato** and publishes to TikTok with the `postCreateTiktokOptionIsAiGenerated` flag set to `true`.

## ⚙️ Requirements

-   **Kie.ai API Key**: For VEO 3 video generation.
-   **Blotato Account**: For TikTok automation and publishing.
-   **Node.js/Python**: Depending on your implementation environment.

## 📝 License

Refer to [SKILL.md](SKILL.md) for detailed technical specifications and API schemas.
