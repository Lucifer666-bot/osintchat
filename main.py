import asyncio, tkinter as tk
from ttkthemes import ThemedTk
from gui import App
import db

if __name__ == "__main__":
    root = ThemedTk(theme="equilux")     # tema escuro
    root.title("OSINT Chat")
    root.geometry("800x600")
    asyncio.run(db.init_db())
    App(root)
    root.mainloop()