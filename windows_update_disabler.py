import tkinter as tk
from tkinter import messagebox
import winreg
import os


class WindowsUpdateDisabler:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows Update Controller")
        self.root.geometry("450x320")
        self.root.resizable(False, False)

        try:
            self.root.iconbitmap(default="")
        except:
            pass

        self.registry_path = r"SYSTEM\CurrentControlSet\Services\wuauserv"
        self.value_name = "ImagePath"

        self.create_widgets()

        self.update_status()

    def create_widgets(self):
        main_container = tk.Frame(self.root, bg="white")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = tk.Label(
            main_container,
            text="Windows Update Service Controller",
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg="#0066cc",
        )
        title_label.pack(pady=(0, 20))

        status_frame = tk.LabelFrame(
            main_container,
            text="Current Status",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="black",
            relief=tk.GROOVE,
            borderwidth=2,
        )
        status_frame.pack(fill=tk.X, pady=(0, 15))

        status_container = tk.Frame(status_frame, bg="white")
        status_container.pack(fill=tk.X, padx=10, pady=10)

        self.status_label = tk.Label(
            status_container,
            text="Checking status...",
            font=("Segoe UI", 12),
            bg="white",
            fg="black",
        )
        self.status_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.status_indicator = tk.Label(
            status_container, text="⚪", font=("Segoe UI", 20), bg="white"
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=(10, 0))

        path_frame = tk.LabelFrame(
            main_container,
            text="Registry ImagePath Value",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="black",
            relief=tk.GROOVE,
            borderwidth=2,
        )
        path_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.path_text = tk.Text(
            path_frame,
            height=4,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#f8f8f8",
            fg="black",
            relief=tk.SUNKEN,
            borderwidth=1,
        )
        self.path_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.action_button = tk.Button(
            main_container,
            text="Loading...",
            command=self.toggle_service,
            font=("Segoe UI", 12, "bold"),
            bg="#0078d4",  # Windows blue
            fg="white",
            activebackground="#005a9e",
            activeforeground="white",
            relief=tk.RAISED,
            borderwidth=2,
            height=2,
            width=20,
            cursor="hand2",
        )
        self.action_button.pack(pady=(10, 8), fill=tk.X)

        refresh_button = tk.Button(
            main_container,
            text="🔄 Refresh Status",
            command=self.update_status,
            font=("Segoe UI", 10),
            bg="#f0f0f0",
            fg="black",
            activebackground="#e0e0e0",
            activeforeground="black",
            relief=tk.RAISED,
            borderwidth=1,
            height=1,
            width=15,
            cursor="hand2",
        )
        refresh_button.pack()

    def get_image_path(self):
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, self.registry_path, 0, winreg.KEY_READ
            ) as key:
                image_path, _ = winreg.QueryValueEx(key, self.value_name)
                return image_path
        except Exception as e:
            return None

    def is_service_enabled(self, image_path):
        if not image_path:
            return False

        return "svchost.exe" in image_path and "svchost0.exe" not in image_path

    def update_status(self):
        image_path = self.get_image_path()

        if image_path:
            enabled = self.is_service_enabled(image_path)

            if enabled:
                status_text = "✅ Windows Update: ENABLED"
                self.status_label.config(text=status_text, fg="#00aa00")
                self.status_indicator.config(text="🟢")
                self.action_button.config(
                    text="🚫 Disable Windows Update",
                    bg="#dc3545",  # Red for disable
                    activebackground="#c82333",
                )
            else:
                status_text = "❌ Windows Update: DISABLED"
                self.status_label.config(text=status_text, fg="#cc0000")
                self.status_indicator.config(text="🔴")
                self.action_button.config(
                    text="✅ Enable Windows Update",
                    bg="#28a745",  # Green for enable
                    activeforeground="white",
                    activebackground="#218838",
                )

            # update ImagePath display
            self.path_text.delete(1.0, tk.END)
            self.path_text.insert(1.0, image_path.strip())
        else:
            self.status_label.config(
                text="⚠️ Status: Cannot read registry", fg="#ff6600"
            )
            self.status_indicator.config(text="⚠️")
            self.action_button.config(
                text="❌ Registry Access Error",
                bg="#6c757d",
                state=tk.DISABLED,
                relief=tk.FLAT,
            )
            self.path_text.delete(1.0, tk.END)
            self.path_text.insert(
                1.0, "Failed to read registry value.\nRun as Administrator?"
            )

    def toggle_service(self):
        image_path = self.get_image_path()

        if not image_path:
            messagebox.showerror("Error", "Could not read current ImagePath value")
            return

        try:
            if self.is_service_enabled(image_path):
                new_path = image_path.replace("svchost.exe", "svchost0.exe")
                action = "disable"
                confirm_msg = "Are you sure you want to DISABLE Windows Update?\n\nThis will prevent automatic Windows updates."
            else:
                new_path = image_path.replace("svchost0.exe", "svchost.exe")
                action = "enable"
                confirm_msg = "Are you sure you want to ENABLE Windows Update?\n\nThis will restore automatic Windows updates."

            if messagebox.askyesno("Confirm Action", confirm_msg):
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE, self.registry_path, 0, winreg.KEY_WRITE
                ) as key:
                    winreg.SetValueEx(
                        key, self.value_name, 0, winreg.REG_EXPAND_SZ, new_path
                    )

                messagebox.showinfo(
                    "Success",
                    f"Windows Update service has been {action}d.\n\n"
                    "You may need to restart the service or your computer for changes to take effect.",
                )

                self.update_status()

        except PermissionError:
            messagebox.showerror(
                "Permission Error",
                "Permission denied!\n\nPlease run this application as Administrator.",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to modify registry:\n{str(e)}")


def main():
    root = tk.Tk()
    app = WindowsUpdateDisabler(root)
    root.mainloop()


if __name__ == "__main__":
    main()
