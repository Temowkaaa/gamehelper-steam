from __future__ import annotations

import csv
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from app import ApiError, load_local_games


class GameHelperApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GameHelper Steam")
        self.geometry("1040x680")
        self.minsize(820, 520)

        self.games: list[dict[str, Any]] = []
        self.sort_column = "minutes"
        self.sort_reverse = True

        self.configure(background="#101317")
        self.create_widgets()
        self.refresh(fetch_names=False)

    def create_widgets(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#101317")
        style.configure("Header.TLabel", background="#101317", foreground="#eef3f8", font=("Segoe UI", 20, "bold"))
        style.configure("Muted.TLabel", background="#101317", foreground="#98a5b3")
        style.configure("Summary.TLabel", background="#171b21", foreground="#eef3f8", padding=10)
        style.configure("TButton", padding=(12, 7))
        style.configure("Treeview", rowheight=30, fieldbackground="#171b21", background="#171b21", foreground="#eef3f8")
        style.configure("Treeview.Heading", padding=8, font=("Segoe UI", 9, "bold"))

        root = ttk.Frame(self, padding=18)
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root)
        header.pack(fill=tk.X)

        title_area = ttk.Frame(header)
        title_area.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(title_area, text="GameHelper Steam", style="Header.TLabel").pack(anchor=tk.W)
        self.status_var = tk.StringVar(value="Локальный поиск Steam...")
        ttk.Label(title_area, textvariable=self.status_var, style="Muted.TLabel").pack(anchor=tk.W, pady=(4, 0))

        ttk.Button(header, text="Сканировать", command=lambda: self.refresh(fetch_names=False)).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(header, text="Обновить названия", command=lambda: self.refresh(fetch_names=True)).pack(side=tk.RIGHT)

        summary = ttk.Frame(root)
        summary.pack(fill=tk.X, pady=(18, 12))
        self.total_var = tk.StringVar(value="Всего часов: 0")
        self.count_var = tk.StringVar(value="Игр: 0")
        self.played_var = tk.StringVar(value="Запускались: 0")
        ttk.Label(summary, textvariable=self.total_var, style="Summary.TLabel").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Label(summary, textvariable=self.count_var, style="Summary.TLabel").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Label(summary, textvariable=self.played_var, style="Summary.TLabel").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        toolbar = ttk.Frame(root)
        toolbar.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(toolbar, text="Поиск", style="Muted.TLabel").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_games())
        search = ttk.Entry(toolbar, textvariable=self.search_var, width=34)
        search.pack(side=tk.LEFT, padx=(8, 16))

        ttk.Label(toolbar, text="Минимум часов", style="Muted.TLabel").pack(side=tk.LEFT)
        self.min_hours_var = tk.StringVar(value="0")
        self.min_hours_var.trace_add("write", lambda *_: self.render_games())
        ttk.Entry(toolbar, textvariable=self.min_hours_var, width=8).pack(side=tk.LEFT, padx=(8, 16))

        ttk.Button(toolbar, text="Открыть в Steam", command=self.open_selected_game).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(toolbar, text="Экспорт CSV", command=self.export_csv).pack(side=tk.RIGHT)

        table_frame = ttk.Frame(root)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "hours", "appid", "last_played")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.table.heading("name", text="Игра", command=lambda: self.sort_by("name"))
        self.table.heading("hours", text="Часы", command=lambda: self.sort_by("minutes"))
        self.table.heading("appid", text="AppID", command=lambda: self.sort_by("appid"))
        self.table.heading("last_played", text="Последний запуск", command=lambda: self.sort_by("lastPlayed"))
        self.table.column("name", width=520, minwidth=220)
        self.table.column("hours", width=110, anchor=tk.E)
        self.table.column("appid", width=100, anchor=tk.E)
        self.table.column("last_played", width=150, anchor=tk.CENTER)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.table.bind("<Double-1>", lambda _event: self.open_selected_game())

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.table.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.configure(yscrollcommand=scrollbar.set)

    def refresh(self, fetch_names: bool) -> None:
        self.set_busy(True, "Обновляю названия через Steam Store..." if fetch_names else "Ищу локальные данные Steam...")
        threading.Thread(target=self.load_games_worker, args=(fetch_names,), daemon=True).start()

    def load_games_worker(self, fetch_names: bool) -> None:
        try:
            payload = load_local_games(fetch_names=fetch_names)
            self.after(0, lambda: self.apply_payload(payload))
        except ApiError as error:
            self.after(0, lambda: self.show_error(str(error)))
        except Exception as error:
            self.after(0, lambda: self.show_error(f"Непредвиденная ошибка: {error}"))

    def apply_payload(self, payload: dict[str, Any]) -> None:
        self.games = payload["games"]
        self.total_var.set(f"Всего часов: {format_number(payload['totalHours'])}")
        self.count_var.set(f"Игр: {format_number(payload['gameCount'])}")
        self.played_var.set(f"Запускались: {format_number(payload['playedGames'])}")
        self.status_var.set(f"Steam найден: {payload['steamPath']}")
        self.set_busy(False)
        self.render_games()

    def render_games(self) -> None:
        query = self.search_var.get().strip().lower()
        try:
            min_hours = float(self.min_hours_var.get().replace(",", ".") or 0)
        except ValueError:
            min_hours = 0

        visible = [
            game
            for game in self.games
            if query in game["name"].lower() and float(game["hours"]) >= min_hours
        ]
        visible.sort(key=self.sort_key, reverse=self.sort_reverse)

        self.table.delete(*self.table.get_children())
        for game in visible:
            self.table.insert(
                "",
                tk.END,
                iid=str(game["appid"]),
                values=(
                    game["name"],
                    format_number(game["hours"]),
                    game["appid"],
                    format_timestamp(game["lastPlayed"]),
                ),
            )

    def sort_key(self, game: dict[str, Any]) -> Any:
        value = game.get(self.sort_column)
        if isinstance(value, str):
            return value.lower()
        return value

    def sort_by(self, column: str) -> None:
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = column in {"minutes", "lastPlayed"}
        self.render_games()

    def open_selected_game(self) -> None:
        selected = self.table.selection()
        if not selected:
            return
        webbrowser.open(f"https://store.steampowered.com/app/{selected[0]}/")

    def export_csv(self) -> None:
        if not self.games:
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="steam_hours.csv",
        )
        if not path:
            return

        with Path(path).open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(["AppID", "Название", "Часы", "Минуты", "Последний запуск"])
            for game in self.games:
                writer.writerow(
                    [
                        game["appid"],
                        game["name"],
                        format_number(game["hours"]),
                        game["minutes"],
                        format_timestamp(game["lastPlayed"]),
                    ]
                )
        messagebox.showinfo("Экспорт", "CSV-файл сохранен.")

    def show_error(self, message: str) -> None:
        self.set_busy(False)
        self.status_var.set(message)
        messagebox.showerror("GameHelper", message)

    def set_busy(self, busy: bool, message: str | None = None) -> None:
        if message:
            self.status_var.set(message)
        self.config(cursor="watch" if busy else "")


def format_number(value: float | int) -> str:
    return f"{value:,.1f}".replace(",", " ").replace(".", ",")


def format_timestamp(value: int) -> str:
    if not value:
        return ""
    return datetime.fromtimestamp(value).strftime("%d.%m.%Y")


if __name__ == "__main__":
    GameHelperApp().mainloop()
