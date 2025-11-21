# Jhakaas: Photo Enhancement Strategy

This document outlines the specific photo editing and enhancement capabilities, categorized by where they are processed (Client vs. Server) and their associated cost/complexity.

## Enhancement & Editing Matrix

| Feature Category | Feature Name | Execution | Tech Stack | Cost Tier | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Basic Edits** | **Crop & Rotate** | 🟢 **Client-Side** | Canvas API | Free | Standard cropping (1:1, 4:5, 9:16) and rotation. |
| | **Adjustments** | 🟢 **Client-Side** | CSS Filters / WebGL | Free | Brightness, Contrast, Saturation, Warmth, Vignette. |
| | **Basic Filters** | 🟢 **Client-Side** | WebGL (LUTs) | Free | Standard Instagram-like filters (Vivid, B&W, Sepia, Cool). |
| | **Text & Stickers** | 🟢 **Client-Side** | Canvas API | Free | Add text captions or fun stickers (e.g., "Goa 2025"). |
| **AI Style Transfer** | **"The Sangeet"** | 🔴 **Server AI** | Stable Diffusion / LoRA | Premium | Adds a golden, cinematic glow, enhances jewelry sparkle. |
| | **"Monsoon Mood"** | 🔴 **Server AI** | Stable Diffusion | Premium | Adds rain, mist, and moody blue/green tones. |
| | **"Bollywood Poster"** | 🔴 **Server AI** | ControlNet + SD | Premium | Transforms the photo into a hand-painted vintage movie poster. |
| | **"Sketch / Art"** | 🔴 **Server AI** | Style Transfer Models | Premium | Converts photo to Pencil Sketch, Oil Painting, or Watercolor. |
| | **"Cyberpunk / Neon"** | 🔴 **Server AI** | Stable Diffusion | Premium | Futuristic neon lighting, great for party/night shots. |
| **Face & People** | **Group Beauty Mode** | 🔴 **Server AI** | GFPGAN / CodeFormer | Premium | Enhances faces, smooths skin, and fixes lighting for *everyone* in the group. |
| | **"Open Eyes"** | 🔴 **Server AI** | In-painting | Premium | Fixes blinking eyes in group shots. |
| | **Remove Photobomber**| 🔴 **Server AI** | In-painting (LaMa) | Premium | Select and remove unwanted people/objects from the background. |
| **Background** | **Portrait Blur (Bokeh)**| 🔴 **Server AI** | Depth Estimation | Premium | DSLR-like background blur effect. |
| | **Sky Replacement** | 🔴 **Server AI** | Segmentation + In-painting| Premium | Replaces dull grey skies with sunny blue or dramatic sunsets. |
| **Generative** | **Magic Expand** | 🔴 **Server AI** | Out-painting | Premium | Expands a 1:1 photo to 9:16 for Stories by generating new content. |

## Technical Implementation Notes

### 🟢 Client-Side (Instant)
*   **Library**: `react-easy-crop` for cropping, `pixi.js` or custom WebGL shaders for filters.
*   **UX**: Instant feedback, no loading spinners.
*   **Storage**: Processed on the user's device; only the final result is uploaded if saved.

### 🔴 Server-Side (AI / Async)
*   **Provider**: Replicate (e.g., Stable Diffusion XL, CodeFormer) or custom GPU worker (Modal/RunPod).
*   **UX**: Asynchronous queue. User clicks "Apply", sees a "Processing..." state (10-30s), and gets a notification when done.
*   **Cost Control**: These operations cost money per run.
    *   **Preview**: Generate a low-res preview for fast feedback (cheaper).
    *   **Final**: Generate high-res only when the user "Votes" or "Downloads".
