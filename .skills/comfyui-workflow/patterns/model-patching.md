# Custom Model Patching Patterns

## When to Use

Modify a diffusion model's internal behavior at runtime — custom attention mechanisms, alternative sampling strategies, cross-attention injection, or monkey-patching forward methods. Use when standard nodes cannot express the desired modification, and you need direct control over the model's computation graph.

## Required Nodes

| Node Type | Purpose |
|---|---|
| `CheckpointLoaderSimple` | Load base diffusion model |
| `ModelPatchNode` | Custom node that patches the model (node name varies) |
| `CLIPTextEncode` | Encode text prompt |
| `EmptyLatentImage` | Create blank latent |
| `KSampler` | Denoise latent using patched model |
| `VAEDecode` | Decode latent to pixel image |
| `SaveImage` | Save final output |

## Connection Order

```
CheckpointLoaderSimple
  ├── model → ModelPatchNode.model
  ├── clip  → CLIPTextEncode.clip
  └── vae   → VAEDecode.vae

ModelPatchNode
  └── MODEL → KSampler.model

CLIPTextEncode (positive)
  └── CONDITIONING → KSampler.positive

CLIPTextEncode (negative)
  └── CONDITIONING → KSampler.negative

EmptyLatentImage
  └── LATENT → KSampler.latent_image

KSampler
  └── LATENT → VAEDecode.samples

VAEDecode
  └── IMAGE → SaveImage.images
```

## Node-by-Node Wiring Guide

### 1. CheckpointLoaderSimple

```
Inputs:
  ckpt_name: "juggernautXL_v9.safetensors"          (widget, model file)

Outputs:
  MODEL → ModelPatchNode.model
  CLIP  → CLIPTextEncode.clip
  VAE   → VAEDecode.vae
```

### 2. ModelPatchNode

Custom node that modifies the model. The exact node name depends on the custom node pack. Common examples:

- `ModelPatchAttnKVBias` — modify attention key/value
- `PatchModelAddDownscale` — add downscale to model
- `ModelMergeSimple` — merge two models
- Custom Python node using `model.clone()` and `model_options`

```
Inputs:
  model:      ← CheckpointLoaderSimple.MODEL
  strength:   1.0                                  (widget, float)
  [custom parameters specific to the patch node]

Outputs:
  MODEL → KSampler.model
```

### 3. CLIPTextEncode (positive)

```
Inputs:
  text: "a highly detailed photograph of a mountain landscape"
  clip: ← CheckpointLoaderSimple.CLIP

Outputs:
  CONDITIONING → KSampler.positive
```

### 4. CLIPTextEncode (negative)

```
Inputs:
  text: "blurry, low quality, distorted"
  clip: ← CheckpointLoaderSimple.CLIP

Outputs:
  CONDITIONING → KSampler.negative
```

### 5. EmptyLatentImage

```
Inputs:
  width:      1024                                 (widget, int)
  height:     1024                                 (widget, int)
  batch_size: 1                                    (widget, int)

Outputs:
  LATENT → KSampler.latent_image
```

### 6. KSampler

```
Inputs:
  model:        ← ModelPatchNode.MODEL
  positive:     ← CLIPTextEncode.positive
  negative:     ← CLIPTextEncode.negative
  latent_image: ← EmptyLatentImage.LATENT
  seed:         42                                 (widget, int)
  steps:        30                                 (widget, int)
  cfg:          7.0                                (widget, float)
  sampler_name: "dpmpp_2m"                         (widget, enum)
  scheduler:    "karras"                           (widget, enum)

Outputs:
  LATENT → VAEDecode.samples
```

### 7. VAEDecode

```
Inputs:
  samples: ← KSampler.LATENT
  vae:     ← CheckpointLoaderSimple.VAE

Outputs:
  IMAGE → SaveImage.images
```

### 8. SaveImage

```
Inputs:
  images: ← VAEDecode.IMAGE
  filename_prefix: "patched"
```

## Writing Custom Patch Nodes

### Core API Pattern

```python
class MyModelPatch:
    """Custom model patch node for ComfyUI."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "patch"
    CATEGORY = "model/patch"

    def patch(self, model, strength):
        # CRITICAL: clone the model to avoid modifying the original
        m = model.clone()

        # Access transformer options for hook registration
        # m.model_options["transformer_options"] is the dict for patches

        # Example: register a custom attention processor
        def custom_attn_fn(q, k, v, extra_options):
            # q, k, v are tensors: [batch, heads, seq_len, dim]
            # Modify attention here
            return k * strength, v * strength

        # Set transformer options
        m.model_options["transformer_options"]["my_custom_fn"] = custom_attn_fn

        return (m,)
```

### model.clone() Behavior

```python
m = model.clone()
```

- Creates a shallow copy of the model object
- `m.model_options` is deep-copied — safe to modify without affecting the original
- `m.model.model` (the actual neural network) is shared — weight modifications affect both
- Always clone before patching to prevent side effects

### model_options["transformer_options"]

This dict controls hooks into the model's attention and feed-forward layers:

```python
m.model_options["transformer_options"] = {
    # Pre-existing keys from other patches
    "patches": {...},
    "cond_or_uncond": [...],

    # Your custom keys
    "my_custom_fn": my_function,
    "my_attention_scale": 1.5,
}
```

Common transformer_options keys:

| Key | Type | Purpose |
|---|---|---|
| `patches` | dict | Registered patch functions by name |
| `cond_or_uncond` | list | Per-batch conditioning mode indicator |
| `attn_bias` | tensor | Attention bias added to attention scores |
| `positive` | tensor | Positive conditioning embeddings |
| `negative` | tensor | Negative conditioning embeddings |
| Custom keys | any | Your own data — accessed in patched functions |

### Monkey-Patching Forward Methods

Replace a layer's forward method to intercept computation:

```python
def patch(self, model, strength):
    m = model.clone()

    # Store original forward method
    original_forward = m.model.diffusion_model.middle_block.forward

    def patched_forward(x, context=None, **kwargs):
        # Pre-processing
        x = x * strength

        # Call original
        result = original_forward(x, context=context, **kwargs)

        # Post-processing
        return result * (1.0 / strength)

    # Replace forward method
    m.model.diffusion_model.middle_block.forward = patched_forward

    return (m,)
```

### Attention Hook Pattern

```python
def patch(self, model, scale):
    m = model.clone()

    def attn_hook(q, k, v, extra_options):
        """Called before attention computation.

        Args:
            q: Query tensor [batch*heads, seq_len, dim]
            k: Key tensor [batch*heads, seq_len, dim]
            v: Value tensor [batch*heads, seq_len, dim]
            extra_options: dict with 'block', 'block_index', etc.

        Returns:
            (modified_k, modified_v)
        """
        # Example: scale keys to control attention sharpness
        k = k * scale
        return k, v

    # Register the hook
    m.model_options["transformer_options"]["patches"]["attn"] = [attn_hook]

    return (m,)
```

### Sampling Hook Pattern

```python
def patch(self, model, step_offset):
    m = model.clone()

    def sample_hook(args):
        """Called at each sampling step.

        Args:
            args: dict with 'input', 'sigma', 'cond', 'uncond', etc.
        """
        # Modify the denoised prediction
        denoised = args["denoised"]
        # Apply custom logic
        return denoised

    m.model_options["transformer_options"]["patches"]["sample"] = [sample_hook]

    return (m,)
```

## Common Patch Patterns

### Attention Scaling

Control attention sharpness globally:

```python
def patch(self, model, scale):
    m = model.clone()
    m.model_options["transformer_options"]["attn_scale"] = scale
    return (m,)
```

### Cross-Attention Injection

Inject external features into cross-attention:

```python
def patch(self, model, features):
    m = model.clone()
    m.model_options["transformer_options"]["injection_features"] = features
    # Register a hook that concatenates features to k/v
    return (m,)
```

### Custom Sigma Schedule

Modify the noise schedule during sampling:

```python
def patch(self model, shift):
    m = model.clone()

    def sigma_hook(sigmas):
        # Shift the sigma schedule
        return sigmas * shift

    m.model_options["transformer_options"]["patches"]["sigmas"] = [sigma_hook]
    return (m,)
```

### Layer-Specific Modification

Patch only specific layers by checking `extra_options`:

```python
def attn_hook(q, k, v, extra_options):
    block = extra_options.get("block", None)
    if block == "middle":
        # Only modify middle block attention
        k = k * 2.0
    return k, v
```

## Key Considerations

- **Always clone**: `model.clone()` is mandatory before any modification. Modifying the original model affects all subsequent uses and can corrupt the workflow.
- **Patch ordering**: Multiple patches are applied in registration order. If two patches modify the same hook, the last one registered wins (or they compose, depending on hook type).
- **VRAM**: Cloning adds minimal overhead (shallow copy), but patches that store tensors or create new modules increase memory usage.
- **Compatibility**: Patches are model-architecture-specific. A patch designed for SDXL's attention structure won't work on SD1.5 or Flux.
- **Debugging**: Use `print()` inside patch functions to inspect tensor shapes and values. ComfyUI logs these to the console.
- **Reversibility**: Cloned models are independent. The original model is unchanged. Discard the cloned model by not connecting it.
- **transformer_options lifecycle**: Options are set once at clone time and accessed during every forward pass. They persist for the entire sampling process.
- **Custom node packs**: Many model patches are available in community node packs (e.g., ComfyUI-Advanced-ControlNet, ComfyUI-Inspire-Pack, ComfyUI-Impact-Pack). Check before writing from scratch.

## Example Widget Values

### Simple Attention Scale

```
CheckpointLoaderSimple: ckpt_name = "sd_xl_base_1.0.safetensors"
ModelPatchNode: strength = 1.5
CLIPTextEncode: text = "a highly detailed portrait, sharp focus"
KSampler: seed=42, steps=30, cfg=7.0, sampler_name="dpmpp_2m", scheduler="karras"
```

### Custom Sampling Hook

```
CheckpointLoaderSimple: ckpt_name = "juggernautXL_v9.safetensors"
ModelPatchNode: step_offset=5, strength=0.8
CLIPTextEncode: text = "abstract art, dynamic composition"
KSampler: seed=123, steps=25, cfg=6.5
```
