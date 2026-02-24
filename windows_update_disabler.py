import tkinter as tk
from tkinter import messagebox
import winreg
import subprocess
import os
import sys
import tempfile
import shutil


class WindowsUpdateDisabler:
    REGISTRY_PATH = r"SYSTEM\CurrentControlSet\Services\wuauserv"
    VALUE_NAME = "ImagePath"
    SERVICE_NAME = "wuauserv"
    TASK_NAME = "PersistWUADisable"
    ENABLED_HOST, DISABLED_HOST = "svchost.exe", "svchost0.exe"

    COLORS = {
        "bg": "#f0f0f0",
        "white": "white",
        "primary": "#0067C0",
        "primary_active": "#005a9e",
        "success": "#107C10",
        "success_active": "#0e6b0e",
        "danger": "#D13438",
        "danger_active": "#b02b2f",
        "enabled_text": "#107C10",
        "disabled_text": "#D13438",
        "warning_text": "#ca5010",
    }

    STATUS_CONFIG = {
        True: {
            "text": "Windows Update is enabled",
            "indicator": "✓",
            "btn": "Disable Windows Update",
            "color": "danger",
        },
        False: {
            "text": "Windows Update is disabled",
            "indicator": "✕",
            "btn": "Enable Windows Update",
            "color": "success",
        },
    }

    def __init__(self, root=None):
        self.root = root
        if root:
            self._setup_window()
            self.create_widgets()
            self.update_status()

    def _setup_window(self):
        if not self.root:
            return
        self.root.title("Windows Update Controller")
        self.root.geometry("420x200")
        self.root.resizable(False, False)
        self.root.configure(bg=self.COLORS["bg"])

    def create_widgets(self):
        main = tk.Frame(self.root, bg=self.COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(
            main,
            text="Windows Update Service Controller",
            font=("Segoe UI", 14),
            bg=self.COLORS["bg"],
        ).pack(pady=(10, 20))

        status_frame = tk.Frame(
            main, bg=self.COLORS["white"], relief=tk.SOLID, borderwidth=1
        )
        status_frame.pack(fill=tk.X, pady=(0, 15), padx=20)

        self.status_label = tk.Label(
            status_frame,
            text="Checking...",
            font=("Segoe UI", 11),
            bg=self.COLORS["white"],
        )
        self.status_label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=15, pady=12)

        self.status_indicator = tk.Label(
            status_frame, text="⚪", font=("Segoe UI", 16), bg=self.COLORS["white"]
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        self.action_button = tk.Button(
            main,
            text="Loading...",
            command=self.toggle_service,
            font=("Segoe UI", 11),
            fg="white",
            relief=tk.FLAT,
            height=2,
            cursor="hand2",
        )
        self.action_button.pack(pady=10, padx=20, fill=tk.X)

    def _run_cmd(self, cmd, silent=True):
        flags = subprocess.CREATE_NO_WINDOW
        if silent:
            flags |= subprocess.DETACHED_PROCESS
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=15, creationflags=flags
            )
        except Exception:
            return None

    def _reset_components(self):
        """Resets Windows Update folders to clear cache and corruption."""
        # stop related services first to unlock files
        services = ["wuauserv", "bits", "cryptsvc", "msiserver"]
        for svc in services:
            self._run_cmd(["net", "stop", svc])

        windir = os.environ.get("WINDIR", "C:\\Windows")
        paths = [
            os.path.join(windir, "SoftwareDistribution"),
            os.path.join(windir, "System32", "catroot2"),
        ]

        for path in paths:
            if os.path.exists(path):
                try:
                    # Rename is safer/more reliable than immediate deletion while script runs
                    shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass

    def _get_registry_value(self):
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, self.REGISTRY_PATH, 0, winreg.KEY_READ
            ) as key:
                return winreg.QueryValueEx(key, self.VALUE_NAME)[0]
        except Exception:
            return None

    def update_status(self):
        path = self._get_registry_value()
        if not path:
            self.status_label.config(
                text="⚠️ Run as Administrator Required", fg=self.COLORS["warning_text"]
            )
            self.action_button.config(state=tk.DISABLED, bg="#cccccc")
            return

        is_enabled = self.ENABLED_HOST in path and self.DISABLED_HOST not in path
        cfg = self.STATUS_CONFIG[is_enabled]
        state_key = "enabled" if is_enabled else "disabled"

        self.status_label.config(text=cfg["text"], fg=self.COLORS[f"{state_key}_text"])
        self.status_indicator.config(text=cfg["indicator"])
        self.action_button.config(
            text=cfg["btn"],
            bg=self.COLORS[cfg["color"]],
            activebackground=self.COLORS[f"{cfg['color']}_active"],
            state=tk.NORMAL,
        )

    def toggle_service(self):
        path = self._get_registry_value()
        if not path:
            return

        is_enabled = self.ENABLED_HOST in path and self.DISABLED_HOST not in path
        new_path = (
            path.replace(self.ENABLED_HOST, self.DISABLED_HOST)
            if is_enabled
            else path.replace(self.DISABLED_HOST, self.ENABLED_HOST)
        )

        msg = (
            "DISABLE Windows Update?\n\nThis affects Microsoft Store."
            if is_enabled
            else "ENABLE and RESET Windows Update?\n\nThis will clear the update cache and restore services."
        )

        if not messagebox.askyesno("Confirm", msg):
            return

        try:
            if not is_enabled:
                self._reset_components()

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, self.REGISTRY_PATH, 0, winreg.KEY_WRITE
            ) as key:
                winreg.SetValueEx(
                    key, self.VALUE_NAME, 0, winreg.REG_EXPAND_SZ, new_path
                )

            # Start/Stop Service
            self._run_cmd(["net", "stop" if is_enabled else "start", self.SERVICE_NAME])

            self._manage_persistence(is_enabled)
            self.update_status()
            messagebox.showinfo(
                "Success",
                f"Service {'disabled' if is_enabled else 'enabled and reset'}.",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _manage_persistence(self, enable_task):
        if not enable_task:
            self._run_cmd(["schtasks", "/delete", "/tn", self.TASK_NAME, "/f"])
            return

        base_path = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
        xml_path = os.path.join(base_path, "PersistWUADisable.xml")
        if not os.path.exists(xml_path):
            return

        with open(xml_path, "r", encoding="utf-16") as f:
            content = (
                f.read()
                .replace("{AUTHOR}", os.environ.get("USERNAME", "System"))
                .replace("{DESCRIPTION}", "Maintains WU disable state")
                .replace("{EXECUTABLE_PATH}", f'"{sys.executable}"')
            )

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-16", delete=False, suffix=".xml"
        ) as tmp:
            tmp.write(content)
            tmp_name = tmp.name

        try:
            self._run_cmd(
                ["schtasks", "/create", "/tn", self.TASK_NAME, "/xml", tmp_name, "/f"]
            )
        finally:
            os.unlink(tmp_name)

    def headless_reapply(self):
        path = self._get_registry_value()
        if path and self.ENABLED_HOST in path and self.DISABLED_HOST not in path:
            new_path = path.replace(self.ENABLED_HOST, self.DISABLED_HOST)
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, self.REGISTRY_PATH, 0, winreg.KEY_WRITE
            ) as key:
                winreg.SetValueEx(
                    key, self.VALUE_NAME, 0, winreg.REG_EXPAND_SZ, new_path
                )
            self._run_cmd(["net", "stop", self.SERVICE_NAME])


def main():
    if "--reapply-disable" in sys.argv:
        WindowsUpdateDisabler().headless_reapply()
    else:
        root = tk.Tk()
        WindowsUpdateDisabler(root)
        root.mainloop()


if __name__ == "__main__":
    main()
