import os
import webp
from PIL import Image
from typing import Optional

def convert_to_webp(old_path:str, new_path:Optional[str] = None, skip_exists = True, delete_source = True, full_new_path = True) -> None:
    """
    convert any picture file into webp format.
    if new_path is None, old_path = old_path remove suffix add webp
    if skip_exists, do nothing if new_path exist, else reconvert
    if delete_source, delete source file after convert
    if not full_new_path, the new_path is only a dir, and export new_path/{old_path base name}.webp
    """
    class auto_delete_source:
        def __enter__(self):
            pass
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None and delete_source:
                os.remove(old_path)

    if not os.path.exists(old_path):
        raise FileNotFoundError(old_path)

    if new_path is None:
        dot = old_path.rfind('.')
        new_path = old_path[:dot] + '.webp'
    elif not full_new_path:
        basename = os.path.basename(old_path)
        dot = basename.rfind('.')
        new_path = os.path.join(new_path, basename[:dot] + '.webp')
    
    with auto_delete_source():
        if os.path.exists(new_path):
            if skip_exists:
                return
            else:
                os.remove(new_path)
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
        frame_duration = gif.info.get('duration', None)
        if frame_duration is None:
            _pic_to_webp(old_path, new_path)
            return
        fps = int(1000 / frame_duration)

        frames = []
        for fid in range(gif.n_frames):
            gif.seek(fid)
            frames.append(gif.copy())
        webp.save_images(frames, new_path, fps=fps, lossless = False)

if __name__ == '__main__':
    for dir, _, fs in os.walk(r'C:\Users\57856\Desktop\src'):
        for f in fs:
            if f.endswith('.webp'):
                continue
            p = os.path.join(dir, f)
            print(p)
            try:
                convert_to_webp(old_path=p)
            except Exception as e:
                print(e)
                continue
