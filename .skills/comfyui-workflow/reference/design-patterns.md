# ComfyUI Design Patterns

Pipeline architecture patterns for building ComfyUI workflows.

---

## 1. Linear Pipeline

The most common and straightforward pattern. Data flows in a single path from input to output.

### When to Use

- Simple text-to-image generation
- Basic image processing
- Learning and prototyping
- When you need a single, predictable output

### Required Nodes

```
CheckpointLoaderSimple → CLIPTextEncode (positive)
                      → CLIPTextEncode (negative)
                      → EmptyLatentImage
                      → KSampler
                      → VAEDecode
                      → SaveImage
```

### Connection Order

```
1. CheckpointLoaderSimple
   ├── MODEL → KSampler.model
   ├── CLIP  → CLIPTextEncode.positive.clip
   └── CLIP  → CLIPTextEncode.negative.clip

2. CLIPTextEncode (positive)
   └── CONDITIONING → KSampler.positive

3. CLIPTextEncode (negative)
   └── CONDITIONING → KSampler.negative

4. EmptyLatentImage
   └── LATENT → KSampler.latent_image

5. KSampler
   └── LATENT → VAEDecode.samples

6. VAEDecode (VAE from CheckpointLoaderSimple)
   └── IMAGE → SaveImage
```

### Key Considerations

- The VAE output from CheckpointLoaderSimple connects to VAEDecode
- Both CLIPTextEncode nodes share the same CLIP source
- EmptyLatentImage determines output resolution
- KSampler denoise=1.0 for txt2img, <1.0 for img2img

---

## 2. Branching Pipeline

A single source feeds multiple independent paths that may converge at the end.

### When to Use

- Generating multiple variations from the same model
- Comparing different prompts with the same settings
- Processing the same latent with different decoders
- A/B testing configurations

### Required Nodes

```
CheckpointLoaderSimple → CLIPTextEncode (prompt A) → KSampler A → VAEDecode A → SaveImage A
                      → CLIPTextEncode (prompt B) → KSampler B → VAEDecode B → SaveImage B
                      → EmptyLatentImage (shared)
```

### Connection Order

```
1. CheckpointLoaderSimple (single source)
   ├── MODEL  → KSampler A.model, KSampler B.model
   ├── CLIP   → CLIPTextEncode A.clip, CLIPTextEncode B.clip
   └── VAE    → VAEDecode A.vae, VAEDecode B.vae

2. EmptyLatentImage (shared)
   └── LATENT → KSampler A.latent_image, KSampler B.latent_image

3. Each branch operates independently:
   CLIPTextEncode A → KSampler A → VAEDecode A → SaveImage A
   CLIPTextEncode B → KSampler B → VAEDecode B → SaveImage B
```

### Key Considerations

- Branches can have different seeds for variation
- Use different file prefixes to distinguish outputs
- Branches execute in parallel when possible
- Consider using groups to visually separate branches

---

## 3. Multi-Pass Pipeline

Generate a base image, then refine it through multiple passes.

### When to Use

- High-quality image generation with refinement
- Inpainting workflows (generate → mask → regenerate)
- Detail enhancement passes
- Super-resolution pipelines

### Required Nodes

```
CheckpointLoaderSimple → KSampler (pass 1) → VAEDecode → ImageScale → VAEEncode → KSampler (pass 2) → VAEDecode → SaveImage
```

### Connection Order

```
Pass 1: Generate base
1. CheckpointLoaderSimple → KSampler (steps=20, denoise=1.0) → LATENT

Pass 2: Refine
2. LATENT → VAEDecode → IMAGE
3. IMAGE → ImageScale (upscale)
4. ImageScale → VAEEncode → LATENT (upscaled)
5. LATENT (upscaled) → KSampler (steps=10, denoise=0.5) → LATENT (refined)
6. LATENT (refined) → VAEDecode → IMAGE (final)
7. IMAGE → SaveImage
```

### Key Considerations

- Pass 1 uses high denoise (1.0) for generation
- Pass 2 uses lower denoise (0.3-0.6) for refinement
- Steps can be reduced in refinement passes
- Consider using a different sampler for refinement (e.g., dpmpp_2m for refinement)
- Use KSamplerAdvanced for precise step control in multi-pass

---

## 4. Model Patching Chain

Apply model modifications (LoRA, IP-Adapter, etc.) before sampling.

### When to Use

- Using LoRA for style/character consistency
- Applying IP-Adapter for image-guided generation
- Combining multiple model modifications
- Custom model conditioning

### Required Nodes

```
CheckpointLoaderSimple → LoraLoader → IPAdapterApply → KSampler
CLIPVisionLoader → IPAdapterModelLoader → IPAdapterApply
```

### Connection Order

```
1. CheckpointLoaderSimple
   ├── MODEL  → LoraLoader.model
   └── CLIP   → LoraLoader.clip

2. LoraLoader
   ├── MODEL  → IPAdapterApply.model
   └── CLIP   → CLIPTextEncode.clip

3. CLIPVisionLoader
   └── CLIP_VISION → IPAdapterApply.clip_vision

4. IPAdapterModelLoader
   └── IPADAPTER → IPAdapterApply.ipadapter

5. LoadImage (reference image)
   └── IMAGE → IPAdapterApply.image

6. IPAdapterApply
   └── MODEL → KSampler.model

7. CLIPTextEncode → KSampler.positive
8. EmptyLatentImage → KSampler.latent_image
9. KSampler → VAEDecode → SaveImage
```

### Key Considerations

- LoRA strength affects style intensity (0.5-1.0 typical)
- IP-Adapter weight controls reference image influence
- Multiple LoRAs can be chained: LoRA1 → LoRA2 → KSampler
- Order of patches matters: different order = different results
- Some patches modify CLIP, some modify MODEL, some modify both

---

## 5. Video Pipeline

Generate or process video with temporal consistency.

### When to Use

- Text-to-video generation
- Image animation
- Video style transfer
- Frame interpolation

### Required Nodes

```
CheckpointLoaderSimple → CLIPTextEncode → EmptyLatentImage → KSampler → VAEDecode → VHS_VideoCombine
AnimateDiffLoader → KSampler
```

### Connection Order

```
1. CheckpointLoaderSimple
   ├── MODEL → AnimateDiffLoader.model
   └── CLIP  → CLIPTextEncode.clip

2. AnimateDiffLoader
   └── MODEL → KSampler.model

3. CLIPTextEncode → KSampler.positive

4. EmptyLatentImage (batch_size=16 for 16 frames)
   └── LATENT → KSampler.latent_image

5. KSampler
   └── LATENT → VAEDecode.samples

6. VAEDecode
   └── IMAGE → VHS_VideoCombine.images

7. VHS_VideoCombine
   → Configure: frame_rate=8, format="image/gif"
```

### Key Considerations

- Batch size in EmptyLatentImage = number of frames
- AnimateDiff provides temporal consistency
- Frame rate affects playback speed (8-12 fps typical)
- Use consistent seeds across frames for coherence
- Consider frame interpolation for smoother output
- Video formats: GIF, WebP, MP4, WebM

---

## 6. ControlNet Stacking

Apply multiple ControlNet models sequentially for precise spatial control.

### When to Use

- Complex pose + depth + edge control
- Architectural visualization with multiple constraints
- Character consistency with pose + face control
- Fine-grained spatial composition

### Required Nodes

```
ControlNetLoader (depth) → ControlNetApplyAdvanced
ControlNetLoader (pose) → ControlNetApplyAdvanced
ControlNetLoader (canny) → ControlNetApplyAdvanced
```

### Connection Order

```
1. ControlNetLoader (depth)
   └── CONTROL_NET → ControlNetApplyAdvanced.control_net (first)

2. ControlNetLoader (pose)
   └── CONTROL_NET → ControlNetApplyAdvanced.control_net (second)

3. ControlNetLoader (canny)
   └── CONTROL_NET → ControlNetApplyAdvanced.control_net (third)

4. First ControlNetApplyAdvanced:
   ├── positive (from CLIPTextEncode) → output positive
   └── negative (from CLIPTextEncode) → output negative

5. Second ControlNetApplyAdvanced:
   ├── positive (from first) → output positive
   └── negative (from first) → output negative

6. Third ControlNetApplyAdvanced:
   ├── positive → KSampler.positive
   └── negative → KSampler.negative

7. Each ControlNetApplyAdvanced needs:
   ├── image (from LoadImage or preprocessors)
   ├── strength (0.0-1.0)
   ├── start_percent (0.0)
   └── end_percent (1.0)
```

### Key Considerations

- ControlNets are applied in sequence (chained)
- Each ControlNet can have independent strength
- Use start/end percentages to control when each ControlNet is active
- Lower strength values (0.3-0.7) prevent over-constraining
- Different preprocessors may be needed for different ControlNets

---

## 7. Prompt Scheduling

Switch prompts at different stages of sampling for temporal variation.

### When to Use

- Changing style mid-generation
- Transitioning between subjects
- Creating composite styles
- Time-based animation effects

### Required Nodes

```
CLIPTextEncode (prompt A) → ConditioningSetTimestepRange → ConditioningCombine
CLIPTextEncode (prompt B) → ConditioningSetTimestepRange → ConditioningCombine
```

### Connection Order

```
1. CLIPTextEncode (prompt A)
   └── CONDITIONING → ConditioningSetTimestepRange.conditioning
      (start_percent=0.0, end_percent=0.5)

2. CLIPTextEncode (prompt B)
   └── CONDITIONING → ConditioningSetTimestepRange.conditioning
      (start_percent=0.5, end_percent=1.0)

3. Both ConditioningSetTimestepRange outputs
   └── CONDITIONING → ConditioningCombine (or ConditioningConcat)

4. ConditioningCombine
   └── CONDITIONING → KSampler.positive

5. Rest of pipeline: KSampler → VAEDecode → SaveImage
```

### Key Considerations

- Prompt A applies from step 0% to 50%
- Prompt B applies from step 50% to 100%
- Smooth transitions use overlapping ranges
- Use ConditioningCombine for merging, ConditioningConcat for appending
- Advanced scheduling can use multiple ranges with different strengths

---

## 8. Audio-Reactive Pipeline

Use audio analysis to drive visual generation parameters.

### When to Use

- Music visualization
- Audio-driven animation
- Beat-synchronized effects
- Rhythmic pattern generation

### Required Nodes

```
Audio Analysis Node → Scheduler → ConditioningModifier → KSampler
```

### Connection Order

```
1. Load Audio
   └── AUDIO → AudioAnalyzer.input

2. AudioAnalyzer
   ├── BEAT → BeatScheduler.beats
   └── ENERGY → FloatToStrength.energy

3. BeatScheduler
   └── SIGMAS → SamplerCustom.sigmas

4. FloatToStrength
   └── FLOAT → ConditioningSetStrength.strength

5. ConditioningSetStrength
   └── CONDITIONING → KSampler.positive

6. KSampler → VAEDecode → VHS_VideoCombine
```

### Key Considerations

- Audio analysis extracts beats, energy, frequency bands
- Beat synchronization requires accurate BPM detection
- Strength modulation creates pulsing effects
- Consider smoothing for less jarring transitions
- Frame rate should match or be a multiple of audio sample rate

---

## 9. Dynamic Branching

Conditionally execute different paths based on runtime values.

### When to Use

- Conditional processing based on image properties
- Different pipelines for different input types
- Error handling with fallback paths
- A/B testing with random selection

### Required Nodes

```
ImageAnalyzer → ConditionRouter → Pipeline A or Pipeline B
```

### Connection Order

```
1. LoadImage
   ├── IMAGE → ImageAnalyzer.image
   └── IMAGE → Pipeline A.image, Pipeline B.image

2. ImageAnalyzer
   └── BOOLEAN → ConditionRouter.condition

3. ConditionRouter
   ├── true_path → Pipeline A (triggered when true)
   └── false_path → Pipeline B (triggered when false)

4. Pipeline A
   └── IMAGE → SaveImage (filename_prefix="A")

5. Pipeline B
   └── IMAGE → SaveImage (filename_prefix="B")
```

### Key Considerations

- ComfyUI evaluates all nodes by default; use lazy inputs for true conditional execution
- Both branches may be evaluated even if only one output is used
- Consider using Switch node for cleaner branching
- Seed management across branches for consistency

---

## 10. Batch Processing

Process multiple items in a loop or batch configuration.

### When to Use

- Processing multiple images with same settings
- Generating variations of a prompt
- Creating image grids
- Bulk operations on datasets

### Required Nodes

```
LoadImageBatch → KSampler (loop) → SaveImageBatch
```

### Connection Order

```
1. LoadImage (or LoadImageBatch)
   └── IMAGE → BatchProcess.input

2. CheckpointLoaderSimple
   ├── MODEL → KSampler.model
   └── CLIP  → CLIPTextEncode.clip

3. CLIPTextEncode → KSampler.positive

4. KSampler
   └── LATENT → VAEDecode.samples

5. VAEDecode
   └── IMAGE → SaveImage
```

### Key Considerations

- Use batch_size in EmptyLatentImage for parallel generation
- Each image in batch gets same seed (use seed+batch_index for variation)
- Batch processing increases VRAM usage proportionally
- Consider processing in smaller batches for memory efficiency
- Use different filename_prefix for each batch item

---

## Pattern Selection Guide

| Use Case | Recommended Pattern |
|---|---|
| Simple txt2img | Linear Pipeline |
| Style comparison | Branching Pipeline |
| High-res output | Multi-Pass Pipeline |
| Character consistency | Model Patching Chain |
| Animation | Video Pipeline |
| Precise control | ControlNet Stacking |
| Style transitions | Prompt Scheduling |
| Music visualization | Audio-Reactive |
| Conditional logic | Dynamic Processing |
| Bulk generation | Batch Processing |

## Combining Patterns

Patterns can be combined for complex workflows:

```
Model Patching Chain + Multi-Pass:
  CheckpointLoader → LoRA → KSampler (pass1) → Upscale → LoRA → KSampler (pass2) → Save

Branching + ControlNet:
  Single loader → Branch A (with ControlNet depth) → Save
                → Branch B (with ControlNet pose) → Save

Video + Prompt Scheduling:
  AnimateDiff → KSampler (prompt changes per frame batch) → VideoCombine
```
