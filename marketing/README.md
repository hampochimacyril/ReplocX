# Marketing assets

Promotional material for the Representative Location Explorer. Nothing here uses
private research data — all visuals reference the synthetic demo and the method.

## Files

- **`promo.html`** — a self-running ~84-second product tour with 3D-style motion,
  on-screen captions, a soft ambient music bed, and **spoken narration** using your
  device's voices. Opens with who it's for (modelers, researchers, planners, policy
  makers), then walks through the app (overview → ZIP → scenario → trade-offs). Open it
  in a browser and click **▶ Play with narration**.
  - **Better voice:** a voice menu (top-right) lists installed voices; ★ marks premium
    ones. On macOS install one once via System Settings → Accessibility → Spoken Content
    → System Voice → Manage Voices → English → "Ava (Premium)" (or a Siri voice).
  - **To produce a voiced MP4:** screen-record the window while it plays
    (QuickTime → New Screen Recording, capture system audio), or use Descript/CapCut.

- **`promo.mp4`** — a rendered 1600×900 motion-graphics video (~84s, H.264 + AAC)
  with an ambient music bed and **no voice**, ready to upload directly to
  LinkedIn / X / a landing page. Add narration from `VO_script.md` if you want voice.

- **`VO_script.md`** — the timed voiceover script + a one-take continuous version
  for ElevenLabs / Descript / Murf, plus caption lines.

- **`generate_promo_video.py`** — regenerates `promo.mp4` (pure Python + ffmpeg):
  ```bash
  pip install pillow numpy
  python3 generate_promo_video.py
  ```

## Recommended path to a "studio" version

1. Open `promo.html`, confirm timing/voice you like.
2. For broadcast-quality voice, paste the continuous script from `VO_script.md`
   into ElevenLabs, export the audio, and lay it over `promo.mp4` in any editor
   (the scene timings in `VO_script.md` line up with the MP4).
3. Export 1080p H.264 and publish.

> Note: the videos are "3D-style" motion graphics (depth, parallax, CSS-3D tilt in
> the HTML). They are not a real-time 3D engine render.
