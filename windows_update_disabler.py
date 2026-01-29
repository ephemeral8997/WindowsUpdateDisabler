import tkinter as tk
from tkinter import messagebox
import winreg
import os


class WindowsUpdateDisabler:
    # Constants
    REGISTRY_PATH = r"SYSTEM\CurrentControlSet\Services\wuauserv"
    VALUE_NAME = "ImagePath"
    ENABLED_HOST = "svchost.exe"
    DISABLED_HOST = "svchost0.exe"

    # UI Constants
    COLORS = {
        "bg": "white",
        "primary": "#0078d4",
        "primary_active": "#005a9e",
        "success": "#28a745",
        "success_active": "#218838",
        "danger": "#dc3545",
        "danger_active": "#c82333",
        "neutral": "#f0f0f0",
        "neutral_active": "#e0e0e0",
        "disabled": "#6c757d",
        "text_bg": "#f8f8f8",
        "enabled_text": "#00aa00",
        "disabled_text": "#cc0000",
        "warning_text": "#ff6600",
    }

    def __init__(self, root):
        self.root = root
        self._setup_window()
        self.create_widgets()
        self.update_status()

    def _setup_window(self):
        self.root.title("Windows Update Controller")
        self.root.geometry("450x320")
        self.root.resizable(False, False)
        try:
            self.root.iconbitmap(default="")
        except:
            pass

    def create_widgets(self):
        main_container = tk.Frame(self.root, bg=self.COLORS["bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._create_title(main_container)
        self._create_status_frame(main_container)
        self._create_path_frame(main_container)
        self._create_action_buttons(main_container)

    def _create_title(self, parent):
        tk.Label(
            parent,
            text="Windows Update Service Controller",
            font=("Segoe UI", 16, "bold"),
            bg=self.COLORS["bg"],
            fg=self.COLORS["primary"],
        ).pack(pady=(0, 20))

    def _create_status_frame(self, parent):
        status_frame = self._create_label_frame(parent, "Current Status")
        status_frame.pack(fill=tk.X, pady=(0, 15))

        status_container = tk.Frame(status_frame, bg=self.COLORS["bg"])
        status_container.pack(fill=tk.X, padx=10, pady=10)

        self.status_label = tk.Label(
            status_container,
            text="Checking status...",
            font=("Segoe UI", 12),
            bg=self.COLORS["bg"],
            fg="black",
        )
        self.status_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.status_indicator = tk.Label(
            status_container, text="⚪", font=("Segoe UI", 20), bg=self.COLORS["bg"]
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=(10, 0))

    def _create_path_frame(self, parent):
        path_frame = self._create_label_frame(parent, "Registry ImagePath Value")
        path_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.path_text = tk.Text(
            path_frame,
            height=4,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.COLORS["text_bg"],
            fg="black",
            relief=tk.SUNKEN,
            borderwidth=1,
        )
        self.path_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _create_action_buttons(self, parent):
        self.action_button = self._create_button(
            parent,
            text="Loading...",
            command=self.toggle_service,
            font=("Segoe UI", 12, "bold"),
            bg=self.COLORS["primary"],
            active_bg=self.COLORS["primary_active"],
            height=2,
            width=20,
        )
        self.action_button.pack(pady=(10, 8), fill=tk.X)

        self._create_button(
            parent,
            text="🔄 Refresh Status",
            command=self.update_status,
            font=("Segoe UI", 10),
            bg=self.COLORS["neutral"],
            active_bg=self.COLORS["neutral_active"],
            height=1,
            width=15,
        ).pack()

    def _create_label_frame(self, parent, text):
        return tk.LabelFrame(
            parent,
            text=text,
            font=("Segoe UI", 11, "bold"),
            bg=self.COLORS["bg"],
            fg="black",
            relief=tk.GROOVE,
            borderwidth=2,
        )

    def _create_button(self, parent, text, command, font, bg, active_bg, height, width):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=font,
            bg=bg,
            fg="white",
            activebackground=active_bg,
            activeforeground="white",
            relief=tk.RAISED,
            borderwidth=2 if height > 1 else 1,
            height=height,
            width=width,
            cursor="hand2",
        )

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

        if enabled:
            self._set_status(
                "✅ Windows Update: ENABLED", self.COLORS["enabled_text"], "🟢"
            )
            self._set_action_button(
                "🚫 Disable Windows Update",
                self.COLORS["danger"],
                self.COLORS["danger_active"],
            )
        else:
            self._set_status(
                "❌ Windows Update: DISABLED", self.COLORS["disabled_text"], "🔴"
            )
            self._set_action_button(
                "✅ Enable Windows Update",
                self.COLORS["success"],
                self.COLORS["success_active"],
            )

        self._update_path_display(image_path.strip())

    def _update_status_error(self):
        self._set_status(
            "⚠️ Status: Cannot read registry", self.COLORS["warning_text"], "⚠️"
        )
        self.action_button.config(
            text="❌ Registry Access Error",
            bg=self.COLORS["disabled"],
            state=tk.DISABLED,
            relief=tk.FLAT,
        )
        self._update_path_display(
            "Failed to read registry value.\nRun as Administrator?"
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

    def _update_path_display(self, text):
        self.path_text.delete(1.0, tk.END)
        self.path_text.insert(1.0, text)

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
            f"Are you sure you want to {action.upper()} Windows Update?\n\n"
            f"This will {'prevent' if enabled else 'restore'} automatic Windows updates."
        )

        if messagebox.askyesno("Confirm Action", confirm_msg):
            self._update_registry(new_path)
            messagebox.showinfo(
                "Success",
                f"Windows Update service has been {action}d.\n\n"
                "You may need to restart the service or your computer for changes to take effect.",
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
