import os
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

DB_PATH = "cashier.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL CHECK(price >= 0)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL CHECK(total >= 0)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                menu_item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                price REAL NOT NULL CHECK(price >= 0),
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
            )
            """
        )


class CashierApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Small Cashier")
        self.geometry("880x520")
        self.resizable(False, False)
        self.menu_items = []
        self.order_items = []
        self._setup_style()
        self._build_ui()
        self.load_menu()
        self.invoice_window = None

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f6f8")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("Header.TLabel", background="#f5f6f8", font=("Segoe UI", 16, "bold"))
        style.configure("Subheader.TLabel", background="#ffffff", font=("Segoe UI", 11, "bold"))
        style.configure("TLabel", background="#ffffff", font=("Segoe UI", 10))
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="#ffffff",
            background="#4f46e5",
            borderwidth=0,
            padding=(14, 6),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#4338ca"), ("disabled", "#a5b4fc")],
        )
        style.configure(
            "Neutral.TButton",
            font=("Segoe UI", 10),
            foreground="#111827",
            background="#e5e7eb",
            borderwidth=0,
            padding=(12, 6),
        )
        style.map("Neutral.TButton", background=[("active", "#d1d5db")])
        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 10),
            foreground="#ffffff",
            background="#ef4444",
            borderwidth=0,
            padding=(12, 6),
        )
        style.map("Danger.TButton", background=[("active", "#dc2626")])
        style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=28,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        self.configure(background="#f5f6f8")
        main = ttk.Frame(self, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(main, text="Restaurant Cashier", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        left = ttk.Frame(main, style="Card.TFrame", padding=12)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        right = ttk.Frame(main, style="Card.TFrame", padding=12)
        right.grid(row=1, column=1, sticky="nsew")

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        ttk.Label(left, text="Menu Items", style="Subheader.TLabel").pack(anchor="w")
        self.menu_list = ttk.Treeview(left, columns=("name", "price"), show="headings", height=10)
        self.menu_list.heading("name", text="Item")
        self.menu_list.heading("price", text="Price")
        self.menu_list.column("name", width=260)
        self.menu_list.column("price", width=100, anchor="center")
        self.menu_list.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        add_frame = ttk.Frame(left)
        add_frame.pack(fill=tk.X, pady=(12, 0))
        ttk.Label(add_frame, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Label(add_frame, text="Price").grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.name_entry = ttk.Entry(add_frame, width=18)
        self.name_entry.grid(row=1, column=0, sticky="w")
        self.price_entry = ttk.Entry(add_frame, width=12)
        self.price_entry.grid(row=1, column=1, sticky="w", padx=(8, 0))
        ttk.Button(add_frame, text="Add Item", style="Accent.TButton", command=self.add_menu_item).grid(
            row=1, column=2, padx=(8, 0)
        )

        ttk.Label(right, text="Current Order", style="Subheader.TLabel").pack(anchor="w")
        self.order_list = ttk.Treeview(
            right, columns=("name", "price"), show="headings", height=10
        )
        self.order_list.heading("name", text="Item")
        self.order_list.heading("price", text="Price")
        self.order_list.column("name", width=260)
        self.order_list.column("price", width=100, anchor="center")
        self.order_list.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        controls = ttk.Frame(right)
        controls.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(controls, text="Add to Order", style="Neutral.TButton", command=self.add_to_order).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(
            controls, text="Remove Selected", style="Danger.TButton", command=self.remove_from_order
        ).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(controls, text="Checkout", style="Accent.TButton", command=self.checkout).grid(
            row=0, column=2
        )
        ttk.Button(
            controls, text="Print Invoice", style="Neutral.TButton", command=self.print_invoice
        ).grid(row=0, column=3, padx=(8, 0))

        self.total_var = tk.StringVar(value="Total: 0.00")
        ttk.Label(right, textvariable=self.total_var, font=("Segoe UI", 12, "bold")).pack(
            anchor="e", pady=(12, 0)
        )

    def load_menu(self):
        for item in self.menu_list.get_children():
            self.menu_list.delete(item)
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT id, name, price FROM menu_items ORDER BY name").fetchall()
        self.menu_items = rows
        for item_id, name, price in rows:
            self.menu_list.insert("", tk.END, iid=str(item_id), values=(name, f"{price:.2f} EGP"))

    def add_menu_item(self):
        name = self.name_entry.get().strip()
        price_text = self.price_entry.get().strip()
        if not name or not price_text:
            messagebox.showwarning("Missing data", "Please enter name and price.")
            return
        try:
            price = float(price_text)
        except ValueError:
            messagebox.showwarning("Invalid price", "Price must be a number.")
            return
        if price < 0:
            messagebox.showwarning("Invalid price", "Price must be positive.")
            return
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("INSERT INTO menu_items (name, price) VALUES (?, ?)", (name, price))
        except sqlite3.IntegrityError:
            messagebox.showwarning("Duplicate", "This item already exists.")
            return
        self.name_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.load_menu()

    def add_to_order(self):
        selection = self.menu_list.selection()
        if not selection:
            messagebox.showwarning("Select item", "Choose a menu item first.")
            return
        item_id = int(selection[0])
        match = next((item for item in self.menu_items if item[0] == item_id), None)
        if not match:
            messagebox.showwarning("Select item", "Choose a menu item first.")
            return
        _, name, price = match
        self.order_items.append({"menu_item_id": item_id, "name": name, "price": price})
        self.order_list.insert("", tk.END, values=(name, f"{price:.2f} EGP"))
        self.update_total()

    def remove_from_order(self):
        selection = self.order_list.selection()
        if not selection:
            return
        item_id = selection[0]
        index = self.order_list.index(item_id)
        self.order_list.delete(item_id)
        self.order_items.pop(index)
        self.update_total()

    def update_total(self):
        total = sum(item["price"] for item in self.order_items)
        self.total_var.set(f"Total: {total:.2f} EGP")

    def build_invoice_text(self, order_id, created_at):
        lines = [
            "Restaurant Cashier",
            "-" * 32,
            f"Order ID: {order_id}",
            f"Date: {created_at}",
            "-" * 32,
        ]
        for item in self.order_items:
            lines.append(f"{item['name']:<20} {item['price']:>8.2f}")
        lines.extend(
            [
                "-" * 32,
                f"Total: {sum(item['price'] for item in self.order_items):.2f} EGP",
                "",
                "Thank you!",
            ]
        )
        return "\n".join(lines)

    def show_invoice(self, invoice_text, order_id):
        if self.invoice_window and self.invoice_window.winfo_exists():
            self.invoice_window.destroy()
        self.invoice_window = tk.Toplevel(self)
        self.invoice_window.title(f"Invoice #{order_id}")
        self.invoice_window.geometry("420x520")
        self.invoice_window.resizable(False, False)

        frame = ttk.Frame(self.invoice_window, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Invoice #{order_id}", font=("Segoe UI", 12, "bold")).pack(
            anchor="w"
        )
        text = tk.Text(frame, width=48, height=24, font=("Consolas", 10))
        text.insert("1.0", invoice_text)
        text.configure(state="disabled")
        text.pack(fill=tk.BOTH, expand=True, pady=(8, 8))

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X)
        ttk.Button(
            buttons,
            text="Print",
            style="Accent.TButton",
            command=lambda: self.send_to_printer(invoice_text, order_id),
        ).pack(side=tk.RIGHT)

    def send_to_printer(self, invoice_text, order_id):
        invoices_dir = os.path.join(os.getcwd(), "invoices")
        os.makedirs(invoices_dir, exist_ok=True)
        file_path = os.path.join(invoices_dir, f"invoice_{order_id}.txt")
        with open(file_path, "w", encoding="utf-8") as handle:
            handle.write(invoice_text)
        if os.name == "nt":
            try:
                os.startfile(file_path, "print")
                messagebox.showinfo("Printing", "Invoice sent to the default printer.")
            except OSError:
                messagebox.showwarning(
                    "Printing failed", "Could not send to printer. Check printer setup."
                )
        else:
            messagebox.showinfo(
                "Saved",
                f"Invoice saved to {file_path}. Printing is supported on Windows using the default printer.",
            )

    def print_invoice(self):
        if not self.order_items:
            messagebox.showwarning("Empty order", "Add items before printing.")
            return
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        invoice_text = self.build_invoice_text(order_id="Draft", created_at=created_at)
        self.show_invoice(invoice_text, order_id="Draft")

    def checkout(self):
        if not self.order_items:
            messagebox.showwarning("Empty order", "Add items before checkout.")
            return
        total = sum(item["price"] for item in self.order_items)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("INSERT INTO orders (total) VALUES (?)", (total,))
            order_id = cursor.lastrowid
            created_at = conn.execute(
                "SELECT created_at FROM orders WHERE id = ?", (order_id,)
            ).fetchone()[0]
            for item in self.order_items:
                conn.execute(
                    """
                    INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, item["menu_item_id"], 1, item["price"]),
                )
        invoice_text = self.build_invoice_text(order_id=order_id, created_at=created_at)
        self.show_invoice(invoice_text, order_id=order_id)
        self.send_to_printer(invoice_text, order_id=order_id)
        self.order_items.clear()
        for item in self.order_list.get_children():
            self.order_list.delete(item)
        self.update_total()
        messagebox.showinfo("Saved", "Order saved successfully.")


if __name__ == "__main__":
    init_db()
    app = CashierApp()
    app.mainloop()
