import sqlite3
import tkinter as tk
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
        self.geometry("720x420")
        self.resizable(False, False)
        self.menu_items = []
        self.order_items = []
        self._build_ui()
        self.load_menu()

    def _build_ui(self):
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        ttk.Label(left, text="Menu Items").pack(anchor="w")
        self.menu_list = tk.Listbox(left, height=12)
        self.menu_list.pack(fill=tk.BOTH, expand=True)

        add_frame = ttk.Frame(left)
        add_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(add_frame, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Label(add_frame, text="Price").grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.name_entry = ttk.Entry(add_frame, width=18)
        self.name_entry.grid(row=1, column=0, sticky="w")
        self.price_entry = ttk.Entry(add_frame, width=12)
        self.price_entry.grid(row=1, column=1, sticky="w", padx=(8, 0))
        ttk.Button(add_frame, text="Add Item", command=self.add_menu_item).grid(
            row=1, column=2, padx=(8, 0)
        )

        ttk.Label(right, text="Current Order").pack(anchor="w")
        self.order_list = tk.Listbox(right, height=12)
        self.order_list.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(right)
        controls.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(controls, text="Add to Order", command=self.add_to_order).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(controls, text="Remove Selected", command=self.remove_from_order).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(controls, text="Checkout", command=self.checkout).grid(row=0, column=2)

        self.total_var = tk.StringVar(value="Total: 0.00")
        ttk.Label(right, textvariable=self.total_var, font=("Arial", 12, "bold")).pack(
            anchor="e", pady=(8, 0)
        )

    def load_menu(self):
        self.menu_list.delete(0, tk.END)
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT id, name, price FROM menu_items ORDER BY name").fetchall()
        self.menu_items = rows
        for item_id, name, price in rows:
            self.menu_list.insert(tk.END, f"{name} - {price:.2f} EGP")

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
        selection = self.menu_list.curselection()
        if not selection:
            messagebox.showwarning("Select item", "Choose a menu item first.")
            return
        index = selection[0]
        item_id, name, price = self.menu_items[index]
        self.order_items.append({"menu_item_id": item_id, "name": name, "price": price})
        self.order_list.insert(tk.END, f"{name} - {price:.2f} EGP")
        self.update_total()

    def remove_from_order(self):
        selection = self.order_list.curselection()
        if not selection:
            return
        index = selection[0]
        self.order_list.delete(index)
        self.order_items.pop(index)
        self.update_total()

    def update_total(self):
        total = sum(item["price"] for item in self.order_items)
        self.total_var.set(f"Total: {total:.2f} EGP")

    def checkout(self):
        if not self.order_items:
            messagebox.showwarning("Empty order", "Add items before checkout.")
            return
        total = sum(item["price"] for item in self.order_items)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("INSERT INTO orders (total) VALUES (?)", (total,))
            order_id = cursor.lastrowid
            for item in self.order_items:
                conn.execute(
                    """
                    INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, item["menu_item_id"], 1, item["price"]),
                )
        self.order_items.clear()
        self.order_list.delete(0, tk.END)
        self.update_total()
        messagebox.showinfo("Saved", "Order saved successfully.")


if __name__ == "__main__":
    init_db()
    app = CashierApp()
    app.mainloop()
