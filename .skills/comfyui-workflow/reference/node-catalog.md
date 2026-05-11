# ComfyUI Node Catalog

Reference catalog of built-in and popular custom nodes. Each entry lists the exact node type name, display name, category, inputs, and outputs.

---

## Loaders

### CheckpointLoaderSimple

- **Display Name**: Load Checkpoint
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| ckpt_name | COMBO | — | Model filenames in `models/checkpoints/` |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MODEL | MODEL | Diffusion model |
| CLIP | CLIP | CLIP text encoder |
| VAE | VAE | VAE model |

---

### CheckpointLoader

- **Display Name**: Load Checkpoint (Advanced)
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| config_name | COMBO | — | Config file names |
| ckpt_name | COMBO | — | Model filenames |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MODEL | MODEL | Diffusion model |
| CLIP | CLIP | CLIP text encoder |
| VAE | VAE | VAE model |
| CLIP_VISION | CLIP_VISION | CLIP vision encoder |

---

### VAELoader

- **Display Name**: Load VAE
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| vae_name | COMBO | — | VAE filenames in `models/vae/` |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| VAE | VAE | VAE model |

---

### UNETLoader

- **Display Name**: UNET Loader (Advanced)
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| unet_name | COMBO | — | UNET filenames in `models/diffusion_models/` |
| weight_dtype | COMBO | "default" | "default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MODEL | MODEL | Diffusion model |

---

### DualCLIPLoader

- **Display Name**: Dual CLIP Loader
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| clip_name1 | COMBO | — | CLIP filenames |
| clip_name2 | COMBO | — | CLIP filenames |
| type | COMBO | "sdxl" | "sdxl", "sd3", "flux" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CLIP | CLIP | Combined CLIP encoder |

---

### TripleCLIPLoader

- **Display Name**: Triple CLIP Loader
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| clip_name1 | COMBO | — | CLIP filenames |
| clip_name2 | COMBO | — | CLIP filenames |
| clip_name3 | COMBO | — | CLIP filenames |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CLIP | CLIP | Combined CLIP encoder |

---

### LoraLoader

- **Display Name**: Load LoRA
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| clip | CLIP | — | (required) |
| lora_name | COMBO | — | LoRA filenames in `models/loras/` |
| strength_model | FLOAT | 1.0 | -10.0 to 10.0, step 0.01 |
| strength_clip | FLOAT | 1.0 | -10.0 to 10.0, step 0.01 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MODEL | MODEL | Patched model |
| CLIP | CLIP | Patched CLIP |

---

### LoraLoaderModelOnly

- **Display Name**: Load LoRA (Model Only)
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| lora_name | COMBO | — | LoRA filenames |
| strength_model | FLOAT | 1.0 | -10.0 to 10.0, step 0.01 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MODEL | MODEL | Patched model |

---

### ControlNetLoader

- **Display Name**: Load ControlNet Model
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| control_net_name | COMBO | — | ControlNet filenames in `models/controlnet/` |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONTROL_NET | CONTROL_NET | ControlNet model |

---

### IPAdapterModelLoader

- **Display Name**: Load IPAdapter Model
- **Category**: ipadapter

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| ipadapter_file | COMBO | — | IPAdapter filenames |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IPADAPTER | IPADAPTER_MODEL | IP-Adapter model |

---

### CLIPVisionLoader

- **Display Name**: Load CLIP Vision
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| clip_name | COMBO | — | CLIP vision filenames in `models/clip_vision/` |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CLIP_VISION | CLIP_VISION | CLIP vision model |

---

### StyleModelLoader

- **Display Name**: Load Style Model
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| style_model_name | COMBO | — | Style model filenames |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| STYLE_MODEL | STYLE_MODEL | Style model |

---

### LoaderDeprecated

- **Display Name**: Load Diffusion Model (Deprecated)
- **Category**: loaders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| ckpt_name | COMBO | — | Model filenames |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MODEL | MODEL | Diffusion model |
| CLIP | CLIP | CLIP encoder |
| VAE | VAE | VAE model |

---

## Sampling

### KSampler

- **Display Name**: KSampler
- **Category**: sampling

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| positive | CONDITIONING | — | (required) |
| negative | CONDITIONING | — | (required) |
| latent_image | LATENT | — | (required) |
| seed | INT | 0 | 0 to 2^32-1 |
| steps | INT | 20 | 1 to 10000 |
| cfg | FLOAT | 8.0 | 0.0 to 100.0 |
| sampler_name | COMBO | "euler" | "euler", "euler_ancestral", "heun", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_sde", "dpmpp_sde_gpu", "dpmpp_2m", "dpmpp_2m_sde", "dpmpp_2m_sde_gpu", "dpmpp_3m_sde", "dpmpp_3m_sde_gpu", "ddpm", "lcm", "ddim", "uni_pc", "uni_pc_bh2" |
| scheduler | COMBO | "normal" | "normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "beta" |
| denoise | FLOAT | 1.0 | 0.0 to 1.0 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Sampled latent |

---

### KSamplerAdvanced

- **Display Name**: KSampler (Advanced)
- **Category**: sampling

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| positive | CONDITIONING | — | (required) |
| negative | CONDITIONING | — | (required) |
| latent_image | LATENT | — | (required) |
| noise_seed | INT | 0 | 0 to 2^32-1 |
| steps | INT | 20 | 1 to 10000 |
| cfg | FLOAT | 8.0 | 0.0 to 100.0 |
| sampler_name | COMBO | "euler" | (same as KSampler) |
| scheduler | COMBO | "normal" | (same as KSampler) |
| start_at_step | INT | 0 | 0 to 10000 |
| end_at_step | INT | 10000 | 0 to 10000 |
| return_with_leftover_noise | COMBO | "disable" | "enable", "disable" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Sampled latent |

---

### SamplerCustom

- **Display Name**: SamplerCustom
- **Category**: sampling

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| add_noise | BOOLEAN | true | — |
| noise_seed | INT | 0 | 0 to 2^32-1 |
| cfg | FLOAT | 8.0 | 0.0 to 100.0 |
| positive | CONDITIONING | — | (required) |
| negative | CONDITIONING | — | (required) |
| sampler | SAMPLER | — | (required) |
| sigmas | SIGMAS | — | (required) |
| latent_image | LATENT | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| output | LATENT | Sampled latent |
| denoised_output | LATENT | Denoised latent |

---

### BasicGuider

- **Display Name**: BasicGuider
- **Category**: sampling/guiders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| conditioning | CONDITIONING | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| GUIDER | GUIDER | Guider object |

---

### CFGGuider

- **Display Name**: CFGGuider
- **Category**: sampling/guiders

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| positive | CONDITIONING | — | (required) |
| negative | CONDITIONING | — | (required) |
| cfg | FLOAT | 8.0 | 0.0 to 100.0 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| GUIDER | GUIDER | Guider object |

---

### BasicScheduler

- **Display Name**: BasicScheduler
- **Category**: sampling/schedulers

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| scheduler | COMBO | "normal" | "normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "beta" |
| steps | INT | 20 | 1 to 10000 |
| denoise | FLOAT | 1.0 | 0.0 to 1.0 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| SIGMAS | SIGMAS | Sigma schedule |

---

### KSamplerSelect

- **Display Name**: KSamplerSelect
- **Category**: sampling/samplers

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| sampler_name | COMBO | "euler" | (same as KSampler sampler options) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| SAMPLER | SAMPLER | Sampler object |

---

### ModelSamplingDiscrete

- **Display Name**: ModelSamplingDiscrete
- **Category**: sampling

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| sampling | COMBO | "eps" | "eps", "v_prediction", "lcm", "x0" |
| zsnr | BOOLEAN | false | — |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MODEL | MODEL | Modified model |

---

### ModelSamplingFlux

- **Display Name**: ModelSamplingFlux
- **Category**: sampling

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| model | MODEL | — | (required) |
| max_shift | FLOAT | 1.15 | 0.0 to 100.0 |
| base_shift | FLOAT | 0.5 | 0.0 to 100.0 |
| width | INT | 1024 | 16 to 16384 |
| height | INT | 1024 | 16 to 16384 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MODEL | MODEL | Model with Flux sampling |

---

## Latent

### EmptyLatentImage

- **Display Name**: Empty Latent Image
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| width | INT | 512 | 16 to 16384 |
| height | INT | 512 | 16 to 16384 |
| batch_size | INT | 1 | 1 to 4096 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Empty latent tensor |

---

### LatentUpscale

- **Display Name**: Latent Upscale
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| samples | LATENT | — | (required) |
| upscale_method | COMBO | "nearest-exact" | "nearest-exact", "bilinear", "area", "bislerp" |
| width | INT | 512 | 16 to 16384 |
| height | INT | 512 | 16 to 16384 |
| crop | COMBO | "disabled" | "disabled", "center" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Upscaled latent |

---

### LatentBatch

- **Display Name**: Latent Batch
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| samples1 | LATENT | — | (required) |
| samples2 | LATENT | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Batched latent |

---

### LatentRotate

- **Display Name**: Latent Rotate
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| samples | LATENT | — | (required) |
| rotation | COMBO | "none" | "none", "90 degrees", "180 degrees", "270 degrees", "90 degrees mirror", "180 degrees mirror", "270 degrees mirror" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Rotated latent |

---

### LatentFlip

- **Display Name**: Latent Flip
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| samples | LATENT | — | (required) |
| flip_method | COMBO | "x-axis: vertically" | "x-axis: vertically", "y-axis: horizontally", "x-y-axis: x=y" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Flipped latent |

---

### LatentCrop

- **Display Name**: Latent Crop
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| samples | LATENT | — | (required) |
| width | INT | 512 | 16 to 16384 |
| height | INT | 512 | 16 to 16384 |
| x | INT | 0 | 0 to 16384 |
| y | INT | 0 | 0 to 16384 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Cropped latent |

---

## VAE

### VAEDecode

- **Display Name**: VAE Decode
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| samples | LATENT | — | (required) |
| vae | VAE | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Decoded image(s) |

---

### VAEEncode

- **Display Name**: VAE Encode
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| pixels | IMAGE | — | (required) |
| vae | VAE | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Encoded latent |

---

### VAEDecodeTiled

- **Display Name**: VAE Decode (Tiled)
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| samples | LATENT | — | (required) |
| vae | VAE | — | (required) |
| tile_size | INT | 512 | 64 to 4096 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Decoded image(s) |

---

### VAEEncodeTiled

- **Display Name**: VAE Encode (Tiled)
- **Category**: latent

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| pixels | IMAGE | — | (required) |
| vae | VAE | — | (required) |
| tile_size | INT | 512 | 64 to 4096 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| LATENT | LATENT | Encoded latent |

---

## Conditioning

### CLIPTextEncode

- **Display Name**: CLIP Text Encode
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| text | STRING | "" | multiline |
| clip | CLIP | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONDITIONING | CONDITIONING | Text conditioning |

---

### ConditioningCombine

- **Display Name**: Conditioning Combine
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| conditioning_1 | CONDITIONING | — | (required) |
| conditioning_2 | CONDITIONING | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONDITIONING | CONDITIONING | Combined conditioning |

---

### ConditioningConcat

- **Display Name**: Conditioning Concat
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| conditioning_to | CONDITIONING | — | (required) |
| conditioning_from | CONDITIONING | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONDITIONING | CONDITIONING | Concatenated conditioning |

---

### ConditioningSetArea

- **Display Name**: Conditioning Set Area
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| conditioning | CONDITIONING | — | (required) |
| width | INT | 512 | 16 to 16384 |
| height | INT | 512 | 16 to 16384 |
| x | INT | 0 | 0 to 16384 |
| y | INT | 0 | 0 to 16384 |
| strength | FLOAT | 1.0 | 0.0 to 10.0 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONDITIONING | CONDITIONING | Area-conditioned output |

---

### ConditioningSetMask

- **Display Name**: Conditioning Set Mask
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| conditioning | CONDITIONING | — | (required) |
| mask | MASK | — | (required) |
| strength | FLOAT | 1.0 | 0.0 to 10.0 |
| set_cond_area | COMBO | "default" | "default", "mask bounds" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONDITIONING | CONDITIONING | Mask-conditioned output |

---

### CLIPSetLastLayer

- **Display Name**: CLIP Set Last Layer
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| clip | CLIP | — | (required) |
| stop_at_clip_layer | INT | -1 | -1 to -24 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CLIP | CLIP | Modified CLIP |

---

### ControlNetApply

- **Display Name**: Apply ControlNet
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| conditioning | CONDITIONING | — | (required) |
| control_net | CONTROL_NET | — | (required) |
| image | IMAGE | — | (required) |
| strength | FLOAT | 1.0 | 0.0 to 10.0 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONDITIONING | CONDITIONING | ControlNet-conditioned output |

---

### ControlNetApplyAdvanced

- **Display Name**: Apply ControlNet (Advanced)
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| positive | CONDITIONING | — | (required) |
| negative | CONDITIONING | — | (required) |
| control_net | CONTROL_NET | — | (required) |
| image | IMAGE | — | (required) |
| strength | FLOAT | 1.0 | 0.0 to 10.0 |
| start_percent | FLOAT | 0.0 | 0.0 to 1.0 |
| end_percent | FLOAT | 1.0 | 0.0 to 1.0 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| positive | CONDITIONING | Positive with ControlNet |
| negative | CONDITIONING | Negative with ControlNet |

---

## Image

### SaveImage

- **Display Name**: Save Image
- **Category**: image

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| images | IMAGE | — | (required) |
| filename_prefix | STRING | "ComfyUI" | — |

**Outputs**: None (terminal node)

---

### PreviewImage

- **Display Name**: Preview Image
- **Category**: image

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| images | IMAGE | — | (required) |

**Outputs**: None (terminal node)

---

### LoadImage

- **Display Name**: Load Image
- **Category**: image

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| image | COMBO | — | Image filenames in `input/` |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Loaded image |
| MASK | MASK | Alpha mask from image |

---

### ImageScale

- **Display Name**: Image Scale
- **Category**: image

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| image | IMAGE | — | (required) |
| upscale_method | COMBO | "nearest-exact" | "nearest-exact", "bilinear", "area", "bislerp", "lanczos" |
| width | INT | 512 | 1 to 16384 |
| height | INT | 512 | 1 to 16384 |
| crop | COMBO | "disabled" | "disabled", "center" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Scaled image |

---

### ImageScaleBy

- **Display Name**: Image Scale By
- **Category**: image

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| image | IMAGE | — | (required) |
| upscale_method | COMBO | "nearest-exact" | "nearest-exact", "bilinear", "area", "bislerp", "lanczos" |
| scale_by | FLOAT | 1.0 | 0.01 to 8.0 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Scaled image |

---

### ImageInvert

- **Display Name**: Image Invert
- **Category**: image

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| image | IMAGE | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Inverted image |

---

### ImageBatch

- **Display Name**: Image Batch
- **Category**: image

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| image1 | IMAGE | — | (required) |
| image2 | IMAGE | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Batched images |

---

### ImagePadForOutpaint

- **Display Name**: Pad Image for Outpainting
- **Category**: image

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| image | IMAGE | — | (required) |
| left | INT | 0 | 0 to 16384 |
| top | INT | 0 | 0 to 16384 |
| right | INT | 0 | 0 to 16384 |
| bottom | INT | 0 | 0 to 16384 |
| feathering | INT | 40 | 0 to 16384 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Padded image |
| MASK | MASK | Padding mask |

---

## Mask

### EmptyMask

- **Display Name**: Empty Mask
- **Category**: mask

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| width | INT | 512 | 16 to 16384 |
| height | INT | 512 | 16 to 16384 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MASK | MASK | Empty (zero) mask |

---

### MaskToImage

- **Display Name**: Convert Mask to Image
- **Category**: mask

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| mask | MASK | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Mask as grayscale image |

---

### ImageToMask

- **Display Name**: Convert Image to Mask
- **Category**: mask

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| image | IMAGE | — | (required) |
| channel | COMBO | "alpha" | "alpha", "red", "green", "blue" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MASK | MASK | Extracted mask |

---

### MaskComposite

- **Display Name**: Mask Composite
- **Category**: mask

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| destination | MASK | — | (required) |
| source | MASK | — | (required) |
| x | INT | 0 | 0 to 16384 |
| y | INT | 0 | 0 to 16384 |
| operation | COMBO | "multiply" | "multiply", "add", "subtract", "lightest", "darkest" |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MASK | MASK | Composited mask |

---

### MaskBatch

- **Display Name**: Mask Batch
- **Category**: mask

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| mask1 | MASK | — | (required) |
| mask2 | MASK | — | (required) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MASK | MASK | Batched masks |

---

## Video (VHS - Video Helper Suite)

### VHS_VideoCombine

- **Display Name**: Video Combine
- **Category**: video

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| images | IMAGE | — | (required) |
| frame_rate | INT | 8 | 1 to 120 |
| loop_count | INT | 0 | 0 to 100 |
| filename_prefix | STRING | "AnimateDiff" | — |
| format | COMBO | "image/gif" | "image/gif", "image/webp", "image/apng", "video/h264-mp4", "video/h265-mp4", "video/webm" |
| pingpong | BOOLEAN | false | — |
| save_output | BOOLEAN | true | — |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| VHS_FILENAMES | VHS_FILENAMES | Output file info |

---

### VHS_LoadVideo

- **Display Name**: Load Video
- **Category**: video

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| video | COMBO | — | Video filenames in `input/` |
| force_rate | INT | 0 | 0 to 120 |
| force_size | COMBO | "Disabled" | "Disabled", "256x?", "?x256", "256x256", "512x?", "?x512", "512x512" |
| custom_width | INT | 512 | 0 to 16384 |
| custom_height | INT | 512 | 0 to 16384 |
| frame_load_cap | INT | 0 | 0 to 10000 |
| skip_first_frames | INT | 0 | 0 to 10000 |
| select_every_nth | INT | 1 | 1 to 100 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Video frames as images |
| frame_rate | FLOAT | Detected frame rate |
| duration | FLOAT | Video duration in seconds |

---

### VHS_LoadVideoPath

- **Display Name**: Load Video (Path)
- **Category**: video

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| video | STRING | "" | file path |
| force_rate | INT | 0 | 0 to 120 |
| force_size | COMBO | "Disabled" | (same as VHS_LoadVideo) |
| custom_width | INT | 512 | 0 to 16384 |
| custom_height | INT | 512 | 0 to 16384 |
| frame_load_cap | INT | 0 | 0 to 10000 |
| skip_first_frames | INT | 0 | 0 to 10000 |
| select_every_nth | INT | 1 | 1 to 100 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Video frames as images |
| frame_rate | FLOAT | Detected frame rate |
| duration | FLOAT | Video duration in seconds |

---

## KJNodes

### ImageConcatMulti

- **Display Name**: Image Concat Multi
- **Category**: KJNodes/image

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| images_* | IMAGE | — | Dynamic inputs (auto-generated) |
| axis | COMBO | "horizontal" | "horizontal", "vertical" |
| match_size | BOOLEAN | false | — |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| IMAGE | IMAGE | Concatenated image |

---

### ConditioningMultiCombine

- **Display Name**: Conditioning Multi Combine
- **Category**: KJNodes/conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| conditioning_* | CONDITIONING | — | Dynamic inputs (auto-generated) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONDITIONING | CONDITIONING | Combined conditioning |

---

### MaskBatchMulti

- **Display Name**: Mask Batch Multi
- **Category**: KJNodes/mask

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| mask_* | MASK | — | Dynamic inputs (auto-generated) |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| MASK | MASK | Batched masks |

---

### INTConstant

- **Display Name**: INT Constant
- **Category**: KJNodes/constants

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| value | INT | 0 | — |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| INT | INT | Integer value |

---

### FLOATConstant

- **Display Name**: FLOAT Constant
- **Category**: KJNodes/constants

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| value | FLOAT | 0.0 | — |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| FLOAT | FLOAT | Float value |

---

### STRINGConstant

- **Display Name**: STRING Constant
- **Category**: KJNodes/constants

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| value | STRING | "" | — |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| STRING | STRING | String value |

---

### BoolConstant

- **Display Name**: Bool Constant
- **Category**: KJNodes/constants

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| value | BOOLEAN | false | — |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| BOOLEAN | BOOLEAN | Boolean value |

---

## Flux-Specific

### CLIPTextEncodeFlux

- **Display Name**: CLIP Text Encode (Flux)
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| clip | CLIP | — | (required) |
| clip_l | STRING | "" | multiline |
| t5xxl | STRING | "" | multiline |
| guidance | FLOAT | 3.5 | 0.0 to 100.0 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONDITIONING | CONDITIONING | Flux conditioning |

---

### FluxGuidance

- **Display Name**: Flux Guidance
- **Category**: conditioning

**Inputs**:
| Name | Type | Default | Options |
|---|---|---|---|
| conditioning | CONDITIONING | — | (required) |
| guidance | FLOAT | 3.5 | 0.0 to 100.0 |

**Outputs**:
| Name | Type | Description |
|---|---|---|
| CONDITIONING | CONDITIONING | Conditioning with guidance |

---

## Node Type Quick Reference

| Category | Node Type | Key Outputs |
|---|---|---|
| Loaders | CheckpointLoaderSimple | MODEL, CLIP, VAE |
| Loaders | UNETLoader | MODEL |
| Loaders | LoraLoader | MODEL, CLIP |
| Loaders | ControlNetLoader | CONTROL_NET |
| Loaders | CLIPVisionLoader | CLIP_VISION |
| Sampling | KSampler | LATENT |
| Sampling | SamplerCustom | LATENT |
| Sampling | BasicGuider | GUIDER |
| Sampling | BasicScheduler | SIGMAS |
| Latent | EmptyLatentImage | LATENT |
| Latent | LatentUpscale | LATENT |
| VAE | VAEDecode | IMAGE |
| VAE | VAEEncode | LATENT |
| Conditioning | CLIPTextEncode | CONDITIONING |
| Conditioning | ControlNetApply | CONDITIONING |
| Image | SaveImage | (none) |
| Image | LoadImage | IMAGE, MASK |
| Image | ImageScale | IMAGE |
| Mask | EmptyMask | MASK |
| Mask | MaskToImage | IMAGE |
| Video | VHS_VideoCombine | VHS_FILENAMES |
| Video | VHS_LoadVideo | IMAGE |
| Flux | CLIPTextEncodeFlux | CONDITIONING |
| Flux | FluxGuidance | CONDITIONING |
