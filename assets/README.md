# AEGIS PRO brand assets

- `logo.svg` / `logo.png`: horizontal system logo, editable vector source and raster export.
- `app-icon.svg` / `app-icon.png`: square application icon.
- `splash-screen.svg` / `splash-screen.png`: 1080×1920 vertical launch screen.
- Colors: deep navy `#06101F`, cyan `#39DDFE`, blue `#146AFF`, silver `#E8F7FF`.

SVG files are the canonical, editable assets. PNG files are convenient for desktop/mobile packaging. The splash is a static design asset; native launch-screen integration is platform-specific and is not installed by this Python CLI package.
- `app-icon-192.png`, `app-icon-512.png`: PWA-style icon sizes.
- `app-icon-foreground.svg` / `.png`: transparent Android adaptive-icon foreground, to be paired with a dark navy background in native app packaging.
- `app-icon.ico`: Windows desktop icon; `favicon-32.png`: browser favicon.
