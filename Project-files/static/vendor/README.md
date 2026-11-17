# Bundled browser libraries

These upstream distributions are served locally so the portal and dashboard do
not need internet access to download their scripts. WiPay's theme, icon and fonts
also work without external requests.

| Library | Version | Source | License |
|---|---|---|---|
| Chart.js | 4.4.9 | https://github.com/chartjs/Chart.js | MIT, see `Chart.js-LICENSE.md` |
| jsQR | 1.4.0 | https://github.com/cozmo/jsQR | Apache-2.0, see `jsQR-LICENSE` |

The distribution files are unmodified. To update a library, download its versioned
distribution from upstream, retain its license and run `python tools/check_ui.py`.
