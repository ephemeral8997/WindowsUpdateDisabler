import tkinter as tk
from tkinter import messagebox
import winreg
import subprocess
import os
import sys


class WindowsUpdateDisabler:
    REGISTRY_PATH = r"SYSTEM\CurrentControlSet\Services\wuauserv"
    VALUE_NAME = "ImagePath"
    SERVICE_NAME = "wuauserv"
    ENABLED_HOST = "svchost.exe"
    DISABLED_HOST = "svchost0.exe"

    COLORS = {
        "bg": "#f0f0f0",
        "white": "white",
        "primary": "#0067C0",
        "primary_active": "#005a9e",
        "success": "#107C10",
        "success_active": "#0e6b0e",
        "danger": "#D13438",
        "danger_active": "#b02b2f",
        "text_bg": "white",
        "enabled_text": "#107C10",
        "disabled_text": "#D13438",
        "warning_text": "#ca5010",
    }

    STATUS_CONFIG = {
        "enabled": {
            "text": "Windows Update is enabled",
            "indicator": "✓",
            "button_text": "Disable Windows Update",
        },
        "disabled": {
            "text": "Windows Update is disabled",
            "indicator": "✕",
            "button_text": "Enable Windows Update",
        },
    }

    def __init__(self, root):
        self.root = root
        self._setup_window()
        self.create_widgets()
        self.update_status()

    def _setup_window(self):
        self.root.title("Windows Update Controller")
        self.root.geometry("420x200")
        self.root.resizable(False, False)
        self.root.configure(bg=self.COLORS["bg"])
        try:
            self.root.iconbitmap(default="")
        except:
            pass

    def create_widgets(self):
        main_container = tk.Frame(self.root, bg=self.COLORS["bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(
            main_container,
            text="Windows Update Service Controller",
            font=("Segoe UI", 14),
            bg=self.COLORS["bg"],
            fg="black",
        ).pack(pady=(10, 20))

        status_frame = tk.Frame(
            main_container, bg=self.COLORS["white"], relief=tk.SOLID, borderwidth=1
        )
        status_frame.pack(fill=tk.X, pady=(0, 15), padx=20)

        status_container = tk.Frame(status_frame, bg=self.COLORS["white"])
        status_container.pack(fill=tk.X, padx=15, pady=12)

        self.status_label = tk.Label(
            status_container,
            text="Checking status...",
            font=("Segoe UI", 11),
            bg=self.COLORS["white"],
            fg="black",
        )
        self.status_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.status_indicator = tk.Label(
            status_container, text="⚪", font=("Segoe UI", 16), bg=self.COLORS["white"]
        )
        self.status_indicator.pack(side=tk.RIGHT)

        self.action_button = tk.Button(
            main_container,
            text="Loading...",
            command=self.toggle_service,
            font=("Segoe UI", 11),
            bg=self.COLORS["primary"],
            fg="white",
            activebackground=self.COLORS["primary_active"],
            activeforeground="white",
            relief=tk.FLAT,
            borderwidth=0,
            height=2,
            cursor="hand2",
        )
        self.action_button.pack(pady=10, padx=20, fill=tk.X)

    def get_image_path(self):
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, self.REGISTRY_PATH, 0, winreg.KEY_READ
            ) as key:
                image_path, _ = winreg.QueryValueEx(key, self.VALUE_NAME)
                return image_path
        except Exception:
            return None

    def is_service_enabled(self, image_path):
        if not image_path:
            return False
        return self.ENABLED_HOST in image_path and self.DISABLED_HOST not in image_path

    def update_status(self):
        image_path = self.get_image_path()

        if not image_path:
            self.status_label.config(
                text="⚠️ Cannot read registry", fg=self.COLORS["warning_text"]
            )
            self.status_indicator.config(text="⚠️")
            self.action_button.config(
                text="Run as Administrator Required",
                bg="#cccccc",
                state=tk.DISABLED,
                relief=tk.FLAT,
            )
            return

        enabled = self.is_service_enabled(image_path)
        state = "enabled" if enabled else "disabled"
        config = self.STATUS_CONFIG[state]

        self.status_label.config(text=config["text"], fg=self.COLORS[f"{state}_text"])
        self.status_indicator.config(text=config["indicator"])

        color_key = "danger" if enabled else "success"
        self.action_button.config(
            text=config["button_text"],
            bg=self.COLORS[color_key],
            activebackground=self.COLORS[f"{color_key}_active"],
            state=tk.NORMAL,
            relief=tk.RAISED,
        )

    def toggle_service(self):
        image_path = self.get_image_path()

        if not image_path:
            messagebox.showerror("Error", "Could not read current ImagePath value")
            return

        try:
            self._perform_toggle(image_path)
        except PermissionError:
            messagebox.showerror(
                "Permission Error",
                "Permission denied!\n\nPlease run this application as Administrator.",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to modify registry:\n{str(e)}")

    def _perform_toggle(self, image_path):
        enabled = self.is_service_enabled(image_path)
        new_path, action = self._get_toggle_params(image_path, enabled)

        confirm_msg = (
            "Are you sure you want to DISABLE Windows Update?\n\n"
            "This will prevent both automatic AND manual Windows updates.\n\n"
            "Note: Some apps like Microsoft Store use the Windows Update service.\n"
            "You may need to re-enable it temporarily when installing apps from the Store."
            if enabled
            else "Are you sure you want to ENABLE Windows Update?\n\n"
            "This will restore both automatic and manual Windows updates."
        )

        if not messagebox.askyesno("Confirm Action", confirm_msg):
            return

        self._update_registry(new_path)
        self.update_status()

        try:
            self._control_service("stop" if enabled else "start")
        except:
            pass

        if enabled:
            self._create_persistence_task()
        else:
            self._remove_persistence_task()

        messagebox.showinfo(
            "Success",
            f"Windows Update service has been {action}d.\n\n"
            f"{'Persistence enabled' if enabled else 'Persistence disabled'}.\n"
            "Changes take effect immediately.",
        )

    def _get_toggle_params(self, image_path, enabled):
        if enabled:
            return image_path.replace(self.ENABLED_HOST, self.DISABLED_HOST), "disable"
        else:
            return image_path.replace(self.DISABLED_HOST, self.ENABLED_HOST), "enable"

    def _update_registry(self, new_path):
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, self.REGISTRY_PATH, 0, winreg.KEY_WRITE
        ) as key:
            winreg.SetValueEx(key, self.VALUE_NAME, 0, winreg.REG_EXPAND_SZ, new_path)

    def _control_service(self, action):
        cmd = ["net", action, self.SERVICE_NAME]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if (
            result.returncode != 0
            and "The requested service has already been" not in result.stderr
        ):
            raise RuntimeError(
                result.stderr.strip() or f"Command failed with code {result.returncode}"
            )

    def _create_persistence_task(self):
        if getattr(sys, "frozen", False):
            xml_template_path = os.path.join(sys._MEIPASS, "PersistWUADisable.xml")
        else:
            xml_template_path = os.path.abspath("PersistWUADisable.xml")

        if not os.path.isfile(xml_template_path):
            return

        exe_path = os.path.abspath(sys.executable).replace("\\", "\\\\")
        author = (
            os.environ.get("USERDOMAIN", "") + "\\" + os.environ.get("USERNAME", "")
        )
        description = "Reapplies Windows Update disable state on system startup"

        try:
            with open(xml_template_path, "r", encoding="utf-16") as f:
                content = f.read()
        except Exception:
            return

        content = content.replace("{AUTHOR}", author)
        content = content.replace("{DESCRIPTION}", description)
        content = content.replace("{EXECUTABLE_PATH}", exe_path)

        import tempfile

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-16", delete=False, suffix=".xml"
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
        except Exception:
            return

        try:
            subprocess.run(
                [
                    "schtasks",
                    "/create",
                    "/tn",
                    "PersistWUADisable",
                    "/xml",
                    tmp_path,
                    "/f",
                ],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                timeout=15,
            )
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _remove_persistence_task(self):
        subprocess.run(
            ["schtasks", "/delete", "/tn", "PersistWUADisable", "/f"],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        )

    def _reapply_disable_if_needed(self):
        image_path = self.get_image_path()
        if image_path and self.is_service_enabled(image_path):
            new_path = image_path.replace(self.ENABLED_HOST, self.DISABLED_HOST)
            self._update_registry(new_path)
            try:
                self._control_service("stop")
            except:
                pass


def main():
    if "--reapply-disable" in sys.argv:
        disabler = WindowsUpdateDisabler.__new__(WindowsUpdateDisabler)
        disabler._reapply_disable_if_needed()
        return

    root = tk.Tk()
    app = WindowsUpdateDisabler(root)
    root.mainloop()


if __name__ == "__main__":
    main()
