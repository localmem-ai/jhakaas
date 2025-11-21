# Decision Record: AI Model Hosting Strategy

## Context
Jhakaas requires advanced AI photo enhancement features (Style Transfer, Face Restoration, In-painting). We need to decide between hosting our own models (e.g., on AWS, Lambda Labs, RunPod) or using managed external services (e.g., Replicate, OpenAI, Stability AI).

## Options Analysis

### Option A: External Managed Services (e.g., Replicate, Stability AI)
**Pros:**
- **Speed to Market:** Immediate access to state-of-the-art models (SDXL, CodeFormer, etc.) via simple APIs.
- **Zero Infrastructure:** No need to manage GPU clusters, scaling, or cold starts.
- **Pay-per-use:** Costs scale linearly with usage; no cost for idle time.
- **Reliability:** Managed uptime and scaling.

**Cons:**
- **Higher Marginal Cost:** Per-generation cost is higher than raw GPU compute at scale.
- **Latency:** Cold boots on serverless endpoints can still take time (though improving).
- **Privacy/Data:** Images leave our infrastructure (though most providers have strict privacy policies).

### Option B: Self-Hosted / Custom GPU Infrastructure (e.g., AWS EC2, RunPod, Modal)
**Pros:**
- **Cost at Scale:** Significantly cheaper per generation if utilization is high (near 100%).
- **Control:** Full control over the inference pipeline, custom optimizations, and fine-tuning.
- **Data Sovereignty:** Images never leave our controlled environment.

**Cons:**
- **High Maintenance:** Requires DevOps to manage auto-scaling, driver updates, and model deployment.
- **Idle Costs:** You pay for the GPU even when no one is using it (unless using serverless GPU providers like Modal, which bridges the gap).
- **Complexity:** Significant engineering effort to set up queues, workers, and storage.

## Recommendation: Option A (External Service - Replicate) for Phase 1

**Rationale:**
For the "Jhakaas" MVP and initial growth phase, **speed and low engineering overhead are paramount**. Managing GPU infrastructure is complex and distracts from building the core product experience. Replicate offers an excellent balance of model variety (SDXL, GFPGAN, etc.) and ease of use.

**Technical Workflow (Phase 1):**
1.  **Client** uploads photo to Supabase Storage.
2.  **Client** requests enhancement via Next.js API Route.
3.  **Next.js API** calls Replicate API with image URL and parameters.
4.  **Replicate** processes image asynchronously.
5.  **Replicate** sends webhook to Next.js API upon completion.
6.  **Next.js API** updates database and notifies Client (via Supabase Realtime).

## Future Path (Phase 2)
Once volume exceeds ~10,000 generations/day, or if we develop proprietary fine-tuned models (LoRAs) that require specific optimization, we should evaluate moving to **Modal** or **RunPod** to reduce costs while maintaining a serverless-like developer experience.
