# YouTube acquisition setup and sign-in failures

The reported failure contains two independent conditions: no supported JavaScript
runtime, then YouTube asking for sign-in/bot verification. The notebook now updates
yt-dlp's default dependencies, checks Deno >=2.3 or Node >=22, and installs the
official Linux Deno release if neither is available. The installer verifies the
release asset SHA-256 digest. JS runtime options are passed explicitly to both
channel listing and video download. Setup follows yt-dlp's
[EJS documentation](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

This fixes the missing-runtime setup; it does not guarantee that YouTube accepts
requests from a Colab/Kaggle runtime. The downloader reports sign-in requirements
without automated proxy/account rotation or repeated attempts. Stop and inspect
the message rather than repeatedly running the failed download cell.

If using your own authorized YouTube session, optionally place a Netscape-format
cookie file in the private cloud runtime and set COOKIE_FILE to that path. Keep it
outside WORK_ROOT, for example /content/youtube_cookies.txt. Do not paste its
contents into chat/notebook cells or commit it. Cookies are credentials, and they
may not resolve a cloud-origin block. See yt-dlp's
[cookie FAQ](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)
and [YouTube notes](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies).
COOKIE_FILE stays None by default; there is no automatic browser-cookie extraction.
The exporter skips cookie-named files and .env, and acquisition rejects cookies
inside WORK_ROOT. Cookie paths/content are not stored in job identity.

Completed cloud downloads can now be reused before any YouTube request. They need
matching video.info.json and a video whose duration passes ffprobe validation.
Set WORK_ROOT to the same persistent cloud directory on later runs to retain this
cache. Partial/mismatched downloads do not qualify. This is reuse of your prior
file, not another method of fetching a blocked video. Source URLs and checksums
remain attached to processing results.

Open the latest GitHub notebook, restart the runtime, enable T4 and run setup from
the beginning. It should print the selected JS runtime before processing. If the
sign-in error remains, access is still blocked; no successful cloud download is
claimed by this patch. The pipeline's OCR/GPU/filter code is unchanged.
