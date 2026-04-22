---
name: video-generator-veo3-KIE-blotato
description: An end-to-end automation skill designed to interface with the VEO 3 (Kie) API for programmatic video creation. It automates the generation and publication of transformation-style content, providing a seamless pipeline from raw data to TikTok using Blotato. Ideal for users looking to architect a fully autonomous AI video production suite.
---

# Viral Video Generator (VEO 3 & TikTok Frame Size)

This skill provides a structured workflow for generating cinematic Before/After transformation videos using AI and publishing them to TikTok.

## Workflow Overview

1.  **Creative Ideation**: Generate a striking Before/After concept with specific visual tags.
2.  **Structured Prompting**: Convert the idea into a detailed JSON schema optimized for the VEO 3 (Kie) API.
3.  **Video Generation**: Execute the generation via the Kie.ai API.
4.  **Publishing**: Retrieve the rendered video and upload it to TikTok via Blotato.

## Phase 1: Creative Ideation

When generating video concepts, adhere to these strict constraints:

-   **Theme**: Always focus on a striking **BEFORE/AFTER transformation** of a single non-human subject (object, environment, or natural phenomenon).
-   **Subject Constraints**: Avoid humans, brands, and clichés (e.g., messy room to clean room).
-   **Formatting**: Output exactly one idea in this one-line structure:
    `BEFORE: [short phrase] → AFTER: [short phrase] | TRANSITION: [style] | STYLE: [tag1, tag2] | PALETTE: [color1, color2] | CAMERA: [movement] | LIGHTING: [descriptor]`

### Metadata Generation
For every video, generate:
-   **Caption**: Short, punchy, viral-friendly title with one emoji.
-   **Hashtags**: Exactly 12 hashtags (4 topic-relevant, 4 all-time popular, 4 currently trending). All lowercase.
-   **Sound Description**: Max 15 words describing the audio flow (e.g., "beat drop at transition").

## Phase 2: Structured Video Scripting

The final prompt for VEO 3 MUST follow the structured JSON schema. This ensures the AI model understands the cinematic nuances.

### Master Schema
```json
{
  "description": "Brief narrative description of the scene.",
  "style": "cinematic | photorealistic | stylized | gritty | elegant",
  "camera": {
    "type": "fixed | dolly | Steadicam | crane combo",
    "movement": "e.g., slow push-in, pan, orbit",
    "lens": "optional focal length"
  },
  "lighting": {
    "type": "natural | dramatic | high-contrast",
    "sources": "e.g., sunset, halogen, ambient glow",
    "FX": "optional fog, reflections, flares"
  },
  "environment": {
    "location": "e.g., desert, lab, kitchen",
    "set_pieces": ["list of key props"],
    "mood": "ambient atmosphere"
  },
  "subject": {
    "product": {
      "brand": "Brand name",
      "model": "Product model",
      "action": "Description of transformation or assembly"
    }
  },
  "motion": {
    "type": "e.g., transformation, explosion, vortex",
    "details": "visual flow of evolution"
  }
}
```

## Phase 3: Execution Logic

### 1. Generate Video (VEO 3)
-   **Endpoint**: `https://api.kie.ai/api/v1/veo/generate`
-   **Headers**: `Authorization: Bearer <API_KEY>`, `Content-Type: application/json`
-   **Model**: Use `veo3_fast`.
-   **Aspect Ratio**: `9:16` (vertical).
-   **Prompt**: The stringified version of the structured JSON from Phase 2.

### 2. Rendering & Polling
-   Rendering typically takes ~3 minutes.
-   Poll the status using `taskId` at `https://api.kie.ai/api/v1/veo/record-info`.
-   **Headers**: `Authorization: Bearer <API_KEY>`

### 3. TikTok Publication (Blotato)
-   Retrieve the `resultUrls[0]` from the polling response.
-   Upload the media to Blotato.
-   Publish to TikTok using the generated **Caption** and **Video URL**.
-   Ensure `postCreateTiktokOptionIsAiGenerated` is set to `true`.
