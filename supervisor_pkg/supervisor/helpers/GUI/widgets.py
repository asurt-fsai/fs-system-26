import tkinter as tk

class Dashboard:
    def __init__(self, root):
        self.root = root

        self.vel = tk.Label(root, text="0", fg="white", bg="black")
        self.vel.place(relx=.6, rely=.6)

        self.steer = tk.Label(root, text="0", fg="white", bg="black")
        self.steer.place(relx=.8, rely=.6)

        self.state = tk.Label(root, text="state", fg="white", bg="black")
        self.state.place(relx=.4, rely=.6)

    def update_cmd(self, vel, steer):
        self.vel.config(text=str(vel))
        self.steer.config(text=str(steer))

    def update_state(self, state):
        if isinstance(state, str):
            self.state.config(text=state)
            return
        if state == 1:
            self.state.config(text="driving")
        elif state == 2:
            self.state.config(text="finished")