# Advanced Patterns Reference

Expert-level patterns for ComfyUI custom node development.

## Dynamic Outputs

Nodes that produce a variable number of outputs based on input parameters.

```python
class DynamicSplitter:
    RETURN_TYPES = tuple(["IMAGE"] * 50)  # Maximum possible outputs

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "count": ("INT", {"default": 2, "min": 1, "max": 50}),
            }
        }

    FUNCTION = "split"
    CATEGORY = "image/batch"

    @classmethod
    def IS_DYNAMIC(cls):
        return True

    @classmethod
    def get_output_types(cls, count=1, **kwargs):
        return tuple(["IMAGE"] * int(count))

    @classmethod
    def get_output_names(cls, count=1, **kwargs):
        return tuple([f"image_{i+1}" for i in range(int(count))])

    def split(self, image, count):
        chunks = torch.chunk(image, int(count), dim=0)
        return tuple(chunks)
```

## Model Patching

Clone and modify model behavior without altering the original.

```python
class AttentionOverride:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0}),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "patch"
    CATEGORY = "model/patching"

    def patch(self, model, scale):
        model_clone = model.clone()

        # Store custom parameters in model_options
        model_clone.model_options["transformer_options"]["attention_scale"] = scale

        # Inject into the processing pipeline
        model_clone.set_model_attn1_patch(self.attention_patch)

        return (model_clone,)

    def attention_patch(self, q, k, v, extra_options):
        scale = extra_options["transformer_options"].get("attention_scale", 1.0)
        return q, k * scale, v
```

### model.clone()

Creates a shallow copy of the model. Changes to the clone don't affect the original.

```python
model_clone = model.clone()
```

### model_options and transformer_options

Store custom parameters that are accessible during inference.

```python
model_clone.model_options["my_custom_param"] = value
model_clone.model_options["transformer_options"]["my_param"] = value

# Access in patches via extra_options
def my_patch(self, *args, extra_options):
    value = extra_options["model_options"].get("my_custom_param")
    value = extra_options["transformer_options"].get("my_param")
```

### set_model_attn1_patch

Override self-attention computation.

```python
def my_attn1_patch(self, q, k, v, extra_options):
    # q, k, v: query, key, value tensors
    # Modify and return
    return q, k, v

model_clone.set_model_attn1_patch(my_attn1_patch)
```

### set_model_attn2_patch

Override cross-attention computation.

```python
def my_attn2_patch(self, q, k, v, extra_options):
    return q, k, v

model_clone.set_model_attn2_patch(my_attn2_patch)
```

### set_model_unet_function_wrapper

Override the entire UNet forward pass.

```python
def my_unet_wrapper(apply_model, args):
    # args contains: input, timestep, cond, uncond, etc.
    result = apply_model(args["input"], args["timestep"], **args["cond"])
    return result

model_clone.set_model_unet_function_wrapper(my_unet_wrapper)
```

## Monkey-Patching

Inject custom behavior into model forward methods.

```python
class CrossAttentionInjector:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "style_image": ("IMAGE",),
                "injection_strength": ("FLOAT", {"default": 1.0}),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "inject"
    CATEGORY = "model/patching"

    def inject(self, model, style_image, injection_strength):
        model_clone = model.clone()

        # Store style features for injection
        style_features = self.extract_features(style_image)
        model_clone.model_options["transformer_options"]["style_features"] = style_features
        model_clone.model_options["transformer_options"]["injection_strength"] = injection_strength

        # Patch cross-attention
        model_clone.set_model_attn2_patch(self.style_injection)

        return (model_clone,)

    def style_injection(self, q, k, v, extra_options):
        strength = extra_options["transformer_options"].get("injection_strength", 1.0)
        style = extra_options["transformer_options"].get("style_features")

        if style is not None and strength > 0:
            # Blend style features into cross-attention
            k = k * (1 - strength) + style * strength

        return q, k, v

    def extract_features(self, image):
        # Extract features for style injection
        return image.mean(dim=1, keepdim=True)
```

## Custom Samplers

Implement custom noise, sampler, and guider interfaces.

### Custom Noise

```python
class PerlinNoise:
    """Generates Perlin noise instead of standard Gaussian noise."""

    def __init__(self, seed, scale=1.0):
        self.seed = seed
        self.scale = scale

    def generate_noise(self, latent):
        torch.manual_seed(self.seed)
        # Generate Perlin-like noise
        noise = torch.randn_like(latent)
        # Apply frequency scaling
        noise = noise * self.scale
        return noise

# Node to create custom noise
class PerlinNoiseNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0}),
            }
        }

    RETURN_TYPES = ("NOISE",)
    FUNCTION = "create_noise"
    CATEGORY = "sampling/noise"

    def create_noise(self, seed, scale):
        return (PerlinNoise(seed, scale),)
```

### Custom Sampler

```python
class AdaptiveSampler:
    """Adjusts step size based on convergence."""

    def __init__(self, tolerance=0.01, max_steps=20):
        self.tolerance = tolerance
        self.max_steps = max_steps

    def sample(self, model, sigmas, latent, **kwargs):
        current = latent
        for i in range(len(sigmas) - 1):
            sigma = sigmas[i]
            sigma_next = sigmas[i + 1]

            # Standard Euler step
            denoised = model(current, sigma, **kwargs)
            d = (current - denoised) / sigma
            current = current + d * (sigma_next - sigma)

            # Check convergence
            if torch.abs(d).mean() < self.tolerance:
                break

        return current

# Node to create custom sampler
class AdaptiveSamplerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tolerance": ("FLOAT", {"default": 0.01, "min": 0.001, "max": 1.0}),
                "max_steps": ("INT", {"default": 20, "min": 1, "max": 100}),
            }
        }

    RETURN_TYPES = ("SAMPLER",)
    FUNCTION = "create_sampler"
    CATEGORY = "sampling/samplers"

    def create_sampler(self, tolerance, max_steps):
        return (AdaptiveSampler(tolerance, max_steps),)
```

## Memory Optimization

### Model Offloading

Move model components to CPU when not in use.

```python
class ModelOffload:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "offload_to": (["cpu", "disk"],),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "offload"
    CATEGORY = "model/optimization"

    def offload(self, model, offload_to):
        model_clone = model.clone()

        if offload_to == "cpu":
            model_clone.model_options["transformer_options"]["offload_device"] = "cpu"
        elif offload_to == "disk":
            model_clone.model_options["transformer_options"]["offload_device"] = "disk"

        return (model_clone,)
```

### Quantization

Apply quantization to reduce memory usage.

```python
class QuantizeModel:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "precision": (["fp16", "bf16", "int8"],),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "quantize"
    CATEGORY = "model/optimization"

    def quantize(self, model, precision):
        model_clone = model.clone()

        if precision == "fp16":
            model_clone.model_options["transformer_options"]["dtype"] = torch.float16
        elif precision == "bf16":
            model_clone.model_options["transformer_options"]["dtype"] = torch.bfloat16
        elif precision == "int8":
            model_clone.model_options["transformer_options"]["quantize"] = "int8"

        return (model_clone,)
```

### Tiled Processing

Process large images in tiles to reduce memory usage.

```python
class TiledProcessor:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "tile_size": ("INT", {"default": 512, "min": 64, "max": 2048}),
                "overlap": ("INT", {"default": 64, "min": 0, "max": 256}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "process_tiled"
    CATEGORY = "image/processing"

    def process_tiled(self, image, tile_size, overlap):
        b, h, w, c = image.shape
        result = torch.zeros_like(image)

        for y in range(0, h, tile_size - overlap):
            for x in range(0, w, tile_size - overlap):
                # Extract tile
                y_end = min(y + tile_size, h)
                x_end = min(x + tile_size, w)
                tile = image[:, y:y_end, x:x_end, :]

                # Process tile
                processed = self.process_tile(tile)

                # Blend with overlap
                result[:, y:y_end, x:x_end, :] = processed

        return (result,)

    def process_tile(self, tile):
        # Apply processing to individual tile
        return tile * 1.0  # Placeholder
```

## Custom Types

Define and use custom type strings for domain-specific data.

```python
# Define a custom type
RETURN_TYPES = ("STYLE_DATA",)
RETURN_NAMES = ("style",)

# Use the custom type in another node
("STYLE_DATA",)

# Custom types can be any uppercase string
RETURN_TYPES = ("EMBEDDING_VECTOR", "ATTENTION_MAP", "FEATURE_PYRAMID")
```

### Type Aliasing for Clarity

Use descriptive type names even if they're technically the same underlying type.

```python
# Instead of generic "IMAGE" for different purposes
RETURN_TYPES = ("SOURCE_IMAGE",)    # Original input
RETURN_TYPES = ("REFERENCE_IMAGE",) # Style reference
RETURN_TYPES = ("MASK_IMAGE",)      # Processing mask

# These are all IMAGE tensors but semantically different
```

## Lazy Evaluation

Defer expensive computations until the value is actually needed.

```python
class ExpensiveNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "enhance": ("BOOLEAN", {"default": True}),
                "enhanced_image": ("IMAGE", {"lazy": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "process"
    CATEGORY = "image/processing"

    def process(self, image, enhance, enhanced_image=None):
        if enhance:
            # enhanced_image is only evaluated when accessed
            return (enhanced_image,)
        return (image,)
```

## Raw Links

Access the raw link data instead of the resolved value.

```python
class RawLinkNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "data": ("STRING", {"rawLink": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "process"
    CATEGORY = "utility"

    def process(self, data):
        # data contains the raw link information
        # instead of the resolved value
        return (str(data),)
```

## INPUT_IS_LIST for Batch Processing

Receive all inputs as lists, even single connections.

```python
class BatchProcessor:
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "strengths": ("FLOAT",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "process_batch"
    CATEGORY = "image/batch"

    def process_batch(self, images, strengths):
        results = []
        for img, strength in zip(images, strengths):
            results.append(img * strength)
        return (results,)
```

## OUTPUT_IS_LIST for Sequential Outputs

Produce outputs that are lists of items.

```python
class SequenceGenerator:
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "generate"
    CATEGORY = "image/batch"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "count": ("INT", {"default": 4, "min": 1, "max": 100}),
            }
        }

    def generate(self, count):
        images = [torch.randn(1, 512, 512, 3) for _ in range(count)]
        return (images,)
```

## SEARCH_ALIASES for Discoverability

Extra keywords to help users find your node in search.

```python
class GaussianBlur:
    SEARCH_ALIASES = ["blur", "smooth", "gaussian", "filter", "soft", "defocus"]
    DESCRIPTION = "Applies Gaussian blur to an image"
```

## IS_CHANGED for Cache Control

Control when a node re-executes.

```python
class RandomNode:
    @classmethod
    def IS_CHANGED(cls, seed, **kwargs):
        # Re-execute when seed changes
        return seed

class TimeBasedNode:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always re-execute (use current time)
        import time
        return time.time()

class StaticNode:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Never re-execute (returns constant)
        return "static_value"
```

## VALIDATE_INPUTS for Input Validation

Validate inputs before execution.

```python
class ValidatedNode:
    @classmethod
    def VALIDATE_INPUTS(cls, image, strength, **kwargs):
        if not isinstance(image, torch.Tensor):
            return "image must be a tensor"
        if strength < 0 or strength > 1:
            return "strength must be between 0 and 1"
        return True

    # Accept all inputs
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True
```

## Conditional Node Availability

Use try/except to gracefully handle missing dependencies.

```python
NODE_CLASS_MAPPINGS = {}

# Always available
from .core_nodes import MathNode
NODE_CLASS_MAPPINGS["MathNode"] = MathNode

# Requires optional dependency
try:
    import cv2
    from .cv_nodes import EdgeDetectNode
    NODE_CLASS_MAPPINGS["EdgeDetectNode"] = EdgeDetectNode
except ImportError:
    pass

# Requires GPU
try:
    import torch
    if torch.cuda.is_available():
        from .gpu_nodes import GPUNode
        NODE_CLASS_MAPPINGS["GPUNode"] = GPUNode
except (ImportError, RuntimeError):
    pass
```

## Composite Pattern

Build complex nodes by combining simpler operations.

```python
class ImagePipeline:
    """Applies a configurable pipeline of image operations."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "blur_radius": ("INT", {"default": 0, "min": 0, "max": 20}),
                "brightness": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0}),
                "contrast": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0}),
                "sharpen": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "pipeline"
    CATEGORY = "image/processing"

    def pipeline(self, image, blur_radius, brightness, contrast, sharpen):
        result = image

        # Step 1: Blur
        if blur_radius > 0:
            result = self.apply_blur(result, blur_radius)

        # Step 2: Brightness
        result = result * brightness

        # Step 3: Contrast
        mean = result.mean(dim=(1, 2), keepdim=True)
        result = (result - mean) * contrast + mean

        # Step 4: Sharpen
        if sharpen:
            result = self.apply_sharpen(result)

        return (torch.clamp(result, 0, 1),)

    def apply_blur(self, image, radius):
        # Apply Gaussian blur
        return image  # Placeholder

    def apply_sharpen(self, image):
        # Apply sharpening
        return image  # Placeholder
```
