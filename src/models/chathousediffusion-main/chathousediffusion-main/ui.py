import tkinter as tk
import math
from tkinter import Button, Text, Frame, Label
from PIL import Image, ImageDraw, ImageTk
from predict import predict_prepare
from functools import partial
from prompt2json import prompt2json, updatePrompt
from openai import OpenAI
import json

api_info=json.load(open("api_info.json"))

client = OpenAI(
    # 此处请替换自己的api
    api_key=api_info["api_key"],
    base_url=api_info["base_url"],
)


class DrawingApp:
    def __init__(self, root):

        self.root = root
        self.root.title("Floor Plan Generator")

        top_frame = Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        pil_image = Image.open("label.png")
        resized_image = pil_image.resize((400, 100), Image.Resampling.LANCZOS)
        self.label_image = ImageTk.PhotoImage(resized_image)
        label = Label(top_frame, image=self.label_image)
        label.pack(side=tk.BOTTOM)

        bottom_frame = Frame(root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=5)

        self.canvas = tk.Canvas(root, bg="white", width=400, height=400)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)

        self.draw_mode_button = Button(
            top_frame, text="Line", command=self.toggle_draw_mode
        )
        self.draw_mode_button.pack(side=tk.LEFT, padx=5)

        undo_button = Button(top_frame, text="Cancel (ctrl-z)", command=self.undo)
        undo_button.pack(side=tk.LEFT, pady=5, padx=5)

        clear_button = Button(top_frame, text="Clear", command=self.clear_canvas)
        clear_button.pack(side=tk.RIGHT, pady=5, padx=5)

        self.generate_button = Button(
            top_frame,
            text="Generate",
            command=partial(self.generate_image, repredict=False),
        )
        self.generate_button.pack(side=tk.RIGHT, pady=5, padx=5)

        self.regenerate_button = Button(
            top_frame,
            text="Regenerate",
            command=partial(self.generate_image, repredict=True),
        )
        self.regenerate_button.pack(side=tk.RIGHT, pady=5, padx=5)
        self.regenerate_button.config(state=tk.DISABLED)

        self.save_button = Button(top_frame, text="Save", command=self.save_image)
        self.save_button.pack(side=tk.RIGHT, pady=5, padx=5)
        self.save_button.config(state=tk.DISABLED)

        self.text_input = Label(bottom_frame, text="Text prompt")
        self.text_input.pack(side=tk.LEFT, padx=5)

        self.text_input = Text(bottom_frame, width=45, height=4)
        self.text_input.place
        self.text_input.pack(side=tk.RIGHT, padx=5)

        self.drawing_enabled = False
        self.last_point = None
        self.lines = []
        self.image = Image.new("RGB", (400, 400), "white")
        self.image_draw = ImageDraw.Draw(self.image)

        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Escape>", self.exit_draw_mode)

        self.text_history = []
        self.binary_image = None

        self.trainer=predict_prepare()

    def toggle_draw_mode(self):
        self.drawing_enabled = not self.drawing_enabled
        self.draw_mode_button.config(
            text="Exit (Esc)" if self.drawing_enabled else "Line"
        )
        if not self.drawing_enabled:
            self.canvas.delete("temp_line")
            self.last_point = None

    def handle_click(self, event):
        if not self.drawing_enabled:
            return

        snap_point = self.get_snap_point(event.x, event.y)
        if self.last_point:
            self.canvas.create_line(self.last_point + snap_point, fill="black", width=2)
            self.image_draw.line(self.last_point + snap_point, fill="black", width=2)
            self.lines.append((self.last_point, snap_point))
        self.last_point = snap_point
        self.canvas.delete("temp_line")

    def on_mouse_move(self, event):
        if not self.drawing_enabled or not self.last_point:
            return
        snap_point = self.get_snap_point(event.x, event.y)
        self.canvas.delete("temp_line")
        self.canvas.create_line(
            self.last_point + snap_point, fill="black", dash=(4, 2), tags="temp_line"
        )

    def get_snap_point(self, x, y):
        # Calculate the angle for orthogonal snapping
        if self.last_point:
            dx, dy = x - self.last_point[0], y - self.last_point[1]
            if dx != 0:  # Prevent division by zero
                angle = abs(
                    math.atan(dy / dx) * (180 / math.pi)
                )  # Convert angle to degrees
                # Check if the angle is within 10 degrees of horizontal or vertical
                if angle < 10 or angle > 80:
                    if abs(dx) > abs(dy):
                        for line in self.lines[:-1]:
                            if abs(x - line[0][0]) < 10:
                                return (line[0][0], self.last_point[1])
                        return (x, self.last_point[1])  # Snap horizontally
                    else:
                        for line in self.lines[:-1]:
                            if abs(y - line[0][1]) < 10:
                                return (self.last_point[0], line[0][1])
                        return (self.last_point[0], y)  # Snap vertically
        # Endpoint snapping
        for line in self.lines[:-1]:
            for point in (line[0], line[1]):
                if abs(x - point[0]) < 10 and abs(y - point[1]) < 10:
                    return point
                if abs(x - point[0]) < 10:
                    return (point[0], y)
                if abs(y - point[1]) < 10:
                    return (x, point[1])
        return (x, y)

    def undo(self, event=None):
        if not self.lines:
            return
        self.lines.pop()
        self.last_point = self.lines[-1][1] if self.lines else None
        self.redraw_canvas()

    def redraw_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (400, 400), "white")
        self.image_draw = ImageDraw.Draw(self.image)
        for line in self.lines:
            self.canvas.create_line(line[0] + line[1], fill="black", width=2)
            self.image_draw.line(line[0] + line[1], fill="black", width=2)

    def get_binary(self):
        if len(self.lines) > 1:
            self.image_draw.line(
                self.lines[-1][1] + self.lines[0][0], fill="black", width=2
            )

        fill_image = self.image.copy()
        fill_draw = ImageDraw.Draw(fill_image)

        for line in self.lines:
            fill_draw.line(line[0] + line[1], fill="black", width=2)

        bbox = fill_image.getbbox()
        ImageDraw.floodfill(
            fill_image, xy=(bbox[0] + 1, bbox[1] + 1), value=(0, 0, 0), border=None
        )

        gray_image = fill_image.convert("L")
        binary_image = gray_image.point(lambda x: 0 if x > 128 else 255, "1")

        binary_image = binary_image.resize((64, 64), Image.Resampling.BOX)
        self.binary_image = binary_image

    def exit_draw_mode(self, event=None):
        self.drawing_enabled = False
        self.draw_mode_button.config(text="Line")
        self.canvas.delete("temp_line")  # Remove any temporary line
        self.last_point = None  # Reset last point

    def clear_canvas(self):
        self.canvas.delete("all")
        self.lines = []
        self.image = Image.new("RGB", (400, 400), "white")
        self.image_draw = ImageDraw.Draw(self.image)
        self.text_input.delete(1.0, tk.END)
        self.exit_draw_mode()
        self.binary_image = None
        self.generate_button.config(text="Generate")
        self.regenerate_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)

    def generate_image(self, repredict=False):
        text = self.text_input.get("1.0", tk.END)
        if self.binary_image is None:
            self.get_binary()
        mask = self.binary_image
        # save mask
        mask.save("mask.png")

        ## text generation ###########
        if len(text) < 5:
            new_text = self.text_history[-1]
        if repredict:
            self.text_history = []
            if len(text) >= 5:
                new_text, mid = prompt2json(text, client=client, model=api_info["model"])
        else:
            if self.generate_button.cget("text") == "Generate":
                new_text, mid = prompt2json(text, client=client, model=api_info["model"])
            elif self.generate_button.cget("text") == "Edit":
                new_text, mid = updatePrompt(
                    original_json_str=self.mid,
                    new_description=text,
                    client=client,
                    model=api_info["model"],
                )
            self.mid=mid
        # save new_text as json
        with open("new_text.json", "w") as f:
            f.write(new_text)
        self.text_history.append(new_text)
        ##############################
        
        prediction = self.trainer.predict(mask, new_text, repredict=repredict)
        self.canvas.delete("all")
        self.lines = []
        self.text_input.delete(1.0, tk.END)
        # draw prediction on canvas
        prediction = prediction.resize((400, 400))
        self.image = prediction
        self.image_draw = ImageDraw.Draw(self.image)
        self.tk_image = ImageTk.PhotoImage(prediction)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        self.exit_draw_mode()
        self.generate_button.config(text="Edit")
        self.regenerate_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)

    def save_image(self):
        self.image.save("drawing.png")


root = tk.Tk()
app = DrawingApp(root)
root.mainloop()
