import torch


def _parse_color(color_str, channels, device, dtype):

    s = color_str.strip()
    try:
        if s.startswith("#"):
            s = s.lstrip("#")
            vals = [int(s[i:i + 2], 16) / 255.0 for i in range(0, 6, 2)]
        else:
            vals = [float(v) for v in s.replace(";", ",").split(",") if v.strip() != ""]
            if any(v > 1.0 for v in vals):
                vals = [v / 255.0 for v in vals]
    except Exception:
        vals = [0.0, 0.0, 0.0]

    if len(vals) == 1:
        vals = vals * 3
    vals = (vals + [0.0, 0.0, 0.0])[:3] if len(vals) < 3 else vals[:3]

    if channels == 1:
        vals = [sum(vals) / 3.0]
    elif channels == 4:
        vals = vals + [1.0]
    elif channels > 4:
        vals = vals + [1.0] * (channels - 3)

    return torch.tensor(vals, device=device, dtype=dtype)


def _source_index(before, n, after, mode, device):

    coords = torch.arange(-before, n + after, device=device)
    if n == 1:
        return torch.zeros_like(coords)
    if mode == "edge_pixel":
        return coords.clamp(0, n - 1)
    if mode == "reflect":  
        period = 2 * (n - 1)
        c = coords.abs() % period
        return torch.where(c >= n, period - c, c)
    if mode == "mirror":  
        period = 2 * n
        c = coords % period
        return torch.where(c >= n, period - 1 - c, c)
    return coords.clamp(0, n - 1)


class ImagePadExtended:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "left": ("INT", {"default": 0, "min": 0, "max": 16384, "step": 1}),
                "right": ("INT", {"default": 0, "min": 0, "max": 16384, "step": 1}),
                "top": ("INT", {"default": 0, "min": 0, "max": 16384, "step": 1}),
                "bottom": ("INT", {"default": 0, "min": 0, "max": 16384, "step": 1}),
                "extra_padding": ("INT", {"default": 0, "min": 0, "max": 16384, "step": 1}),
                "pad_mode": (["edge_pixel", "color", "reflect", "mirror"],),
                "color": ("STRING", {"default": "0, 0, 0"}),
            },
            "optional": {
                "mask": ("MASK",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("images", "masks")
    FUNCTION = "pad"
    CATEGORY = "image/transform"

    def pad(self, image, left, right, top, bottom, extra_padding, pad_mode, color, mask=None):
        B, H, W, C = image.shape
        left += extra_padding
        right += extra_padding
        top += extra_padding
        bottom += extra_padding

        new_h = H + top + bottom
        new_w = W + left + right
        device = image.device


        out_mask = torch.ones((B, new_h, new_w), device=device, dtype=torch.float32)
        if mask is not None:
            m = mask.to(device)
            if m.dim() == 2:
                m = m.unsqueeze(0)
            if m.shape[0] != B:
                m = m[:1].expand(B, -1, -1) if m.shape[0] == 1 else m[:B]
            if m.shape[1] != H or m.shape[2] != W:
                m = torch.nn.functional.interpolate(
                    m.unsqueeze(1).float(), size=(H, W), mode="nearest"
                ).squeeze(1)
            out_mask[:, top:top + H, left:left + W] = m.float()
        else:
            out_mask[:, top:top + H, left:left + W] = 0.0

        # ---- Image ----
        if pad_mode == "color":
            fill = _parse_color(color, C, device, image.dtype)
            out = fill.view(1, 1, 1, C).expand(B, new_h, new_w, C).clone()
            out[:, top:top + H, left:left + W, :] = image
        else:
            ys = _source_index(top, H, bottom, pad_mode, device)
            xs = _source_index(left, W, right, pad_mode, device)
            out = image[:, ys, :, :][:, :, xs, :]

        return (out, out_mask)


NODE_CLASS_MAPPINGS = {
    "ImagePadExtended": ImagePadExtended,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImagePadExtended": "Image Pad (Extended)",
}