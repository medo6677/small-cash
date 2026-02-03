# Small Cashier (Desktop, SQLite)

Tiny desktop cashier app for trying out a restaurant POS flow with SQLite.

## Features
- Add menu items with name and price.
- Add items to an order, remove them, and checkout.
- Orders are stored in `cashier.db` using SQLite.

## Run
```bash
python app.py
```

## Notes
- Default currency label is **EGP** (editable in `app.py`).
- Database file `cashier.db` is created automatically in the project root.
