import tkinter as tk
from tkinter import messagebox
import winreg


class WindowsUpdateDisabler:
    # Constants
    REGISTRY_PATH = r"SYSTEM\CurrentControlSet\Services\wuauserv"
    VALUE_NAME = "ImagePath"
    ENABLED_HOST = "svchost.exe"
    DISABLED_HOST = "svchost0.exe"

    # UI Constants
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

        self._create_title(main_container)
        self._create_status_frame(main_container)
        self._create_action_buttons(main_container)

    def _create_title(self, parent):
        tk.Label(
            parent,
            text="Windows Update Service Controller",
            font=("Segoe UI", 14),
            bg=self.COLORS["bg"],
            fg="black",
        ).pack(pady=(10, 20))

    def _create_status_frame(self, parent):
        status_frame = tk.Frame(
            parent, bg=self.COLORS["white"], relief=tk.SOLID, borderwidth=1
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

    def _create_action_buttons(self, parent):
        self.action_button = tk.Button(
            parent,
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

        if image_path:
            self._update_status_with_path(image_path)
        else:
            self._update_status_error()

    def _update_status_with_path(self, image_path):
        enabled = self.is_service_enabled(image_path)
        state = "enabled" if enabled else "disabled"
        config = self.STATUS_CONFIG[state]

        self._set_status(
            config["text"], self.COLORS[f"{state}_text"], config["indicator"]
        )

        color_key = "danger" if enabled else "success"
        self._set_action_button(
            config["button_text"],
            self.COLORS[color_key],
            self.COLORS[f"{color_key}_active"],
        )

    def _update_status_error(self):
        self._set_status("⚠️ Cannot read registry", self.COLORS["warning_text"], "⚠️")
        self.action_button.config(
            text="Run as Administrator Required",
            bg="#cccccc",
            state=tk.DISABLED,
            relief=tk.FLAT,
        )

    def _set_status(self, text, color, indicator):
        self.status_label.config(text=text, fg=color)
        self.status_indicator.config(text=indicator)

    def _set_action_button(self, text, bg, active_bg):
        self.action_button.config(
            text=text,
            bg=bg,
            activebackground=active_bg,
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

        if enabled:
            confirm_msg = (
                "Are you sure you want to DISABLE Windows Update?\n\n"
                "This will prevent both automatic AND manual Windows updates.\n\n"
                "Note: Some apps like Microsoft Store use the Windows Update service.\n"
                "You may need to re-enable it temporarily when installing apps from the Store."
            )
        else:
            confirm_msg = (
                "Are you sure you want to ENABLE Windows Update?\n\n"
                "This will restore both automatic and manual Windows updates."
            )

        if messagebox.askyesno("Confirm Action", confirm_msg):
            self._update_registry(new_path)
            messagebox.showinfo(
                "Success",
                f"Windows Update service has been {action}d.\n\nChanges take effect immediately.",
            )
            self.update_status()

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


def main():
    root = tk.Tk()
    app = WindowsUpdateDisabler(root)
    root.mainloop()


if __name__ == "__main__":
    main()
