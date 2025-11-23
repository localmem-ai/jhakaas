# 🔒 License Audit - Commercial Use Compliance

**Date:** 2025-11-23  
**Purpose:** Verify all models and LoRAs can be used commercially  
**Status:** ⚠️ **CRITICAL ISSUE FOUND**

---

## ⚠️ **CRITICAL FINDING: InstantID NOT COMMERCIALLY LICENSED**

### **🚨 BLOCKER: InsightFace Models**

**InstantID uses InsightFace face models which are NON-COMMERCIAL ONLY**

- **InstantID Code:** Apache License 2.0 ✅ (Commercial OK)
- **InsightFace Face Models:** ❌ **NON-COMMERCIAL RESEARCH ONLY**

**From InstantID GitHub:**
> "The face models from InsightFace (both manual and auto-downloaded) are for non-commercial research purposes only according to their license."

**Impact:**
- ❌ **Cannot use InstantID for commercial Jhakaas platform**
- ❌ **Any product using InsightFace embeddings inherits non-commercial license**
- ❌ **This affects your entire worker service**

---

## 📋 **Full License Audit**

### **✅ SAFE FOR COMMERCIAL USE:**

| Model/LoRA | License | Commercial Use | Status |
|------------|---------|----------------|--------|
| **SDXL Base 1.0** | CreativeML Open RAIL++-M | ✅ **YES** | Safe |
| **VAE FP16 Fix** | CreativeML Open RAIL++-M | ✅ **YES** | Safe |
| **PS2 LoRA** | Not specified (likely permissive) | ⚠️ **Unknown** | Check needed |
| **Pixel Art LoRA** | Not specified | ⚠️ **Unknown** | Check needed |
| **Aesthetic LoRA** | Not specified | ⚠️ **Unknown** | Check needed |
| **Anime LoRA (ntc-ai)** | Not specified | ⚠️ **Unknown** | Check needed |
| **Cartoon LoRA (ntc-ai)** | Not specified | ⚠️ **Unknown** | Check needed |
| **Pixar LoRA (ntc-ai)** | Not specified | ⚠️ **Unknown** | Check needed |

### **❌ NOT SAFE FOR COMMERCIAL USE:**

| Model/LoRA | License | Commercial Use | Status |
|------------|---------|----------------|--------|
| **InstantID** | Apache 2.0 (code) | ❌ **NO** | **BLOCKER** |
| **InsightFace (AntelopeV2)** | Non-commercial research only | ❌ **NO** | **BLOCKER** |

---

## 🔍 **Detailed License Analysis**

### **1. SDXL Base 1.0** ✅
- **License:** CreativeML Open RAIL++-M
- **Commercial Use:** ✅ **YES - Explicitly allowed**
- **Restrictions:** 
  - Cannot use for harmful purposes
  - Must include license in derivatives
  - Ethical usage guidelines apply
- **Source:** https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
- **Verdict:** **SAFE FOR COMMERCIAL USE**

### **2. InstantID** ❌
- **Code License:** Apache 2.0 ✅
- **Face Models License:** Non-commercial research only ❌
- **Commercial Use:** ❌ **NO - InsightFace models are non-commercial**
- **Critical Quote:**
  > "The face models from InsightFace (both manual and auto-downloaded) are for non-commercial research purposes only according to their license."
- **Source:** https://github.com/InstantX/InstantID
- **Verdict:** **CANNOT USE FOR COMMERCIAL JHAKAAS PLATFORM**

### **3. InsightFace (AntelopeV2)** ❌
- **License:** Non-commercial research only
- **Commercial Use:** ❌ **NO**
- **Impact:** Blocks commercial use of InstantID
- **Source:** https://github.com/deepinsight/insightface
- **Verdict:** **BLOCKER FOR COMMERCIAL USE**

### **4. VAE FP16 Fix** ✅
- **License:** CreativeML Open RAIL++-M (inherits from SDXL)
- **Commercial Use:** ✅ **YES**
- **Verdict:** **SAFE**

### **5. LoRAs (ntc-ai, artificialguybr, nerijs)** ⚠️
- **License:** Not explicitly stated on most models
- **Commercial Use:** ⚠️ **UNKNOWN - Need to verify each**
- **Action Required:** Check each LoRA's HuggingFace page for license
- **Verdict:** **NEEDS VERIFICATION**

---

## 🚨 **CRITICAL RECOMMENDATIONS**

### **Immediate Actions Required:**

1. **❌ STOP using InstantID for commercial Jhakaas**
   - Current implementation violates InsightFace license
   - Cannot launch commercially with this setup

2. **✅ Find Commercial-Friendly Alternatives:**

   **Option A: Use IP-Adapter + ControlNet (No InsightFace)**
   - IP-Adapter: https://huggingface.co/h94/IP-Adapter
   - License: Apache 2.0 ✅
   - Face embeddings: Use CLIP instead of InsightFace
   - **Pros:** Commercially safe
   - **Cons:** Less accurate face preservation

   **Option B: Use FaceID (Commercial License)**
   - FaceID: https://huggingface.co/h94/IP-Adapter-FaceID
   - Check if uses commercial-safe face detection
   - **Pros:** Similar to InstantID
   - **Cons:** Need to verify license

   **Option C: Train Your Own Face Encoder**
   - Use commercial-safe face detection (e.g., MediaPipe)
   - Train custom IP-Adapter
   - **Pros:** Full control, commercial-safe
   - **Cons:** Requires ML expertise and compute

   **Option D: License InsightFace Commercially**
   - Contact InsightFace team for commercial license
   - **Pros:** Keep current setup
   - **Cons:** May be expensive

3. **✅ Verify All LoRA Licenses:**
   - Check each LoRA on HuggingFace
   - Document licenses
   - Remove any non-commercial LoRAs

---

## 📊 **Commercial-Safe Architecture**

### **Recommended Stack (All Commercial-Safe):**

```
✅ SDXL Base 1.0 (CreativeML Open RAIL++-M)
✅ IP-Adapter (Apache 2.0)
✅ ControlNet (Apache 2.0)
✅ MediaPipe Face Detection (Apache 2.0)
✅ CLIP Image Encoder (MIT License)
✅ VAE FP16 Fix (CreativeML Open RAIL++-M)
```

**This stack is 100% commercial-safe!**

---

## 🔄 **Migration Path**

### **Phase 1: Immediate (This Week)**
1. Document current license violations
2. Research IP-Adapter alternatives
3. Test IP-Adapter + ControlNet without InsightFace
4. Verify LoRA licenses

### **Phase 2: Short-term (1-2 Weeks)**
1. Implement IP-Adapter + MediaPipe face detection
2. Test face preservation quality
3. Compare results with InstantID
4. Update documentation

### **Phase 3: Long-term (1-2 Months)**
1. If quality not acceptable, train custom face encoder
2. Use commercial-safe datasets
3. Deploy production-ready commercial stack

---

## 📝 **LoRA License Verification Checklist**

Need to manually check these on HuggingFace:

- [ ] ntc-ai/SDXL-LoRA-slider.anime
- [ ] ntc-ai/SDXL-LoRA-slider.cartoon
- [ ] ntc-ai/SDXL-LoRA-slider.pixar-style
- [ ] ntc-ai/SDXL-LoRA-slider.aesthetic
- [ ] artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl
- [ ] nerijs/pixel-art-xl

**How to check:**
1. Visit HuggingFace model page
2. Look for "License" field in model card
3. If not specified, check README or contact author
4. Document findings

---

## ⚖️ **Legal Considerations**

### **Risk Assessment:**

| Risk | Severity | Likelihood | Impact |
|------|----------|------------|--------|
| **Using InstantID commercially** | 🔴 **CRITICAL** | High | Legal action, forced shutdown |
| **Using unlicensed LoRAs** | 🟡 **MEDIUM** | Medium | Takedown requests |
| **SDXL commercial use** | 🟢 **LOW** | Low | Explicitly allowed |

### **Liability:**
- Using non-commercial models commercially = **License violation**
- Potential consequences:
  - Cease and desist letters
  - Lawsuits
  - Platform shutdown
  - Reputation damage

---

## ✅ **Action Plan**

### **Immediate (Today):**
1. ✅ Document license audit (this file)
2. ⚠️ **DO NOT deploy current InstantID setup commercially**
3. ✅ Research IP-Adapter alternatives

### **This Week:**
1. Test IP-Adapter + MediaPipe
2. Verify all LoRA licenses
3. Create commercial-safe branch

### **Next 2 Weeks:**
1. Implement commercial-safe face preservation
2. Test quality vs InstantID
3. Update deployment

### **Before Launch:**
1. ✅ All models verified commercial-safe
2. ✅ Legal review if needed
3. ✅ Documentation updated
4. ✅ Terms of Service include proper attributions

---

## 📚 **Resources**

### **Commercial-Safe Alternatives:**
- **IP-Adapter:** https://github.com/tencent-ailab/IP-Adapter
- **MediaPipe Face Detection:** https://developers.google.com/mediapipe
- **CLIP:** https://github.com/openai/CLIP
- **ControlNet:** https://github.com/lllyasviel/ControlNet

### **License Information:**
- **CreativeML Open RAIL++-M:** https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md
- **Apache 2.0:** https://www.apache.org/licenses/LICENSE-2.0
- **InsightFace License:** https://github.com/deepinsight/insightface/blob/master/LICENSE

---

## 🎯 **Bottom Line**

### **Current Status:**
❌ **CANNOT LAUNCH COMMERCIALLY WITH INSTANTID**

### **Required Action:**
🔄 **MUST REPLACE INSTANTID WITH COMMERCIAL-SAFE ALTERNATIVE**

### **Timeline:**
- **Research:** 1-2 days
- **Implementation:** 1-2 weeks
- **Testing:** 1 week
- **Total:** 2-3 weeks to commercial-safe setup

---

**⚠️ CRITICAL: Do not launch Jhakaas commercially until this is resolved!**

**Next Step:** Research and test IP-Adapter + MediaPipe as InstantID replacement.

---

*Last Updated: 2025-11-23*  
*Audited By: AI Assistant*  
*Status: BLOCKER IDENTIFIED - ACTION REQUIRED*
