import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import struct
import os
import csv
import copy

PALETTE_PATH = 'color.pal'
RECOLOUR_CSV_PATH = 'recolour.txt'
SCALE_FACTOR = 4  # will be adjusted dynamically per frame

def load_palette(pal_path):
    with open(pal_path, 'rb') as f:
        data = f.read(768)
    return [(r * 4, g * 4, b * 4) for r, g, b in struct.iter_unpack('BBB', data)]

def load_recolour_map(csv_path):
    recolour_map = {}
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) == 2:
                recolour_map[int(row[0])] = int(row[1])
    return recolour_map

def frm_is_single_direction(frm_type):
    return frm_type.upper() in {"FR0", "FR1", "FR2", "FR3", "FR4", "FR5"}

def get_total_frames(frm_bytes, frm_type):
    frame_count = struct.unpack(">H", frm_bytes[8:10])[0]
    return frame_count if frm_is_single_direction(frm_type) else frame_count * 6

def parse_frames(frm_bytes):
    header = frm_bytes[:62]
    offset = 62
    frames = []

    total = get_total_frames(frm_bytes, frm_type="")
    for _ in range(total):
        width, height = struct.unpack(">HH", frm_bytes[offset:offset + 4])
        size = width * height
        pixel_data = list(frm_bytes[offset + 12: offset + 12 + size])
        frames.append({
            'offset': offset,
            'header': frm_bytes[offset:offset + 12],
            'width': width,
            'height': height,
            'pixels': pixel_data
        })
        offset += 12 + size
    return header, frames

def rebuild_frm(header, frames):
    body = b''.join(f['header'] + bytes(f['pixels']) for f in frames)
    return header + body

def scale_image(pixels, width, height, palette, max_size=(300, 300)):
    img = Image.new("RGB", (width, height))
    img.putdata([palette[i] for i in pixels])
    scale_w = max_size[0] // width
    scale_h = max_size[1] // height
    scale = min(scale_w, scale_h, SCALE_FACTOR)
    return img.resize((width * scale, height * scale), Image.NEAREST), scale

class RecolourApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FRM Recolour Tool")

        self.palette = load_palette(PALETTE_PATH)
        self.recolour_map = load_recolour_map(RECOLOUR_CSV_PATH)
        self.root.geometry("900x600")

        # GUI Variables
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.frm_prefix = tk.StringVar()
        self.out_prefix = tk.StringVar()
        self.anim_type = tk.StringVar()

        # UI Layout
        self.build_controls()
        self.bind_keys()
        self.frame_index = 0
        self.input_frames = []
        self.output_frames = []
        self.frm_header = b''
        self.scale = 1

    def build_controls(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=5)

        tk.Label(control_frame, text="Input Dir:").grid(row=0, column=0)
        tk.Entry(control_frame, textvariable=self.input_dir, width=25).grid(row=0, column=1)

        tk.Label(control_frame, text="Input Prefix:").grid(row=0, column=2)
        tk.Entry(control_frame, textvariable=self.frm_prefix, width=15).grid(row=0, column=3)

        tk.Label(control_frame, text="Anim Type:").grid(row=0, column=4)
        tk.Entry(control_frame, textvariable=self.anim_type, width=5).grid(row=0, column=5)

        tk.Label(control_frame, text="Output Dir:").grid(row=1, column=0)
        tk.Entry(control_frame, textvariable=self.output_dir, width=25).grid(row=1, column=1)

        tk.Label(control_frame, text="Output Prefix:").grid(row=1, column=2)
        tk.Entry(control_frame, textvariable=self.out_prefix, width=15).grid(row=1, column=3)

        tk.Button(control_frame, text="Load FRM", command=self.load_frm).grid(row=0, column=6, rowspan=2, padx=5)
        tk.Button(control_frame, text="Save FRM", command=self.save_frm).grid(row=0, column=7, rowspan=2, padx=5)
        tk.Button(control_frame, text="Undo Frame", command=self.undo_frame).grid(row=0, column=8, rowspan=2, padx=5)

        nav_frame = tk.Frame(self.root)
        nav_frame.pack()

        #tk.Button(nav_frame, text="←", command=self.prev_frame).pack(side="left", padx=5)
        #tk.Button(nav_frame, text="→", command=self.next_frame).pack(side="left", padx=5)

        self.prev5_btn = tk.Button(nav_frame, text="⏴×5", font=("Arial", 16), command=lambda: self.change_frame(-5))
        self.prev1_btn = tk.Button(nav_frame, text="←", font=("Arial", 20, "bold"), command=lambda: self.change_frame(-1))
        self.next1_btn = tk.Button(nav_frame, text="→", font=("Arial", 20, "bold"), command=lambda: self.change_frame(1))
        self.next5_btn = tk.Button(nav_frame, text="×5⏵", font=("Arial", 16), command=lambda: self.change_frame(5))

        self.prev5_btn.grid(row=0, column=0, padx=15)
        self.prev1_btn.grid(row=0, column=1, padx=15)
        self.next1_btn.grid(row=0, column=2, padx=15)
        self.next5_btn.grid(row=0, column=3, padx=15)
        self.canvas_orig = tk.Canvas(self.root)
        self.canvas_orig.pack(side="right", padx=60)

        self.canvas_edit = tk.Canvas(self.root)
        self.canvas_edit.pack(side="left", padx=60)

        self.canvas_edit.bind("<Button-1>", self.start_select)
        self.canvas_edit.bind("<B1-Motion>", self.update_select)
        self.canvas_edit.bind("<ButtonRelease-1>", self.finish_select)
        
    def bind_keys(self):
        self.root.bind("<Left>", lambda e: self.change_frame(-1))
        self.root.bind("<Right>", lambda e: self.change_frame(1))
        
    def load_frm(self):
        prefix = self.frm_prefix.get().upper()
        suffix = self.anim_type.get().upper()
        in_dir = self.input_dir.get()
        filename = os.path.join(in_dir, prefix + suffix + ".FRM")
        if not os.path.exists(filename):
            messagebox.showerror("Error", f"File not found: {filename}")
            return
        with open(filename, "rb") as f:
            self.frm_data = f.read()

        self.frm_type = filename[-4:-1]
        self.frm_header, self.input_frames = parse_frames(self.frm_data)
        self.output_frames = copy.deepcopy(self.input_frames)
        self.frame_index = 0
        self.display_frame()

    def display_frame(self):
        f_in = self.input_frames[self.frame_index]
        f_out = self.output_frames[self.frame_index]

        img_in, self.scale = scale_image(f_in['pixels'], f_in['width'], f_in['height'], self.palette)
        img_out, _ = scale_image(f_out['pixels'], f_out['width'], f_out['height'], self.palette)

        self.tk_img_in = ImageTk.PhotoImage(img_in)
        self.tk_img_out = ImageTk.PhotoImage(img_out)

        self.canvas_orig.config(width=img_in.width, height=img_in.height)
        self.canvas_edit.config(width=img_out.width, height=img_out.height)

        self.canvas_orig.create_image(0, 0, anchor="nw", image=self.tk_img_in)
        self.canvas_edit.create_image(0, 0, anchor="nw", image=self.tk_img_out)

        self.sel_start = None
        self.sel_rect = None

    def start_select(self, event):
        self.sel_start = (event.x // self.scale, event.y // self.scale)
        self.clear_selection()

    def update_select(self, event):
        if not self.sel_start:
            return
        x0, y0 = self.sel_start
        x1, y1 = event.x // self.scale, event.y // self.scale
        if self.sel_rect:
            self.canvas_edit.delete(self.sel_rect)
        self.sel_rect = self.canvas_edit.create_rectangle(x0 * self.scale, y0 * self.scale,
                                                          x1 * self.scale, y1 * self.scale,
                                                          outline="red")

    def finish_select(self, event):
        if not self.sel_start:
            return
        x0, y0 = self.sel_start
        x1, y1 = event.x // self.scale, event.y // self.scale
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))

        frame = self.output_frames[self.frame_index]
        w, h = frame['width'], frame['height']
        pixels = frame['pixels']

        for y in range(y0, min(y1+1, h)):
            for x in range(x0, min(x1+1, w)):
                idx = y * w + x
                val = pixels[idx]
                if val in self.recolour_map:
                    pixels[idx] = self.recolour_map[val]

        self.display_frame()

    def clear_selection(self):
        if self.sel_rect:
            self.canvas_orig.delete(self.sel_rect)
            self.sel_rect = None

    def save_frm(self):
        out_prefix = self.out_prefix.get().upper()
        suffix = self.anim_type.get().upper()
        out_dir = self.output_dir.get()
        out_name = os.path.join(out_dir, out_prefix + suffix + ".FRM")
        new_data = rebuild_frm(self.frm_header, self.output_frames)
        with open(out_name, "wb") as f:
            f.write(new_data)
        messagebox.showinfo("Saved", f"Saved to {out_name}")

    #def undo_frame(self):
    #    self.output_frames[self.frame_index] = dict(self.input_frames[self.frame_index])
    #    self.display_frame()

    #def next_frame(self):
    #    if self.frame_index < len(self.output_frames) - 1:
    #        self.frame_index += 1
    #        self.display_frame()

    #def prev_frame(self):
    #    if self.frame_index > 0:
    #        self.frame_index -= 1
    #        self.display_frame()

    def undo_frame(self):
        i = self.frame_index
        self.output_frames[i] = copy.deepcopy(self.input_frames[i])#[:]
        self.display_frame()


    def change_frame(self, delta):
        self.frame_index = (self.frame_index + delta) % len(self.output_frames)
        self.display_frame()
    

if __name__ == "__main__":
    root = tk.Tk()
    app = RecolourApp(root)
    root.mainloop()
