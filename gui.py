import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import asyncio, threading, json, os, datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from osint_core import pipeline
import db

class ChatTab:
    def __init__(self, nb, target):
        self.target = target
        self.frame = ttk.Frame(nb)
        nb.add(self.frame, text=target[:15])
        self.text = tk.Text(self.frame, state="disabled", wrap="word", bg="#1e1e1e", fg="#ffffff")
        self.text.pack(fill="both", expand=True)
        self.scroll = ttk.Scrollbar(self.frame, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side="right", fill="y")
        self.add("system", f"Iniciando OSINT sobre: {target}")
        threading.Thread(target=self.run_osint, daemon=True).start()
        ttk.Button(self.frame, text="Exportar PDF", command=self.export_pdf).pack(pady=4)

    def add(self, role, text):
        self.text.configure(state="normal")
        self.text.insert("end", f"{role.upper()}: {text}\n")
        self.text.configure(state="disabled")
        asyncio.run(db.save_message(self.target, role, text))

    def run_osint(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(pipeline(self.target))
        self.add("bot", json.dumps(result, indent=2, ensure_ascii=False))

    def export_pdf(self):
        msgs = asyncio.run(db.load_chat(self.target))
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        c = canvas.Canvas(path, pagesize=letter)
        textobj = c.beginText(40, letter[1]-40)
        textobj.setFont("Courier", 10)
        for m in msgs:
            textobj.textLines(json.dumps(m, ensure_ascii=False))
        c.drawText(textobj)
        c.save()
        messagebox.showinfo("Pronto", f"Relatório salvo em {path}")

class App:
    def __init__(self, root):
        self.root = root
        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True)
        self.menu = tk.Menu(root)
        root.config(menu=self.menu)
        self.menu.add_command(label="Novo Alvo", command=self.new_target)
        threading.Thread(target=self.restore_tabs, daemon=True).start()

    def restore_tabs(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        targets = loop.run_until_complete(self._all_targets())
        for t in targets:
            ChatTab(self.nb, t)

    async def _all_targets(self):
        async with aiosqlite.connect(db.DB) as db_:
            cur = await db_.execute("SELECT target FROM chats")
            rows = await cur.fetchall()
            return [r[0] for r in rows]

    def new_target(self):
        target = simpledialog.askstring("Novo Alvo", "Nome ou telefone:")
        if target:
            ChatTab(self.nb, target.strip())