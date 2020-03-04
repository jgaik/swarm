import numpy as np
from controller import Controller
import tkinter as tk
from tkinter import ttk
import gui
from threading import Thread

class App:
  _time_refresh = 300

  def __init__(self, master):
    self.master = master
    self.gui = gui.GuiMain(master, self.send)
    self.controller = None
    self.th = None
    self.setup = gui.GuiSetup(master, self.setupEvent, self.end)
    self.master.withdraw()
    self.master.protocol("WM_DELETE_WINDOW", self.end)

  def update(self):
    if self.controller.isOnline():
      if (self.master.state() == 'withdrawn'):
        self.gui.setIds(self.controller.getIds())
        self.master.deiconify()
      if (self.setup.status()):
        self.setup.stop()
      self.gui.drawMarkers(self.controller.getMarkers())
    self.master.after(self._time_refresh, self.update)

  def end(self):
    if self.controller is not None:
      self.controller.stop()
    self.master.destroy()

  def send(self):
    data = self.gui.getData()
    if data:
      self.controller.setData(data)

  def setupEvent(self):
    if self.setup.start():
      self.start()

  def start(self):
    self.controller = Controller(self.setup.port_num,
      self.setup.port_baudrate,
      self.setup.tcp_ip,
      self.setup.tcp_port)
    self.th = Thread(target=self.controller.run)
    self.controller.start()
    self.th.start()
    self.update()

if __name__ == "__main__":
  root = tk.Tk()
  app = App(root)
  root.mainloop()