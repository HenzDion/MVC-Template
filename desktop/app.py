"""Tkinter desktop client for the Express user-profile API."""

from __future__ import annotations

import json
import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = os.environ.get(
    "USER_PROFILE_API_URL", "http://localhost:3000/api/users"
).rstrip("/")
FIELDS = ("firstName", "lastName", "email", "phone", "bio", "avatarUrl")
COLORS = {
    "background": "#f2f5f1",
    "surface": "#ffffff",
    "ink": "#23342b",
    "muted": "#7b8980",
    "line": "#e3e9e2",
    "green": "#285d4b",
    "green_dark": "#1e493a",
    "green_pale": "#e9f1e9",
    "coral": "#c98065",
    "red": "#a44f43",
}


class ApiError(Exception):
    """An HTTP or connection error returned by the profile API."""


class ProfileApi:
    def __init__(self, base_url: str = API_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, user_id: int | None = None,
                payload: dict[str, str] | None = None) -> Any:
        url = self.base_url
        if user_id is not None:
            url = f"{url}/{user_id}"

        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            url,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urlopen(request, timeout=8) as response:
                if response.status == 204:
                    return None
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8")).get("error")
            except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                detail = None
            raise ApiError(detail or f"The API returned HTTP {error.code}.") from error
        except (URLError, TimeoutError, OSError) as error:
            raise ApiError(
                f"Could not connect to {self.base_url}. Start the Express API and try again."
            ) from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ApiError("The API returned an invalid response.") from error

        if not isinstance(result, dict) or "data" not in result:
            raise ApiError("The API response did not include profile data.")
        return result["data"]


class ProfileDialog(tk.Toplevel):
    def __init__(self, parent: "ProfileApp", user: dict[str, Any] | None = None) -> None:
        super().__init__(parent)
        self.app = parent
        self.user = user
        self.value_vars: dict[str, tk.StringVar] = {}
        self.bio_text: tk.Text | None = None
        self.save_button: ttk.Button | None = None
        self.error_label: ttk.Label | None = None

        self.title("Edit profile" if user else "Add a person")
        self.configure(bg=COLORS["surface"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        shell = ttk.Frame(self, padding=(23, 19, 23, 18), style="Dialog.TFrame")
        shell.pack(fill="both", expand=True)
        heading = ttk.Label(
            shell,
            text="Edit profile" if user else "Add a person",
            style="DialogTitle.TLabel",
        )
        heading.pack(anchor="w")
        ttk.Label(
            shell,
            text="Add the details you want to keep close.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(3, 16))

        form = ttk.Frame(shell, style="Dialog.TFrame")
        form.pack(fill="x")
        fields = (
            ("firstName", "First name *", "given-name"),
            ("lastName", "Last name *", "family-name"),
            ("email", "Email address *", "name@company.com"),
            ("phone", "Phone number", "+1 (555) 000-0000"),
            ("avatarUrl", "Avatar image URL", "https://example.com/photo.jpg"),
        )
        for key, label, placeholder in fields:
            ttk.Label(form, text=label, style="FormLabel.TLabel").pack(
                anchor="w", pady=(0, 4)
            )
            value = tk.StringVar(value=(user or {}).get(key, "") or "")
            self.value_vars[key] = value
            entry = ttk.Entry(form, textvariable=value, width=48)
            entry.pack(fill="x", pady=(0, 11), ipady=5)
            entry.insert(0, "")
            if key == "firstName":
                entry.focus_set()

        ttk.Label(form, text="About them", style="FormLabel.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        self.bio_text = tk.Text(
            form,
            height=4,
            width=48,
            wrap="word",
            relief="solid",
            bd=1,
            highlightthickness=0,
            padx=8,
            pady=7,
            font=("Segoe UI", 9),
            fg=COLORS["ink"],
            bg="#fcfdfb",
        )
        self.bio_text.pack(fill="x")
        self.bio_text.insert("1.0", (user or {}).get("bio") or "")

        self.error_label = ttk.Label(
            form, text="", style="Error.TLabel", wraplength=390
        )
        self.error_label.pack(anchor="w", pady=(8, 0))

        footer = ttk.Frame(shell, style="Dialog.TFrame")
        footer.pack(fill="x", pady=(15, 0))
        ttk.Button(footer, text="Cancel", command=self.destroy).pack(side="right")
        self.save_button = ttk.Button(
            footer,
            text="Save changes" if user else "Create profile",
            style="Primary.TButton",
            command=self.submit,
        )
        self.save_button.pack(side="right", padx=(0, 8))

        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<Return>", lambda _event: self.submit())
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx() + 250}+{parent.winfo_rooty() + 105}")

    def submit(self) -> None:
        payload = {key: value.get().strip() for key, value in self.value_vars.items()}
        payload["bio"] = self.bio_text.get("1.0", "end-1c").strip() if self.bio_text else ""
        for required in ("firstName", "lastName", "email"):
            if not payload[required]:
                self.show_error(f"{required[0].upper() + required[1:]} is required.")
                return

        if self.save_button:
            self.save_button.configure(state="disabled", text="Saving...")
        self.app.save_profile(self, payload, self.user.get("id") if self.user else None)

    def show_error(self, message: str) -> None:
        if self.error_label and self.error_label.winfo_exists():
            self.error_label.configure(text=message)
        if self.save_button and self.save_button.winfo_exists():
            self.save_button.configure(state="normal", text="Save changes" if self.user else "Create profile")


class ProfileApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.api = ProfileApi()
        self.users: list[dict[str, Any]] = []
        self.selected_id: int | None = None
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Connecting to API...")
        self.count_var = tk.StringVar(value="0 profiles")
        self.detail_widgets: list[tk.Widget] = []

        self.title("Fieldnote | People Directory")
        self.geometry("1120x720")
        self.minsize(900, 600)
        self.configure(bg=COLORS["background"])
        self._configure_styles()
        self._build_layout()
        self.search_var.trace_add("write", lambda *_args: self._render_users())
        self.refresh_users()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background=COLORS["background"])
        style.configure("Surface.TFrame", background=COLORS["surface"])
        style.configure("Dialog.TFrame", background=COLORS["surface"])
        style.configure("Brand.TLabel", background=COLORS["background"], foreground=COLORS["green"], font=("Segoe UI", 17, "bold"))
        style.configure("Title.TLabel", background=COLORS["background"], foreground=COLORS["ink"], font=("Segoe UI", 24, "bold"))
        style.configure("Subtitle.TLabel", background=COLORS["background"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("DialogTitle.TLabel", background=COLORS["surface"], foreground=COLORS["ink"], font=("Segoe UI", 17, "bold"))
        style.configure("Muted.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("FormLabel.TLabel", background=COLORS["surface"], foreground="#59675e", font=("Segoe UI", 9, "bold"))
        style.configure("Error.TLabel", background=COLORS["surface"], foreground=COLORS["red"], font=("Segoe UI", 9))
        style.configure("StatLabel.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("Segoe UI", 8, "bold"))
        style.configure("StatValue.TLabel", background=COLORS["surface"], foreground=COLORS["ink"], font=("Segoe UI", 13, "bold"))
        style.configure("Status.TLabel", background=COLORS["background"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("TButton", padding=(11, 7), font=("Segoe UI", 9))
        style.configure("Primary.TButton", background=COLORS["green"], foreground="#ffffff", borderwidth=0, padding=(12, 8), font=("Segoe UI", 9, "bold"))
        style.map("Primary.TButton", background=[("active", COLORS["green_dark"]), ("disabled", "#9aafa1")])
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground=COLORS["ink"], rowheight=38, borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#f8faf7", foreground="#849087", relief="flat", padding=(8, 9), font=("Segoe UI", 8, "bold"))
        style.map("Treeview", background=[("selected", COLORS["green_pale"])], foreground=[("selected", COLORS["green_dark"])])

    def _build_layout(self) -> None:
        header = ttk.Frame(self, style="App.TFrame", padding=(30, 19, 30, 13))
        header.pack(fill="x")
        ttk.Label(header, text="fieldnote.", style="Brand.TLabel").pack(side="left")
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").pack(side="right", padx=(0, 3))

        heading = ttk.Frame(self, style="App.TFrame", padding=(30, 19, 30, 18))
        heading.pack(fill="x")
        ttk.Label(heading, text="People directory", style="Title.TLabel").pack(anchor="w")
        ttk.Label(heading, text="A thoughtful home for the people you work with.", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

        stats = ttk.Frame(self, style="Surface.TFrame", padding=(16, 12))
        stats.pack(fill="x", padx=30)
        ttk.Label(stats, text="TOTAL PEOPLE", style="StatLabel.TLabel").pack(side="left")
        ttk.Label(stats, textvariable=self.count_var, style="StatValue.TLabel").pack(side="left", padx=(12, 0))
        ttk.Button(stats, text="↻  Refresh", command=self.refresh_users).pack(side="right")

        toolbar = ttk.Frame(self, style="App.TFrame", padding=(30, 20, 30, 10))
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="All profiles", foreground=COLORS["ink"], background=COLORS["background"], font=("Segoe UI", 13, "bold")).pack(side="left")
        actions = ttk.Frame(toolbar, style="App.TFrame")
        actions.pack(side="right")
        search = ttk.Entry(actions, textvariable=self.search_var, width=30)
        search.pack(side="left", padx=(0, 9), ipady=5)
        search.insert(0, "")
        search.bind("<Control-a>", lambda event: self._select_all(event, search))
        ttk.Button(actions, text="＋  Add person", style="Primary.TButton", command=self.add_profile).pack(side="left")

        body = ttk.Frame(self, style="App.TFrame", padding=(30, 0, 30, 16))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=7, minsize=470)
        body.columnconfigure(1, weight=4, minsize=270)
        body.rowconfigure(0, weight=1)

        list_panel = ttk.Frame(body, style="Surface.TFrame", padding=(8, 8, 8, 5))
        list_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        list_panel.rowconfigure(0, weight=1)
        list_panel.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            list_panel,
            columns=("name", "email", "phone", "added"),
            show="headings",
            selectmode="browse",
        )
        for column, label, width in (
            ("name", "PERSON", 165),
            ("email", "EMAIL", 210),
            ("phone", "PHONE", 120),
            ("added", "ADDED", 105),
        ):
            self.tree.heading(column, text=label, anchor="w")
            self.tree.column(column, width=width, minwidth=75, anchor="w", stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(list_panel, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.tag_configure("odd", background="#fbfcfa")

        detail = ttk.Frame(body, style="Surface.TFrame", padding=(20, 17))
        detail.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self.detail = detail
        self._show_empty_detail()

        footer = ttk.Frame(self, style="App.TFrame", padding=(30, 0, 30, 13))
        footer.pack(fill="x")
        ttk.Label(footer, text="FIELDNOTE  •  USER PROFILES", style="Status.TLabel").pack(side="left")
        ttk.Label(footer, text=f"API  {self.api.base_url}", style="Status.TLabel").pack(side="right")

    @staticmethod
    def _select_all(event: tk.Event, entry: ttk.Entry) -> str:
        entry.selection_range(0, "end")
        return "break"

    def _run_async(self, method: str, user_id: int | None = None,
                   payload: dict[str, str] | None = None,
                   on_success: Callable[[Any], None] | None = None,
                   on_error: Callable[[str], None] | None = None) -> None:
        self.status_var.set("Connecting to API...")

        def work() -> None:
            try:
                result = self.api.request(method, user_id, payload)
            except ApiError as error:
                message = str(error)
                self.after(0, lambda: self._handle_error(message, on_error))
                return
            self.after(0, lambda: self._handle_success(result, on_success))

        threading.Thread(target=work, daemon=True).start()

    def _handle_error(self, message: str,
                      callback: Callable[[str], None] | None) -> None:
        self.status_var.set("API unavailable")
        if callback:
            callback(message)
        else:
            messagebox.showerror("Could not reach profiles", message, parent=self)

    def _handle_success(self, result: Any,
                        callback: Callable[[Any], None] | None) -> None:
        self.status_var.set("API connected")
        if callback:
            callback(result)

    def refresh_users(self) -> None:
        previous_id = self.selected_id

        def loaded(data: Any) -> None:
            if not isinstance(data, list):
                self._handle_error("The API did not return a profile list.", None)
                return
            self.users = data
            self.count_var.set(f"{len(data)} profile" + ("s" if len(data) != 1 else ""))
            self._render_users(preferred_id=previous_id)

        self._run_async("GET", on_success=loaded)

    def _render_users(self, preferred_id: int | None = None) -> None:
        current_id = preferred_id if preferred_id is not None else self.selected_id
        needle = self.search_var.get().strip().casefold()
        matches = [
            user for user in self.users
            if not needle or any(
                needle in str(user.get(field) or "").casefold()
                for field in ("firstName", "lastName", "email", "phone")
            )
        ]
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected_item = None
        for index, user in enumerate(matches):
            user_id = int(user["id"])
            full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
            added = self._format_date(user.get("createdAt"))
            tags = ("odd",) if index % 2 else ()
            self.tree.insert(
                "", "end", iid=str(user_id),
                values=(full_name, user.get("email", ""), user.get("phone") or "—", added),
                tags=tags,
            )
            if user_id == current_id:
                selected_item = str(user_id)

        if selected_item:
            self.tree.selection_set(selected_item)
            self.tree.focus(selected_item)
            self.tree.see(selected_item)
            self.selected_id = int(selected_item)
            self._show_profile(self._find_user(self.selected_id))
        elif matches:
            first_id = int(matches[0]["id"])
            self.tree.selection_set(str(first_id))
            self.selected_id = first_id
            self._show_profile(matches[0])
        else:
            self.selected_id = None
            self._show_empty_detail()

    @staticmethod
    def _format_date(value: Any) -> str:
        if not value:
            return "—"
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.strftime("%b %d, %Y")
        except ValueError:
            return str(value)[:10]

    def _find_user(self, user_id: int | None) -> dict[str, Any] | None:
        return next((user for user in self.users if int(user["id"]) == user_id), None)

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        self.selected_id = int(selection[0])
        self._show_profile(self._find_user(self.selected_id))

    def _clear_detail(self) -> None:
        for widget in self.detail.winfo_children():
            widget.destroy()

    def _show_empty_detail(self) -> None:
        self._clear_detail()
        self.detail.columnconfigure(0, weight=1)
        content = ttk.Frame(self.detail, style="Surface.TFrame")
        content.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(content, text="◉", foreground=COLORS["green"], background=COLORS["green_pale"], font=("Segoe UI", 24), padding=(9, 4)).pack(pady=(0, 10))
        ttk.Label(content, text="Your directory starts here", foreground=COLORS["ink"], background=COLORS["surface"], font=("Segoe UI", 11, "bold")).pack()
        ttk.Label(content, text="Add a profile to keep important\ndetails close.", foreground=COLORS["muted"], background=COLORS["surface"], justify="center", font=("Segoe UI", 9)).pack(pady=(5, 12))
        ttk.Button(content, text="＋  Add person", style="Primary.TButton", command=self.add_profile).pack()

    def _show_profile(self, user: dict[str, Any] | None) -> None:
        if not user:
            self._show_empty_detail()
            return
        self._clear_detail()
        self.detail.columnconfigure(0, weight=1)

        top = ttk.Frame(self.detail, style="Surface.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="PROFILE CARD", foreground="#98a49b", background=COLORS["surface"], font=("Segoe UI", 8, "bold")).pack(side="left")
        ttk.Button(top, text="Edit", command=lambda: self.edit_profile(user)).pack(side="right")

        initials = f"{user.get('firstName', 'U')[:1]}{user.get('lastName', '')[:1]}".upper()
        avatar = tk.Label(self.detail, text=initials or "U", width=4, height=2, bg=COLORS["green_pale"], fg=COLORS["green"], font=("Segoe UI", 18, "bold"))
        avatar.pack(pady=(21, 9))
        name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
        ttk.Label(self.detail, text=name, foreground=COLORS["ink"], background=COLORS["surface"], font=("Segoe UI", 14, "bold"), wraplength=250).pack()
        ttk.Label(self.detail, text="●  Directory member", foreground="#66806c", background=COLORS["green_pale"], padding=(7, 4), font=("Segoe UI", 8)).pack(pady=(7, 18))

        ttk.Separator(self.detail).pack(fill="x", pady=(0, 15))
        self._detail_field("EMAIL ADDRESS", user.get("email") or "Not provided")
        self._detail_field("PHONE", user.get("phone") or "Not provided")
        self._detail_field("ABOUT", user.get("bio") or "No introduction added yet.")
        if user.get("avatarUrl"):
            self._detail_field("AVATAR URL", user["avatarUrl"])

        bottom = ttk.Frame(self.detail, style="Surface.TFrame")
        bottom.pack(side="bottom", fill="x", pady=(15, 0))
        ttk.Separator(bottom).pack(fill="x", pady=(0, 12))
        ttk.Label(bottom, text="ADDED TO DIRECTORY", foreground="#98a49b", background=COLORS["surface"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
        ttk.Label(bottom, text=self._format_date(user.get("createdAt")), foreground=COLORS["ink"], background=COLORS["surface"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 8))
        ttk.Button(bottom, text="Delete profile", command=lambda: self.delete_profile(user)).pack(anchor="w")

    def _detail_field(self, label: str, value: str) -> None:
        block = ttk.Frame(self.detail, style="Surface.TFrame")
        block.pack(fill="x", pady=(0, 13))
        ttk.Label(block, text=label, foreground="#98a49b", background=COLORS["surface"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
        ttk.Label(block, text=value, foreground="#536158", background=COLORS["surface"], font=("Segoe UI", 9), wraplength=245, justify="left").pack(anchor="w", pady=(4, 0))

    def add_profile(self) -> None:
        ProfileDialog(self)

    def edit_profile(self, user: dict[str, Any]) -> None:
        ProfileDialog(self, user)

    def save_profile(self, dialog: ProfileDialog, payload: dict[str, str],
                     user_id: int | None) -> None:
        method = "PATCH" if user_id is not None else "POST"

        def saved(_result: Any) -> None:
            dialog.destroy()
            self.refresh_users()

        self._run_async(
            method,
            user_id=user_id,
            payload=payload,
            on_success=saved,
            on_error=dialog.show_error,
        )

    def delete_profile(self, user: dict[str, Any]) -> None:
        name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
        if not messagebox.askyesno(
            "Delete profile",
            f"Delete {name}'s profile? This cannot be undone.",
            parent=self,
        ):
            return

        def deleted(_result: Any) -> None:
            self.refresh_users()

        self._run_async(
            "DELETE",
            user_id=int(user["id"]),
            on_success=deleted,
        )


if __name__ == "__main__":
    ProfileApp().mainloop()