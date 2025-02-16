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
        self.symbol_color = "#8B0000"  # Dark red for both symbols and pins
        self.offset_x = 0  # Add offset support
        self.offset_y = 0
        self.zoom = 1.0  # Add zoom factor
        
    def draw_wire(self, x1, y1, x2, y2, layer="94"):
        x1, y1 = self.rotate_point(x1, y1)
        x2, y2 = self.rotate_point(x2, y2)
        
        canvas_x1 = x1 * self.scale * self.zoom + self.offset_x
        canvas_y1 = -y1 * self.scale * self.zoom + self.offset_y
        canvas_x2 = x2 * self.scale * self.zoom + self.offset_x
        canvas_y2 = -y2 * self.scale * self.zoom + self.offset_y
        
        return self.canvas.create_line(
            canvas_x1, canvas_y1, 
            canvas_x2, canvas_y2,
            fill=self.get_layer_color(layer), 
            width=2 * self.zoom  # Scale line width with zoom
        )
    
    def draw_circle(self, x, y, radius, layer="94"):
        x, y = self.rotate_point(x, y)
        canvas_x = x * self.scale * self.zoom + self.offset_x
        canvas_y = -y * self.scale * self.zoom + self.offset_y  # Invert y coordinate
        r = radius * self.scale * self.zoom  # Apply zoom to radius too
        
        return self.canvas.create_oval(
            canvas_x - r, canvas_y - r,
            canvas_x + r, canvas_y + r,
            outline=self.get_layer_color(layer),
            width=2 * self.zoom  # Scale line width with zoom
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
    
    def draw_text(self, x, y, text, size=1.0, layer="94", align="center", tags=()):
        x, y = self.rotate_point(x, y)
        
        # Apply zoom and offset to coordinates
        canvas_x = x * self.scale * self.zoom + self.offset_x
        canvas_y = -y * self.scale * self.zoom + self.offset_y
        
        # Handle special text alignment for component labels
        if text.startswith('>'):
            # Move component values and names slightly above the component
            canvas_y -= self.scale * 0.8 * self.zoom  # Scale offset with zoom
            if text == '>VALUE':
                canvas_y -= self.scale * 0.8 * self.zoom  # Scale offset with zoom
        
        # Scale font size with zoom
        font_size = int(size * 12 * self.zoom)  # Scale font size with zoom
        
        # Map text anchors
        anchor_map = {
            "center": "center",
            "start": "w",
            "end": "e",
            "left": "w",
            "right": "e"
        }
        anchor = anchor_map.get(align, "center")
        
        return self.canvas.create_text(
            canvas_x, canvas_y,
            text=text,
            fill=self.get_layer_color(layer),
            font=("Arial", font_size),
            anchor=anchor,
            tags=tags  # Add tags parameter
        )
    
    def draw_pin(self, x, y, length, direction, name, layer="91"):
        x, y = self.rotate_point(x, y)
        dx, dy = self.get_direction_vector(direction)
        
        # Adjust pin direction for pin 2
        if name == "2":
            dx = -dx  # Reverse direction for pin 2
        
        # Draw pin line
        pin = self.draw_wire(
            x, y,
            x + dx * length, y + dy * length,
            layer
        )
        
        # Calculate pin number position
        number_offset = 0.3  # Offset in grid units
        
        # Position pin numbers consistently
        if name == "2":
            text_x = x + dx * length * 0.2  # Position number closer to the component
        else:
            text_x = x + dx * length * 0.2
        text_y = y - number_offset  # Always place numbers above the pin
        
        # Add pin number
        text = self.draw_text(
            text_x,
            text_y,
            str(name),
            size=0.7,  # Slightly smaller pin numbers
            layer=layer,
            align="center"  # Center align all pin numbers
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
        # Convert direction to float and handle special cases
        try:
            if isinstance(direction, str):
                # Map text directions to angles
                direction_map = {
                    'R': 0,    # Right
                    'L': 180,  # Left
                    'U': 90,   # Up
                    'D': 270,  # Down
                    'io': 0,   # Default to right for IO pins
                    'in': 180, # Input pins come from left
                    'out': 0,  # Output pins go to right
                    '1': 0,    # Pin 1 goes right
                    '2': 0,    # Pin 2 also goes right (changed from 180)
                }
                angle = direction_map.get(direction, 0)
            else:
                angle = float(direction)
            
            # Apply rotation and convert to radians
            angle_rad = math.radians((angle + self.rotation) % 360)
            return (math.cos(angle_rad), math.sin(angle_rad))
        except (ValueError, TypeError):
            # If conversion fails, default to rightward direction
            return (1, 0)
    
    def get_layer_color(self, layer):
        colors = {
            "91": self.symbol_color,  # Pins - now using same dark red
            "94": self.symbol_color,  # Symbols
            "95": "#808080",  # Names
            "96": "#404040",  # Values
            "97": "#FF0000",  # Info
            "98": "#0000FF",  # Guide
        }
        return colors.get(layer, self.symbol_color)

    def draw_origin_markers(self, x, y, is_text=False):
        """Draw origin marker cross"""
        # Increase cross size (was 3)
        size = 5 * self.zoom  # Bigger cross size
        color = "#808080" if is_text else self.symbol_color
        
        # Convert coordinates
        canvas_x = x * self.scale * self.zoom + self.offset_x
        canvas_y = -y * self.scale * self.zoom + self.offset_y
        
        # Draw the cross
        markers = []
        # Horizontal line
        markers.append(self.canvas.create_line(
            canvas_x - size, canvas_y,
            canvas_x + size, canvas_y,
            fill=color, width=1.5 * self.zoom  # Slightly thicker lines
        ))
        # Vertical line
        markers.append(self.canvas.create_line(
            canvas_x, canvas_y - size,
            canvas_x, canvas_y + size,
            fill=color, width=1.5 * self.zoom  # Slightly thicker lines
        ))
        
        return markers

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
        
        # Initialize zoom before creating canvas and drawing grid
        self.zoom = 1.0
        
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
        
        # Add keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.menu_new())
        self.root.bind('<Control-o>', lambda e: self.menu_open())
        self.root.bind('<Control-s>', lambda e: self.menu_save())
        self.root.bind('<Control-z>', lambda e: self.menu_undo())
        self.root.bind('<Control-y>', lambda e: self.menu_redo())
        self.root.bind('<Control-x>', lambda e: self.menu_cut())
        self.root.bind('<Control-c>', lambda e: self.menu_copy())
        self.root.bind('<Control-v>', lambda e: self.menu_paste())
        self.root.bind('<Control-plus>', lambda e: self.menu_zoom_in())
        self.root.bind('<Control-minus>', lambda e: self.menu_zoom_out())
        self.root.bind('<Control-0>', lambda e: self.menu_zoom_reset())
        self.root.bind('<Control-g>', self.toggle_grid)
        self.root.bind('<Control-Shift-G>', self.toggle_snap)
        
        # Add keyboard bindings for delete
        self.root.bind('<Delete>', self.delete_selected)
        self.root.bind('<BackSpace>', self.delete_selected)
        
        # Force initial grid draw after window is fully initialized
        self.root.update_idletasks()  # Ensure geometry is updated
        self.draw_grid()
        
        self.placed_components = []  # Track placed components
        self.component_counters = {}  # Track component numbers
        
        # Add zoom bindings
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mousewheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mousewheel)    # Linux scroll down
        
        self.moving_component = None  # Track which component is being moved
        
        # Add selection variables
        self.selection_start_x = None
        self.selection_start_y = None
        self.selection_rectangle = None
        self.selected_components = []
        self.is_selecting = False
        
        # Bind mouse events for selection
        self.canvas.bind('<ButtonPress-1>', self.start_selection)
        self.canvas.bind('<B1-Motion>', self.update_selection)
        self.canvas.bind('<ButtonRelease-1>', self.end_selection)
        
    def create_menu_bar(self):
        # Create notebook for tabs
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(fill=tk.X)
        
        # Create tab frames
        file_tab = ttk.Frame(self.tab_control)
        edit_tab = ttk.Frame(self.tab_control)
        view_tab = ttk.Frame(self.tab_control)
        grid_tab = ttk.Frame(self.tab_control)  # New grid tab
        
        # Add tabs to notebook
        self.tab_control.add(file_tab, text='File')
        self.tab_control.add(edit_tab, text='Edit')
        self.tab_control.add(view_tab, text='View')
        self.tab_control.add(grid_tab, text='Grid')  # Add grid tab
        
        # Style for toolbar buttons
        style = ttk.Style()
        style.configure(
            'Toolbar.TButton',
            padding=2,
            relief='flat',
            background='#f0f0f0'
        )
        
        # File tab buttons
        file_buttons = [
            ("New", "📄", self.menu_new, "Ctrl+N"),
            ("Open", "📂", self.menu_open, "Ctrl+O"),
            ("Save", "💾", self.menu_save, "Ctrl+S"),
        ]
        
        file_toolbar = ttk.Frame(file_tab)
        file_toolbar.pack(fill=tk.X, padx=2, pady=2)
        self.create_button_group(file_toolbar, "File", file_buttons)
        
        # Edit tab buttons
        edit_buttons = [
            ("Undo", "↩️", self.menu_undo, "Ctrl+Z"),
            ("Redo", "↪️", self.menu_redo, "Ctrl+Y"),
            None,  # Separator
            ("Cut", "✂️", self.menu_cut, "Ctrl+X"),
            ("Copy", "📋", self.menu_copy, "Ctrl+C"),
            ("Paste", "📌", self.menu_paste, "Ctrl+V"),
        ]
        
        edit_toolbar = ttk.Frame(edit_tab)
        edit_toolbar.pack(fill=tk.X, padx=2, pady=2)
        self.create_button_group(edit_toolbar, "Edit", edit_buttons)
        
        # View tab buttons
        view_buttons = [
            ("Zoom In", "🔍+", self.menu_zoom_in, "Ctrl++"),
            ("Zoom Out", "🔍-", self.menu_zoom_out, "Ctrl+-"),
            ("Reset View", "🔍1", self.menu_zoom_reset, "Ctrl+0"),
        ]
        
        view_toolbar = ttk.Frame(view_tab)
        view_toolbar.pack(fill=tk.X, padx=2, pady=2)
        self.create_button_group(view_toolbar, "View", view_buttons)
        
        # Grid tab - horizontal layout
        grid_toolbar = ttk.Frame(grid_tab)
        grid_toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Show Grid checkbox
        self.grid_visible_var = tk.BooleanVar(value=True)
        show_grid_cb = ttk.Checkbutton(
            grid_toolbar,
            text="Show Grid",
            variable=self.grid_visible_var,
            command=self.toggle_grid
        )
        show_grid_cb.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(grid_toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=2)
        
        # Grid Style radio buttons in a labeled frame
        style_frame = ttk.LabelFrame(grid_toolbar, text="Style")
        style_frame.pack(side=tk.LEFT, padx=5)
        
        self.grid_style_var = tk.StringVar(value="lines")
        ttk.Radiobutton(
            style_frame,
            text="Lines",
            variable=self.grid_style_var,
            value="lines",
            command=self.update_grid_style
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            style_frame,
            text="Dots",
            variable=self.grid_style_var,
            value="dots",
            command=self.update_grid_style
        ).pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(grid_toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=2)
        
        # Grid Size input
        ttk.Label(grid_toolbar, text="Size:").pack(side=tk.LEFT, padx=(5, 0))
        self.grid_size_var = tk.StringVar(value="20")
        size_entry = ttk.Entry(
            grid_toolbar,
            textvariable=self.grid_size_var,
            width=5
        )
        size_entry.pack(side=tk.LEFT, padx=5)
        
        # Bind validation and update
        size_entry.bind('<Return>', self.update_grid_size)
        size_entry.bind('<FocusOut>', self.update_grid_size)
        
        # Snap to Grid checkbox
        self.snap_grid_var = tk.BooleanVar(value=True)
        snap_grid_cb = ttk.Checkbutton(
            grid_toolbar,
            text="Snap to Grid",
            variable=self.snap_grid_var,
            command=self.toggle_snap
        )
        snap_grid_cb.pack(side=tk.LEFT, padx=5)

    def create_button_group(self, parent, group_name, buttons):
        frame = ttk.LabelFrame(parent, text=group_name)
        frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        for button_info in buttons:
            if button_info is None:  # Separator
                ttk.Separator(frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
                continue
            
            name, icon, command, accelerator = button_info
            btn = ttk.Button(
                frame,
                text=f"{icon}\n{name}",
                command=command,
                style='Toolbar.TButton',
                width=8
            )
            btn.pack(side=tk.LEFT, padx=1, pady=1)
            
            # Create tooltip with keyboard shortcut
            self.create_tooltip(btn, f"{name} ({accelerator})")

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
            ("select", "⬚", "Select"),
            ("move", "⬌", "Move"),
            ("rotate", "⟳", "Rotate"),
            ("mirror", "⟷", "Mirror"),
            ("duplicate", "⎘", "Duplicate"),
            ("delete", "⌫", "Delete"),
            ("add_part", "⊕", "Add Part"),
            ("replace", "↷", "Replace"),
            ("edit_part", "✎", "Edit Part"),
            ("net", "⌇", "Net"),
            ("junction", "●", "Junction"),
            ("label", "T", "Label"),
            ("name", "N", "Name"),
            ("value", "V", "Value"),
            ("split", "Y", "Split")
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
    
    def select_tool(self, tool):
        self.current_tool = tool
        self.logger.info(f"Selected tool: {tool}")
        
        # Update button appearances
        for btn_id, btn in self.tool_buttons.items():
            if btn_id == tool:
                btn.config(bg="#e0e0e0")
            else:
                btn.config(bg="white")
        
        if tool == "delete":
            # Enable delete mode
            self.canvas.bind("<Button-1>", self.handle_delete_click)
            # Unbind other tool events
            self.canvas.unbind("<Motion>")
            self.canvas.unbind("<B1-Motion>")
        elif tool == "add_part":
            # Open parts window and bind events for component placement
            self.open_parts_window()
            self.canvas.unbind("<Button-1>")
            self.canvas.bind("<Motion>", self.update_component_position)
            self.canvas.bind("<Button-1>", self.place_component)

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
        for item in getattr(self, 'grid_items', []):
            self.canvas.delete(item)
        self.grid_items = []
        
        if not self.grid_visible_var.get():
            return
        
        # Convert grid size to int first, then multiply by zoom
        base_grid_size = int(self.grid_size_var.get())
        grid_size = int(base_grid_size * self.zoom)  # Scale grid with zoom
        
        # Get visible area
        visible_left = self.canvas.canvasx(0)
        visible_top = self.canvas.canvasy(0)
        visible_right = self.canvas.canvasx(self.canvas.winfo_width())
        visible_bottom = self.canvas.canvasy(self.canvas.winfo_height())
        
        # Extend grid area
        left = int(visible_left - grid_size * 5)
        top = int(visible_top - grid_size * 5)
        right = int(visible_right + grid_size * 5)
        bottom = int(visible_bottom + grid_size * 5)
        
        # Ensure grid starts at multiples of grid_size
        start_x = (left // grid_size) * grid_size
        start_y = (top // grid_size) * grid_size
        
        # Draw grid lines or dots
        if self.grid_style_var.get() == "lines":
            for x in range(start_x, right + grid_size, grid_size):
                line = self.canvas.create_line(x, top, x, bottom, 
                                             fill='#e0e0e0', 
                                             width=max(1, 0.5 * self.zoom))
                self.grid_items.append(line)
            
            for y in range(start_y, bottom + grid_size, grid_size):
                line = self.canvas.create_line(left, y, right, y, 
                                             fill='#e0e0e0', 
                                             width=max(1, 0.5 * self.zoom))
                self.grid_items.append(line)
        else:  # dots
            dot_size = max(1, self.zoom)
            for x in range(start_x, right + grid_size, grid_size):
                for y in range(start_y, bottom + grid_size, grid_size):
                    dot = self.canvas.create_oval(
                        x - dot_size, y - dot_size,
                        x + dot_size, y + dot_size,
                        fill='#e0e0e0',
                        outline='#e0e0e0'
                    )
                    self.grid_items.append(dot)

    def drag_canvas(self, event):
        if self.canvas_drag:
            # Calculate the movement delta
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            
            # Move all canvas objects
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            
            # Update last position
            self.last_x = event.x
            self.last_y = event.y
            
            # Update grid based on new canvas position
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
        # Clear any existing temporary component
        if isinstance(self.temp_component, dict):
            for items in self.temp_component.values():
                for item in items:
                    self.canvas.delete(item)
        elif isinstance(self.temp_component, list):
            for item in self.temp_component:
                self.canvas.delete(item)
        self.temp_component = {}
        
        # Create new temporary component
        if self.current_component in self.symbols:
            # Snap to grid
            grid_size = 20
            x = round(x / grid_size) * grid_size
            y = round(y / grid_size) * grid_size
            
            symbol_data = self.symbols[self.current_component]
            symbol = EagleSymbol(self.canvas)
            
            # Set position offset
            symbol.offset_x = x
            symbol.offset_y = y
            
            # Track different parts of the component
            symbol_items = []  # Main symbol elements (wires, circles, pins)
            name_items = []   # Name text and origin
            value_items = []  # Value text and origin
            
            # Add symbol origin marker first
            origin_markers = symbol.draw_origin_markers(0, 0)
            symbol_items.extend(origin_markers)
            
            for element in symbol_data:
                element_type = element[0]
                if element_type == 'text':
                    tx, ty, size, text, layer = element[1:6]
                    if text not in ['>SPICEMODEL', '>SPICEEXTRA']:
                        # Create text and its origin marker
                        if text == '>NAME':
                            text_item = symbol.draw_text(tx, ty, text, size, layer, tags=('name',))
                            origin_markers = symbol.draw_origin_markers(tx, ty, is_text=True)
                            name_items.extend([text_item] + origin_markers)
                        elif text == '>VALUE':
                            text_item = symbol.draw_text(tx, ty, text, size, layer, tags=('value',))
                            origin_markers = symbol.draw_origin_markers(tx, ty, is_text=True)
                            value_items.extend([text_item] + origin_markers)
                else:
                    # Add other elements to symbol items
                    if element_type == 'wire':
                        item = symbol.draw_wire(*element[1:6])
                        symbol_items.append(item)
                    elif element_type == 'circle':
                        item = symbol.draw_circle(*element[1:5])
                        symbol_items.append(item)
                    elif element_type == 'pin':
                        items = symbol.draw_pin(*element[1:7])
                        symbol_items.extend(items)
            
            # Store all items in temp_component dictionary
            self.temp_component = {
                'symbol': symbol_items,
                'name': name_items,
                'value': value_items
            }
        else:
            self.logger.warning(f"Symbol {self.current_component} not found in library")

    def update_component_position(self, event):
        if self.current_component and self.temp_component:
            # Store new position
            self.mouse_x = event.x
            self.mouse_y = event.y
            
            # Create new temporary component at new position
            self.create_temp_component(event.x, event.y)
            
            self.logger.debug(f"Component position: ({event.x}, {event.y})")

    def place_component(self, event):
        if self.current_component and self.temp_component:
            # Get the next component number
            base_name = self.current_component
            count = self.component_counters.get(base_name, 0) + 1
            self.component_counters[base_name] = count
            
            # Snap to grid
            grid_size = int(self.grid_size_var.get())
            x = round(event.x / grid_size) * grid_size
            y = round(event.y / grid_size) * grid_size
            
            # Create permanent component
            self.create_temp_component(x, y)
            
            # Store component with separate parts
            component_data = {
                'symbol': self.temp_component['symbol'],
                'name': self.temp_component['name'],
                'value': self.temp_component['value'],
                'type': base_name,
                'name_text': f"{base_name}{count}",
                'origin': (x, y)
            }
            self.placed_components.append(component_data)
            
            # Add click handlers for movement
            for item in component_data['symbol']:
                self.canvas.tag_bind(item, '<Button-1>', 
                    lambda e, c=component_data: self.start_component_move(e, c))
                self.canvas.tag_bind(item, '<B1-Motion>', 
                    lambda e, c=component_data: self.move_component(e, c))
                self.canvas.tag_bind(item, '<ButtonRelease-1>', 
                    lambda e, c=component_data: self.stop_component_move(e, c))
            
            # Clear temporary component references but don't delete the items
            self.temp_component = []
            self.current_component = None
            self.canvas.unbind("<Motion>")
            
            self.logger.info(f"Placed {base_name} at ({x}, {y})")

    def start_component_move(self, event, component):
        if self.current_tool == "select":
            self.moving_component = component
            self.last_x = event.x
            self.last_y = event.y
            self.logger.debug(f"Started moving component {component['name_text']}")

    def move_component(self, event, component):
        if self.current_tool == "select" and self.moving_component == component:
            # Calculate movement delta
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            
            # Update component position
            component['origin'] = (component['origin'][0] + dx, component['origin'][1] + dy)
            
            # Move all items in the component
            for item in component['symbol']:
                self.canvas.move(item, dx, dy)
            
            # Update last position
            self.last_x = event.x
            self.last_y = event.y
            
            self.logger.debug(f"Moving component {component['name_text']} by ({dx}, {dy})")

    def stop_component_move(self, event, component):
        if self.current_tool == "select" and self.moving_component == component:
            # Snap final position to grid if enabled
            if self.snap_grid_var.get():
                grid_size = int(self.grid_size_var.get())
                new_x = round(component['origin'][0] / grid_size) * grid_size
                new_y = round(component['origin'][1] / grid_size) * grid_size
                
                # Move to final snapped position
                dx = new_x - component['origin'][0]
                dy = new_y - component['origin'][1]
                for item in component['symbol']:
                    self.canvas.move(item, dx, dy)
                
                component['origin'] = (new_x, new_y)
            
            self.moving_component = None
            self.logger.debug(f"Stopped moving component {component['name_text']}")

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
            
            # Store component with separate parts
            component_data = {
                'symbol': symbol_items,
                'name': name_items,
                'value': value_items,
                'type': self.current_component,
                'name_text': auto_name,  # Store actual name text
                'origin': (x, y)
            }
            self.placed_components.append(component_data)
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
                
                if symbol_name == "C":
                    symbol_data = [
                        # Main capacitor plates (vertical lines)
                        ('wire', -1.27, -2, -1.27, 0, "94"),  # Left plate (vertical)
                        ('wire', 1.27, 0, 1.27, 2, "94"),     # Right plate (vertical)
                        # Connection pins
                        ('pin', -5.08, 0, 3, "R", "1", "91"),  # Left pin
                        ('pin', 5.08, 0, 3, "L", "2", "91"),   # Right pin
                        # Value and name labels
                        ('text', 0, -3.81, 1.27, '>VALUE', "96"),  # Value above
                        ('text', 0, 2.54, 1.27, '>NAME', "95"),    # Name below
                    ]
                
                if symbol_name == "AMMETER":
                    symbol_data = [
                        # Circle
                        ('circle', 0, 0, 2.54, "94"),  # Main circle
                        # Arrow
                        ('wire', 0, -1.27, 0, 1.27, "94"),    # Vertical line
                        ('wire', -0.635, 0.635, 0, 1.27, "94"),  # Left diagonal
                        ('wire', 0.635, 0.635, 0, 1.27, "94"),   # Right diagonal
                        # Pins
                        ('pin', 0, -2.54, 2, "D", "1", "91"),  # Top pin
                        ('pin', 0, 2.54, 2, "U", "2", "91"),   # Bottom pin
                        # Labels with adjusted positions
                        ('text', 3.81, 0, 1.27, '>NAME', "95"),    # Name to the right
                        ('text', 3.81, 2.54, 1.27, '>VALUE', "96") # Value above name
                    ]
                
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

    def toggle_grid(self, event=None):
        self.grid_visible = self.grid_visible_var.get()
        self.logger.info(f"Grid visibility: {self.grid_visible}")
        self.draw_grid()

    def toggle_snap(self, event=None):
        self.snap_to_grid = self.snap_grid_var.get()
        self.logger.info(f"Snap to grid: {self.snap_to_grid}")

    def update_grid_style(self, event=None):
        self.logger.info(f"Grid style changed to: {self.grid_style_var.get()}")
        self.draw_grid()

    def update_grid_size(self, event=None):
        try:
            new_size = int(self.grid_size_var.get())
            if new_size < 5:
                new_size = 5
            elif new_size > 100:
                new_size = 100
            self.grid_size_var.set(str(new_size))
            self.logger.info(f"Changed grid size to: {new_size}")
            self.draw_grid()
        except ValueError:
            self.grid_size_var.set("20")  # Reset to default if invalid input

    def on_mousewheel(self, event):
        # Get the mouse position
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Determine zoom direction
        if event.num == 5 or event.delta < 0:  # Scroll down
            factor = 0.9
        else:  # Scroll up
            factor = 1.1
        
        # Update zoom
        old_zoom = self.zoom
        self.zoom *= factor
        
        # Constrain zoom level
        if self.zoom < 0.1:
            self.zoom = 0.1
        elif self.zoom > 5.0:
            self.zoom = 5.0
        
        # Adjust all components scale
        for component in self.placed_components:
            for item in component['symbol']:
                # Get current coordinates
                coords = self.canvas.coords(item)
                if coords:  # Check if item still exists
                    # Scale coordinates around mouse position
                    new_coords = []
                    for i in range(0, len(coords), 2):
                        cx = coords[i]
                        cy = coords[i + 1]
                        # Calculate new position relative to mouse
                        dx = cx - x
                        dy = cy - y
                        new_coords.append(x + dx * (self.zoom / old_zoom))
                        new_coords.append(y + dy * (self.zoom / old_zoom))
                    # Update item position
                    self.canvas.coords(item, *new_coords)
                    
                    # Scale line width for wires
                    if self.canvas.type(item) == "line":
                        self.canvas.itemconfig(item, width=2 * self.zoom)
                    elif self.canvas.type(item) == "text":
                        # Scale font size
                        current_font = self.canvas.itemcget(item, "font")
                        font_name = current_font.split()[0]
                        base_size = 12  # Base font size
                        new_size = int(base_size * self.zoom)
                        self.canvas.itemconfig(item, font=(font_name, new_size))
        
        # Redraw grid with new zoom level
        self.draw_grid()
        self.logger.info(f"Zoom level: {self.zoom:.2f}")

    def start_selection(self, event):
        # Convert screen coordinates to canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Get items at click position with smaller overlap area
        clicked_items = self.canvas.find_overlapping(
            canvas_x-1, canvas_y-1, 
            canvas_x+1, canvas_y+1
        )
        
        # Filter out selection rectangle from clicked items
        clicked_items = [item for item in clicked_items 
                        if item != self.selection_rectangle]
        
        if not clicked_items:
            # Clear any existing selection rectangle
            if self.selection_rectangle:
                self.canvas.delete(self.selection_rectangle)
            
            self.is_selecting = True
            self.selection_start_x = canvas_x
            self.selection_start_y = canvas_y
            
            # Create new selection rectangle
            self.selection_rectangle = self.canvas.create_rectangle(
                canvas_x, canvas_y,
                canvas_x, canvas_y,
                outline='#0078D7',
                dash=(2, 2),
                fill='#0078D7',
                stipple='gray25',
                width=1
            )
            
            # Clear previous selection if not holding shift
            if not event.state & 0x1:  # Check if shift is not pressed
                self.selected_components = []
            
            self.logger.debug(f"Started selection at ({canvas_x}, {canvas_y})")

    def update_selection(self, event):
        if self.is_selecting and self.selection_rectangle:
            current_x = self.canvas.canvasx(event.x)
            current_y = self.canvas.canvasy(event.y)
            
            self.canvas.coords(
                self.selection_rectangle,
                self.selection_start_x, self.selection_start_y,
                current_x, current_y
            )
            
            self.logger.debug(f"Updated selection to ({current_x}, {current_y})")

    def end_selection(self, event):
        if self.is_selecting and self.selection_rectangle:
            coords = self.canvas.coords(self.selection_rectangle)
            x1, y1, x2, y2 = coords
            
            # Normalize coordinates
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Find components in selection area
            newly_selected = []
            for component in self.placed_components:
                origin = component['origin']
                if (x1 <= origin[0] <= x2 and y1 <= origin[1] <= y2):
                    if component not in self.selected_components:
                        newly_selected.append(component)
            
            # Add newly selected components
            self.selected_components.extend(newly_selected)
            
            # Highlight all selected components
            self.highlight_selected_components()
            
            # Clean up selection
            self.canvas.delete(self.selection_rectangle)
            self.selection_rectangle = None
            self.selection_start_x = None
            self.selection_start_y = None
            self.is_selecting = False
            
            self.logger.info(f"Selection ended, {len(newly_selected)} new components selected")

    def highlight_selected_components(self):
        # Remove previous highlights
        for component in self.placed_components:
            for item in component['symbol']:
                self.canvas.itemconfig(item, width=2 * self.zoom)
        
        # Highlight selected components
        for component in self.selected_components:
            for item in component['symbol']:
                # Make selected items thicker
                self.canvas.itemconfig(item, width=3 * self.zoom)

    def delete_selected(self, event=None):
        if not self.selected_components:
            return
        
        # Store number of components being deleted for logging
        num_deleted = len(self.selected_components)
        
        # Delete each selected component
        for component in self.selected_components:
            # Delete all canvas items for this component
            for item in component['symbol']:
                self.canvas.delete(item)
            # Remove from placed components list
            self.placed_components.remove(component)
            
            # Decrement component counter if it was the last one
            component_type = component['type']
            component_number = int(component['name_text'][len(component_type):])
            if component_number == self.component_counters.get(component_type, 0):
                self.component_counters[component_type] = component_number - 1
        
        # Clear selection
        self.selected_components = []
        
        self.logger.info(f"Deleted {num_deleted} component{'s' if num_deleted > 1 else ''}")
            
    def run(self):
        try:
            self.root.geometry("1200x800")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
        finally:
            self.logger.info("Application terminated")

    def handle_delete_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        items = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        
        if not items:
            return
            
        for component in self.placed_components:
            # Check which part was clicked
            clicked_symbol = set(items) & set(component['symbol'])
            clicked_name = set(items) & set(component['name'])
            clicked_value = set(items) & set(component['value'])
            
            if clicked_symbol:
                # Delete entire component if clicking symbol origin
                clicked_item = list(clicked_symbol)[0]
                item_type = self.canvas.type(clicked_item)
                
                is_origin = (item_type == 'line' and 
                           any(self.canvas.type(other) == 'line' 
                               for other in clicked_symbol))
                
                if is_origin:
                    # Delete everything
                    for items in component.values():
                        for item in items:
                            self.canvas.delete(item)
                    self.placed_components.remove(component)
                    # Update counter
                    component_type = component['type']
                    component_number = int(component['name_text'][len(component_type):])
                    if component_number == self.component_counters.get(component_type, 0):
                        self.component_counters[component_type] = component_number - 1
                    self.logger.info(f"Deleted component {component['name_text']}")
                break
                
            elif clicked_name:
                # Hide name if clicking name text or origin
                for item in component['name']:
                    self.canvas.itemconfig(item, state='hidden')
                self.logger.info(f"Hidden name for component {component['name_text']}")
                break
                
            elif clicked_value:
                # Hide value if clicking value text or origin
                for item in component['value']:
                    self.canvas.itemconfig(item, state='hidden')
                self.logger.info(f"Hidden value for component {component['name_text']}")
                break

if __name__ == "__main__":
    app = CircuitApp()
    app.run()