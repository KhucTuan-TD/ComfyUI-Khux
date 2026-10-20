class CropImageDynamic:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),

                "width": ("INT", {"default": 512, "min": 1, "max": 16384, "step": 1, "forceInput": True}),
                "height": ("INT", {"default": 512, "min": 1, "max": 16384, "step": 1, "forceInput": True}),

                "x": ("INT", {"default": 0, "min": 0, "max": 16384, "step": 1}),
                "y": ("INT", {"default": 0, "min": 0, "max": 16384, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "crop"
    CATEGORY = "image/transform"

    def crop(self, image, width, height, x, y):
        # image shape: [batch, H, W, C]
        _, img_h, img_w, _ = image.shape

        x = max(0, min(x, img_w - 1))
        y = max(0, min(y, img_h - 1))
        x2 = min(img_w, x + width)
        y2 = min(img_h, y + height)

        return (image[:, y:y2, x:x2, :],)


NODE_CLASS_MAPPINGS = {
    "CropImageDynamic": CropImageDynamic,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CropImageDynamic": "Crop Image (Dynamic)",
}