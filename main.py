#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Tkinter import *
import tkFileDialog
import tkMessageBox
from PIL import Image, ImageTk
import os
import glob
import math

# colors for the bboxes
# COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']

CLASS_COLORS = ['red', 'blue', 'brown', 'green', 'salmon', 'cyan', 'gold', 'orange', 'purple', 'violet', 'tomato', 'sky blue']
ROTATE_IMAGE = True


class LabelTool:
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("Annotation Tool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=FALSE, height=FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList = []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.rootDir = ''
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None
        self.img = None
        self.rotated_degree = 0
        self.cur_class_idx = -1
        self.truncated = IntVar()
        self.classes = None
        self.cur_scale = 1.0

        # initialize mouse state
        self.STATE = {
            'click': 0,
            'x': 0,
            'y': 0
        }

        # reference to bbox
        self.rect_ids = []
        self.bboxId = None
        self.bboxList = []
        self.indexes_to_change = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        # self.ldBtn = Button(self.frame, text="Load", command=self.choose_dir)
        # self.ldBtn.grid(row=0, column=0, columnspan=3, sticky=W+E)
        # self.choose_dir()

        self.pnl_left = Frame(self.frame)
        self.pnl_left.grid(row=0, column=0, sticky=W+N+S, padx=5)

        self.lbl_class = Label(self.pnl_left, text='Choose object class:')
        self.lbl_class.pack(anchor=W)

        sv_search = StringVar()
        sv_search.trace('w', lambda name, index, mode, sv=sv_search: self.on_search(sv))
        self.txt_search = Entry(self.pnl_left, width=24, textvariable=sv_search)
        self.txt_search.pack(anchor=W)
        pnl = Frame(self.pnl_left)
        pnl.pack(fill=Y, expand=True)
        scrollbar = Scrollbar(pnl, orient=VERTICAL)
        self.lb_class = Listbox(pnl, yscrollcommand=scrollbar.set, width=25, height=25)
        scrollbar.config(command=self.lb_class.yview)
        self.lb_class.bind('<<ListboxSelect>>', self.on_class_select)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.lb_class.pack(side=LEFT, fill=Y)

        self.pnl_add = Frame(self.pnl_left)
        self.pnl_add.pack(anchor=W, fill=X)
        self.txt_class = Entry(self.pnl_add, width=15)
        self.txt_class.pack(side=LEFT, expand=True, fill=X)
        self.btn_add = Button(self.pnl_add, text="Add", command=self.add_class)
        self.btn_add.pack(side=RIGHT)

        self.btn_del = Button(self.pnl_left, text="Delete", command=self.remove_class)
        self.btn_del.pack(anchor=W, fill=X)

        self.chk_truncated = Checkbutton(self.pnl_left, text="Truncated(t)", variable=self.truncated)
        self.chk_truncated.pack(anchor=W)

        self.pnl_rotate = Frame(self.pnl_left)
        self.pnl_rotate.pack()
        self.btn_counterclockwise = Button(self.pnl_rotate, text='↺', command=self.rotate_counterclockwise)
        self.btn_counterclockwise.pack(side=LEFT)
        self.lbl_rotate = Label(self.pnl_rotate, text='0°')
        self.lbl_rotate.pack(side=LEFT)
        self.btn_clockwise = Button(self.pnl_rotate, text='↻', command=self.rotate_clockwise)
        self.btn_clockwise.pack(side=LEFT)
        self.btn_zoom_out = Button(self.pnl_rotate, text='-', command=self.zoom_out)
        self.btn_zoom_out.pack(side=LEFT)
        self.lbl_scale = Label(self.pnl_rotate, text='100%')
        self.lbl_scale.pack(side=LEFT)
        self.btn_zoom_in = Button(self.pnl_rotate, text='+', command=self.zoom_in)
        self.btn_zoom_in.pack(side=LEFT)

        # main panel for labeling
        self.pnl_center = Frame(self.frame)
        self.pnl_center.grid(row=0, column=1, sticky=W+E+N+S)

        self.lbl_image = Label(self.pnl_center, text='')
        self.lbl_image.pack(anchor=W)

        self.canvas = Canvas(self.pnl_center, cursor='tcross')
        self.canvas.bind("<Button-1>", self.mouse_click)
        self.canvas.bind("<Motion>", self.mouse_move)
        self.hbar = Scrollbar(self.pnl_center, orient=HORIZONTAL)
        self.hbar.config(command=self.canvas.xview)
        self.hbar.pack(side=BOTTOM, fill=X)
        self.vbar = Scrollbar(self.pnl_center, orient=VERTICAL)
        self.vbar.config(command=self.canvas.yview)
        self.vbar.pack(side=RIGHT, fill=Y)
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.pack(side=LEFT, expand=True, fill=BOTH)

        # showing bbox info & delete bbox
        self.pnl_right = Frame(self.frame)
        self.pnl_right.grid(row=0, column=2, sticky=E+N+S, padx=5)

        self.lb1 = Label(self.pnl_right, text='Bounding boxes:')
        self.lb1.pack(anchor=W)
        pnl = Frame(self.pnl_right)
        pnl.pack(fill=Y, expand=True)
        scrollbar = Scrollbar(pnl, orient=VERTICAL)
        self.listbox = Listbox(pnl, yscrollcommand=scrollbar.set, selectmode=EXTENDED, width=25, height=25)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox.pack(side=LEFT, fill=Y)
        self.btnDel = Button(self.pnl_right, text='Delete', command=self.del_bbox)
        self.btnDel.pack(anchor=W, fill=X)
        self.btnChangeClass = Button(self.pnl_right, text='Change Class', command=self.change_class)
        self.btnChangeClass.pack(anchor=W, fill=X)
        self.btnChangeSize = Button(self.pnl_right, text='Change Size', command=self.change_size)
        self.btnChangeSize.pack(anchor=W, fill=X)
        self.btnChangeTruncated = Button(self.pnl_right, text='Toggle Truncated', command=self.toggle_truncated)
        self.btnChangeTruncated.pack(anchor=W, fill=X)
        self.btnHideAll = Button(self.pnl_right, text="Hide All", command=self.hide_all)
        self.btnHideAll.pack(anchor=W, fill=X)
        self.btnShowAll = Button(self.pnl_right, text="Show All", command=self.show_all)
        self.btnShowAll.pack(anchor=W, fill=X)

        # control panel for image navigation
        self.pnl_bottom = Frame(self.frame)
        self.pnl_bottom.grid(row=1, column=0, columnspan=3, sticky=W+E)
        self.prevBtn = Button(self.pnl_bottom, text='<< Prev', width=10, command=self.prev_image)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(self.pnl_bottom, text='Next >>', width=10, command=self.next_image)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(self.pnl_bottom, text="Progress:     /    ")
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(self.pnl_bottom, text="Go to Image No.")
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(self.pnl_bottom, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(self.pnl_bottom, text='Go', command=self.goto_image)
        self.goBtn.pack(side=LEFT)

        # display mouse position
        self.disp = Label(self.pnl_bottom, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.parent.bind("<Escape>", self.cancel_bbox)  # press <Espace> to cancel current bbox
        # self.parent.bind("a", self.prev_image)  # press 'a' to go backforward
        # self.parent.bind("d", self.next_image)  # press 'd' to go forward
        self.parent.bind("t", self.change_truncated)
        # for i in range(len(self.classes)):
        #     self.parent.bind(str(i + 1), self.on_num_press)
        # with Windows OS
        self.parent.bind_all("<MouseWheel>", self.mouse_wheel_v)
        self.parent.bind_all("<Shift-MouseWheel>", self.mouse_wheel_h)
        self.parent.bind_all("<Control-MouseWheel>", self.mouse_zoom)
        # with Linux OS
        # self.canvas.bind("<Button-4>", self.mouse_wheel)
        # self.canvas.bind("<Button-5>", self.mouse_wheel)

        self.parent.after(100, self.choose_dir)

    def choose_dir(self, event=None):
        self.rootDir = tkFileDialog.askdirectory()
        self.load_classes()
        self.load_dir()

    def load_dir(self):
        self.parent.focus()
        # if not os.path.isdir(s):
        #     tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
        #     return
        # get image list
        self.imageDir = os.path.join(self.rootDir, 'images')
        self.imageList = sorted(glob.glob(os.path.join(self.imageDir, '*.jpg')))
        if len(self.imageList) == 0:
            self.imageList = sorted(glob.glob(os.path.join(self.imageDir, '*.png')))
        if len(self.imageList) == 0:
            print 'No images found in the specified dir!'
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        # set up output dir
        self.outDir = os.path.join(self.rootDir, 'annotations')
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        self.load_image()
        print '%d images loaded' % self.total

    def add_class(self):
        new_class = self.txt_class.get().strip().encode('utf-8')
        if not new_class:
            return
        self.classes.append(new_class)
        self.classes.sort()
        index = self.classes.index(new_class)
        self.txt_class.delete(0, END)
        self.show_class_list()
        self.lb_class.see(index)
        self.save_classes()

    def remove_class(self):
        sel = self.lb_class.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.classes.pop(idx)
        self.lb_class.delete(idx)
        self.save_classes()

    def load_classes(self):
        with open(os.path.join(self.rootDir, 'classes.txt')) as f:
            self.classes = [line.strip() for line in f.readlines() if line]
        self.show_class_list()

    def save_classes(self):
        with open(os.path.join(self.rootDir, 'classes.txt'), 'w') as f:
            f.writelines([cls + '\n' for cls in self.classes])

    def show_class_list(self):
        self.lb_class.delete(0, END)
        for cls in self.classes:
            self.lb_class.insert(END, '{}'.format(cls))
            self.lb_class.itemconfig(END, fg=self.get_class_color(cls))

    def on_search(self, sv):
        keyword = sv.get().encode('utf-8')
        if not hasattr(self, 'lb_class'):
            return
        self.lb_class.delete(0, END)
        for cls in self.classes:
            if not keyword or keyword in cls:
                self.lb_class.insert(END, '{}'.format(cls))
                self.lb_class.itemconfig(END, fg=self.get_class_color(cls))

    def draw(self):
        self.canvas.delete(ALL)

        if ROTATE_IMAGE:
            img = self.img.rotate(self.rotated_degree, resample=Image.BICUBIC)
        else:
            img = self.img
        if self.cur_scale != 1:
            img = img.resize((int(img.size[0] * self.cur_scale), int(img.size[1] * self.cur_scale)), Image.BILINEAR)
        self.tkimg = ImageTk.PhotoImage(img)
        self.canvas.config(width=self.tkimg.width(), height=self.tkimg.height(), highlightthickness=0)
        self.canvas.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.canvas.config(scrollregion=self.canvas.bbox(ALL))

        for bbox in self.bboxList:
            cls = bbox['class']
            if self.cur_class_idx > -1 and self.classes[self.cur_class_idx] != cls:
                continue
            tmp = bbox['bbox']
            if not ROTATE_IMAGE and self.rotated_degree != 0:
                tmp = self.rotate_annotation(bbox['bbox'][0], bbox['bbox'][1], bbox['bbox'][2], bbox['bbox'][3],
                                             -self.rotated_degree, self.tkimg.width() / 2, self.tkimg.height() / 2)
            truncated = bbox['truncated']
            self.draw_bbox(cls, tmp, truncated)

    def draw_bbox(self, cls, bbox, truncated):
        if self.cur_scale != 1:
            tmp = list(bbox)
            for i in range(4):
                tmp[i] *= self.cur_scale
        else:
            tmp = bbox
        rect_id = self.canvas.create_rectangle(tmp[0], tmp[1], tmp[2], tmp[3], width=1,
                                               outline=self.get_class_color(cls),
                                               dash=(3, 4) if truncated else None)
        self.rect_ids.append(rect_id)

    def rotate_annotation(self, x1, y1, x2, y2, rotated_degree, center_x, center_y):
        x3 = x1
        y3 = y2
        x4 = x2
        y4 = y1
        x1 -= center_x
        y1 -= center_y
        x2 -= center_x
        y2 -= center_y
        x3 -= center_x
        y3 -= center_y
        x4 -= center_x
        y4 -= center_y
        angle = rotated_degree * math.pi / 180
        a = math.cos(angle)
        b = math.sin(angle)
        p0_x = x1 * a + y1 * b + center_x
        p0_y = y1 * a - x1 * b + center_y
        p1_x = x2 * a + y2 * b + center_x
        p1_y = y2 * a - x2 * b + center_y
        p2_x = x3 * a + y3 * b + center_x
        p2_y = y3 * a - x3 * b + center_y
        p3_x = x4 * a + y4 * b + center_x
        p3_y = y4 * a - x4 * b + center_y
        x1 = int(math.floor(min(p0_x, p1_x, p2_x, p3_x)))
        y1 = int(math.floor(min(p0_y, p1_y, p2_y, p3_y)))
        x2 = int(math.ceil(max(p0_x, p1_x, p2_x, p3_x)))
        y2 = int(math.ceil(max(p0_y, p1_y, p2_y, p3_y)))
        return [x1, y1, x2, y2]

    def load_image(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        self.lbl_image.config(text=os.path.split(imagepath)[-1])
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        # load labels
        self.clear_bbox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    parts = line.split()
                    cls = parts[0]
                    if cls == 'rotate':
                        self.rotated_degree = int(parts[1])
                        continue
                    tmp = [int(t.strip()) for t in parts[1:5]]
                    truncated = 1 if len(parts) >= 6 and parts[5] == '1' else 0
                    self.bboxList.append({
                        'class': cls,
                        'bbox': tuple(tmp),
                        'truncated': truncated
                    })
            self.bboxList.sort(key=lambda bbox: bbox['class'])
            for bbox in self.bboxList:
                cls = bbox['class']
                tmp = bbox['bbox']
                self.listbox.insert(END, '%s (%d, %d, %d, %d)' % (cls, tmp[0], tmp[1], tmp[2], tmp[3]))
                self.listbox.itemconfig(END, fg=self.get_class_color(cls))

        self.draw()

    def save_image(self):
        self.bboxList.sort(key=lambda bbox: bbox['class'])
        with open(self.labelfilename, 'w') as f:
            f.write('rotate {}\n'.format(self.rotated_degree))
            for i, item in enumerate(self.bboxList):
                f.write(item['class'] + ' ' + ' '.join(map(str, item['bbox'])) + (' 1' if item['truncated'] else ' 0'))
                if i < len(self.bboxList) - 1:
                    f.write('\n')
        print 'Image No. %d saved' % self.cur

    def mouse_click(self, event):
        if self.cur_scale < 1 - 1e-5:
            tkMessageBox.showwarning('禁止标注', '不允许在小图上进行标注操作')
            return
        x = int(self.canvas.canvasx(event.x))
        y = int(self.canvas.canvasy(event.y))
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = x, y
        else:
            x1, x2 = min(self.STATE['x'], x), max(self.STATE['x'], x)
            y1, y2 = min(self.STATE['y'], y), max(self.STATE['y'], y)
            if self.cur_scale != 1:
                x1 = int(round(float(x1) / self.cur_scale))
                x2 = int(round(float(x2) / self.cur_scale))
                y1 = int(round(float(y1) / self.cur_scale))
                y2 = int(round(float(y2) / self.cur_scale))
            cls = self.classes[self.cur_class_idx]
            self.bboxList.append({
                'class': cls,
                'bbox': (x1, y1, x2, y2),
                'truncated': self.truncated.get()
            })
            self.rect_ids.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '%s (%d, %d, %d, %d)' % (cls, x1, y1, x2, y2))
            self.listbox.itemconfig(END, fg=self.get_class_color(self.classes[self.cur_class_idx]))
        self.STATE['click'] = 1 - self.STATE['click']

    def mouse_move(self, event):
        x = int(self.canvas.canvasx(event.x))
        y = int(self.canvas.canvasy(event.y))
        self.disp.config(text='x: %d, y: %d' % (x, y))
        if self.tkimg:
            if self.hl:
                self.canvas.delete(self.hl)
            self.hl = self.canvas.create_line(0, y, self.tkimg.width(), y, width=1)
            if self.vl:
                self.canvas.delete(self.vl)
            self.vl = self.canvas.create_line(x, 0, x, self.tkimg.height(), width=1)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.canvas.delete(self.bboxId)
            self.bboxId = self.canvas.create_rectangle(self.STATE['x'], self.STATE['y'], x, y, width=1,
                                                          outline=self.get_class_color(self.classes[self.cur_class_idx]),
                                                          dash=(3, 4) if self.truncated.get() else None)

    def mouse_wheel_v(self, event):
        if event.state == 1 or event.state == 4:  # Shift or Control key is pressed
            return
        widget = self.parent.winfo_containing(event.x_root, event.y_root)
        if widget == self.canvas:
            widget.focus_force()  # fix bug on Windows: left listbox scrolls if it has focus
            delta = -1 if event.delta > 0 else 1
            widget.yview_scroll(delta, 'units')

    def mouse_wheel_h(self, event):
        widget = self.parent.winfo_containing(event.x_root, event.y_root)
        if widget == self.canvas:
            delta = -1 if event.delta > 0 else 1
            event.widget.xview_scroll(delta, 'units')

    def cancel_bbox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.canvas.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def del_bbox(self, event=None):
        sel = self.listbox.curselection()
        if len(sel) <= 0:
            return
        sel = [int(s) for s in sel]
        for idx in sorted(sel, reverse=True):
            idx = int(idx)
            self.bboxList.pop(idx)
            self.listbox.delete(idx)
        for rect_id in self.rect_ids:
            self.canvas.delete(rect_id)
        del self.rect_ids[:]

    def change_class(self, event=None):
        sel = self.listbox.curselection()
        if len(sel) <= 0:
            return
        for idx in sel:
            idx = int(idx)
            self.indexes_to_change.append(idx)

    def change_size(self, event=None):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.cur_class_idx = self.classes.index(self.bboxList[idx]['class'])
        self.bboxList.pop(idx)
        self.listbox.delete(idx)
        for rect_id in self.rect_ids:
            self.canvas.delete(rect_id)
        del self.rect_ids[:]

    def toggle_truncated(self, event=None):
        sel = self.listbox.curselection()
        if len(sel) <= 0:
            return
        for idx in sel:
            idx = int(idx)
            self.bboxList[idx]['truncated'] = 1 - self.bboxList[idx]['truncated']
        self.on_select()

    def clear_bbox(self, event=None):
        for idx in range(len(self.rect_ids)):
            self.canvas.delete(self.rect_ids[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.rect_ids = []
        self.bboxList = []

    def hide_all(self, event=None):
        for rect_id in self.rect_ids:
            self.canvas.delete(rect_id)
        self.rect_ids = []

    def show_all(self, event=None):
        self.lb_class.select_clear(0, self.lb_class.size() - 1)
        self.cur_class_idx = -1
        for i, item in enumerate(self.bboxList):
            cls = item['class']
            bbox = item['bbox']
            truncated = item['truncated']
            self.draw_bbox(cls, bbox, truncated)

    def prev_image(self, event=None):
        self.save_image()
        if self.cur > 1:
            self.cur -= 1
            self.load_image()

    def next_image(self, event=None):
        self.save_image()
        if self.cur < self.total:
            self.cur += 1
            self.load_image()

    def goto_image(self, event=None):
        idx = int(self.idxEntry.get())
        if 1 <= idx <= self.total:
            self.save_image()
            self.cur = idx
            self.load_image()

    def on_select(self, event=None):
        self.hide_all()
        sel = self.listbox.curselection()
        for idx in sel:
            idx = int(idx)
            item = self.bboxList[idx]
            cls = item['class']
            bbox = item['bbox']
            truncated = item['truncated']
            self.draw_bbox(cls, bbox, truncated)

    # def on_num_press(self, event):
    #     self.cur_class_idx = int(event.char) - 1
    #     self.lb_class.select_clear(0, self.lb_class.size() - 1)
    #     self.lb_class.selection_set(self.cur_class_idx)

    def on_class_select(self, event):
        sel = self.lb_class.curselection()
        if len(sel) != 1:
            return
        index = int(sel[0])
        cur_class_name = self.lb_class.get(index).encode('utf-8')
        self.cur_class_idx = self.classes.index(cur_class_name)
        # change bbox classes if needed
        if len(self.indexes_to_change) > 0:
            for idx in self.indexes_to_change:
                old_class = self.bboxList[idx]['class']
                new_class = cur_class_name
                self.bboxList[idx]['class'] = new_class
                new_text = self.listbox.get(idx).encode('utf-8').replace(old_class, new_class)
                self.listbox.delete(idx)
                self.listbox.insert(idx, new_text)
                self.listbox.itemconfig(idx, fg=self.get_class_color(new_class))
            del self.indexes_to_change[:]
        # mark the bbox list items selected
        self.listbox.select_clear(0, END)
        for i in range(self.listbox.size()):
            if cur_class_name in self.listbox.get(i).encode('utf-8'):
                self.listbox.select_set(i)
        # redraw the selected rectangles
        self.draw()

    def change_truncated(self, event):
        self.truncated.set(1 - self.truncated.get())

    def rotate_clockwise(self):
        self.rotated_degree -= 1
        self.lbl_rotate.config(text='{}°'.format(self.rotated_degree))
        self.draw()

    def rotate_counterclockwise(self):
        self.rotated_degree += 1
        self.lbl_rotate.config(text='{}°'.format(self.rotated_degree))
        self.draw()

    def zoom_in(self):
        if self.cur_scale >= 2.0 - 1e-5:
            return
        self.cur_scale += 0.1
        self.lbl_scale.config(text='{}%'.format(self.cur_scale * 100))
        self.draw()

    def zoom_out(self):
        if self.cur_scale <= 0.5 + 1e-5:
            return
        self.cur_scale -= 0.1
        self.lbl_scale.config(text='{}%'.format(self.cur_scale * 100))
        self.draw()

    def mouse_zoom(self, event):
        widget = self.parent.winfo_containing(event.x_root, event.y_root)
        if widget == self.canvas:
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()

    def get_class_color(self, cls):
        return CLASS_COLORS[self.classes.index(cls) % len(CLASS_COLORS)]

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width=True, height=True)
    root.mainloop()
