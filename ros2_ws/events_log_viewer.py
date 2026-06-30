#!/usr/bin/env python3
"""Events log viewer and parser for newline-delimited JSON event logs."""

from __future__ import annotations

import json
import os
import sys
import datetime
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import filedialog, messagebox
from tkinter import ttk
from typing import Any, Dict, List, Optional


@dataclass
class Event:
    timestamp: float
    severity: str
    category: str
    event_type: str
    source: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp)

    @property
    def time_label(self) -> str:
        return self.time.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def detail_text(self) -> str:
        return json.dumps(self.details, indent=2, sort_keys=True)


@dataclass
class EventGroup:
    category: str
    event_type: str
    source: str
    start: float
    end: float
    severity: str
    count: int
    examples: List[Event]

    @property
    def start_label(self) -> str:
        return datetime.datetime.fromtimestamp(self.start).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def end_label(self) -> str:
        return datetime.datetime.fromtimestamp(self.end).strftime("%Y-%m-%d %H:%M:%S")


class EventLogParser:
    def __init__(self, path: str) -> None:
        self.path = path
        self.events: List[Event] = []

    def load(self) -> List[Event]:
        if not os.path.isfile(self.path):
            raise FileNotFoundError(f"Event log file not found: {self.path}")

        events: List[Event] = []
        with open(self.path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc

                event = Event(
                    timestamp=float(obj.get("timestamp", 0.0)),
                    severity=str(obj.get("severity", "UNKNOWN")),
                    category=str(obj.get("category", "UNKNOWN")),
                    event_type=str(obj.get("event_type", "UNKNOWN")),
                    source=str(obj.get("source", "UNKNOWN")),
                    details=obj.get("details", {}),
                )
                events.append(event)

        events.sort(key=lambda entry: entry.timestamp)
        self.events = events
        return events

    def categories(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for event in self.events:
            counts[event.category] = counts.get(event.category, 0) + 1
        return counts

    def sources(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for event in self.events:
            counts[event.source] = counts.get(event.source, 0) + 1
        return counts

    def event_types(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for event in self.events:
            counts[event.event_type] = counts.get(event.event_type, 0) + 1
        return counts

    def severities(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for event in self.events:
            counts[event.severity] = counts.get(event.severity, 0) + 1
        return counts

    def min_timestamp(self) -> Optional[float]:
        return self.events[0].timestamp if self.events else None

    def max_timestamp(self) -> Optional[float]:
        return self.events[-1].timestamp if self.events else None


class EventViewerApp:
    BACKGROUND = "#11131a"
    PANEL_BG = "#0f1720"
    CARD_BG = "#0f1a24"
    ACCENT = "#4ba3ff"
    TEXT = "#e6eef8"
    SUBTEXT = "#9fb0c7"
    BORDER = "#0b1620"
    SEVERITY_COLORS = {
        "INFO": "#3fb0ff",
        "WARN": "#ffb14d",
        "ERROR": "#ff6b6b",
        "DEBUG": "#56d7a7",
        "UNKNOWN": "#9fb0c7",
    }

    def __init__(self, master: tk.Tk, log_path: Optional[str] = None) -> None:
        self.master = master
        self.master.title("Events Log Viewer")
        self.master.geometry("1240x780")
        self.master.minsize(1080, 680)
        self.master.configure(bg=self.BACKGROUND)

        self.log_path = log_path or "logging_debug/events_log.json"
        self.parser = EventLogParser(self.log_path)
        self.events: List[Event] = []
        self.filtered_events: List[Event] = []
        self.view_mode = "All"
        self.active_group: Optional[str] = None
        self.grouped_mode: bool = False
        self.current_groups: List[EventGroup] = []
        self.event_marker_map: Dict[int, int] = {}
        self.group_marker_map: Dict[int, int] = {}
        self._highlight_id: Optional[int] = None

        self._setup_style()
        self._build_ui()
        self.load_events(self.log_path)

    def _setup_style(self) -> None:
        style = ttk.Style(self.master)
        style.theme_use("clam")
        style.configure("TFrame", background=self.PANEL_BG)
        style.configure("TLabel", background=self.PANEL_BG, foreground=self.TEXT)
        style.configure("TButton", background="#262d36", foreground=self.TEXT, relief="flat")
        style.configure("TEntry", fieldbackground="#202631", foreground=self.TEXT, background="#202631")
        style.configure("TCombobox", fieldbackground="#202631", foreground=self.TEXT, background="#202631")
        style.configure("Treeview", background="#181c24", fieldbackground="#181c24", foreground=self.TEXT, bordercolor=self.BORDER, borderwidth=0)
        style.configure("Treeview.Heading", background="#1f2730", foreground=self.TEXT, relief="flat")
        style.map("TButton", background=[("active", "#313c4a")])
        style.map("TCombobox", fieldbackground=[("readonly", "#202631")])

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self.master, padding=(12, 10, 12, 8))
        toolbar.pack(fill="x", padx=12, pady=(12, 0))

        self.path_var = tk.StringVar(value=self.log_path)
        path_entry = ttk.Entry(toolbar, textvariable=self.path_var, width=76)
        path_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")

        browse_button = ttk.Button(toolbar, text="Browse", command=self.choose_file)
        browse_button.pack(side="left", padx=(0, 8))
        load_button = ttk.Button(toolbar, text="Load", command=self.on_load_button)
        load_button.pack(side="left")
        # Back button to exit grouped mode (hidden until needed)
        self.back_button = ttk.Button(toolbar, text="Back", command=self.exit_grouped_mode)
        self.back_button.pack(side="left", padx=(8, 0))
        self.back_button.pack_forget()

        mode_frame = ttk.Frame(self.master, padding=(12, 6, 12, 10))
        mode_frame.pack(fill="x", padx=12, pady=(10, 0))

        mode_title = ttk.Label(mode_frame, text="Timeline view:", font=(None, 10, "bold"))
        mode_title.pack(side="left")

        self.view_mode_var = tk.StringVar(value="All")
        for mode in ["All", "Category", "Source", "Event Type"]:
            button = ttk.Radiobutton(
                mode_frame,
                text=mode,
                value=mode,
                variable=self.view_mode_var,
                command=self.on_view_mode_changed,
                style="Toolbutton",
            )
            button.pack(side="left", padx=6)

        filter_frame = ttk.Frame(self.master, padding=(12, 6, 12, 10))
        filter_frame.pack(fill="x", padx=12)

        self.filter_var = tk.StringVar(value="")
        filter_label = ttk.Label(filter_frame, text="Search:", font=(None, 10, "bold"))
        filter_label.pack(side="left")
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=44)
        filter_entry.pack(side="left", padx=(8, 10))
        filter_entry.bind("<KeyRelease>", lambda _: self.apply_filters())

        reset_button = ttk.Button(filter_frame, text="Reset Filters", command=self.reset_filters)
        reset_button.pack(side="left")

        selection_panel = ttk.Frame(self.master, padding=(12, 10, 12, 10), style="TFrame")
        selection_panel.pack(fill="x", padx=12, pady=(0, 10))

        self.group_label = ttk.Label(selection_panel, text="Group by:", font=(None, 10, "bold"))
        self.group_label.grid(row=0, column=0, sticky="w")

        self.group_var = tk.StringVar(value="All")
        self.group_combobox = ttk.Combobox(
            selection_panel,
            textvariable=self.group_var,
            state="readonly",
            width=38,
            values=["All"],
        )
        self.group_combobox.grid(row=0, column=1, padx=(8, 0), sticky="w")
        self.group_combobox.bind("<<ComboboxSelected>>", lambda _: self.apply_filters())

        self.summary_label = ttk.Label(selection_panel, text="", font=(None, 9), foreground=self.SUBTEXT)
        self.summary_label.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # card container: use a normal frame so it expands vertically to fit all cards
        self.cards_frame = ttk.Frame(self.master, padding=(12, 6, 12, 6), style="TFrame")
        self.cards_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.cards_frame.bind("<Configure>", self._on_cards_configure)

        split_frame = ttk.Frame(self.master)
        split_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        left_frame = ttk.Frame(split_frame)
        left_frame.pack(side="left", fill="both", expand=True)

        timeline_frame = ttk.Frame(left_frame, padding=(0, 0, 0, 8))
        timeline_frame.pack(fill="x")

        timeline_title = ttk.Label(timeline_frame, text="Events Timeline", font=(None, 11, "bold"))
        timeline_title.pack(anchor="w")

        self.timeline_canvas = tk.Canvas(
            timeline_frame,
            height=210,
            background=self.BACKGROUND,
            highlightthickness=0,
        )
        self.timeline_canvas.pack(fill="both", expand=True, pady=(10, 0))

        table_frame = ttk.Frame(left_frame)
        table_frame.pack(fill="both", expand=True)

        columns = ("time", "severity", "category", "source", "event_type")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=18,
        )
        for column, width, anchor in [
            ("time", 200, "w"),
            ("severity", 80, "center"),
            ("category", 140, "center"),
            ("source", 180, "w"),
            ("event_type", 160, "w"),
        ]:
            self.tree.heading(column, text=column.replace("_", " ").title())
            self.tree.column(column, width=width, anchor=anchor)

        self.tree.tag_configure("INFO", background="#161b23")
        self.tree.tag_configure("WARN", background="#1f232b")
        self.tree.tag_configure("ERROR", background="#221c20")
        self.tree.tag_configure("DEBUG", background="#17221e")
        self.tree.tag_configure("UNKNOWN", background="#1e2228")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_selection_changed)
        self.tree.pack(fill="both", expand=True, side="left")

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="left", fill="y")

        right_frame = ttk.Frame(split_frame, width=340)
        right_frame.pack(side="right", fill="y")

        details_label = ttk.Label(right_frame, text="Details", font=(None, 11, "bold"))
        details_label.pack(anchor="w", pady=(0, 10))

        self.details_text = tk.Text(
            right_frame,
            wrap="none",
            state="disabled",
            background="#161a20",
            foreground=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            padx=10,
            pady=10,
        )
        self.details_text.pack(fill="both", expand=True)

        details_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)
        details_scroll.pack(side="right", fill="y")

    def _on_cards_configure(self, event: tk.Event) -> None:
        # cards_frame is a plain frame now; no canvas to update.
        # Keep this handler for compatibility but do nothing.
        return

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select events log file",
            initialfile=self.log_path,
            filetypes=[("JSON lines", "*.json *.ndjson"), ("All files", "*")],
        )
        if path:
            self.path_var.set(path)
            self.log_path = path
            self.load_events(path)

    def on_load_button(self) -> None:
        self.load_events(self.path_var.get())

    def load_events(self, path: str) -> None:
        try:
            parser = EventLogParser(path)
            self.events = parser.load()
            self.parser = parser
        except Exception as exc:
            messagebox.showerror("Load Error", str(exc))
            return

        self.view_mode = "All"
        self.view_mode_var.set("All")
        self.active_group = None
        self.filter_var.set("")
        self.filtered_events = self.events
        self.grouped_mode = False
        self.current_groups = []
        self.update_group_controls()
        self.refresh_event_list()
        self.redraw_timeline()

    def reset_filters(self) -> None:
        self.active_group = None
        self.filter_var.set("")
        self.filtered_events = self.events
        self.grouped_mode = False
        self.current_groups = []
        self.update_group_controls()
        self.refresh_event_list()
        self.redraw_timeline()

    def on_view_mode_changed(self) -> None:
        self.view_mode = self.view_mode_var.get()
        self.active_group = None
        self.group_var.set("All")
        self.grouped_mode = False
        self.current_groups = []
        self.update_group_controls()
        self.apply_filters()

    def apply_filters(self) -> None:
        query = self.filter_var.get().strip().lower()
        group_value = self.group_var.get()
        filtered: List[Event] = self.events

        if self.view_mode == "Category" and group_value not in ("All", ""):
            filtered = [event for event in filtered if event.category == group_value]
        elif self.view_mode == "Source" and group_value not in ("All", ""):
            filtered = [event for event in filtered if event.source == group_value]
        elif self.view_mode == "Event Type" and group_value not in ("All", ""):
            filtered = [event for event in filtered if event.event_type == group_value]

        if query:
            filtered = [
                event
                for event in filtered
                if query in event.source.lower()
                or query in event.event_type.lower()
                or query in event.category.lower()
                or query in event.severity.lower()
            ]

        self.filtered_events = filtered
        self.refresh_event_list()
        self.redraw_timeline()

    def update_group_controls(self) -> None:
        if self.view_mode == "All":
            self.group_label.config(text="Overview")
            self.group_combobox.configure(values=["All"])
            self.group_var.set("All")
            summary = f"{len(self.events)} total events"
        elif self.view_mode == "Category":
            self.group_label.config(text="Category")
            values = ["All"] + sorted(self.parser.categories().keys())
            self.group_combobox.configure(values=values)
            self.group_var.set("All")
            summary = f"{len(values) - 1} categories"
        elif self.view_mode == "Source":
            self.group_label.config(text="Source")
            values = ["All"] + sorted(self.parser.sources().keys())
            self.group_combobox.configure(values=values)
            self.group_var.set("All")
            summary = f"{len(values) - 1} sources"
        else:
            self.group_label.config(text="Event Type")
            values = ["All"] + sorted(self.parser.event_types().keys())
            self.group_combobox.configure(values=values)
            self.group_var.set("All")
            summary = f"{len(values) - 1} event types"

        self.summary_label.config(text=summary)
        self.update_cards()

    def update_cards(self) -> None:
        for child in self.cards_frame.winfo_children():
            child.destroy()
        # Two card rows: categories (resource usage etc.) and top sources
        categories = sorted(self.parser.categories().items(), key=lambda x: (-x[1], x[0]))
        sources = sorted(self.parser.sources().items(), key=lambda x: (-x[1], x[0]))

        # Category cards
        header = ttk.Label(self.cards_frame, text="By Category", font=(None, 10, "bold"))
        header.pack(anchor="w", pady=(0, 6), padx=8)
        row_frame = ttk.Frame(self.cards_frame)
        row_frame.pack(fill="x")
        for item, count in categories[:12]:
            card = tk.Frame(row_frame, bg=self.CARD_BG, bd=0, relief="flat")
            card.pack(side="left", padx=8, pady=4, ipadx=12, ipady=10)
            # bind click to frame and children so whole card is clickable
            cb = lambda ev, item=item: self.on_group_card_clicked(item, kind="category")
            card.bind("<Button-1>", cb)

            # hover effect
            def _on_enter(e, c=card, tl=None, sl=None):
                try:
                    c.config(bg=self.BORDER)
                except Exception:
                    pass
                if tl:
                    tl.config(fg=self.ACCENT)

            def _on_leave(e, c=card, tl=None, sl=None):
                try:
                    c.config(bg=self.CARD_BG)
                except Exception:
                    pass
                if tl:
                    tl.config(fg=self.TEXT)


            title_label = tk.Label(card, text=item, bg=self.CARD_BG, fg=self.TEXT, font=(None, 10, "bold"))
            title_label.pack(anchor="w")
            title_label.bind("<Button-1>", cb)
            subtitle = f"{count} event{'s' if count != 1 else ''}"
            subtitle_label = tk.Label(card, text=subtitle, bg=self.CARD_BG, fg=self.SUBTEXT, font=(None, 9))
            subtitle_label.pack(anchor="w", pady=(6, 0))
            subtitle_label.bind("<Button-1>", cb)
            card.bind("<Enter>", lambda e, c=card, tl=title_label: _on_enter(e, c, tl))
            card.bind("<Leave>", lambda e, c=card, tl=title_label: _on_leave(e, c, tl))
            title_label.bind("<Enter>", lambda e, c=card, tl=title_label: _on_enter(e, c, tl))
            title_label.bind("<Leave>", lambda e, c=card, tl=title_label: _on_leave(e, c, tl))

        # Source cards (top sources)
        header2 = ttk.Label(self.cards_frame, text="Top Sources", font=(None, 10, "bold"))
        header2.pack(anchor="w", pady=(8, 6), padx=8)
        row_frame2 = ttk.Frame(self.cards_frame)
        row_frame2.pack(fill="x")
        for item, count in sources[:12]:
            card = tk.Frame(row_frame2, bg=self.CARD_BG, bd=0, relief="flat")
            card.pack(side="left", padx=8, pady=4, ipadx=12, ipady=10)
            cb2 = lambda ev, item=item: self.on_group_card_clicked(item, kind="source")
            card.bind("<Button-1>", cb2)

            # hover for source cards
            def _on_enter_s(e, c=card, tl=None):
                try:
                    c.config(bg=self.BORDER)
                except Exception:
                    pass
                if tl:
                    tl.config(fg=self.ACCENT)

            def _on_leave_s(e, c=card, tl=None):
                try:
                    c.config(bg=self.CARD_BG)
                except Exception:
                    pass
                if tl:
                    tl.config(fg=self.TEXT)


            title_label = tk.Label(card, text=item, bg=self.CARD_BG, fg=self.TEXT, font=(None, 10, "bold"))
            title_label.pack(anchor="w")
            title_label.bind("<Button-1>", cb2)
            subtitle = f"{count} event{'s' if count != 1 else ''}"
            subtitle_label = tk.Label(card, text=subtitle, bg=self.CARD_BG, fg=self.SUBTEXT, font=(None, 9))
            subtitle_label.pack(anchor="w", pady=(6, 0))
            subtitle_label.bind("<Button-1>", cb2)
            card.bind("<Enter>", lambda e, c=card, tl=title_label: _on_enter_s(e, c, tl))
            card.bind("<Leave>", lambda e, c=card, tl=title_label: _on_leave_s(e, c, tl))
            title_label.bind("<Enter>", lambda e, c=card, tl=title_label: _on_enter_s(e, c, tl))
            title_label.bind("<Leave>", lambda e, c=card, tl=title_label: _on_leave_s(e, c, tl))

    def on_card_selected(self, item: str) -> None:
        # Legacy compatibility: if called without kind, treat as category
        self.on_group_card_clicked(item, kind="category")

    def on_group_card_clicked(self, item: str, kind: str = "category") -> None:
        # Enter grouped mode and show timeline for the selected card
        self.grouped_mode = True
        # show back button
        try:
            self.back_button.pack(side="left", padx=(8, 0))
        except Exception:
            pass
        if kind == "category":
            self.view_mode = "Category"
            self.view_mode_var.set("Category")
            self.group_var.set(item)
            events = [e for e in self.events if e.category == item]
        else:
            self.view_mode = "Source"
            self.view_mode_var.set("Source")
            self.group_var.set(item)
            events = [e for e in self.events if e.source == item]

        self.filtered_events = events
        self.current_groups = self._make_groups_from_events(events)
        self.refresh_event_list()
        self.redraw_timeline()

    def refresh_event_list(self) -> None:
        self.tree.delete(*self.tree.get_children())
        if self.grouped_mode and self.current_groups:
            for index, group in enumerate(self.current_groups):
                tag = group.severity if group.severity in ("INFO", "WARN", "ERROR", "DEBUG") else "UNKNOWN"
                values = (
                    f"{group.start_label} — {group.end_label}",
                    group.severity,
                    group.category,
                    group.source,
                    group.event_type,
                )
                self.tree.insert("", "end", iid=f"g{index}", values=values, tags=(tag,))

            if self.current_groups:
                self.tree.selection_set("g0")
                self.on_group_selected()
        else:
            for index, event in enumerate(self.filtered_events):
                tag = event.severity if event.severity in ("INFO", "WARN", "ERROR", "DEBUG") else "UNKNOWN"
                self.tree.insert(
                    "",
                    "end",
                    iid=str(index),
                    values=(event.time_label, event.severity, event.category, event.source, event.event_type),
                    tags=(tag,),
                )

            if self.filtered_events:
                self.tree.selection_set(str(0))
                self.on_event_selected()
            else:
                self._clear_details()

    def _severity_rank(self, severity: str) -> int:
        order = {"ERROR": 4, "WARN": 3, "INFO": 2, "DEBUG": 1}
        return order.get(severity.upper(), 0)

    def _make_groups_from_events(self, events: List[Event]) -> List[EventGroup]:
        groups: Dict[tuple, EventGroup] = {}
        for ev in events:
            key = (ev.category, ev.event_type, ev.source)
            if key not in groups:
                groups[key] = EventGroup(
                    category=ev.category,
                    event_type=ev.event_type,
                    source=ev.source,
                    start=ev.timestamp,
                    end=ev.timestamp,
                    severity=ev.severity,
                    count=1,
                    examples=[ev],
                )
            else:
                g = groups[key]
                g.start = min(g.start, ev.timestamp)
                g.end = max(g.end, ev.timestamp)
                # choose highest-severity label
                if self._severity_rank(ev.severity) > self._severity_rank(g.severity):
                    g.severity = ev.severity
                g.count += 1
                g.examples.append(ev)

        # sort groups by count desc then start time
        sorted_groups = sorted(groups.values(), key=lambda gg: (-gg.count, gg.start))
        return sorted_groups

    def exit_grouped_mode(self) -> None:
        self.grouped_mode = False
        self.current_groups = []
        self.group_var.set("All")
        # hide back button
        try:
            self.back_button.pack_forget()
        except Exception:
            pass
        # restore filtered events based on current view mode and filters
        self.apply_filters()

    def redraw_timeline(self) -> None:
        self.timeline_canvas.delete("all")
        # reset marker maps
        self.event_marker_map.clear()
        self.group_marker_map.clear()
        if self._highlight_id:
            try:
                self.timeline_canvas.delete(self._highlight_id)
            except Exception:
                pass
            self._highlight_id = None
        width = int(self.timeline_canvas.winfo_width() or 1)
        height = int(self.timeline_canvas.winfo_height() or 1)
        if width < 10 or height < 10:
            return
        # Use global timeline range across all loaded events so scaling is consistent
        if not self.events:
            return
        min_t = min(e.timestamp for e in self.events)
        max_t = max(e.timestamp for e in self.events)
        span = max_t - min_t or 1.0
        margin = 34
        y_center = height // 2

        self.timeline_canvas.create_line(margin, y_center, width - margin, y_center, fill="#2f3640", width=3)

        ticks = 5
        for tick_index in range(ticks):
            x = margin + (width - 2 * margin) * tick_index / (ticks - 1)
            timestamp = min_t + (span * tick_index / (ticks - 1))
            tick_time = datetime.datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            self.timeline_canvas.create_line(x, y_center - 12, x, y_center + 12, fill="#2f3640", width=1)
            self.timeline_canvas.create_text(x, y_center + 26, text=tick_time, fill=self.SUBTEXT, font=(None, 9))

        if self.grouped_mode and self.current_groups:
            bar_height = 18
            for idx, group in enumerate(self.current_groups):
                x1 = margin + (width - 2 * margin) * ((group.start - min_t) / span)
                x2 = margin + (width - 2 * margin) * ((group.end - min_t) / span)
                color = self.SEVERITY_COLORS.get(group.severity, self.SEVERITY_COLORS["UNKNOWN"])
                # draw bar with subtle border for visibility
                self.timeline_canvas.create_rectangle(
                    x1,
                    y_center - bar_height // 2,
                    x2,
                    y_center + bar_height // 2,
                    fill=color,
                    outline=self.BORDER,
                    width=1,
                )
                # last seen marker (contrasting circle)
                marker = self.timeline_canvas.create_oval(
                    x2 - 8, y_center - 12, x2 + 8, y_center + 12, fill=color, outline=self.TEXT, width=2
                )
                # store group marker id for highlighting
                self.group_marker_map[idx] = marker
                # label
                label_text = f"{group.event_type} ({group.count})"
                self.timeline_canvas.create_text((x1 + x2) / 2, y_center - 20, text=label_text, fill=self.TEXT, font=(None, 10, "bold"))
                self.timeline_canvas.tag_bind(marker, "<Button-1>", self._make_group_marker_callback(idx))
        else:
            marker_radius = 8
            for idx, event in enumerate(self.filtered_events):
                x = margin + (width - 2 * margin) * ((event.timestamp - min_t) / span)
                color = self.SEVERITY_COLORS.get(event.severity, self.SEVERITY_COLORS["UNKNOWN"])
                marker = self.timeline_canvas.create_oval(
                    x - marker_radius,
                    y_center - marker_radius,
                    x + marker_radius,
                    y_center + marker_radius,
                    fill=color,
                    outline=self.TEXT,
                    width=1,
                )
                # store mapping to event index
                self.event_marker_map[idx] = marker
                self.timeline_canvas.tag_bind(marker, "<Button-1>", self._make_marker_callback_index(idx))

        # summary
        if self.grouped_mode and self.current_groups:
            summary = f"{len(self.current_groups)} groups · {datetime.datetime.fromtimestamp(min_t).strftime('%Y-%m-%d %H:%M:%S')} — {datetime.datetime.fromtimestamp(max_t).strftime('%Y-%m-%d %H:%M:%S')}"
            self.timeline_canvas.create_text(margin, 18, text=summary, anchor="nw", fill=self.SUBTEXT, font=(None, 9, "italic"))
        elif self.filtered_events:
            first = self.filtered_events[0]
            last = self.filtered_events[-1]
            summary = f"{len(self.filtered_events)} events · {first.time_label} — {last.time_label}"
            self.timeline_canvas.create_text(margin, 18, text=summary, anchor="nw", fill=self.SUBTEXT, font=(None, 9, "italic"))

    def _make_marker_callback(self, event_record: Event):
        def callback(_: tk.Event) -> None:
            index = self.filtered_events.index(event_record)
            self.tree.selection_set(str(index))
            self.tree.see(str(index))
            self.on_event_selected()

        return callback

    def _make_marker_callback_index(self, index: int):
        def callback(_: tk.Event) -> None:
            self.tree.selection_set(str(index))
            self.tree.see(str(index))
            self.on_event_selected()

        return callback

    def _make_group_marker_callback(self, group_index: int):
        def callback(_: tk.Event) -> None:
            iid = f"g{group_index}"
            self.tree.selection_set(iid)
            self.tree.see(iid)
            self.on_group_selected()

        return callback

    def _highlight_for_event_index(self, index: int) -> None:
        # remove previous highlight
        if self._highlight_id:
            try:
                self.timeline_canvas.delete(self._highlight_id)
            except Exception:
                pass
            self._highlight_id = None
        marker = self.event_marker_map.get(index)
        if not marker:
            return
        bbox = self.timeline_canvas.bbox(marker)
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        pad = 6
        self._highlight_id = self.timeline_canvas.create_oval(x1 - pad, y1 - pad, x2 + pad, y2 + pad, outline=self.ACCENT, width=3)
        self.timeline_canvas.tag_raise(self._highlight_id)

    def _highlight_for_group_index(self, index: int) -> None:
        if self._highlight_id:
            try:
                self.timeline_canvas.delete(self._highlight_id)
            except Exception:
                pass
            self._highlight_id = None
        marker = self.group_marker_map.get(index)
        if marker:
            bbox = self.timeline_canvas.bbox(marker)
            if not bbox:
                return
            x1, y1, x2, y2 = bbox
            pad = 8
            self._highlight_id = self.timeline_canvas.create_oval(x1 - pad, y1 - pad, x2 + pad, y2 + pad, outline=self.ACCENT, width=3)
            self.timeline_canvas.tag_raise(self._highlight_id)

    def on_group_selected(self, _: Optional[tk.Event] = None) -> None:
        # selection is a grouped row
        selection = self.tree.selection()
        if not selection:
            self._clear_details()
            return
        iid = selection[0]
        if not iid.startswith("g"):
            return
        try:
            index = int(iid[1:])
        except Exception:
            return
        if index < 0 or index >= len(self.current_groups):
            return
        group = self.current_groups[index]
        # show aggregated details
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, f"Category: {group.category}\n")
        self.details_text.insert(tk.END, f"Event Type: {group.event_type}\n")
        self.details_text.insert(tk.END, f"Source: {group.source}\n")
        self.details_text.insert(tk.END, f"Severity: {group.severity}\n")
        self.details_text.insert(tk.END, f"Count: {group.count}\n")
        self.details_text.insert(tk.END, f"First seen: {group.start_label}\n")
        self.details_text.insert(tk.END, f"Last seen: {group.end_label}\n\n")
        self.details_text.insert(tk.END, "Examples:\n")
        # show up to 5 example events
        for ex in group.examples[:5]:
            self.details_text.insert(tk.END, f"- {ex.time_label} | {ex.severity} | {ex.details}\n")
        self.details_text.configure(state="disabled")
        # highlight group marker on timeline
        try:
            gidx = self.current_groups.index(group)
        except Exception:
            gidx = None
        if gidx is not None:
            self._highlight_for_group_index(gidx)

    def on_event_selected(self, _: Optional[tk.Event] = None) -> None:
        selection = self.tree.selection()
        if not selection:
            self._clear_details()
            return
        item_id = selection[0]
        if not item_id.isdigit():
            return
        index = int(item_id)
        if index < 0 or index >= len(self.filtered_events):
            return
        event = self.filtered_events[index]
        self._show_details(event)
        # highlight corresponding marker on timeline
        self._highlight_for_event_index(index)

    def on_tree_selection_changed(self, _: Optional[tk.Event] = None) -> None:
        selection = self.tree.selection()
        if not selection:
            self._clear_details()
            return
        iid = selection[0]
        if iid.startswith("g"):
            self.on_group_selected()
        else:
            self.on_event_selected()

    def _show_details(self, event: Event) -> None:
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, f"Timestamp: {event.time_label}\n")
        self.details_text.insert(tk.END, f"Severity: {event.severity}\n")
        self.details_text.insert(tk.END, f"Category: {event.category}\n")
        self.details_text.insert(tk.END, f"Event Type: {event.event_type}\n")
        self.details_text.insert(tk.END, f"Source: {event.source}\n\n")
        self.details_text.insert(tk.END, "Details:\n")
        self.details_text.insert(tk.END, event.detail_text)
        self.details_text.configure(state="disabled")

    def _clear_details(self) -> None:
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.configure(state="disabled")


def main() -> int:
    log_path = None
    if len(sys.argv) > 1:
        log_path = sys.argv[1]

    root = tk.Tk()
    app = EventViewerApp(root, log_path)
    root.after(120, app.redraw_timeline)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
