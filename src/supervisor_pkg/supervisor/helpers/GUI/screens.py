import tkinter as tk

class Screens:
    def __init__(self, root):
        self.screen1 = tk.Frame(root, bg="black")
        self.screen2 = tk.Frame(root, bg="black")

    def show1(self):
        self.screen1.pack(fill="both", expand=True)
        self.screen2.pack_forget()

    def show2(self):
        self.screen1.pack_forget()
        self.screen2.pack(fill="both", expand=True)