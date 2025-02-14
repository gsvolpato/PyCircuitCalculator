import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk
import math
import logging

class EagleSymbol:
    def __init__(self, canvas):
        self.canvas = canvas
        self.scale = 20  # Scale factor to convert Eagle units to pixels
        self.rotation = 0  # Current rotation in degrees
        
    def draw_wire(self, x1, y1, x2, y2, layer="94"):
        x1, y1 = self.rotate_point(x1, y1)
        x2, y2 = self.rotate_point(x2, y2)
        
        canvas_x1 = x1 * self.scale
        canvas_y1 = -y1 * self.scale
        canvas_x2 = x2 * self.scale
        canvas_y2 = -y2 * self.scale
        
        return self.canvas.create_line(
            canvas_x1, canvas_y1, 
            canvas_x2, canvas_y2,
            fill=self.get_layer_color(layer), 
            width=2
        )
    
    def draw_circle(self, x, y, radius, layer="94"):
        x, y = self.rotate_point(x, y)
        canvas_x = x * self.scale
        canvas_y = -y * self.scale
        r = radius * self.scale
        
        return self.canvas.create_oval(
            canvas_x - r, canvas_y - r,
            canvas_x + r, canvas_y + r,
            outline=self.get_layer_color(layer),
            width=2
        )
    
    def draw_arc(self, x, y, radius, start_angle, end_angle, layer="94"):
        x, y = self.rotate_point(x, y)
        canvas_x = x * self.scale
        canvas_y = -y * self.scale
        r = radius * self.scale
        
        # Convert angles to degrees and adjust for coordinate system
        start = (start_angle + self.rotation) % 360
        extent = (end_angle - start_angle) % 360
        
        return self.canvas.create_arc(
            canvas_x - r, canvas_y - r,
            canvas_x + r, canvas_y + r,
            start=start, extent=extent,
            outline=self.get_layer_color(layer),
            style="arc", width=2
        )
    
    def draw_text(self, x, y, text, size=1.0, layer="94", align="center"):
        x, y = self.rotate_point(x, y)
        canvas_x = x * self.scale
        canvas_y = -y * self.scale
        
        font_size = int(size * 12)  # Convert Eagle text size to points
        return self.canvas.create_text(
            canvas_x, canvas_y,
            text=text,
            fill=self.get_layer_color(layer),
            font=("Arial", font_size),
            anchor=align
        )
    
    def draw_pin(self, x, y, length, direction, name, layer="94"):
        x, y = self.rotate_point(x, y)
        dx, dy = self.get_direction_vector(direction)
        
        # Convert coordinates to strings for text concatenation
        pin_x = str(x * self.scale)
        pin_y = str(-y * self.scale)
        
        # Draw pin line
        pin = self.draw_wire(
            x, y,
            x + dx * length, y + dy * length,
            layer
        )
        
        # Add pin name
        text = self.draw_text(
            x + dx * length * 1.2,
            y + dy * length * 1.2,
            str(name),  # Convert name to string
            size=0.8,
            layer=layer
        )
        
        return [pin, text]
    
    def rotate_point(self, x, y):
        if self.rotation == 0:
            return x, y
        angle = math.radians(self.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)
    
    def get_direction_vector(self, direction):
        angle = math.radians((direction + self.rotation) % 360)
        return (math.cos(angle), math.sin(angle))
    
    def get_layer_color(self, layer):
        colors = {
            "91": "#404040",  # Pins
            "94": "#000000",  # Symbols
            "95": "#808080",  # Names
            "96": "#404040",  # Values
            "97": "#FF0000",  # Info
            "98": "#0000FF",  # Guide
        }
        return colors.get(layer, "#000000")

class CircuitApp:
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        
        self.root = tk.Tk()
        self.root.title("Circuit Calculator")
        
        self.create_menu_bar()
        self.main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.create_sidebar()
        self.create_canvas()
        
        self.current_tool = "select"
        self.selected_components = []
        self.temp_component = []  # Changed to list to store multiple canvas items
        self.mouse_x = 0
        self.mouse_y = 0
        
        self.load_eagle_library("eagle_libraries/ngspice-simulation.lbr")
        
        self.sidebar_visible = True
        self.current_component = None
        
        self.exit_via_menu = False
        self.root.protocol("WM_DELETE_WINDOW", self.close_application_window)
        self.root.bind('<Alt-F4>', self.close_application_hotkey)
        
        # Force initial grid draw after window is fully initialized
        self.root.update_idletasks()  # Ensure geometry is updated
        self.draw_grid()
        
    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.menu_new)
        file_menu.add_command(label="Open", command=self.menu_open)
        file_menu.add_command(label="Save", command=self.menu_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.menu_exit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.menu_undo)
        edit_menu.add_command(label="Redo", command=self.menu_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.menu_cut)
        edit_menu.add_command(label="Copy", command=self.menu_copy)
        edit_menu.add_command(label="Paste", command=self.menu_paste)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.menu_zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.menu_zoom_out)
        view_menu.add_command(label="Reset Zoom", command=self.menu_zoom_reset)

    def menu_new(self):
        self.logger.info("Menu: New")
        # Add new file functionality

    def menu_open(self):
        self.logger.info("Menu: Open")
        # Add open file functionality

    def menu_save(self):
        self.logger.info("Menu: Save")
        # Add save functionality

    def menu_exit(self):
        self.logger.info("Menu: Exit selected")
        self.exit_via_menu = True
        self.close_application()

    def menu_undo(self):
        self.logger.info("Menu: Undo")
        # Add undo functionality

    def menu_redo(self):
        self.logger.info("Menu: Redo")
        # Add redo functionality

    def menu_cut(self):
        self.logger.info("Menu: Cut")
        # Add cut functionality

    def menu_copy(self):
        self.logger.info("Menu: Copy")
        # Add copy functionality

    def menu_paste(self):
        self.logger.info("Menu: Paste")
        # Add paste functionality

    def menu_zoom_in(self):
        self.logger.info("Menu: Zoom In")
        # Add zoom in functionality

    def menu_zoom_out(self):
        self.logger.info("Menu: Zoom Out")
        # Add zoom out functionality

    def menu_zoom_reset(self):
        self.logger.info("Menu: Reset Zoom")
        # Add zoom reset functionality

    def close_application_window(self):
        self.logger.info("Window close button (X) clicked")
        self.close_application()

    def close_application_hotkey(self, event):
        self.logger.info("Alt-F4 pressed")
        self.close_application()

    def close_application(self):
        if not self.exit_via_menu:
            self.logger.info("Application closed by window X or Alt-F4")
        self.logger.info("Application closing")
        self.root.quit()

    def create_sidebar(self):
        self.sidebar_frame = tk.Frame(self.main_container, width=80, bg='white')
        self.main_container.add(self.sidebar_frame)
        
        # Tool icons/buttons configuration
        tools = [
            ("select", "⬚", "Selection tool"),
            ("move", "⬌", "Move components"),
            ("rotate", "⟳", "Rotate"),
            ("mirror", "⟷", "Mirror"),
            ("duplicate", "⎘", "Duplicate"),
            ("delete", "⌫", "Delete"),
            ("add_part", "⊕", "Add Part"),
            ("replace", "↷", "Replace"),
            ("edit_part", "✎", "Edit Part"),
            ("net", "⌇", "Add Net"),
            ("junction", "●", "Add Junction"),
            ("label", "T", "Add Label"),
            ("name", "N", "Add Name"),
            ("value", "V", "Add Value"),
            ("split", "Y", "Split Wire")
        ]
        
        # Create tool buttons
        self.current_tool = tk.StringVar(value="select")
        self.tool_buttons = {}
        
        for row, (tool_id, symbol, tooltip) in enumerate(tools):
            btn = tk.Button(
                self.sidebar_frame,
                text=symbol,
                width=3,
                height=1,
                font=("Arial", 16),
                relief="flat",
                bg="white",
                activebackground="#e0e0e0",
                command=lambda t=tool_id: self.select_tool(t)
            )
            btn.grid(row=row, column=0, padx=5, pady=2, sticky="ew")
            
            # Create tooltip
            self.create_tooltip(btn, tooltip)
            
            self.tool_buttons[tool_id] = btn
        
        # Configure grid to center buttons
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
    
    def create_tooltip(self, widget, text):
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, bg="lightyellow", padx=5, pady=2)
            label.pack()
            
            widget.tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def select_tool(self, tool_id):
        self.logger.info(f"Selected tool: {tool_id}")
        self.current_tool = tool_id
        
        # Update button appearances
        for btn_id, btn in self.tool_buttons.items():
            if btn_id == tool_id:
                btn.config(bg="#e0e0e0")
            else:
                btn.config(bg="white")
        
        # Open parts window when add_part tool is selected
        if tool_id == "add_part":
            self.open_parts_window()

    def open_parts_window(self):
        parts_window = tk.Toplevel(self.root)
        parts_window.title("Select Component")
        parts_window.geometry("400x600")
        
        # Search frame
        search_frame = tk.Frame(parts_window)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(fill=tk.X)
        
        # Components list
        list_frame = tk.Frame(parts_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with scrollbar
        tree = ttk.Treeview(list_frame, show='tree', selectmode='browse')
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Organize components by category
        categories = {}
        for symbol_name in self.symbols.keys():
            # Extract category from symbol name (assuming format like "category/name")
            if '/' in symbol_name:
                category, name = symbol_name.split('/', 1)
            else:
                category = "Uncategorized"
                name = symbol_name
            
            if category not in categories:
                categories[category] = []
            categories[category].append((name, symbol_name))
        
        # Populate treeview
        for category, components in categories.items():
            category_id = tree.insert("", "end", text=category)
            for name, full_name in sorted(components):
                tree.insert(category_id, "end", text=name, values=(full_name,))
        
        def filter_components(event=None):
            search_text = search_var.get().lower()
            tree.delete(*tree.get_children())
            
            for category, components in categories.items():
                matching_components = [
                    (name, full_name) for name, full_name in components
                    if search_text in name.lower() or search_text in full_name.lower()
                ]
                
                if matching_components:
                    category_id = tree.insert("", "end", text=category)
                    for name, full_name in matching_components:
                        tree.insert(category_id, "end", text=name, values=(full_name,))
        
        def on_component_select(event):
            selected_item = tree.selection()[0]
            item_values = tree.item(selected_item)
            if item_values['values']:  # Make sure it's a component, not a category
                symbol_name = item_values['values'][0]
                self.logger.info(f"Selected component: {symbol_name}")
                self.current_component = symbol_name
                parts_window.destroy()
                # Switch to placement mode
                self.start_component_placement()
        
        # Bind events
        search_var.trace('w', lambda *args: filter_components())
        tree.bind('<Double-1>', on_component_select)
        search_entry.focus_set()

    def start_component_placement(self):
        self.canvas.bind("<Motion>", self.update_component_position)
        self.canvas.bind("<Button-1>", self.place_component)
        # Create initial preview
        self.create_temp_component(self.mouse_x, self.mouse_y)

    def create_canvas(self):
        self.canvas_frame = tk.Frame(self.main_container)
        self.main_container.add(self.canvas_frame)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='white', scrollregion=(-2000, -2000, 4000, 4000))
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add canvas dragging with middle mouse button
        self.canvas.bind('<Button-2>', self.start_canvas_drag)
        self.canvas.bind('<B2-Motion>', self.drag_canvas)
        self.canvas.bind('<ButtonRelease-2>', self.stop_canvas_drag)
        
        # Initialize canvas drag variables
        self.canvas_drag = False
        self.last_x = 0
        self.last_y = 0
        self.grid_items = []  # Store grid lines
        
        # Initialize component counters
        self.component_counters = {}
        
        # Bind window and canvas resize events
        self.root.bind('<Configure>', self.on_window_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)

    def on_window_configure(self, event=None):
        # Only handle if it's the main window being resized
        if event is None or event.widget == self.root:
            # Schedule grid redraw to allow canvas to update first
            self.root.after(100, self.draw_grid)

    def on_canvas_configure(self, event=None):
        # Canvas size changed - redraw grid
        self.draw_grid()

    def draw_grid(self):
        # Clear existing grid
        for item in self.grid_items:
            self.canvas.delete(item)
        self.grid_items.clear()
        
        # Get canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:  # Canvas not ready yet
            self.canvas.after(100, self.draw_grid)
            return
        
        # Get visible area with scroll offset
        visible_left = self.canvas.canvasx(0)
        visible_top = self.canvas.canvasy(0)
        visible_right = self.canvas.canvasx(width)
        visible_bottom = self.canvas.canvasy(height)
        
        # Extend grid area
        left = int(visible_left - 100)
        top = int(visible_top - 100)
        right = int(visible_right + 100)
        bottom = int(visible_bottom + 100)
        
        # Grid spacing
        spacing = 20
        
        # Ensure grid starts at multiples of spacing
        start_x = (left // spacing) * spacing
        start_y = (top // spacing) * spacing
        
        # Draw vertical lines
        for x in range(start_x, right + spacing, spacing):
            line = self.canvas.create_line(x, top, x, bottom, fill='#E0E0E0')
            self.grid_items.append(line)
        
        # Draw horizontal lines
        for y in range(start_y, bottom + spacing, spacing):
            line = self.canvas.create_line(left, y, right, y, fill='#E0E0E0')
            self.grid_items.append(line)

    def drag_canvas(self, event):
        if self.canvas_drag:
            # Calculate the movement delta
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            
            # Move all canvas objects
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self.canvas.scan_mark(self.last_x, self.last_y)
            
            self.last_x = event.x
            self.last_y = event.y
            
            # Redraw grid after drag
            self.draw_grid()
            
            self.logger.debug(f"Canvas dragged by ({dx}, {dy})")

    def stop_canvas_drag(self, event):
        self.canvas_drag = False
        # Final grid redraw after drag ends
        self.draw_grid()
        self.logger.debug("Stopped canvas drag")

    def get_next_component_number(self, component_type):
        if component_type not in self.component_counters:
            self.component_counters[component_type] = 1
        else:
            self.component_counters[component_type] += 1
        return self.component_counters[component_type]

    def create_temp_component(self, x, y):
        if self.temp_component:
            for item in self.temp_component:
                self.canvas.delete(item)
        
        symbol = EagleSymbol(self.canvas)
        self.temp_component = []
        
        if self.current_component in self.symbols:
            # Snap to grid
            x = round(x / 20) * 20
            y = round(y / 20) * 20
            
            symbol_data = self.symbols[self.current_component]
            
            for cmd, *args in symbol_data:
                try:
                    # Skip SPICEMODEL and SPICEEXTRA
                    if cmd == 'text':
                        tx, ty, size, content, layer = args
                        if content in ['>SPICEMODEL', '>SPICEEXTRA']:
                            continue
                        # Keep >NAME and >VALUE as is for preview
                        text = symbol.draw_text(
                            tx + x/symbol.scale,
                            ty - y/symbol.scale,
                            content,
                            size,
                            layer
                        )
                        self.temp_component.append(text)
                    elif cmd == 'wire':
                        x1, y1, x2, y2, layer = args
                        line = symbol.draw_wire(
                            x1 + x/symbol.scale,
                            y1 - y/symbol.scale,
                            x2 + x/symbol.scale,
                            y2 - y/symbol.scale,
                            layer
                        )
                        self.temp_component.append(line)
                    elif cmd == 'circle':
                        cx, cy, radius, layer = args
                        symbol.draw_circle(
                            cx + x/symbol.scale,
                            cy + y/symbol.scale,
                            radius,
                            layer
                        )
                    elif cmd == 'arc':
                        x1, y1, x2, y2, curve, layer = args
                        symbol.draw_arc(
                            x1 + x/symbol.scale,
                            y1 + y/symbol.scale,
                            abs(x2-x1)/2,  # radius
                            0,  # start angle
                            curve,  # end angle
                            layer
                        )
                    elif cmd == 'pin':
                        px, py, length, direction, name, layer = args
                        pins = symbol.draw_pin(
                            px + x/symbol.scale,
                            py - y/symbol.scale,  # Invert y coordinate
                            length,
                            direction,
                            name,
                            layer
                        )
                        self.temp_component.extend(pins)
                except Exception as e:
                    self.logger.error(f"Error drawing {cmd}: {str(e)}")
        else:
            self.logger.warning(f"Symbol {self.current_component} not found in library")

    def update_component_position(self, event):
        if self.current_component and self.temp_component:
            # Store new position
            self.mouse_x = event.x
            self.mouse_y = event.y
            
            # Calculate offset from grid
            grid_size = 20
            x = round(event.x / grid_size) * grid_size
            y = round(event.y / grid_size) * grid_size
            
            # Delete old temporary component
            for item in self.temp_component:
                self.canvas.delete(item)
            
            # Create new temporary component at new position
            self.create_temp_component(x, y)
            
            self.logger.debug(f"Component position: ({x}, {y})")

    def place_component(self, event):
        if self.current_component and self.temp_component:
            x, y = event.x, event.y
            self.logger.info(f"Placed {self.current_component} at ({x}, {y})")
            # Create permanent component
            self.add_component(x, y)
            # Clean up temp component
            for item in self.temp_component:
                self.canvas.delete(item)
            self.temp_component = None
            self.current_component = None
            self.canvas.unbind("<Motion>")
            self.canvas.unbind("<Button-1>")

    def add_resistor(self, x, y):
        self.add_component(x, y)

    def add_capacitor(self, x, y):
        self.add_component(x, y)

    def add_inductor(self, x, y):
        self.add_component(x, y)

    def add_voltage_source(self, x, y):
        self.add_component(x, y)

    def add_ac_source(self, x, y):
        self.add_component(x, y)

    def add_battery(self, x, y):
        self.add_component(x, y)

    def add_component(self, x, y):
        self.logger.info(f"Adding component {self.current_component} at ({x}, {y})")
        symbol = EagleSymbol(self.canvas)
        
        if self.current_component in self.symbols:
            # Generate automatic name when placing component
            component_number = self.get_next_component_number(self.current_component)
            auto_name = f"{self.current_component}{component_number}"
            
            symbol_data = self.symbols[self.current_component]
            for cmd, *args in symbol_data:
                try:
                    if cmd == 'text':
                        tx, ty, size, content, layer = args
                        # Skip SPICEMODEL and SPICEEXTRA
                        if content in ['>SPICEMODEL', '>SPICEEXTRA']:
                            continue
                        # Replace >NAME with auto_name when placing
                        if content == '>NAME':
                            content = auto_name
                        symbol.draw_text(
                            tx + x/symbol.scale,
                            ty - y/symbol.scale,
                            content,
                            size,
                            layer
                        )
                    elif cmd == 'wire':
                        x1, y1, x2, y2, layer = args
                        symbol.draw_wire(
                            x1 + x/symbol.scale,
                            y1 - y/symbol.scale,
                            x2 + x/symbol.scale,
                            y2 - y/symbol.scale,
                            layer
                        )
                    elif cmd == 'circle':
                        cx, cy, radius, layer = args
                        symbol.draw_circle(
                            cx + x/symbol.scale,
                            cy + y/symbol.scale,
                            radius,
                            layer
                        )
                    elif cmd == 'arc':
                        x1, y1, x2, y2, curve, layer = args
                        symbol.draw_arc(
                            x1 + x/symbol.scale,
                            y1 + y/symbol.scale,
                            abs(x2-x1)/2,  # radius
                            0,  # start angle
                            curve,  # end angle
                            layer
                        )
                    elif cmd == 'pin':
                        px, py, length, direction, name, layer = args
                        symbol.draw_pin(
                            px + x/symbol.scale,
                            py - y/symbol.scale,  # Invert y coordinate
                            length,
                            direction,
                            name,
                            layer
                        )
                except Exception as e:
                    self.logger.error(f"Error drawing {cmd}: {str(e)}")
        else:
            self.logger.warning(f"Symbol {self.current_component} not found in library")

    def load_eagle_library(self, filename):
        self.logger.info(f"Loading library: {filename}")
        try:
            self.symbols = {}
            tree = ET.parse(filename)
            root = tree.getroot()
            
            symbol_count = 0
            for symbol in root.findall(".//symbols/symbol"):
                symbol_name = symbol.get('name')
                symbol_data = []
                
                # Parse wires (lines)
                for wire in symbol.findall("wire"):
                    x1 = float(wire.get('x1', '0'))
                    y1 = float(wire.get('y1', '0'))
                    x2 = float(wire.get('x2', '0'))
                    y2 = float(wire.get('y2', '0'))
                    layer = wire.get('layer', '94')
                    symbol_data.append(('wire', x1, y1, x2, y2, layer))
                
                # Parse circles
                for circle in symbol.findall("circle"):
                    x = float(circle.get('x', '0'))
                    y = float(circle.get('y', '0'))
                    radius = float(circle.get('radius', '1'))
                    layer = circle.get('layer', '94')
                    symbol_data.append(('circle', x, y, radius, layer))
                
                # Parse arcs
                for arc in symbol.findall("arc"):
                    x1 = float(arc.get('x1', '0'))
                    y1 = float(arc.get('y1', '0'))
                    x2 = float(arc.get('x2', '0'))
                    y2 = float(arc.get('y2', '0'))
                    curve = float(arc.get('curve', '90'))
                    layer = arc.get('layer', '94')
                    symbol_data.append(('arc', x1, y1, x2, y2, curve, layer))
                
                # Parse text
                for text in symbol.findall("text"):
                    x = float(text.get('x', '0'))
                    y = float(text.get('y', '0'))
                    size = float(text.get('size', '1'))
                    layer = text.get('layer', '95')
                    content = text.text or ''
                    symbol_data.append(('text', x, y, size, content, layer))
                
                # Parse pins with safe length handling
                for pin in symbol.findall("pin"):
                    x = float(pin.get('x', '0'))
                    y = float(pin.get('y', '0'))
                    length_str = pin.get('length', 'short')
                    # Convert Eagle pin lengths to numeric values
                    length_map = {
                        'short': 2.54,
                        'middle': 5.08,
                        'long': 7.62,
                        'point': 0
                    }
                    length = length_map.get(length_str, 2.54)
                    direction = pin.get('direction', 'io')
                    name = pin.get('name', '')
                    layer = "91"  # Standard pin layer
                    symbol_data.append(('pin', x, y, length, direction, name, layer))
                
                self.symbols[symbol_name] = symbol_data
                symbol_count += 1
            
            self.logger.info(f"Loaded {symbol_count} symbols from library")
        except Exception as e:
            self.logger.error(f"Error loading library: {str(e)}")

    def on_component_select(self, event):
        selected_item = self.tree.selection()[0]
        component_name = self.tree.item(selected_item)['text']
        if component_name in self.component_functions:
            self.current_component = component_name

    def start_canvas_drag(self, event):
        self.canvas_drag = True
        self.last_x = event.x
        self.last_y = event.y
        self.logger.debug("Started canvas drag")

    def run(self):
        try:
            self.root.geometry("1200x800")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
        finally:
            self.logger.info("Application terminated")

if __name__ == "__main__":
    app = CircuitApp()
    app.run()