"""Local UI preview using disposable data and simulated network operations.

Run from the repository root: python tools/preview.py
This never starts the production expiry worker or configures the host firewall.
"""
import importlib.util
import os
from pathlib import Path
import tempfile
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
PREVIEW_PASSWORD = "wipay-preview"


def create_preview():
    os.environ.setdefault("ADMIN_SECRET", PREVIEW_PASSWORD)
    spec = importlib.util.spec_from_file_location("wipay_preview", ROOT / "Project-files/app4.py")
    portal = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(portal)
    # Retain the TemporaryDirectory until the server/test is shut down.
    portal.preview_directory = tempfile.TemporaryDirectory(prefix="wipay-preview-")
    portal.DB = str(Path(portal.preview_directory.name) / "portal.db")
    portal.is_iptables_allowed = lambda ip: False
    portal.get_mac_for_ip = lambda ip: "02:00:00:00:00:99"
    portal.get_dnsmasq_leases = lambda: {}
    portal.add_iptables_allow = lambda *args, **kwargs: None
    portal.remove_iptables_allow = lambda *args, **kwargs: None
    portal.set_speed_limit = lambda *args, **kwargs: None
    portal.remove_speed_limit = lambda *args, **kwargs: None
    portal.get_system_health = lambda: dict(
        cpu_percent=18, ram_percent=34, ram_used_mb=348, ram_total_mb=1024,
        cpu_temp=46, upstream_ok=True, upstream_latency=12, portal_ok=True,
        eth0_up=True, eth0_ip="192.168.50.1", wan_iface="wlan0",
        wan_rx_mbps=24.8, wan_tx_mbps=6.4, wan_rx_mb=3420, wan_tx_mb=640,
        wan_total_gb=3.965, lan_rx_mb=3420, lan_tx_mb=640,
        load_1="0.18", load_5="0.24", load_15="0.21", uptime="12h 24m", uptime_secs=44640,
    )
    portal.init_db()
    now = datetime.utcnow()
    db = portal.get_db()
    db.execute("UPDATE settings SET value=? WHERE key='portal_title'", ("Good WiFi starts here.",))
    db.execute("UPDATE settings SET value=? WHERE key='portal_subtitle'",
               ("Enter your voucher to get online, or choose a plan and request access below.",))
    for i, (name, minutes, speed) in enumerate([
        ("Mika’s phone", 60, 10), ("Guest laptop", 180, 10), ("Front desk", 1440, 20)
    ], 1):
        ip = f"192.168.50.{20+i}"
        db.execute("INSERT INTO devices (mac,name,ip,first_seen,last_seen,connected) VALUES (?,?,?,?,?,1)",
                   (f"02:00:00:00:00:{i:02d}", name, ip, now.isoformat(), now.isoformat()))
        db.execute("INSERT INTO codes (code,duration_minutes,created_at,used_by,used_at,expires_at,speed_mbps) VALUES (?,?,?,?,?,?,?)",
                   (f"DEMO-{i:04d}", minutes, now.isoformat(), ip, now.isoformat(),
                    (now+timedelta(minutes=minutes)).isoformat(), speed))
    db.execute("INSERT INTO codes (code,duration_minutes,created_at,speed_mbps) VALUES ('WIFI-2026',120,?,10)", (now.isoformat(),))
    db.execute("INSERT INTO lobby_requests (ip,mac,device_name,plan_name,plan_minutes,plan_speed,plan_label,requested_at) VALUES (?,?,?,?,?,?,?,?)",
               ("192.168.50.42", "02:00:00:00:00:42", "Guest phone", "1 Hour", 60, 10, "₱20", now.isoformat()))
    db.commit()
    db.close()
    return portal


if __name__ == "__main__":
    portal = create_preview()
    print("WiPay UI preview: http://127.0.0.1:8090/portal", flush=True)
    print("Admin: /admin — password is ADMIN_SECRET or wipay-preview", flush=True)
    portal.app.run(host="127.0.0.1", port=8090, debug=False, threaded=True)
