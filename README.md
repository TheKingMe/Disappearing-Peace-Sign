# ✌️ Disappearing Peace Sign Meme Effect (Cinematic Photorealism Edition)

A real-time Python computer vision effect inspired by the viral **Nileseyy Niles "Peace Out" / Disappearing Meme** (*"Come abbandonare i meeting con stile"*).

---

## 🎬 Hollywood-Grade Visual Realism Features

1. **🔥 Burning Plasma Ember Rim**:
   - Right at the active disintegration wavefront, the edge of your skin and clothing glows with an emissive electric-cyan plasma rim as it disintegrates into the air, mirroring movie-grade VFX (like the Thanos snap).

2. **💡 Dynamic Ambient Lighting Auto-Matching**:
   - Automatically samples the room lighting in real-time outside your silhouette and dynamically matches the exposure, brightness, and color temperature of the background to your live room.
   - Completely eliminates lighting seams or brightness jumps when dissolving!

3. **👤 Dual-Layer Contact & Ambient Shadow**:
   - Casts a two-stage shadow onto the background behind you:
     - **Sharp Contact Shadow**: Darker and tighter near your body.
     - **Soft Diffuse Penumbra**: Wider and softer on the wall.
   - The shadow dissolves organically from the bottom up as your body disappears, giving your live body realistic 3D physical depth.

4. **✨ Thermal Turbulence & Color-Sampled Embers**:
   - Embers don't just float straight up; they oscillate with convective thermal updraft physics (atmospheric air drag and turbulence).
   - 35% of the particles inherit and amplify the real colors of your shirt, skin, and hair at the spot they were born, mixed with luminous neon cyber embers.

5. **🎥 100% Live Motion Tracking**:
   - You can move your head, smile, blink, talk, and wave goodbye live as you dissolve.

---

## 📱 How to Use Your Phone Camera

### Method 1: Using Iriun Webcam or DroidCam (USB or Wi-Fi — Recommended)
1. Install **Iriun Webcam** (or **DroidCam**) on both your phone and PC.
2. Connect phone via USB cable or ensure both are on the same Wi-Fi.
3. Check which camera index your phone was assigned:
   ```bash
   python main.py --list-cams
   ```
4. Run the code with your phone camera (e.g. index `1` or `2`):
   ```bash
   python main.py --cam 1 --no-vcam
   ```

---

### Method 2: Direct Wi-Fi Stream (No PC software needed!)
1. Install free **IP Webcam** (Android) or **IP Camera Lite** (iPhone) on your phone.
2. Tap **"Start Server"** at the bottom of the app. It will show a URL (e.g. `http://192.168.1.50:8080`).
3. Run the script pointing directly to your phone stream:
   ```bash
   python main.py --cam http://192.168.1.50:8080/video --no-vcam
   ```

---

## 🔴 How to Record in OBS Studio

1. Run the Python app with `--no-vcam`:
   ```bash
   python main.py --no-vcam
   ```
2. In the Python window:
   - Press **`H`** to **HIDE THE HUD TEXT** for a clean recording!
   - Step out for 1s and press **`B`** to capture your clean room background.
3. In OBS Studio:
   - Click **"Start Recording"** (*Avvia registrazione*).
4. Perform the meme:
   - Flash the **✌️ Peace Sign** to dissolve into glowing embers!
   - Flash the **✌️ Peace Sign** again to materialize back into the room!
5. In OBS, click **"Stop Recording"**.

---

## 🎮 Controls Summary

| Key / Gesture | Action |
|---------------|--------|
| **✌️ (Sign)** | **Disappear LIVE** / **Reappear LIVE** |
| **`S`** | **Toggle Realistic Live Shadow** (ON / OFF) |
| **`H`** | **Hide / Show HUD text** (Great for recording!) |
| **`T`** | **Rotate Camera Live** (`0° ➔ 90° ➔ 180° ➔ 270°`) |
| **`B`** | **Capture Clean Background** (Step out for 1s and press `B`) |
| **`V`** | Toggle Virtual Camera ON / OFF |
| **`R` / `Space`** | Instant Reset / Reappear |
| **`M`** | Toggle Meme Sound |
| **`F`** | Fullscreen mode |
| **`Q` / `ESC`** | Quit |
