# Demo Video Storyboard

Output: `docs/demo/representative-location-explorer-demo.webm`

This is a private, captioned product-demo trailer for the Representative Location
Explorer. It is designed for short academic collaborator demos and private pull-request
review.

## Final Export

- Format: WebM, VP9
- Resolution: 1280 x 720
- File size: 14,614,758 bytes
- SHA-256: `b896018517038cd9308bcd7c36499d34f7889de77b0a063c309e7302d6b5bfe4`
- Audio: none; all narration is on-screen so the clip works in silent meetings.

## Sequence

1. Title card: transparent, reproducible location selection.
2. Overview dashboard: 20 strata, candidate count, verified filters, station context.
3. ZIP code explorer: leading-zero ZIP handling and geography-resolution narrative.
4. Scenario builder: density screen, score weights, uniqueness, weather rules, overrides.
5. Candidate ranking: inspect, sort, compare, and export scored candidates.
6. Allocation comparison: independent top-ranked selections versus distinct catchments.
7. Methodology and sources: academic appendix, ResStock rules, limitations, QC.
8. Closing card: private, deterministic, export-ready research handoff.

## Production Notes

- No public hosting or external upload is performed.
- The video is generated from local app screenshots captured at `http://127.0.0.1:8787`.
- The browser-native renderer is `docs/demo/render_demo_video.html`.
- The video is silent by design and uses on-screen captions so it can be shared in
  meetings without audio issues.
- Regenerate by serving the repository locally and opening the renderer in a modern
  Chromium browser:

```bash
python3 -m http.server 8877 --bind 127.0.0.1
open http://127.0.0.1:8877/docs/demo/render_demo_video.html
```

The renderer includes a hidden DOM handoff field used by Codex/browser automation to
save the generated WebM without publishing or uploading the video.
