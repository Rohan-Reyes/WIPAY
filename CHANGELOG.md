# Changelog

## 1.1.0 — 2026-11-17

- Introduce a shared forest and lime theme, WiPay icon, clearer typography and
  responsive cards across the portal, session status, admin sign in and dashboard.
- Add dashboard shortcuts for vouchers, sessions and lobby requests.
- Make plan cards and admin navigation native buttons, add keyboard tab controls,
  visible focus, a skip link, reduced motion support and an accessible mobile drawer.
- Choosing a portal plan now opens and fills the access request form. Returning
  customers see their request confirmation without opening the Request tab again.
- Bundle Chart.js and jsQR locally and remove the sign in page's external font
  import, allowing UI assets to load before internet access is granted.
- Fix a countdown bug that could redirect long sessions at an exact hour boundary
  or incorrectly mark them as nearly expired.
- Refresh the README with real sample screenshots, installation and update steps,
  dependency manifests, and a disposable local preview/browser check.
- Correct the setup guide's repository URL and admin port, and document deployment
  of the new static directory. Existing database schema and network defaults stay
  compatible with 1.0.0.

## 1.0.0

Initial published release (GitHub tag `new`).
