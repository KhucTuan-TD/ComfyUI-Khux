import os
import numpy as np
import torch
import cv2
import folder_paths

VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".gif")


def list_output_videos():
    out_dir = folder_paths.get_output_directory()
    files = []
    for root, _, names in os.walk(out_dir):
        for n in names:
            if n.lower().endswith(VIDEO_EXTS):
                rel = os.path.relpath(os.path.join(root, n), out_dir)
                files.append(rel.replace("\\", "/"))
    files.sort(key=lambda f: os.path.getmtime(os.path.join(out_dir, f)), reverse=True)
    return files or ["(không có video)"]


def resolve_path(rel):
    out_dir = os.path.realpath(folder_paths.get_output_directory())
    full = os.path.realpath(os.path.join(out_dir, rel))
    # chặn path traversal: file phải nằm trong thư mục output
    if os.path.commonpath([out_dir, full]) != out_dir:
        return None
    return full


class LoadVideoFromOutput:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": (list_output_videos(),),
            },
            "optional": {
                "frame_load_cap": ("INT", {"default": 0, "min": 0, "max": 100000, "tooltip": "0 = đọc tất cả"}),
                "skip_first_frames": ("INT", {"default": 0, "min": 0, "max": 100000}),
                "select_every_nth": ("INT", {"default": 1, "min": 1, "max": 100}),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "FLOAT", "INT", "INT")
    RETURN_NAMES = ("images", "frame_count", "fps", "width", "height")
    FUNCTION = "load"
    CATEGORY = "video/output"

    @classmethod
    def IS_CHANGED(cls, video, **kwargs):
        path = resolve_path(video)
        if path and os.path.isfile(path):
            return os.path.getmtime(path)
        return float("nan")

    @classmethod
    def VALIDATE_INPUTS(cls, video, **kwargs):
        path = resolve_path(video)
        if not path or not os.path.isfile(path):
            return f"Không tìm thấy video: {video}"
        return True

    def load(self, video, frame_load_cap=0, skip_first_frames=0, select_every_nth=1):
        path = resolve_path(video)
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError(f"Không mở được video: {path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frames = []
        idx = 0
        while True:
            ok = cap.grab()
            if not ok:
                break
            if idx >= skip_first_frames and (idx - skip_first_frames) % select_every_nth == 0:
                ok, frame = cap.retrieve()
                if not ok:
                    break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame)
                if frame_load_cap and len(frames) >= frame_load_cap:
                    break
            idx += 1
        cap.release()

        if not frames:
            raise RuntimeError("Không đọc được frame nào từ video.")

        images = torch.from_numpy(np.stack(frames).astype(np.float32) / 255.0)
        n, h, w, _ = images.shape
        return (images, n, float(fps), w, h)


NODE_CLASS_MAPPINGS = {"LoadVideoFromOutput": LoadVideoFromOutput}
NODE_DISPLAY_NAME_MAPPINGS = {"LoadVideoFromOutput": "Load Video (Output)"}