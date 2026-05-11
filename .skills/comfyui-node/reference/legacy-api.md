# Legacy v1 API Reference

The standard ComfyUI node API used by 90%+ of custom nodes. No base class required — nodes are plain Python classes with specific class attributes and methods.

## Class Structure

```python
class MyNode:
    # Class attributes (all optional unless noted)
    RETURN_TYPES = ("IMAGE",)          # Required: tuple of output type strings
    RETURN_NAMES = ("output_image",)   # Optional: human-readable output names
    FUNCTION = "process"               # Required: name of the execute method
    CATEGORY = "image/processing"      # Required: slash-separated menu path
    DESCRIPTION = "Does something"     # Optional: shown in node tooltip
    DEPRECATED = False                 # Optional: marks node as deprecated
    INPUT_IS_LIST = False              # Optional: receive inputs as lists
    OUTPUT_IS_LIST = (False,)          # Optional: outputs are lists
    OUTPUT_NODE = False                # Optional: terminal/output-only node
    SEARCH_ALIASES = ["alias1"]        # Optional: extra search keywords

    # Class methods
    @classmethod
    def INPUT_TYPES(s): ...            # Required: define inputs
    @classmethod
    def IS_CHANGED(cls, **kwargs): ... # Optional: cache control
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs): ... # Optional: input validation
    @classmethod
    def IS_DYNAMIC(cls): ...           # Optional: dynamic output count
    @classmethod
    def get_output_types(cls, **kwargs): ...  # Optional: dynamic types
    @classmethod
    def get_output_names(cls, **kwargs): ...  # Optional: dynamic names

    # Instance method
    def execute(self, **kwargs): ...   # Required: main logic
```

## INPUT_TYPES Classmethod

Returns a dict defining all inputs. The method receives the class as `s` (convention).

```python
@classmethod
def INPUT_TYPES(s):
    return {
        "required": {
            # Must be connected for the node to execute
            "image": ("IMAGE",),
            "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            "mode": (["fast", "quality", "balanced"],),
        },
        "optional": {
            # Can be left unconnected
            "mask": ("MASK",),
            "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
        },
        "hidden": {
            # Injected automatically by ComfyUI, not shown in UI
            "unique_id": "UNIQUE_ID",
            "prompt": "PROMPT",
            "extra_pnginfo": "EXTRA_PNGINFO",
            "dynprompt": "DYNPROMPT",
        },
    }
```

### Input Format

Two formats for input values:

```python
# Format 1: Type with options dict
("TYPE", {"default": value, "min": min_val, "max": max_val, ...})

# Format 2: Dropdown from list (no options dict, or optional trailing tuple)
(["option1", "option2", "option3"],)

# Examples:
("INT", {"default": 512, "min": 64, "max": 4096, "step": 64})
("FLOAT", {"default": 0.75, "min": 0.0, "max": 1.0, "step": 0.01})
("STRING", {"default": "", "multiline": True, "placeholder": "Enter text..."})
("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"})
(["model_a", "model_b", "model_c"],)
```

### Hidden Inputs

Special system-injected inputs:

```python
"hidden": {
    "unique_id": "UNIQUE_ID",       # Current node's unique ID
    "prompt": "PROMPT",             # Full workflow prompt dict
    "extra_pnginfo": "EXTRA_PNGINFO", # Metadata for PNG saving
    "dynprompt": "DYNPROMPT",       # Dynamic prompt data
}
```

## RETURN_TYPES Tuple

Tuple of type strings matching input/output type names. Order matters — corresponds to execute() return values.

```python
RETURN_TYPES = ("IMAGE", "MASK", "STRING")
RETURN_NAMES = ("image", "mask", "info_text")  # Optional display names
```

## FUNCTION String

Name of the instance method that executes the node logic. Must match an actual method name.

```python
FUNCTION = "process"

def process(self, image, strength, mask=None):
    ...
    return (result_image, result_mask, info_string)
```

## CATEGORY String

Slash-separated path for the node menu. Use `/` as separator.

```python
CATEGORY = "image/processing"
CATEGORY = "model/loaders"
CATEGORY = "conditioning/style"
CATEGORY = "sampling/custom"
```

## DESCRIPTION String

Human-readable description shown in node tooltips.

```python
DESCRIPTION = "Applies a Gaussian blur to the input image with configurable radius"
```

## SEARCH_ALIASES List

Extra keywords for the node search dialog. Helps users find nodes by alternative terms.

```python
SEARCH_ALIASES = ["blur", "smooth", "gaussian", "filter"]
```

## DEPRECATED Flag

Marks the node as deprecated. Users see a warning but the node still works.

```python
DEPRECATED = True
```

## OUTPUT_NODE Flag

Marks the node as a terminal node (e.g., SaveImage, PreviewImage). These nodes don't need downstream connections.

```python
OUTPUT_NODE = True
```

## INPUT_IS_LIST Flag

When `True`, all inputs are received as lists, even single connections. Useful for batch processing.

```python
INPUT_IS_LIST = True

def execute(self, images, seeds):
    # images is a list of IMAGE tensors
    # seeds is a list of ints
    results = []
    for img, seed in zip(images, seeds):
        results.append(process(img, seed))
    return (results,)
```

## OUTPUT_IS_LIST Tuple

Tuple of booleans indicating which outputs are lists. Corresponds to RETURN_TYPES order.

```python
RETURN_TYPES = ("IMAGE", "MASK")
OUTPUT_IS_LIST = (True, False)  # First output is a list, second is single
```

## IS_CHANGED Classmethod

Controls ComfyUI's caching. Return value is compared across runs — if it changes, the node re-executes.

```python
@classmethod
def IS_CHANGED(cls, image, seed, **kwargs):
    # Return seed to force re-execution when seed changes
    return seed

# Always re-execute
@classmethod
def IS_CHANGED(cls, **kwargs):
    return float("nan")

# Never re-execute (dangerous — only for truly static nodes)
@classmethod
def IS_CHANGED(cls, **kwargs):
    return False
```

## VALIDATE_INPUTS Classmethod

Validates inputs before execution. Return `True` to proceed, or a string error message to reject.

```python
@classmethod
def VALIDATE_INPUTS(cls, image, strength, **kwargs):
    if strength < 0:
        return "Strength must be non-negative"
    return True

# Accept all inputs
@classmethod
def VALIDATE_INPUTS(cls, **kwargs):
    return True
```

## Dynamic Outputs (IS_DYNAMIC)

For nodes that produce a variable number of outputs based on input parameters.

```python
@classmethod
def IS_DYNAMIC(cls):
    return True

@classmethod
def get_output_types(cls, count=1, **kwargs):
    return tuple(["IMAGE"] * int(count))

@classmethod
def get_output_names(cls, count=1, **kwargs):
    return tuple([f"image_{i+1}" for i in range(int(count))])

RETURN_TYPES = tuple(["IMAGE"] * 50)  # Maximum possible outputs
```

## Execute Method

The main logic method. Receives all inputs as keyword arguments. Returns a tuple matching RETURN_TYPES.

```python
def process(self, image, strength, mask=None, seed=0, unique_id=None, **kwargs):
    # image: torch.Tensor of shape [B, H, W, C]
    # strength: float
    # mask: torch.Tensor or None
    # seed: int
    # unique_id: str (from hidden input)

    result = image * strength

    if mask is not None:
        result = result * mask

    # Must return a tuple matching RETURN_TYPES
    return (result,)
```

### Return Type Requirements

```python
# Single output
RETURN_TYPES = ("IMAGE",)
return (result_image,)

# Multiple outputs
RETURN_TYPES = ("IMAGE", "MASK", "STRING")
return (result_image, result_mask, result_info)

# With OUTPUT_NODE — can return UI elements or nothing
OUTPUT_NODE = True
return ()  # or return {"ui": {"text": ["info"]}}
```

## Complete Example

```python
class ImageBlend:
    """Blends two images together with adjustable opacity."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_a": ("IMAGE",),
                "image_b": ("IMAGE",),
                "blend_mode": (["normal", "multiply", "screen", "overlay"],),
                "opacity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {
                "mask": ("MASK",),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("blended_image",)
    FUNCTION = "blend"
    CATEGORY = "image/compositing"
    DESCRIPTION = "Blends two images using various blend modes"
    SEARCH_ALIASES = ["combine", "merge", "mix", "composite"]

    @classmethod
    def IS_CHANGED(cls, image_a, image_b, blend_mode, opacity, mask=None, **kwargs):
        return (blend_mode, opacity)

    @classmethod
    def VALIDATE_INPUTS(cls, image_a, image_b, opacity, **kwargs):
        if opacity < 0 or opacity > 1:
            return "Opacity must be between 0.0 and 1.0"
        return True

    def blend(self, image_a, image_b, blend_mode, opacity, mask=None):
        if blend_mode == "normal":
            result = image_a * (1 - opacity) + image_b * opacity
        elif blend_mode == "multiply":
            result = image_a * image_b
            result = image_a * (1 - opacity) + result * opacity
        elif blend_mode == "screen":
            result = 1 - (1 - image_a) * (1 - image_b)
            result = image_a * (1 - opacity) + result * opacity
        elif blend_mode == "overlay":
            low = 2 * image_a * image_b
            high = 1 - 2 * (1 - image_a) * (1 - image_b)
            result = torch.where(image_a < 0.5, low, high)
            result = image_a * (1 - opacity) + result * opacity

        if mask is not None:
            if mask.dim() == 3:
                mask = mask.unsqueeze(-1)
            result = result * mask + image_a * (1 - mask)

        return (result,)
```
