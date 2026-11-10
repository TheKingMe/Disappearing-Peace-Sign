"""
✌️ Quick Launcher for the Disappearing Peace Sign Meme Effect.
Run with:
    python main.py
Or with phone camera:
    python main.py --cam 1 --no-vcam
Or with phone Wi-Fi IP stream:
    python main.py --cam http://192.168.1.50:8080/video --no-vcam
To list all available cameras:
    python main.py --list-cams
"""

import sys
import argparse
from disappearing_peace import DisappearingApp, list_available_cameras

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="✌️ Disappearing Peace Sign Meme Effect")
    parser.add_argument("--cam", type=str, default="0", help="Camera index (e.g. 0, 1) or phone IP stream URL (default: 0)")
    parser.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270], help="Camera rotation angle in degrees (default: 0)")
    parser.add_argument("--sound", type=str, default="peace_meme_sound.wav", help="Sound file path")
    parser.add_argument("--no-vcam", action="store_true", help="Disable virtual camera (use this when recording in OBS Studio)")
    parser.add_argument("--list-cams", action="store_true", help="Scan and list all connected cameras")
    args = parser.parse_args()

    if args.list_cams:
        list_available_cameras()
        sys.exit(0)

    app = DisappearingApp(
        cam_index=args.cam,
        sound_file=args.sound,
        rotation=args.rotate,
        enable_vcam=not args.no_vcam
    )
    app.run()
