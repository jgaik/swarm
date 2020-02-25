from controller import Controller
import tkinter as tk
from tkinter import ttk

class Gui:

  def __init__(self, master):
    self.master = master

    self.master.title("Swarm controller")

    self.master.columnconfigure(0, weight=1)
    self.master.rowconfigure(0, weight=1)

    x = round((self.master.winfo_screenwidth() - self.master.winfo_reqwidth()) / 2)
    y = round((self.master.winfo_screenheight() - self.master.winfo_reqheight()) / 3)
    self.master.geometry(f"+{x}+{y}")

    self.master.config(menu=tk.Menu(self.master))

    frame_canvas = ttk.Frame(self)
    frame_canvas.grid(row=0,column=0, sticky='news')

    self.cnvTable = tk.Canvas(frame_canvas, width=100, height=100)
    self.cnvTable.grid(row=0,column=0,sticky='news')

    frame_controls = ttk.Frame(self)
    frame_controls.grid(row=0,column=1,sticky='w')

    self.cmbTasks = ttk.Combobox(frame_controls)
    self.cmbTasks['values'] = ['Parameters setting', 'Direct control']
    self.cmbTasks.grid(row=0,column=0,sticky='n')

    frame_settings = ttk.Frame(frame_controls)
    frame_settings.grid(row=1,column=0,sticky='ew')

    self.btnSend = ttk.Button(frame_controls, text="Send")
    self.btnSend.grid(row=2, column=0, sticky='se')

  def drawMarkers(self, markersNew):
    pass

class App:
  _time_refresh = 300

  def __init__(self, master):
    self.master = master
    self.gui = Gui(master)
    self.controller = Controller()

    self.master.protocol("WM_DELETE_WINDOW", self.end)

  def update(self):
    self.master.after(self._time_refresh, self.update)

  def end(self):
    self.controller.stop()
    self.master.destroy()


if __name__ == "__main__":
  root = tk.Tk()
  app = App(root)
  root.mainloop()