import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import tkinter as tk
from PIL import ImageTk, Image, ImageGrab
import ctypes
import scipy.ndimage
from MapUtil import *


def main():
    map_json = map_data_class 
    map_array = map_data_class
    map_graph = map_pretty_class
    map_json = get_data_from_json('MapMeasDemo.json')#get_data_from_json('MapLog.json')
    map_array = compute_map(map_json) #transform the json's map from a vector to a 2D array
    map_graph = create_colored_map(in_map=map_array,file_name="foo",format="png")

    widget = painter_class(map_array,map_graph)

    #add background image to the canvas
    #done in the main because the class does not read the file
    #print(map_graph.file)
    img_file = Image.open(map_graph.file) 
    img_tk = ImageTk.PhotoImage(img_file)
    widget.canvas.create_image(0,0, image=img_tk, anchor='nw')

    #add functionnalities
    widget.canvas.bind('<MouseWheel>',lambda event: set_brush_size(event,widget))
    #When dragging the mouse
    widget.canvas.bind('<B1-Motion>',lambda event: draw_on_canvas(event,widget,map_graph))
    widget.canvas.bind('<B3-Motion>',lambda event: erase_on_canvas(event,widget,map_graph))
    #for a single click
    widget.canvas.bind('<Button-1>',lambda event: draw_on_canvas(event,widget,map_graph))
    widget.canvas.bind('<Button-3>',lambda event: erase_on_canvas(event,widget,map_graph))
    #save button
    widget.button.config(command = lambda: save_canvas(widget,map_array,map_graph))

    #execute the widget
    widget.run()

###############################################################################################
#CLASSES

class map_pretty_class():
        def __init__(self):
            self.file = None
            self.color_0 = None
            self.color_1 = None
            self.palette = None

        def __init__(self,file,c0,c1,palette):
            self.file = file
            self.color_0 = c0
            self.color_1 = c1
            self.palette = palette

class painter_class():
    def __init__(self,map_data,map_pretty):
        #default parameters
        self.brush_size = 5
        #create widget window
        self.window = tk.Tk()
        #add the name of the file
        self.label_file = tk.Label(self.window,text=map_pretty.file)
        #create drawing canvas
        self.canvas = tk.Canvas(self.window,width=map_data.width,height=map_data.height,borderwidth=0,highlightthickness=0)
        self.canvas.config()
        #create a label
        self.label_brush = tk.Label(self.window,text="Brush size = "+str(self.brush_size),height=1,width=self.canvas.winfo_reqwidth())
        #create a button
        self.button = tk.Button(self.window,text="Save map")
        #assemble graphical elements
        self.label_file.pack()
        self.canvas.pack()#expand=1)
        self.label_brush.pack()
        self.button.pack()

        #fix the dimensions
        dimx = int(map_data.width)
        dimy = (self.label_file.winfo_reqheight()+
                self.canvas.winfo_reqheight()+
                self.label_brush.winfo_reqheight()+
                self.button.winfo_reqheight())
        self.window.geometry(str(dimx)+'x'+str(dimy))
        self.window.resizable(False,False)
     
    def run(self):
        self.window.mainloop()

###############################################################################################
#FUNCTIONS IN MAIN 

def create_colored_map(in_map: map_data_class,file_name,format):
    #get the colormap
    # 'magma', 'inferno', 'plasma', 'viridis, 'cividis', 'turbo'
    clrm = mpl.colormaps['viridis']
    clrm_array = (np.asarray(clrm.colors)*255).astype('uint8')

    #plot the result
    #the use of plt.imshow(...) later crashes canvas.create_image(...)
    #map_plt = plt.imshow(in_map.map,cmap=clrm,extent=[in_map.xmin,in_map.xmax,in_map.ymin,in_map.xmax])
    #plt.show   

    #Create an image file
    map_img = Image.fromarray((in_map.map*255).astype('uint8'),'L')
    map_img.putpalette(clrm_array)
    saved_name = file_name+'.'+format
    map_img.save(saved_name)

    #extreme colors of the colormap
    min_color = '#%02x%02x%02x' % tuple(clrm_array[1]) #convert to hex
    max_color = '#%02x%02x%02x' % tuple(clrm_array[-1])

    return map_pretty_class(saved_name,min_color,max_color,clrm_array)

###############################################################################################
#FUNCTIONS FOR THE WIDGET
def set_brush_size(event,self):
    max_brush_size = 100
    min_brush_size = 0
    step_brush_size = 1
    if event.delta>0:
        self.brush_size += step_brush_size
        if self.brush_size>max_brush_size:
            self.brush_size = max_brush_size
    else:
        self.brush_size -= step_brush_size
        if self.brush_size<min_brush_size:
             self.brush_size = min_brush_size
    self.label_brush.config(text="Brush size = "+str(self.brush_size))


def draw_on_canvas(event,widget,graph):
    if widget.brush_size>0:
        widget.canvas.create_oval(event.x - widget.brush_size/2,
            event.y + widget.brush_size/2,
            event.x + widget.brush_size/2,
            event.y - widget.brush_size/2,
            fill    = graph.color_1,
            outline = graph.color_1)

def erase_on_canvas(event,widget,graph):
    if widget.brush_size>0:
        widget.canvas.create_oval(event.x - widget.brush_size/2,
            event.y + widget.brush_size/2,
            event.x + widget.brush_size/2,
            event.y - widget.brush_size/2,
            fill    = graph.color_0,
            outline = graph.color_0)

def save_canvas(widget: painter_class,source_map: map_data_class, graph: map_pretty_class):
    #get the screen scale factor: 100% 125% 150% 200%
    #there is an invisible border around each side
    scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    x = (widget.window.winfo_rootx() + widget.canvas.winfo_x() +1) * scaleFactor
    y = (widget.window.winfo_rooty() + widget.canvas.winfo_y() +1) * scaleFactor
    width = (widget.canvas.winfo_width() -1) * scaleFactor 
    height = (widget.canvas.winfo_height() -1) * scaleFactor
    box = (x,y,x+width,y+height)
    img_edited = ImageGrab.grab(bbox = box)
    img_edited = img_edited.convert(mode='L')
    new_map = np.array(img_edited)/255.0

    # because of the scaling factor, the capture image does not have the same dimension as the original
    # thus a resampling is done
    x_zoom = source_map.width/new_map.shape[0]
    y_zoom = source_map.height/new_map.shape[1]
    new_map = scipy.ndimage.zoom(new_map,(x_zoom,y_zoom))
    #normalisation
    new_map = new_map - np.amin(new_map)
    new_map = new_map/np.amax(new_map)
    # When the screenshot is done, the colors are dimmed, a threshold is applied.
    # In the original picture where there was a 1 is now a 0.65. 
    # Assuming everything has been dimmed by the same factor
    # all value are scaled by 1/0.65 and clamped if they are above 1.
    new_map = new_map*(1/0.65)
    new_map[new_map>1] = 1
    print(new_map.shape)
    plt.imshow(new_map,cmap='viridis')
    plt.colorbar()
    plt.show()
    tempmapdataclass = map_data_class()
    tempmapdataclass.map = new_map
    array_to_json(source_map,tempmapdataclass,"MapEditedDemo.json")

###############################################################################################
#EXECUTION
if __name__ == '__main__':
    main()