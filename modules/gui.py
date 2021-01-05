import transitions
import tkinter as tk
from tkinter import ttk
import numpy as np
import serial.tools.list_ports as ports
import enum
import threading as th
from collections.abc import Mapping
from swarm.shared import config
from swarm.shared.templates import modules


def validateFloatInput(input):
    if input is "" or input is "-":
        return True
    try:
        int(input.replace('.', '', 1))
        return True
    except:
        return False


def validateIntInput(input):
    if input.isdigit() or input is "":
        return True
    else:
        return False


def validateIPInput(input):
    if input.replace('.', '').isdigit() or input is "":
        return True
    else:
        return False


class Marker:
    diameter = 13

    def __init__(self, id, pose):
        self.id = id
        self.pose = pose
        self.objects = []

    def drawingCreate(self, canvas: tk.Canvas, scale):
        r = round(self.diameter*scale/2)
        x = round(self.pose[0]*scale)
        y = canvas.winfo_height() - round(self.pose[1]*scale)
        phi = self.pose[2]
        self.objects.append(canvas.create_text(x, y, text=f"{self.id}"))
        self.objects.append(canvas.create_oval(
            x-r, y-r, x + r, y + r, tag="body"))

        R = np.array([[np.cos(phi), np.sin(phi)], [-np.sin(phi), np.cos(phi)]])
        p_st = np.round(R.dot(np.array([0, -r]))) + (x, y)
        p_end = np.round(R.dot(np.array([0, -r*1.75]))) + (x, y)
        self.objects.append(canvas.create_line(
            p_st[0], p_st[1], p_end[0], p_end[1], arrow=tk.LAST))

    def drawingChange(self, canvas: tk.Canvas, scale):
        r = round(self.diameter*scale/2)
        x = round(self.pose[0]*scale)
        y = canvas.winfo_height() - round(self.pose[1]*scale)
        phi = self.pose[2]
        canvas.coords(self.objects[0], x, y)
        canvas.coords(self.objects[1], x-r, y-r, x+r, y+r)

        R = np.array([[np.cos(phi), np.sin(phi)], [-np.sin(phi), np.cos(phi)]])
        p_st = np.round(R.dot(np.array([0, -r]))) + (x, y)
        p_end = np.round(R.dot(np.array([0, -r*1.75]))) + (x, y)
        canvas.coords(self.objects[2], p_st[0], p_st[1], p_end[0], p_end[1])


class MarkerList:

    def __init__(self, canvas):
        self.canvas = canvas
        self.markers = []

    def updateMarker(self, id, newPose, scale):
        if any([x.id == id for x in self.markers]):
            marker = self.markers[[x.id for x in self.markers].index(id)]
            marker.pose = newPose
            marker.drawingChange(self.canvas, scale)
        else:
            marker = Marker(id, newPose)
            marker.drawingCreate(self.canvas, scale)
            self.markers.append(marker)


class TaskGui:
    frame = None
    name = None
    data = {}

    def __init__(self, master, name):
        self.frame = ttk.Frame(master)
        self.name = name

    def show(self):
        self.frame.tkraise()

    def pack(self):
        self.frame.grid(row=0, column=0, sticky='news')

    def send(self):
        pass


class Parameters(TaskGui):
    ids = []

    def __init__(self, master: ttk.Frame, name):
        super().__init__(master, name)
        self.data = {
            'distance': tk.StringVar(),
            'radiusLeft': tk.StringVar(),
            'radiusRight': tk.StringVar(),
            'pid': [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        }

        validFloat = self.frame.register(validateFloatInput)

        ttk.Label(self.frame, text="Robot ID: ").grid(
            row=0, column=0, sticky='e')
        self.cmbID = ttk.Combobox(
            self.frame, values=['All'], width=3, state='readonly')
        self.cmbID.grid(row=0, column=1, sticky='w')
        self.cmbID.current(0)

        ttk.Label(self.frame, text="Robot settings").grid(
            row=1, column=0, columnspan=2)

        ttk.Label(self.frame, text="Wheel distance [mm]: ").grid(
            row=2, column=0, sticky='e')
        ttk.Entry(self.frame,  width=10, textvariable=self.data['distance'],
                  validate='key', validatecommand=(validFloat, '%P')).grid(row=2, column=1, sticky='e')

        ttk.Label(self.frame, text="Left radius [mm]: ").grid(
            row=3, column=0, sticky='e')
        ttk.Entry(self.frame,  width=10, textvariable=self.data['radiusLeft'],
                  validate='key', validatecommand=(validFloat, '%P')).grid(row=3, column=1, sticky='e')

        ttk.Label(self.frame, text="Right radius [mm]: ").grid(
            row=4, column=0, sticky='e')
        ttk.Entry(self.frame,  width=10, textvariable=self.data['radiusRight'],
                  validate='key', validatecommand=(validFloat, '%P')).grid(row=4, column=1, sticky='e')

        ttk.Label(self.frame, text="PID controller").grid(
            row=6, column=0, columnspan=2)

        ttk.Label(self.frame, text="Kp: ").grid(row=7, column=0, sticky='e')
        ttk.Entry(self.frame,  width=10, textvariable=self.data['pid'][0],
                  validate='key', validatecommand=(validFloat, '%P')).grid(row=7, column=1, sticky='e')

        ttk.Label(self.frame, text="Ki: ").grid(row=8, column=0, sticky='e')
        ttk.Entry(self.frame,  width=10, textvariable=self.data['pid'][1],
                  validate='key', validatecommand=(validFloat, '%P')).grid(row=8, column=1, sticky='e')

        ttk.Label(self.frame, text="Kd: ").grid(row=9, column=0, sticky='e')
        ttk.Entry(self.frame,  width=10, textvariable=self.data['pid'][2],
                  validate='key', validatecommand=(validFloat, '%P')).grid(row=9, column=1, sticky='e')

    def updateIDs(self, ids):
        self.cmbID['values'] = ['All'] + [str(id) for id in ids]

    def send(self):
        dataOut = {
            'task': self.name,
            'data': {},
        }
        for d in self.data:
            if isinstance(self.data[d], list):
                l = []
                value = False
                for x in range(len(self.data[d])):
                    if self.data[d][x].get() is not "":
                        l.append(float(self.data[d][x].get()))
                        value = True
                    else:
                        l.append(0.0)
                if value:
                    dataOut['data'][d] = l
            else:
                if self.data[d].get() is not "" and self.data[d].get() is not "-":
                    dataOut['data'][d] = float(self.data[d].get())
        if dataOut['data']:
            if self.cmbID.current() == 0:
                dataOut['data']['robotID'] = 255
            else:
                dataOut['data']['robotID'] = int(self.cmbID.get())
            return dataOut
        return


class DirectControl(TaskGui):
    ids = []

    def __init__(self, master: ttk.Frame, name):
        super().__init__(master, name)
        self.data = {
            'pathParameters': [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        }
        validFloat = self.frame.register(validateFloatInput)

        ttk.Label(self.frame, text="Robot ID: ").grid(
            row=0, column=0, sticky='e')
        self.cmbID = ttk.Combobox(
            self.frame, values=['All'], width=3, state='readonly')
        self.cmbID.grid(row=0, column=1, sticky='w')
        self.cmbID.current(0)
        ttk.Label(self.frame, text="Path mode: ").grid(
            row=1, column=0, sticky='e')
        self.cmbMode = ttk.Combobox(self.frame, values=[
                                    'Line', 'Turn', 'Arc', 'Velocity'], width=8, state='readonly')
        self.cmbMode.grid(row=1, column=1, sticky='w')
        self.cmbMode.current(0)
        self.cmbMode.bind('<<ComboboxSelected>>', self.selecetedMode)

        ttk.Label(self.frame, text="Path settings").grid(
            row=2, column=0, columnspan=2)

        ttk.Label(self.frame, text="Time [s]: ").grid(
            row=3, column=0, sticky='e')
        ttk.Entry(self.frame,  width=10, textvariable=self.data['pathParameters'][0],
                  validate='key', validatecommand=(validFloat, '%P')).grid(row=3, column=1, sticky='e')

        self.lblParam1 = ttk.Label(self.frame)
        self.lblParam1.grid(row=4, column=0, sticky='e')
        self.param1 = ttk.Entry(self.frame,  width=10, textvariable=self.data['pathParameters'][1],
                                validate='key', validatecommand=(validFloat, '%P'))
        self.param1.grid(row=4, column=1, sticky='e')

        self.lblParam2 = ttk.Label(self.frame)
        self.lblParam2.grid(row=5, column=0, sticky='e')
        self.param2 = ttk.Entry(self.frame,  width=10, textvariable=self.data['pathParameters'][2],
                                validate='key', validatecommand=(validFloat, '%P'))
        self.param2.grid(row=5, column=1, sticky='e')
        self.selecetedMode()

    def updateIDs(self, ids):
        self.cmbID['values'] = ['All'] + [str(id) for id in ids]

    def selecetedMode(self, event=None):
        mode = self.cmbMode.get()
        if mode == 'Line':
            self.lblParam1['text'] = 'Distance [mm]: '
            self.lblParam2.grid_remove()
            self.param2.grid_remove()
        if mode == 'Turn':
            self.lblParam1['text'] = 'Angle distance [deg]: '
            self.lblParam2.grid_remove()
            self.param2.grid_remove()
        if mode == 'Arc':
            self.lblParam1['text'] = 'Angle distance [deg]: '
            self.lblParam2['text'] = 'Arc radius [mm]: '
            self.lblParam2.grid()
            self.param2.grid()
        if mode == 'Velocity':
            self.lblParam1['text'] = 'Left velocity: '
            self.lblParam2['text'] = 'Right velocty: '
            self.lblParam2.grid()
            self.param2.grid()
        self.data['pathParameters'][1].set("")
        self.data['pathParameters'][2].set("")

    def send(self):
        mode = self.cmbMode.get()
        data = self.data['pathParameters']
        if mode == 'Line' or mode == 'Turn':
            if data[0].get().replace("-", "") is "" and data[1].get().replace("-", "") is "":
                return
        if mode == 'Arc' or mode == 'Velocity':
            if not all([d.get().replace("-", "") for d in data]):
                return

        dataOut = {
            'task': self.name,
            'data': {
                'pathMode': mode,
            }
        }
        if self.cmbID.current() == 0:
            dataOut['data']['robotID'] = 255
        else:
            dataOut['data']['robotID'] = int(self.cmbID.get())
        dataOut['data']['pathParameters'] = [
            float(x.get()) for x in data if x.get() is not ""]
        return dataOut


class GuiMain:
    cnvSizeInit = (200, 160)
    scale = 2
    tasks = []

    data = {}

    def __init__(self, master, sendEvent):
        self.master = master

        self.master.title("Swarm controller")

        self.master.resizable(False, False)

        x = round((self.master.winfo_screenwidth() -
                   self.master.winfo_reqwidth()) / 3)
        y = round((self.master.winfo_screenheight() -
                   self.master.winfo_reqheight()) / 4)
        self.master.geometry(f"+{x}+{y}")

        frame_canvas = ttk.Frame(self.master)
        frame_canvas.grid(row=0, column=0, padx=10, pady=10)

        self.cnvTable = tk.Canvas(
            frame_canvas, width=self.cnvSizeInit[0]*self.scale, height=self.cnvSizeInit[1]*self.scale)
        self.cnvTable.config(bg='white', bd=10, highlightbackground='black')
        self.cnvTable.grid(row=0, column=0, sticky='news')
        self.markers = MarkerList(self.cnvTable)

        frame_controls = ttk.Labelframe(self.master)
        frame_controls.grid(row=0, column=1, pady=5, padx=5, sticky='news')

        frame_choice = ttk.Frame(frame_controls)
        frame_choice.pack(side=tk.TOP, fill=tk.X)

        lblTasks = ttk.Label(frame_choice, text="Choose swarm task:")
        lblTasks.pack(side=tk.TOP)
        self.cmbTasks = ttk.Combobox(frame_choice, state='readonly')
        self.cmbTasks.pack(side=tk.TOP)

        frame_tasks = ttk.Frame(frame_controls)
        frame_tasks.pack(fill=tk.BOTH, pady=20, expand=True)

        self.tasks.append(Parameters(frame_tasks, 'Parameters setting'))
        self.tasks.append(DirectControl(frame_tasks, 'Direct control'))
        for t in self.tasks:
            t.pack()

        self.cmbTasks['values'] = [x.name for x in self.tasks]
        self.cmbTasks.bind("<<ComboboxSelected>>", self.selectedTask)
        self.cmbTasks.current(0)
        self.selectedTask()

        frame_actions = ttk.Frame(frame_controls)
        frame_actions.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.btnSend = ttk.Button(
            frame_actions, text="Send", command=sendEvent)
        self.btnSend.pack(side=tk.RIGHT)

    def drawMarkers(self, markersNew):
        self.cnvTable.update()
        for mark in range(4, len(markersNew)):
            if markersNew[mark][3] == 1:
                self.markers.updateMarker(
                    mark, markersNew[mark][0:3], self.scale)

    def addTasks(self, tasklist):
        self.cmbTasks['values'].extend([x for x in tasklist])

    def selectedTask(self, event=None):
        self.tasks[self.cmbTasks.current()].show()

    def getData(self):
        return self.tasks[self.cmbTasks.current()].send()

    def setIds(self, ids):
        self.tasks[0].updateIDs(ids)
        self.tasks[1].updateIDs(ids)


class GuiSetup:
    port_num = ''
    port_baudrate = ''
    tcp_ip = ''
    tcp_port = 0

    def __init__(self, master, startEvent, closeEvent):
        self.master = master
        self.wSetup = tk.Toplevel(self.master)
        self.hide()
        self.wSetup.title('Setup')
        self.wSetup.protocol("WM_DELETE_WINDOW", closeEvent)

        self.frame_main = ttk.Frame(self.wSetup)
        self.frame_main.pack(padx=10, pady=10)

        validInt = self.frame_main.register(validateIntInput)
        validIP = self.frame_main.register(validateIPInput)

        self.wSetup.resizable(False, False)
        x = round((self.master.winfo_screenwidth() -
                   self.master.winfo_reqwidth()) / 2)
        y = round((self.master.winfo_screenheight() -
                   self.master.winfo_reqheight()) / 3)
        self.wSetup.geometry(f"+{x}+{y}")

        self._ports = [p[0] for p in ports.comports()]
        self._file_baudrates = open('contents/setting_baudrate.txt', 'r+')
        self._file_ports = open('contents/setting_port.txt', 'r+')
        self._file_ips = open('contents/setting_ip.txt', 'r+')

        ttk.Label(self.frame_main, text='Robot netwok setup').grid(
            row=0, column=0, columnspan=2, pady=5)
        ttk.Label(self.frame_main, text='Device port:').grid(row=1, column=0)
        self.cmbPorts = ttk.Combobox(
            self.frame_main, values=self._ports, state='readonly')
        self.cmbPorts.current(0)
        self.cmbPorts.grid(row=1, column=1)
        ttk.Label(self.frame_main, text='Port baudrate:').grid(row=2, column=0)
        self.cmbBaudrate = ttk.Combobox(self.frame_main, values=self._file_baudrates.read().splitlines(),
                                        validate='key', validatecommand=(validInt, '%P'))
        self.cmbBaudrate.current(0)
        self.cmbBaudrate.grid(row=2, column=1)

        ttk.Label(self.frame_main, text='Camera server setup').grid(
            row=3, column=0, columnspan=2, pady=5)
        ttk.Label(self.frame_main, text='Server TCP IP:').grid(row=4, column=0)
        self.cmbTcpIp = ttk.Combobox(self.frame_main, values=self._file_ips.read().splitlines(),
                                     validate='key', validatecommand=(validIP, '%P'))
        self.cmbTcpIp.grid(row=4, column=1)
        self.cmbTcpIp.current(0)
        ttk.Label(self.frame_main, text='Server TCP Port:').grid(
            row=5, column=0)
        self.cmbTcpPort = ttk.Combobox(self.frame_main, values=self._file_ports.read().splitlines(),
                                       validate='key', validatecommand=(validInt, '%P'))
        self.cmbTcpPort.grid(row=5, column=1)
        self.cmbTcpPort.current(0)

        self.btnStart = ttk.Button(
            self.frame_main, text='Start', command=startEvent)
        self.btnStart.grid(row=6, column=0, columnspan=2, pady=5)

        self.loadBar = ttk.Progressbar(self.frame_main)
        self.loadBar.grid(row=6, column=0, columnspan=2, pady=5)
        self.loadBar.grid_remove()

    def start(self):
        try:
            self.port_num = self.cmbPorts.get()
            self.port_baudrate = self.cmbBaudrate.get()

            self.tcp_ip = self.cmbTcpIp.get()
            self.tcp_port = int(self.cmbTcpPort.get())

            if self.cmbTcpIp.current() == -1:
                self._file_ips.write(f"\n{self.tcp_ip}")
            if self.cmbTcpPort.current() == -1:
                self._file_ports.write(f"\n{self.tcp_port}")
            if self.cmbBaudrate.current() == -1:
                self._file_baudrates.write(f"\n{self.port_baudrate}")

            self.btnStart.grid_remove()
            self.loadBar.grid()
            self.loadBar.start()
        except:
            return False

        return True

    def stop(self):
        self.loadBar.stop()
        self.loadBar.grid_remove()
        self.btnStart.grid()
        self.hide()
        self._file_baudrates.close()
        self._file_ips.close()
        self._file_ports.close()

    def show(self):
        if (self.wSetup.state() == 'withdrawn'):
            self.wSetup.deiconify()

    def hide(self):
        if (self.wSetup.state() == 'normal'):
            self.wSetup.withdraw()

    def get_data(self):
        return {
            'setup_network': {
                'port_num': self.port_num,
                'port_baudrate': self.port_baudrate
            },
            'setup_camera': {
                'tcp_ip': self.tcp_ip,
                'tcp_port': self.tcp_port
            }
        }


class States(enum.Enum):
    INIT = enum.auto()
    IDLE = enum.auto()
    OPERATION = enum.auto()
    ERROR = enum.auto()
    END = enum.auto()


class Requirements(modules.BaseRequirements):
    datatags = ['tasks', 'ids', 'markers']


class FSM(modules.BaseFSM):
    #pylint: disable=no-member
    _ok = True
    _online = False

    def __init__(self, pipe):
        super(FSM, self).__init__(pipe, config.Request(), Requirements())
        self.root = tk.Tk()
        self._th_loop = th.Thread(target=self._thread_loop)
        self.gui_setup = GuiSetup(
            self.root, self.event_setup, self.event_end)
        self.gui_main = GuiMain(self.root, self.event_start)
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.event_end)

        list_transitions = [
            {
                'trigger': 'change_state',
                'source': 'none',
                'dest': States.INIT,
                'conditions': self._request.is_INIT
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.IDLE,
                'conditions': [self._requirements.have_tasks, self._requirements.have_ids],
                'unless': self._ok
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.ERROR,
                'conditions': self._ok
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.END,
                'conditions': self._request.is_END
            },
        ]
        self.machine = transitions.Machine(model=self,
                                           states=States,
                                           transitions=list_transitions,
                                           initial='none')
        self.machine.add_transition(trigger='change_state',
                                    source=States.INIT,
                                    dest=States.IDLE,
                                    conditions=self._ok)

        self.machine.add_transition(trigger='change_state',
                                    source=[States.IDLE, States.OPERATION],
                                    dest='=',
                                    after=self.update,
                                    conditions=self._requirements.have_camera,
                                    unless=self._request.is_END)

        self.machine.add_transition(trigger='change_state',
                                    source=States.OPERATION,
                                    dest=States.IDLE,
                                    conditions=self._request.is_END,
                                    unless=self._request.is_ERROR)

    def _thread_loop(self):
        while self._online:
            self.change_state()

    def start(self):
        self._online = True
        self._th_loop.start()
        self._th_requests.start()
        self.root.mainloop()

    def on_enter_IDLE(self):
        self.send_response(config.Response.READY)

    def on_enter_INIT(self):
        self.gui_setup.show()

    def on_exit_INIT(self):
        self.gui_setup.stop()
        data = self._requirements.get_data(['tasks', 'ids'])
        self.gui_main.addTasks(data['tasks'])
        self.gui_main.setIds(data['ids'])
        self.root.deiconify()

    def on_enter_END(self):
        self.send_response(config.Response.END)
        self._request.wait_END()
        self._online = False
        self.root.destroy()

    def on_enter_OPERATION(self):
        pass

    def event_setup(self):
        if self.gui_setup.start():
            self._ok &= True
            self.send_response(config.Response.INIT, self.gui_setup.get_data())
        else:
            self._ok &= False
            self.send_response(config.Response.ERROR)

    def event_end(self):
        self.to_END()

    def update(self):
        self.gui_main.drawMarkers(self._requirements.get_data('markers'))

    def event_start(self):
        data = self.gui_main.getData()
        self.send_response(config.Response.OK, data=data)
