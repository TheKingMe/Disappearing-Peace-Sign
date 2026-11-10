"""
=============================================================================
✌️ Disappearing Peace Sign Meme Effect (Professional & Ultra-Stable Edition)
Inspired by: "Come abbandonare i meeting con stile" (Nileseyy Niles Peace Meme)
=============================================================================
Controls:
  [✌️] Peace Sign   : Trigger Disappearance Dissolution & Meme Sound
  [T]               : Rotate Camera (0° -> 90° -> 180° -> 270°)
  [B]               : Capture / Update Clean Background
  [R] / [Space]     : Reappear / Reset to Live Camera
  [M]               : Toggle Sound Effect (Mute / Unmute)
  [V]               : Toggle Virtual Camera Output (Zoom / Teams / Meet)
  [H]               : Toggle HUD Overlay
  [F]               : Toggle Fullscreen
  [Q] / [ESC]       : Quit
=============================================================================
"""

import os
import sys
import time
import math
import random
import argparse
import winsound
import numpy as np
import cv2

# Cleanly suppress TensorFlow Lite / MediaPipe C++ stderr warnings
class SuppressStderr:
    """Context manager to suppress low-level C++ stderr logging on Windows."""
    def __enter__(self):
        try:
            self.null_fd = os.open(os.devnull, os.O_RDWR)
            self.save_fd = os.dup(2)
            os.dup2(self.null_fd, 2)
        except Exception:
            self.save_fd = None
        return self

    def __exit__(self, *_):
        if self.save_fd is not None:
            try:
                os.dup2(self.save_fd, 2)
                os.close(self.null_fd)
                os.close(self.save_fd)
            except Exception:
                pass

with SuppressStderr():
    try:
        from cvzone.HandTrackingModule import HandDetector
        from cvzone.SelfiSegmentationModule import SelfiSegmentation
        import mediapipe as mp
    except ImportError as e:
        print(f"[ERROR] Missing required library: {e}")
        print("Please run: pip install opencv-python cvzone mediapipe pyvirtualcam")
        sys.exit(1)

# Optional virtual camera support
try:
    import pyvirtualcam
    HAS_VIRTUALCAM = True
except ImportError:
    HAS_VIRTUALCAM = False


class Particle:
    """A glowing neon ember particle with convective thermal drift and cooling physics."""
    def __init__(self, x, y, sample_color=None):
        self.x = float(x)
        self.y = float(y)
        # Upward float with subtle organic drift
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-4.5, -1.5)
        self.radius = random.randint(2, 5)
        self.max_life = random.randint(20, 36)
        self.life = self.max_life
        self.phase = random.uniform(0, math.pi * 2)
        self.time = 0.0
        
        # Luminous neon cyber palette (BGR format)
        palette = [
            (255, 240, 40),   # Neon Cyan
            (225, 255, 60),   # Bright Teal
            (90, 255, 140),   # Mint Green
            (255, 170, 20),   # Electric Blue
            (220, 80, 255),   # Magenta / Pink accent
            (255, 255, 255)   # White hot spark
        ]
        
        # 35% of particles inherit boosted clothing/skin/hair color for realistic disintegration
        if sample_color is not None and random.random() < 0.35:
            b, g, r = [min(255, int(c * 1.35 + 35)) for c in sample_color]
            self.color = (b, g, r)
        else:
            self.color = random.choice(palette)

    def update(self):
        self.time += 0.22
        # Thermal convection turbulence (sine wave wobble)
        wobble = math.sin(self.time + self.phase) * 0.8
        self.x += self.vx + wobble
        self.y += self.vy
        self.vy *= 0.98  # air drag
        self.vx *= 0.99
        self.life -= 1
        return self.life > 0

    def draw(self, overlay):
        if self.life <= 0:
            return
        alpha = self.life / self.max_life
        curr_rad = max(1, int(self.radius * (0.35 + 0.65 * alpha)))
        ix, iy = int(self.x), int(self.y)
        h, w = overlay.shape[:2]
        if 0 <= ix < w and 0 <= iy < h:
            # Multi-layer glow: outer halo + bright core
            outer_col = tuple(int(c * alpha * 0.40) for c in self.color)
            core_col = tuple(int(c * alpha * 0.95) for c in self.color)
            cv2.circle(overlay, (ix, iy), curr_rad * 2 + 1, outer_col, -1)
            cv2.circle(overlay, (ix, iy), curr_rad, core_col, -1)
            if alpha > 0.6:
                # White-hot spark core when newly spawned
                cv2.circle(overlay, (ix, iy), max(1, curr_rad // 2), (255, 255, 255), -1)


class DisappearingApp:
    def __init__(self, cam_index=0, sound_file="peace_meme_sound.wav", rotation=0, enable_vcam=True):
        self.cam_index = cam_index
        self.sound_file = os.path.abspath(sound_file) if sound_file else None
        self.enable_vcam = enable_vcam and HAS_VIRTUALCAM
        self.sound_enabled = True
        self.show_hud = True
        self.fullscreen = False
        self.rotation = rotation % 360  # 0, 90, 180, 270
        
        # Toast notification system
        self.toast_message = ""
        self.toast_timer = 0
        
        # Last valid frame cache (for frame drop stability)
        self.last_valid_frame = None

        print("[*] Initializing AI models (Hand Detector + Selfie Segmenter)...")
        with SuppressStderr():
            self.hand_detector = HandDetector(maxHands=1, detectionCon=0.68, minTrackCon=0.65)
            
            # High-performance recurrent video segmenter for live 60fps tracking
            seg_model = "selfie_segmenter.tflite"
            if not os.path.exists(seg_model):
                import urllib.request
                seg_url = "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/1/selfie_segmenter.tflite"
                urllib.request.urlretrieve(seg_url, seg_model)

            from mediapipe.tasks import python as mp_tasks
            from mediapipe.tasks.python import vision as mp_vision

            base_options = mp_tasks.BaseOptions(model_asset_path=seg_model)
            options = mp_vision.ImageSegmenterOptions(
                base_options=base_options,
                running_mode=mp_vision.RunningMode.VIDEO,
                output_category_mask=True
            )
            self.segmenter = mp_vision.ImageSegmenter.create_from_options(options)
            
        self.seg_timestamp = 0
        self.shadow_enabled = True
        self.shadow_intensity = 0.42  # Realistic dual-layer contact/ambient shadow opacity
        self.exposure_gain = np.array([1.0, 1.0, 1.0], dtype=np.float32)  # Real-time ambient exposure auto-match
        
        # State machine: "IDLE", "DISAPPEARING", "DISAPPEARED", "REAPPEARING"
        self.state = "IDLE"
        self.progress = 0.0
        self.dissolve_speed = 0.020  # ~50 frames (~1.6s) for smooth, natural live movement
        self.disappear_cooldown_until = 0.0  # Cooldown before peace sign can trigger reappear
        
        # Gesture tracking stability
        self.peace_consecutive_frames = 0
        self.PEACE_TRIGGER_THRESHOLD = 5  # Stable confirmation count
        self.hand_center = None
        
        # Particles
        self.particles = []
        
        # Background management
        self.bg_frame = None
        self.bg_file = "background.jpg"
        if os.path.exists(self.bg_file):
            loaded = cv2.imread(self.bg_file)
            if loaded is not None:
                self.bg_frame = loaded
                print(f"[+] Loaded existing background from '{self.bg_file}'")
                
        # Camera initialization (supports local hardware index or phone IP stream URL)
        is_stream = isinstance(self.cam_index, str) and ("://" in self.cam_index or not self.cam_index.isdigit())
        if is_stream:
            print(f"[*] Connecting to phone/network stream: {self.cam_index}")
            self.cap = cv2.VideoCapture(self.cam_index)
            if not self.cap.isOpened():
                raise RuntimeError(f"Could not connect to camera stream: {self.cam_index}")
        else:
            try:
                cam_num = int(self.cam_index)
            except (ValueError, TypeError):
                cam_num = 0
                
            backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
            self.cap = cv2.VideoCapture(cam_num, backend)
            if not self.cap.isOpened():
                print(f"[!] Warning: Could not open camera {cam_num} with DirectShow, trying default backend...")
                self.cap = cv2.VideoCapture(cam_num)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    raise RuntimeError("Failed to open any webcam.")

        # Request high-definition resolution (for hardware webcams)
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        except Exception:
            pass
        
        # Warm-up read retry loop to allow webcam sensor/stream to activate
        test_frame = None
        for _ in range(25):
            ret, frame = self.cap.read()
            if ret and frame is not None:
                test_frame = frame
                break
            time.sleep(0.08)
            
        if test_frame is None:
            print(f"\n[ERROR] Could not open camera '{self.cam_index}'.")
            print("        If you are trying to use your phone, make sure your phone webcam app")
            print("        (like Iriun Webcam, DroidCam, or IP Webcam) is running and connected!")
            list_available_cameras()
            sys.exit(1)
            
        self.base_h, self.base_w = test_frame.shape[:2]
        
        if self.rotation in [90, 270]:
            self.w, self.h = self.base_h, self.base_w
        else:
            self.w, self.h = self.base_w, self.base_h
            
        print(f"[+] Camera feed ready: {self.w}x{self.h} (Rotation: {self.rotation}°)")
        
        # Adapt background to current orientation
        self._ensure_background_fit()
        
        # Generate organic noise wave map
        self._init_noise_map()
        
        # Virtual Camera
        self.vcam = None
        if self.enable_vcam:
            self._start_vcam()

    def _apply_rotation(self, frame):
        """Applies configured rotation angle to the frame."""
        if self.rotation == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif self.rotation == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame

    def _ensure_background_fit(self):
        """Ensures the background matches current frame dimensions."""
        if self.bg_frame is not None:
            if self.bg_frame.shape[:2] != (self.h, self.w):
                self.bg_frame = cv2.resize(self.bg_frame, (self.w, self.h), interpolation=cv2.INTER_AREA)

    def _init_noise_map(self):
        """Generates a smooth fractal-like organic wave map for natural edge disintegration."""
        np.random.seed(42)
        raw_noise = np.random.uniform(-16, 16, (self.h, self.w)).astype(np.float32)
        self.noise_map = cv2.GaussianBlur(raw_noise, (25, 25), 8)

    def _start_vcam(self):
        """Starts pyvirtualcam instance with error handling."""
        if not HAS_VIRTUALCAM:
            return
        try:
            self.vcam = pyvirtualcam.Camera(
                width=self.w, height=self.h, fps=30, 
                fmt=pyvirtualcam.PixelFormat.BGR, backend='obs'
            )
            print(f"[+] Virtual Camera active on: {self.vcam.device}")
            self.show_toast("Virtual Camera: ON (OBS Virtual Camera)")
        except Exception as e:
            try:
                # Fallback to default backend if obs keyword fails
                self.vcam = pyvirtualcam.Camera(
                    width=self.w, height=self.h, fps=30, 
                    fmt=pyvirtualcam.PixelFormat.BGR
                )
                print(f"[+] Virtual Camera active on: {self.vcam.device}")
                self.show_toast("Virtual Camera: ON")
            except Exception as err:
                print(f"[-] Virtual camera note: {err}")
                self.vcam = None

    def _stop_vcam(self):
        """Safely stops virtual camera."""
        if self.vcam is not None:
            try:
                self.vcam.close()
            except Exception:
                pass
            self.vcam = None

    def rotate_camera(self):
        """Cycles camera rotation live: 0° -> 90° -> 180° -> 270°."""
        self.rotation = (self.rotation + 90) % 360
        if self.rotation in [90, 270]:
            self.w, self.h = self.base_h, self.base_w
        else:
            self.w, self.h = self.base_w, self.base_h

        self._ensure_background_fit()
        self._init_noise_map()
        
        # If virtual camera was running, restart it with new dimensions
        if self.vcam is not None:
            self._stop_vcam()
            self._start_vcam()
            
        self.show_toast(f"Camera Rotated: {self.rotation}°")
        print(f"[+] Camera rotation set to: {self.rotation}° ({self.w}x{self.h})")

    def show_toast(self, message, duration=60):
        """Displays a temporary toast notification on the HUD."""
        self.toast_message = message
        self.toast_timer = duration

    def capture_background(self, frame):
        """Captures and saves the clean background frame."""
        self.bg_frame = frame.copy()
        cv2.imwrite(self.bg_file, self.bg_frame)
        self.show_toast("Background Saved! (background.jpg)")
        print(f"[+] Clean background captured and saved to '{self.bg_file}'!")

    def play_meme_sound(self):
        """Plays the peace meme audio asynchronously."""
        if not self.sound_enabled or not self.sound_file:
            return
        if os.path.exists(self.sound_file):
            try:
                winsound.PlaySound(self.sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                print(f"[!] Audio note: {e}")

    def is_peace_sign(self, hand):
        """
        Rock-solid gesture recognition for the ✌️ Peace Sign:
        1. Invariant Euclidean distance-to-wrist ratio check
        2. CVZone finger extension state check
        3. Index & Middle fingertip separation (V-shape verification)
        """
        lmList = hand["lmList"]
        if len(lmList) < 21:
            return False

        wrist = np.array(lmList[0][:2], dtype=np.float32)
        idx_tip = np.array(lmList[8][:2], dtype=np.float32)
        idx_pip = np.array(lmList[6][:2], dtype=np.float32)
        mid_tip = np.array(lmList[12][:2], dtype=np.float32)
        mid_pip = np.array(lmList[10][:2], dtype=np.float32)
        rng_tip = np.array(lmList[16][:2], dtype=np.float32)
        rng_pip = np.array(lmList[14][:2], dtype=np.float32)
        pnk_tip = np.array(lmList[20][:2], dtype=np.float32)
        pnk_pip = np.array(lmList[18][:2], dtype=np.float32)

        # Distance from wrist
        d_idx_tip = np.linalg.norm(idx_tip - wrist)
        d_idx_pip = np.linalg.norm(idx_pip - wrist)
        d_mid_tip = np.linalg.norm(mid_tip - wrist)
        d_mid_pip = np.linalg.norm(mid_pip - wrist)
        d_rng_tip = np.linalg.norm(rng_tip - wrist)
        d_rng_pip = np.linalg.norm(rng_pip - wrist)
        d_pnk_tip = np.linalg.norm(pnk_tip - wrist)
        d_pnk_pip = np.linalg.norm(pnk_pip - wrist)

        # Index and middle must be clearly extended away from wrist
        idx_extended = d_idx_tip > (d_idx_pip * 1.20)
        mid_extended = d_mid_tip > (d_mid_pip * 1.20)
        # Ring and pinky must be folded toward wrist
        rng_folded = d_rng_tip < (d_rng_pip * 1.15)
        pnk_folded = d_pnk_tip < (d_pnk_pip * 1.15)

        # Fingers state check
        fingers = self.hand_detector.fingersUp(hand)
        cvzone_check = (fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0)

        # V-shape separation check between index and middle tips
        v_separation = np.linalg.norm(idx_tip - mid_tip) > (d_idx_pip * 0.22)

        return (idx_extended and mid_extended and rng_folded and pnk_folded) and (cvzone_check or v_separation)

    def get_person_mask(self, frame):
        """Runs fast recurrent segmentation to extract a live feathered, anti-aliased person silhouette."""
        proc_w, proc_h = 320, 240
        small = cv2.resize(frame, (proc_w, proc_h))
        imgRGB = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        
        self.seg_timestamp += 33
        with SuppressStderr():
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
            result = self.segmenter.segment_for_video(mp_img, self.seg_timestamp)
            
        cmask = result.category_mask.numpy_view()
        # category 0 is person
        mask_small = (cmask[:, :, 0] == 0).astype(np.float32)
        
        # Soften small mask before upsampling to eliminate jagged blockiness
        mask_small = cv2.GaussianBlur(mask_small, (5, 5), 0)
        
        # Upsample to full resolution
        full_mask = cv2.resize(mask_small, (self.w, self.h), interpolation=cv2.INTER_LINEAR)
        # Apply gentle edge blur for smooth hair and clothing boundaries
        full_mask = cv2.GaussianBlur(full_mask, (11, 11), 3)
        return full_mask

    def start_disappearing(self, frame):
        """Initiates the live dissolve sequence."""
        print("[!] ✌️ Peace Sign verified! Initiating live dissolution effect...")
        self.state = "DISAPPEARING"
        self.progress = 0.0
        self.particles.clear()
        
        # Play sound
        self.play_meme_sound()
        
        # Compute initial baseline bounding range of person
        first_mask = self.get_person_mask(frame)
        y_indices = np.where(first_mask > 0.25)[0]
        if len(y_indices) > 0:
            self.person_bbox_y = (int(np.min(y_indices)), int(np.max(y_indices)))
        else:
            self.person_bbox_y = (0, self.h)

    def reset_to_idle(self):
        """Brings the user back to live webcam."""
        self.state = "IDLE"
        self.progress = 0.0
        self.particles.clear()
        self.peace_consecutive_frames = 0
        self.hand_center = None
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        self.show_toast("Reappeared (Live Camera)")
        print("[+] Reappeared to live webcam.")

    def compute_live_shadow(self, visible_mask, dx=8, dy=14):
        """Computes a realistic dual-layer (contact + ambient diffuse) shadow."""
        if not self.shadow_enabled or self.bg_frame is None:
            return np.zeros((self.h, self.w), dtype=np.float32)
            
        proc_w, proc_h = 320, 180
        small_mask = cv2.resize(visible_mask, (proc_w, proc_h), interpolation=cv2.INTER_NEAREST)
        
        # 1. Close contact shadow (sharp and dark near body)
        M_contact = np.float32([[1, 0, dx * 0.4], [0, 1, dy * 0.4]])
        shifted_contact = cv2.warpAffine(small_mask, M_contact, (proc_w, proc_h))
        blur_contact = cv2.GaussianBlur(shifted_contact, (15, 15), 4)
        
        # 2. Diffuse ambient drop shadow (softer and wider on wall)
        M_diffuse = np.float32([[1, 0, dx], [0, 1, dy]])
        shifted_diffuse = cv2.warpAffine(small_mask, M_diffuse, (proc_w, proc_h))
        blur_diffuse = cv2.GaussianBlur(shifted_diffuse, (31, 31), 9)
        
        combined = blur_contact * 0.55 + blur_diffuse * 0.45
        full_shadow = cv2.resize(combined, (self.w, self.h), interpolation=cv2.INTER_LINEAR)
        shadow_factor = np.clip(full_shadow * (1.0 - visible_mask) * self.shadow_intensity, 0.0, 1.0)
        return shadow_factor

    def get_exposure_matched_bg(self, live_frame, person_mask):
        """Dynamically matches brightness and color temperature of the background to the live room lighting."""
        if self.bg_frame is None:
            return np.full_like(live_frame, 25, dtype=np.float32)
            
        bg_f = self.bg_frame.astype(np.float32)
        
        # Sample background area outside the person
        bg_region = person_mask < 0.08
        count = np.sum(bg_region)
        
        if count > 2000:
            step = max(1, int(count // 1000))
            mean_live = np.mean(live_frame[bg_region][::step], axis=0)
            mean_bg = np.mean(self.bg_frame[bg_region][::step], axis=0) + 1e-4
            
            target_gain = np.clip(mean_live / mean_bg, 0.75, 1.35)
            self.exposure_gain = 0.90 * self.exposure_gain + 0.10 * target_gain
            
        return np.clip(bg_f * self.exposure_gain, 0.0, 255.0)

    def update_and_render_dissolve(self, current_frame):
        """
        Renders the anti-aliased organic particle dissolve effect while keeping the user LIVE.
        Features dynamic ambient exposure matching, dual-layer contact shadow, and burning plasma ember rim!
        """
        # 1. Compute LIVE segmentation mask on the current moving frame
        live_mask = self.get_person_mask(current_frame)
        
        # Update head position smoothly if user moves their head
        y_indices = np.where(live_mask > 0.25)[0]
        if len(y_indices) > 0:
            curr_min_y = int(np.min(y_indices))
            self.person_bbox_y = (min(self.person_bbox_y[0], curr_min_y), self.person_bbox_y[1])
            
        min_y, max_y = self.person_bbox_y
        span = max(10, max_y - min_y)
        
        # Cutoff wave travels upward from max_y to min_y
        target_y = max_y - self.progress * span
        cutoff_map = target_y + self.noise_map
        y_grid = np.arange(self.h, dtype=np.float32)[:, None]
        
        fade_band = 18.0  # Smooth transition feathering band
        # Alpha factor: 0.0 (top, keep person) to 1.0 (bottom, dissolved to background)
        alpha_transition = np.clip((y_grid - (cutoff_map - fade_band)) / (2.0 * fade_band), 0.0, 1.0)
        
        # Visible person mask: live moving silhouette not yet dissolved
        visible_mask = live_mask * (1.0 - alpha_transition)
        person_weight = visible_mask[:, :, None]
        
        # Dynamic live dual-layer contact shadow onto background
        shadow_factor = self.compute_live_shadow(visible_mask)
        
        # Dynamically exposure-matched background to eliminate any lighting jump
        bg_target = self.get_exposure_matched_bg(current_frame, live_mask)
        bg_shaded = bg_target * (1.0 - shadow_factor[:, :, None])
            
        # CRITICAL: Use current_frame LIVE so the user is moving in real-time!
        person_f = current_frame.astype(np.float32)
        
        # 2. Glowing Burning Plasma Rim along the active wave front
        rim_factor = np.exp(-((alpha_transition - 0.5) ** 2) / 0.035) * (live_mask > 0.2)
        rim_color = np.array([255, 235, 60], dtype=np.float32)  # Electric cyan-plasma
        rim_overlay = (rim_factor[:, :, None] * rim_color).astype(np.float32)
        
        # 3. Seamless composite with live shadow + burning rim
        composite = person_f * person_weight + bg_shaded * (1.0 - person_weight)
        composite = np.clip(composite + rim_overlay * 1.5, 0, 255).astype(np.uint8)
        
        # 4. Identify active wave front on LIVE silhouette to emit glowing embers
        wave_front = (live_mask > 0.3) & (np.abs(y_grid - cutoff_map) < 14)
        wy, wx = np.where(wave_front)
        
        # Spawn particles along active live wave front with sampled body colors
        if len(wy) > 0 and self.progress < 0.98:
            num_to_spawn = min(32, max(6, len(wy) // 16))
            for _ in range(num_to_spawn):
                idx = random.randint(0, len(wy) - 1)
                px, py = wx[idx], wy[idx]
                sample_col = current_frame[py, px]
                self.particles.append(Particle(px, py, sample_color=sample_col))
                
        # Render particles onto additive glow overlay
        particle_overlay = np.zeros_like(composite, dtype=np.uint8)
        surviving = []
        for p in self.particles:
            if p.update():
                p.draw(particle_overlay)
                surviving.append(p)
        self.particles = surviving
        
        if len(self.particles) > 0:
            particle_overlay = cv2.GaussianBlur(particle_overlay, (5, 5), 0)
            composite = cv2.add(composite, particle_overlay)
            
        # Advance progression
        self.progress += self.dissolve_speed
        if self.progress >= 1.0:
            self.progress = 1.0
            if len(self.particles) == 0:
                self.state = "DISAPPEARED"
                self.disappear_cooldown_until = time.time() + 1.2  # 1.2s cooldown before peace sign triggers reappear
                self.peace_consecutive_frames = 0
                self.hand_center = None
                print("[+] Disappearance complete! Show ✌️ Peace Sign again to reappear.")
                self.show_toast("Show ✌️ Peace Sign again to Reappear!")
                
        return composite

    def start_reappearing(self, frame):
        """Initiates the live materialize/reappearance sequence when peace sign is shown again."""
        print("[!] ✌️ Peace Sign verified! Materializing back live...")
        self.state = "REAPPEARING"
        self.progress = 1.0  # 1.0 (empty) -> 0.0 (fully materialized)
        self.particles.clear()
        self.peace_consecutive_frames = 0
        self.hand_center = None
        
        # Compute initial live person bounds
        live_mask = self.get_person_mask(frame)
        y_indices = np.where(live_mask > 0.25)[0]
        if len(y_indices) > 0:
            self.person_bbox_y = (int(np.min(y_indices)), int(np.max(y_indices)))
        else:
            self.person_bbox_y = (0, self.h)
            
        self.show_toast("Materializing back live! ✌️")

    def update_and_render_reappear(self, current_frame):
        """Renders the person materializing back live into reality with glowing neon embers, burning rim, and live shadow."""
        # 1. Compute LIVE segmentation mask on current moving frame
        live_mask = self.get_person_mask(current_frame)
        
        min_y, max_y = self.person_bbox_y
        span = max(10, max_y - min_y)
        
        # Cutoff wave travels downward: progress goes from 1.0 down to 0.0
        target_y = min_y + (1.0 - self.progress) * span
        cutoff_map = target_y + self.noise_map
        y_grid = np.arange(self.h, dtype=np.float32)[:, None]
        
        fade_band = 18.0
        # Where y < cutoff_map: person is revealed
        alpha_reveal = 1.0 - np.clip((y_grid - (cutoff_map - fade_band)) / (2.0 * fade_band), 0.0, 1.0)
        
        # Person blend weight from live mask
        visible_mask = live_mask * alpha_reveal
        person_weight = visible_mask[:, :, None]
        
        # Dynamic live dual-layer contact shadow
        shadow_factor = self.compute_live_shadow(visible_mask)
        
        # Exposure-matched background
        bg_target = self.get_exposure_matched_bg(current_frame, live_mask)
        bg_shaded = bg_target * (1.0 - shadow_factor[:, :, None])
            
        # LIVE current frame so user moves while materializing back
        person_f = current_frame.astype(np.float32)
        
        # Burning rim along materialization wave
        rim_factor = np.exp(-((alpha_reveal - 0.5) ** 2) / 0.035) * (live_mask > 0.2)
        rim_color = np.array([255, 235, 60], dtype=np.float32)
        rim_overlay = (rim_factor[:, :, None] * rim_color).astype(np.float32)
        
        composite = person_f * person_weight + bg_shaded * (1.0 - person_weight)
        composite = np.clip(composite + rim_overlay * 1.5, 0, 255).astype(np.uint8)
        
        # Spawn glowing embers at the active materialization wave front
        wave_front = (live_mask > 0.3) & (np.abs(y_grid - cutoff_map) < 14)
        wy, wx = np.where(wave_front)
        
        if len(wy) > 0 and self.progress > 0.05:
            num_to_spawn = min(32, max(6, len(wy) // 16))
            for _ in range(num_to_spawn):
                idx = random.randint(0, len(wy) - 1)
                px, py = wx[idx], wy[idx]
                sample_col = current_frame[py, px]
                self.particles.append(Particle(px, py, sample_color=sample_col))
                
        particle_overlay = np.zeros_like(composite, dtype=np.uint8)
        surviving = []
        for p in self.particles:
            if p.update():
                p.draw(particle_overlay)
                surviving.append(p)
        self.particles = surviving
        
        if len(self.particles) > 0:
            particle_overlay = cv2.GaussianBlur(particle_overlay, (5, 5), 0)
            composite = cv2.add(composite, particle_overlay)
            
        # Advance progress toward 0.0 (materializing complete)
        self.progress -= self.dissolve_speed * 1.3
        if self.progress <= 0.0:
            self.progress = 0.0
            if len(self.particles) == 0:
                self.reset_to_idle()
                
        return composite
        
        # Spawn glowing embers at the active materialization wave front
        wave_front = (live_mask > 0.3) & (np.abs(y_grid - cutoff_map) < 14)
        wy, wx = np.where(wave_front)
        
        if len(wy) > 0 and self.progress > 0.05:
            num_to_spawn = min(28, max(5, len(wy) // 18))
            for _ in range(num_to_spawn):
                idx = random.randint(0, len(wy) - 1)
                self.particles.append(Particle(wx[idx], wy[idx]))
                
        particle_overlay = np.zeros_like(composite, dtype=np.uint8)
        surviving = []
        for p in self.particles:
            if p.update():
                p.draw(particle_overlay)
                surviving.append(p)
        self.particles = surviving
        
        if len(self.particles) > 0:
            particle_overlay = cv2.GaussianBlur(particle_overlay, (5, 5), 0)
            composite = cv2.add(composite, particle_overlay)
            
        # Advance progress toward 0.0 (materializing complete)
        self.progress -= self.dissolve_speed * 1.3
        if self.progress <= 0.0:
            self.progress = 0.0
            if len(self.particles) == 0:
                self.reset_to_idle()
                
        return composite
                
        return composite

    def draw_hud(self, frame):
        """Draws a clean, modern floating status card and toast messages."""
        if not self.show_hud:
            return frame
            
        overlay = frame.copy()
        
        # Modern translucent card at top-left
        card_w, card_h = 350, 115
        cv2.rectangle(overlay, (14, 14), (14 + card_w, 14 + card_h), (18, 18, 18), -1)
        cv2.addWeighted(overlay, 0.70, frame, 0.30, 0, frame)
        cv2.rectangle(frame, (14, 14), (14 + card_w, 14 + card_h), (65, 65, 65), 1)
        
        # Status Badge
        badge_colors = {
            "IDLE": (0, 235, 120),
            "DISAPPEARING": (0, 220, 255),
            "DISAPPEARED": (0, 90, 255),
            "REAPPEARING": (255, 180, 0)
        }
        status_color = badge_colors.get(self.state, (255, 255, 255))
        cv2.circle(frame, (32, 38), 6, status_color, -1)
        cv2.putText(frame, f"STATUS: {self.state}", (46, 43), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.58, status_color, 1, cv2.LINE_AA)
        
        # Shortcut keys
        cv2.putText(frame, "[✌️] Peace Sign : Disappear / Reappear", (26, 68), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(frame, f"[T] Rotate: {self.rotation}° | [B] Save BG | [R] Reset", (26, 88), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)
                    
        vcam_lbl = "ON" if self.vcam else "OFF"
        shd_lbl = "ON" if self.shadow_enabled else "OFF"
        cv2.putText(frame, f"[S] Shadow: {shd_lbl} | [V] V-Cam: {vcam_lbl} | [H] Hide HUD", (26, 108), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (175, 175, 175), 1, cv2.LINE_AA)

        # Peace sign confirmation charge meter on card
        if self.state in ["IDLE", "DISAPPEARED"] and self.peace_consecutive_frames > 0:
            charge = min(1.0, self.peace_consecutive_frames / self.PEACE_TRIGGER_THRESHOLD)
            bar_w = int(card_w * charge)
            bar_color = (0, 255, 255) if self.state == "IDLE" else (0, 180, 255)
            cv2.rectangle(frame, (14, 14 + card_h - 4), (14 + bar_w, 14 + card_h), bar_color, -1)

        # Draw reticle on hand in local preview if charging
        if self.hand_center is not None:
            cx, cy, end_angle = self.hand_center
            cv2.circle(frame, (cx, cy), 32, (60, 60, 60), 2, cv2.LINE_AA)
            reticle_col = (0, 255, 255) if self.state == "IDLE" else (0, 180, 255)
            cv2.ellipse(frame, (cx, cy), (32, 32), 0, -90, -90 + end_angle, reticle_col, 3, cv2.LINE_AA)
            if self.state == "DISAPPEARED":
                cv2.putText(frame, "REAPPEARING...", (cx - 55, cy - 42),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 180, 255), 1, cv2.LINE_AA)

        # Toast notification
        if self.toast_timer > 0 and self.toast_message:
            self.toast_timer -= 1
            toast_text = self.toast_message
            (tw, th), _ = cv2.getTextSize(toast_text, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)
            tx = (self.w - tw) // 2
            ty = 45
            t_overlay = frame.copy()
            cv2.rectangle(t_overlay, (tx - 15, ty - 22), (tx + tw + 15, ty + 10), (25, 25, 25), -1)
            cv2.addWeighted(t_overlay, 0.80, frame, 0.20, 0, frame)
            cv2.rectangle(frame, (tx - 15, ty - 22), (tx + tw + 15, ty + 10), (0, 220, 255), 1)
            cv2.putText(frame, toast_text, (tx, ty - 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)
                        
        return frame

    def run(self):
        window_name = "Disappearing Peace Meme"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, min(1280, self.w), min(720, self.h))

        print("\n===============================================================")
        print(" ✌️ DISAPPEARING PEACE EFFECT RUNNING!")
        print(" - Show ✌️ Peace Sign to dissolve like the meme!")
        print(" - Press [T] to rotate camera live (0°, 90°, 180°, 270°)")
        print(" - Press [B] to capture clean room background")
        print(" - Press [R] or [Space] to reappear")
        print(" - Press [H] to hide/show on-screen HUD")
        print(" - Press [Q] or [ESC] to quit")
        print("===============================================================\n")

        if self.bg_frame is None:
            self.show_toast("Step out and press 'B' to save clean background!", duration=120)

        while True:
            ret, raw_frame = self.cap.read()
            if not ret or raw_frame is None:
                if self.last_valid_frame is not None:
                    raw_frame = self.last_valid_frame.copy()
                else:
                    time.sleep(0.01)
                    continue
            else:
                self.last_valid_frame = raw_frame

            # 1. Apply rotation
            frame = self._apply_rotation(raw_frame)
            # 2. Mirror horizontally for natural webcam interaction
            frame = cv2.flip(frame, 1)
            
            output_frame = frame.copy()

            # ----------------------------------------------------
            # State: IDLE
            # ----------------------------------------------------
            if self.state == "IDLE":
                output_frame = frame.copy()
                
                # Hand tracking
                with SuppressStderr():
                    hands, _ = self.hand_detector.findHands(frame, draw=False)
                    
                if hands:
                    hand = hands[0]
                    if self.is_peace_sign(hand):
                        self.peace_consecutive_frames += 1
                        cx, cy = hand["center"]
                        charge_ratio = min(1.0, self.peace_consecutive_frames / self.PEACE_TRIGGER_THRESHOLD)
                        end_angle = int(360 * charge_ratio)
                        self.hand_center = (cx, cy, end_angle)
                        
                        if self.peace_consecutive_frames >= self.PEACE_TRIGGER_THRESHOLD:
                            self.start_disappearing(frame)
                    else:
                        self.peace_consecutive_frames = max(0, self.peace_consecutive_frames - 1)
                        self.hand_center = None
                else:
                    self.peace_consecutive_frames = max(0, self.peace_consecutive_frames - 1)
                    self.hand_center = None

            # ----------------------------------------------------
            # State: DISAPPEARING
            # ----------------------------------------------------
            elif self.state == "DISAPPEARING":
                self.hand_center = None
                output_frame = self.update_and_render_dissolve(frame)

            # ----------------------------------------------------
            # State: DISAPPEARED (Empty background + Peace sign detection to return)
            # ----------------------------------------------------
            elif self.state == "DISAPPEARED":
                if self.bg_frame is not None:
                    output_frame = self.bg_frame.copy()
                else:
                    output_frame = np.full_like(frame, 22)
                    cv2.putText(output_frame, "USER HAS DISAPPEARED", (self.w // 2 - 160, self.h // 2),
                                cv2.FONT_HERSHEY_DUPLEX, 0.75, (200, 200, 200), 1, cv2.LINE_AA)

                # Check if cooldown has elapsed before allowing ✌️ to bring you back
                if time.time() >= self.disappear_cooldown_until:
                    with SuppressStderr():
                        hands, _ = self.hand_detector.findHands(frame, draw=False)
                        
                    if hands:
                        hand = hands[0]
                        if self.is_peace_sign(hand):
                            self.peace_consecutive_frames += 1
                            cx, cy = hand["center"]
                            charge_ratio = min(1.0, self.peace_consecutive_frames / self.PEACE_TRIGGER_THRESHOLD)
                            end_angle = int(360 * charge_ratio)
                            self.hand_center = (cx, cy, end_angle)
                            
                            if self.peace_consecutive_frames >= self.PEACE_TRIGGER_THRESHOLD:
                                self.start_reappearing(frame)
                        else:
                            self.peace_consecutive_frames = max(0, self.peace_consecutive_frames - 1)
                            self.hand_center = None
                    else:
                        self.peace_consecutive_frames = max(0, self.peace_consecutive_frames - 1)
                        self.hand_center = None
                else:
                    self.hand_center = None

            # ----------------------------------------------------
            # State: REAPPEARING
            # ----------------------------------------------------
            elif self.state == "REAPPEARING":
                self.hand_center = None
                output_frame = self.update_and_render_reappear(frame)

            # Stream clean video to Virtual Camera (for Zoom/Teams without HUD text)
            if self.vcam is not None:
                try:
                    self.vcam.send(output_frame)
                    self.vcam.sleep_until_next_frame()
                except Exception:
                    pass

            # Render HUD on preview window
            display_frame = self.draw_hud(output_frame)
            cv2.imshow(window_name, display_frame)

            # Keyboard Input
            key = cv2.waitKey(1) & 0xFF
            if key in [ord('q'), ord('Q'), 27]:  # Q or ESC
                break
            elif key in [ord('t'), ord('T')]:    # Rotate Camera
                self.rotate_camera()
            elif key in [ord('r'), ord('R'), 32]:  # R or Space
                self.reset_to_idle()
            elif key in [ord('b'), ord('B')]:    # Capture Background
                self.capture_background(frame)
            elif key in [ord('m'), ord('M')]:    # Mute Audio
                self.sound_enabled = not self.sound_enabled
                status = "ON" if self.sound_enabled else "OFF"
                self.show_toast(f"Sound: {status}")
            elif key in [ord('s'), ord('S')]:    # Toggle Realistic Shadow
                self.shadow_enabled = not self.shadow_enabled
                status = "ON" if self.shadow_enabled else "OFF"
                self.show_toast(f"Realistic Shadow: {status}")
            elif key in [ord('h'), ord('H')]:    # Toggle HUD
                self.show_hud = not self.show_hud
            elif key in [ord('f'), ord('F')]:    # Toggle Fullscreen
                self.fullscreen = not self.fullscreen
                prop = cv2.WINDOW_FULLSCREEN if self.fullscreen else cv2.WINDOW_NORMAL
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, prop)
            elif key in [ord('v'), ord('V')]:    # Toggle Virtual Camera
                if self.vcam is not None:
                    self._stop_vcam()
                    self.show_toast("Virtual Camera: OFF")
                else:
                    self._start_vcam()

        # Clean exit
        self.cap.release()
        self._stop_vcam()
        cv2.destroyAllWindows()
        print("[+] Application closed cleanly.")


def list_available_cameras(max_tested=8):
    """Scans and prints all active camera indices and resolutions."""
    print("\n[*] Scanning for connected cameras...")
    found = []
    with SuppressStderr():
        for i in range(max_tested):
            backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    found.append((i, w, h))
                cap.release()
                
    if found:
        print("\n--- CONNECTED CAMERAS ---")
        for idx, w, h in found:
            print(f"  Camera Index: {idx}  -->  Resolution: {w}x{h}")
        print("------------------------\n")
        print("To use one of these cameras, run:")
        print(f"  python main.py --cam <index>\n")
    else:
        print("[!] No physical cameras found.")
    return found


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="✌️ Disappearing Peace Meme Effect")
    parser.add_argument("--cam", type=str, default="0", help="Camera index (e.g. 0, 1) or phone IP stream URL (default: 0)")
    parser.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270], help="Camera rotation angle in degrees (default: 0)")
    parser.add_argument("--sound", type=str, default="peace_meme_sound.wav", help="Meme sound file")
    parser.add_argument("--no-vcam", action="store_true", help="Disable virtual camera (recommended when capturing in OBS Studio to record)")
    parser.add_argument("--list-cams", action="store_true", help="Scan and list all connected camera indices")
    args = parser.parse_args()

    if args.list_cams:
        list_available_cameras()
        sys.exit(0)

    app = DisappearingApp(cam_index=args.cam, sound_file=args.sound, rotation=args.rotate, enable_vcam=not args.no_vcam)
    app.run()
