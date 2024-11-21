import os
import webp
from PIL import Image

def convert_to_webp(old_path:str, new_path:str) -> None:
    if old_path.endswith('.gif'):
        _gif_to_webp(old_path, new_path)
    else:
        _pic_to_webp(old_path, new_path)

def read_picture(path:str) -> bytes:
    try:
        st = os.stat(path)
        with open(file=path, mode='rb') as f:
            data = f.read(st.st_size)
            return data
    except Exception as e:
        raise RuntimeError(f"read picture {path} error {e}")

def _pic_to_webp(old_path:str, new_path:str) -> None:
    with Image.open(old_path) as img:
        webp.save_image(img, new_path, quality = 80)

def _gif_to_webp(old_path:str, new_path:str) -> None:
    with Image.open(old_path) as gif:
        frame_duration = gif.info['duration']
        fps = int(1000 / frame_duration)

        frames = []
        for fid in range(gif.n_frames):
            gif.seek(fid)
            frames.append(gif.copy())
        webp.save_images(frames, new_path, fps=fps, lossless = False)

