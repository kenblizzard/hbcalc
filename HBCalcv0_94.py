"""
VOLTEX HIGHBAY LIGHTING CALCULATOR
This program provides a GUI interface for calculating lighting layouts using Voltex High Bays.
It helps determine optimal fixture placement while considering:
- Room dimensions and reflectances
- Technical specifications of individual fixtures (light output, light distribution, etc)
- Lighting requirements (Illuminance levels in Lux)
- Spacing constraints (minimum and maximum distances)
It uses the industry standard method for estimating the quantity of fixtures required to light up a space to a required light level with a specific fixture. The industry standard method used is called ‘the lumen method’. Loads of info on line, or just ask Ron :) 
"""

# ==============================================
# IMPORT LIBRARIES WITH EXPLANATIONS
# ==============================================

# Fundamental math operations and array handling
import numpy as np  

# Data manipulation and CSV file handling
import pandas as pd  

# Basic math functions (ceil, floor, etc.)
import math  

# GUI creation - windows, buttons, labels
import tkinter as tk  

# File dialogs and message boxes
from tkinter import filedialog, messagebox  

# Enhanced GUI widgets (better looking UI elements)
from tkinter import ttk  

# Logging program activity for debugging
import logging  

# ==============================================
# GLOBAL CONSTANTS WITH DESCRIPTIONS
# ==============================================

# Multiplier for SHRNOM (Spacing-to-Height Ratio Nominal) from CSV
# This increases the manufacturer's recommended spacing for better uniformity
# This factor allows me to increase SHRNOM until it balalced with results from Relux
SHR_FACTOR = 1.50  

# Minimum allowed distance between fixtures in meters
# Prevents fixtures from being placed too close together
# 3m seems reasable but this allows me to change in the backend if required
MIN_SPACING = 3.0   

# ==============================================
# LOGGING CONFIGURATION
# ==============================================
logging.basicConfig(
    filename="app.log",          # Log file name
    level=logging.INFO,          # Log level (INFO records normal operations)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log entry format
    datefmt="%Y-%m-%d %H:%M:%S"  # Date/time format
)

# ==============================================
# TOOLTIP CLASS
# ==============================================
class ToolTip:
    """
    Creates interactive help tooltips that appear when hovering over widgets.
    
    Attributes:
        widget: The GUI element this tooltip belongs to
        text: The help message to display
        tooltip: Reference to the tooltip window
    """
    
    def __init__(self, widget, text):
        """Initialize tooltip with target widget and help text"""
        self.widget = widget
        self.text = text
        self.tooltip = None  # Will store the tooltip window
        
        # Bind mouse events to show/hide tooltip
        self.widget.bind("<Enter>", self.show_tooltip)  # Mouse enters
        self.widget.bind("<Leave>", self.hide_tooltip)  # Mouse leaves

    def show_tooltip(self, event=None):
        """Display tooltip window at calculated position"""
        # Get widget position and adjust for tooltip placement
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25  # Offset right
        y += self.widget.winfo_rooty() + 25  # Offset down

        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # No window decorations
        self.tooltip.wm_geometry(f"+{x}+{y}")   # Position near widget
        
        # Create and pack the label with help text
        label = tk.Label(
            self.tooltip, 
            text=self.text,
            background="#ffffe0",  # Light yellow background
            relief="solid",        # Border style
            borderwidth=1          # Border width
        )
        label.pack()

    def hide_tooltip(self, event=None):
        """Destroy tooltip window when mouse leaves"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
# ==============================================
# VISUALIZATION CLASS
# ==============================================
class LayoutVisualizer:
    def __init__(self, parent_frame):
        """
        Initialize the visualizer with a parent frame
        
        Args:
            parent_frame: The tkinter frame where visualizations will be placed
        """
        self.parent = parent_frame
        self.canvas_frame = None  # Will hold the canvas widgets
        self.canvases = []        # Stores references to all created canvases
        
    def setup_visualization_area(self):
        """Create the frame that will contain the visualization canvases"""
        self.canvas_frame = tk.Frame(self.parent)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        return self.canvas_frame
    
    def clear_visualizations(self):
        """Remove all existing visualizations"""
        for canvas in self.canvases:
            canvas.destroy()
        self.canvases = []
        
    def draw_room_layout(self, room_length, room_width, layout_data, title):
        """
        Draw a complete room layout visualization with fixtures and spacing information.
        
        Features:
        - Title and room dimensions at top
        - Spacing/edge information below title
        - Scaled room outline
        - Fixtures as colored circles
        - Automatic error handling for invalid layouts
        
        Args:
            room_length (float): Length of the room in meters
            room_width (float): Width of the room in meters  
            layout_data (dict): Dictionary containing:
                'array': Tuple of (columns, rows) for fixture grid
                'spacing_length': Spacing between fixtures along length (meters)
                'spacing_width': Spacing between fixtures along width (meters)
            title (str): Title to display at top of visualization
        """
        # 1. CANVAS INITIALIZATION
        canvas_width = 450  # Fixed width for visualization area
        canvas_height = 400  # Fixed height for visualization area
        
        # Create canvas with white background and gray border
        canvas = tk.Canvas(
            self.canvas_frame,
            width=canvas_width,
            height=canvas_height,
            bg="white",               # White background color
            highlightthickness=1,     # Border thickness in pixels
            highlightbackground="gray" # Border color
        )
        
        # Position canvas in parent frame with padding
        canvas.pack(side=tk.TOP, padx=5, pady=10)
        
        # Store reference for later cleanup
        self.canvases.append(canvas)

        # 2. SCALING AND POSITION CALCULATIONS
        # Calculate scaling factor to fit room in canvas while maintaining aspect ratio
        scale = min(
            (canvas_width - 40) / room_length,  # Horizontal scaling factor
            (canvas_height - 120) / room_width    # Vertical scaling factor
        )
        
        # Calculate offsets to center the room drawing:
        offset_x = (canvas_width - (room_length * scale)) / 2
        offset_y = 80

        # 3. TEXT ELEMENTS (TOP SECTION)
        # 3.1 Main Title (Topmost element)
        canvas.create_text(
            canvas_width / 2,  # Center horizontally
            15,                # Fixed Y position near top
            text=title,        # Display provided title
            font=("Arial", 10, "bold"),  # Bold font for title
            fill="black"       # Black text color
        )
        
        # 3.2 Room Dimensions (Below title)
        canvas.create_text(
            canvas_width / 2,  # Center horizontally
            35,                # Positioned below title
            text=f"Room: {room_length:.1f}m (L) × {room_width:.1f}m (W)",
            font=("Arial", 8), # Smaller font size
            fill="black"       # Black text
        )
        
        # 3.3 Spacing and Edge Information (Below dimensions)
        if layout_data:  # Only display if layout data exists
            # Calculate edge distances (space from walls to first fixture)
            edge_space_length = (room_length - ((layout_data['array'][0] - 1) * 
                              layout_data['spacing_length'])) / 2
            edge_space_width = (room_width - ((layout_data['array'][1] - 1) * 
                             layout_data['spacing_width'])) / 2
            
            # Create formatted text string
            spacing_info = (
                f"Fixture Spacing: {layout_data['spacing_length']:.2f}m (L) × "
                f"{layout_data['spacing_width']:.2f}m (W)\n"
                f"Edge Distance: {edge_space_length:.2f}m (L) × "
                f"{edge_space_width:.2f}m (W)"
            )
            
            # Draw the spacing information text
            canvas.create_text(
                canvas_width / 2,  # Center horizontally
                55,                # Positioned below dimensions, above room graphic
                text=spacing_info,
                font=("Arial", 8), # Consistent font size
                fill="black",      # Black text
                justify="center"   # Center multi-line text
            )

        # 4. ROOM OUTLINE DRAWING
        # Draw main room rectangle
        canvas.create_rectangle(
            offset_x,               # Top-left X position
            offset_y,               # Top-left Y position
            offset_x + room_length * scale,  # Bottom-right X
            offset_y + room_width * scale,   # Bottom-right Y
            outline="black",        # Border color
            width=2,                # Border thickness
            fill="#f0f0f0"          # Light gray fill color
        )

        # 5. FIXTURE PLACEMENT
        if layout_data:  # Only proceed if we have valid layout data
            array_cols, array_rows = layout_data['array']
            spacing_length = layout_data['spacing_length']
            spacing_width = layout_data['spacing_width']
            
            # Calculate edge spaces (distance from walls to first fixture)
            edge_space_length = (room_length - ((array_cols - 1) * spacing_length)) / 2
            edge_space_width = (room_width - ((array_rows - 1) * spacing_width)) / 2
            
            # Draw each fixture as a blue circle
            for col in range(array_cols):
                for row in range(array_rows):
                    # Calculate fixture position (scaled to canvas coordinates)
                    x = offset_x + (edge_space_length + col * spacing_length) * scale
                    y = offset_y + (edge_space_width + row * spacing_width) * scale
                    
                    # Draw the fixture (10px diameter circle)
                    canvas.create_oval(
                        x - 5, y - 5,  # Top-left coordinates
                        x + 5, y + 5,  # Bottom-right coordinates
                        fill="#1f77b4", # Blue fill color
                        outline="black",# Black border
                        width=1         # Border thickness
                    )

        # 6. ERROR HANDLING - NO VALID LAYOUT
        if not layout_data:
            # Display error message centered on canvas
            canvas.create_text(
                canvas_width / 2,       # Center horizontally
                canvas_height / 2,      # Center vertically
                text="No valid layout for this configuration",
                font=("Arial", 10),     # Readable font size
                fill="red"              # Red color for error
            )
# ==============================================
# CSV FILE HANDLING FUNCTIONS
# ==============================================

def load_uf_table(csv_file_path):
    """
    Load the utilization factor table from a CSV file.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        pandas.DataFrame containing the utilization factors
        
    Raises:
        ValueError: If file is invalid or cannot be read
    """
    try:
        # Read CSV, skipping first 7 rows of metadata
        df = pd.read_csv(csv_file_path, skiprows=7, header=0)
        
        # Remove completely empty rows
        df = df.dropna(how="all")
        
        # Verify we have at least 2 columns (K values + reflectance combinations)
        if df.shape[1] < 2:
            raise ValueError("CSV file must have at least 2 columns.")
            
        # Clean up any whitespace in text columns
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
    except Exception as e:
        # Log error and re-raise with user-friendly message
        logging.error(f"Error loading CSV file: {e}")
        raise ValueError(f"Error loading CSV file: {e}")

def extract_metadata(csv_file_path):
    """
    Extract fixture metadata from the first 7 lines of CSV file.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        Dictionary containing fixture metadata
        
    Raises:
        ValueError: If metadata cannot be extracted
    """
    try:
        # Read just the first 7 lines (metadata section)
        with open(csv_file_path, "r") as file:
            lines = [next(file) for _ in range(7)]

        metadata = {}  # Will store extracted metadata
        
        # Process each metadata line
        for line in lines:
            parts = line.strip().split(",")
            
            # Extract fixture name
            if parts[0] == "Fixture Name":
                metadata["Fixture Name"] = parts[1]
                
            # Extract luminous flux (light output)
            elif parts[0] == "Luminous Flux":
                flux_value = float(parts[1])
                metadata["Luminous Flux"] = f"{flux_value:.0f}"   
                
            # Extract wattage (power consumption)
            elif parts[0] == "Wattage":
                wattage_value = parts[1].strip().rstrip("W")  # Remove "W" suffix
                metadata["Wattage"] = float(wattage_value)
                
            # Extract and calculate spacing-to-height ratio
            elif parts[0] == "SHRNOM":
                metadata["SHRNOM"] = float(parts[1])
                metadata["SHRNOM_Modified"] = float(parts[1]) * SHR_FACTOR

        return metadata
        
    except Exception as e:
        logging.error(f"Error extracting metadata: {e}")
        raise ValueError(f"Error extracting metadata: {e}")
# ==============================================
# FILE LOADING FUNCTION FOR GUI
# ==============================================

def load_csv_file():
    """Handle CSV file selection and loading for the GUI."""
    # Show file selection dialog
    file_path = filedialog.askopenfilename(
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    
    if file_path:
        try:
            # These are global variables that will store our data
            global uf_table, metadata
            
            # Load the utilization factor table
            uf_table = load_uf_table(file_path)
            
            # Extract the fixture metadata
            metadata = extract_metadata(file_path)
            
            # Update the GUI with loaded information
            fixture_name.set(f"Fixture: {metadata['Fixture Name']}")
            luminous_flux.set(f"Luminous Flux: {int(float(metadata['Luminous Flux']))} lumens")
            wattage.set(f"Wattage: {metadata['Wattage']}W")
            shr_nom.set(f"SHRNOM: {metadata['SHRNOM']:.2f} (Modified: {metadata['SHRNOM_Modified']:.2f})")
            
            # Show the file path in the entry box
            csv_file_path_entry.delete(0, tk.END)
            csv_file_path_entry.insert(0, file_path)
            
            # Log successful load
            logging.info(f"CSV file loaded: {file_path}")
            
        except Exception as e:
            logging.error(f"Error loading CSV file: {e}")
            messagebox.showerror("Error", str(e))        
# ==============================================
# LIGHTING CALCULATION FUNCTIONS
# ==============================================

def calculate_room_cavity_index(room_length, room_width, room_height, 
                              working_plane_height, suspension_distance):
    """
    Calculate the Room Cavity Index (K) - a measure of room proportions.
    Note: Dont get confused between the Room Cavity Index (RCI) and Room Cavity Ratio (RCR) 
    The calculation used requires the RCI
    Args:
        room_length: Room length in meters
        room_width: Room width in meters
        room_height: Room height in meters
        working_plane_height: Height of work surface in meters
        suspension_distance: Fixture suspension distance in meters
        
    Returns:
        Room Cavity Index (K) value
        
    Raises:
        ValueError: For invalid input combinations
    """
    # Calculate mounting height (work plane to fixtures)
    h = (room_height - working_plane_height) - suspension_distance
    
    # Validate mounting height is positive
    if h <= 0:
        raise ValueError(
            "Invalid inputs: Working plane height must be greater than suspension distance."
        )
    
    # Standard formula for Room Cavity Index
    return (room_length * room_width) / (h * (room_length + room_width))

def calculate_number_of_fixtures(E, room_length, room_width, luminous_flux, Uf, MF=0.8):
    """
    Calculate how many fixtures are needed to achieve desired illuminance.
    Industry standard method for estimating number of fixtures required in a rectangular room 
    
    Args:
        E: Required illuminance in lux (Application dependant)
        room_length: Room length in meters
        room_width: Room width in meters
        luminous_flux: Fixture light output in lumens
        Uf: Utilization factor (0-1)
        MF: Maintenance factor (0-1, default 0.8)
        
    Returns:
        Number of fixtures needed (rounded up)
        
    Raises:
        ValueError: For invalid inputs
    """
    try:
        luminous_flux = float(luminous_flux)
        
        # Validate all inputs are positive numbers
        if luminous_flux <= 0 or Uf <= 0 or MF <= 0:
            raise ValueError(
                "Invalid inputs: Ensure Luminous Flux, Utilisation Factor, "
                "and Maintenance Factor are valid numbers."
            )
            
        # Standard lighting calculation formula
        return math.ceil(
            (E * room_length * room_width) / 
            (luminous_flux * Uf * MF)
        )
        
    except (ValueError, TypeError):
        raise ValueError("Invalid Luminous Flux value. Please check the CSV file.")

def interpolate_uf(K, Rc, Rw, Rf, df):
    """
    Find utilization factor (Uf) by interpolating between values in the table.
    Uf tables are provided by the manufacturer as part of the overall lighting report
    
    Args:
        K: Room Cavity Index
        Rc: Ceiling reflectance (0-100)
        Rw: Walls reflectance (0-100)
        Rf: Floor reflectance (0-100)
        df: DataFrame containing utilization factors
        
    Returns:
        Interpolated utilization factor
        
    Raises:
        ValueError: For invalid inputs or missing data
    """
    try:
        # Convert K values column to numeric
        df.iloc[:, 0] = pd.to_numeric(df.iloc[:, 0], errors="coerce")
        
        # Remove rows with missing K values
        df = df.dropna(subset=[df.columns[0]])

        # Get valid K value range from table
        min_K = df.iloc[:, 0].min()
        max_K = df.iloc[:, 0].max()
        
        # Check K is within table's range
        if K < min_K or K > max_K:
            raise ValueError(
                f"Room Cavity Index (K) must be between {min_K} and {max_K}."
            )

        # Find all reflectance combinations in the CSV columns
        reflectance_combinations = {}
        for col in df.columns[1:]:
            if isinstance(col, str) and col.startswith("Rc"):
                parts = col.split("_")
                if len(parts) == 3:
                    try:
                        # Extract Rc, Rw, Rf values from column names
                        Rc_val = int(parts[0][2:])  # Extract number after "Rc"
                        Rw_val = int(parts[1][2:])  # Extract number after "Rw"
                        Rf_val = int(parts[2][2:])  # Extract number after "Rf"
                        reflectance_combinations[col] = (Rc_val, Rw_val, Rf_val)
                    except (IndexError, ValueError):
                        continue

        # Verify we found valid reflectance columns
        if not reflectance_combinations:
            raise ValueError("No valid reflectance columns found in the CSV file.")

        # Find closest matching reflectance combinations
        distances = []
        for col, (Rc_csv, Rw_csv, Rf_csv) in reflectance_combinations.items():
            # Calculate "distance" between requested and available reflectances
            distance = abs(Rc_csv - Rc) + abs(Rw_csv - Rw) + abs(Rf_csv - Rf)
            distances.append((distance, col))

        # Sort by distance to find closest matches
        distances.sort(key=lambda x: x[0])
        col1 = distances[0][1]  # Closest match
        col2 = distances[1][1]  # Second closest match

        # Get all K values from the table
        K_values = df.iloc[:, 0].values
        
        # Find the K values that bracket our calculated K
        lower_K = K_values[K_values <= K].max()
        upper_K = K_values[K_values >= K].min()

        # Handle exact match case
        if lower_K == upper_K:
            Uf1 = df[df.iloc[:, 0] == lower_K][col1].values[0]
            Uf2 = df[df.iloc[:, 0] == lower_K][col2].values[0]
        else:
            # Interpolate between bracketing K values for both reflectance combinations
            Uf1_lower = df[df.iloc[:, 0] == lower_K][col1].values[0]
            Uf1_upper = df[df.iloc[:, 0] == upper_K][col1].values[0]
            Uf1 = Uf1_lower + (K - lower_K) * (Uf1_upper - Uf1_lower) / (upper_K - lower_K)

            Uf2_lower = df[df.iloc[:, 0] == lower_K][col2].values[0]
            Uf2_upper = df[df.iloc[:, 0] == upper_K][col2].values[0]
            Uf2 = Uf2_lower + (K - lower_K) * (Uf2_upper - Uf2_lower) / (upper_K - lower_K)

        # Calculate weights based on how close reflectances are
        diff1 = distances[0][0]
        diff2 = distances[1][0]
        weight1 = 1 / (diff1 + 1e-9)  # Small number to avoid division by zero
        weight2 = 1 / (diff2 + 1e-9)

        # Final Uf is weighted average of two closest reflectance combinations
        Uf = (Uf1 * weight1 + Uf2 * weight2) / (weight1 + weight2)
        return float(Uf)

    except Exception as e:
        logging.error(f"Error calculating Uf: {e}")
        raise ValueError(f"Error calculating Uf: {e}")
# ==============================================
# HELPER FUNCTIONS
# ==============================================

def validate_input(value, field_name, min_value=None, max_value=None):
    """
    Validate that input values are numbers within specified ranges.
    
    Args:
        value: Input value to validate
        field_name: Name of field for error messages
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        Validated numeric value
        
    Raises:
        ValueError: For invalid inputs
    """
    try:
        value = float(value)
        
        # Check minimum value constraint
        if min_value is not None and value < min_value:
            raise ValueError(
                f"{field_name} must be greater than or equal to {min_value}."
            )
            
        # Check maximum value constraint
        if max_value is not None and value > max_value:
            raise ValueError(
                f"{field_name} must be less than or equal to {max_value}."
            )
            
        return value
        
    except ValueError:
        raise ValueError(
            f"Invalid input for {field_name}. Please enter a numeric value."
        )

def calculate_aspect_ratio(room_length, room_width):
    """
    Calculate length-to-width ratio of the room.
    
    Args:
        room_length: Room length in meters
        room_width: Room width in meters
        
    Returns:
        Aspect ratio (length/width)
    """
    return room_length / room_width

def calculate_spacing(room_dim, num_fixtures):
    """
    Calculate spacing between fixtures along one dimension.
    
    Args:
        room_dim: Room dimension (length or width) in meters
        num_fixtures: Number of fixtures along this dimension
        
    Returns:
        Spacing between fixtures in meters
    """
    if num_fixtures <= 1:
        return room_dim  # Special case: Only one fixture uses full dimension
    return room_dim / num_fixtures

def calculate_shr(spacing, mounting_height):
    """
    Calculate Spacing-to-Height Ratio (SHR).
    
    Args:
        spacing: Distance between fixtures in meters
        mounting_height: Fixture mounting height in meters
        
    Returns:
        SHR value (or infinity if invalid height)
    """
    if mounting_height <= 0:
        return float('inf')  # Invalid mounting height
    return spacing / mounting_height

def find_valid_arrays(num_fixtures, aspect_ratio, room_length, 
                     room_width, mounting_height, shr_nom):
    """
    Find valid fixture arrangements meeting SHR and spacing requirements.
    
    Args:
        num_fixtures: Calculated number of fixtures needed
        aspect_ratio: Room length-to-width ratio
        room_length: Room length in meters
        room_width: Room width in meters
        mounting_height: Fixture mounting height in meters
        shr_nom: Nominal SHR value from metadata
        
    Returns:
        Tuple of (best_even_array, best_odd_array) layouts
    """
    # Use the modified SHRNOM value from metadata
    shr_nom_value = metadata['SHRNOM_Modified']
    valid_arrays = []
    
    # Try different numbers of rows and columns
    max_dim = num_fixtures + 3  # Don't try more than this
    
    for rows in range(1, max_dim + 1):
        for cols in range(1, max_dim + 1):
            # Skip combinations that don't provide enough fixtures
            if rows * cols < num_fixtures:
                continue
                
            # Determine orientation based on room shape
            if aspect_ratio >= 1:  # Longer than wide
                along_length, across_width = max(rows, cols), min(rows, cols)
            else:  # Wider than long
                along_length, across_width = min(rows, cols), max(rows, cols)
            
            # Calculate spacing in both directions
            spacing_length = calculate_spacing(room_length, along_length)
            spacing_width = calculate_spacing(room_width, across_width)
            
            # Calculate SHR in both directions
            shr_length = calculate_shr(spacing_length, mounting_height)
            shr_width = calculate_shr(spacing_width, mounting_height)
            
            # Check if this arrangement meets SHR requirements
            shr_valid = (shr_length <= shr_nom_value and 
                        shr_width <= shr_nom_value)
            
            # Check minimum spacing requirements with special cases:
            if along_length == 1:  # Single row along length
                spacing_valid = spacing_width >= MIN_SPACING if across_width > 1 else True
            elif across_width == 1:  # Single column across width
                spacing_valid = spacing_length >= MIN_SPACING if along_length > 1 else True
            else:  # Multiple rows and columns
                spacing_valid = (spacing_length >= MIN_SPACING and 
                                spacing_width >= MIN_SPACING)
            
            # Only add if both SHR and spacing requirements are met
            if shr_valid and spacing_valid:
                valid_arrays.append({
                    'array': (along_length, across_width),
                    'spacing_length': spacing_length,
                    'spacing_width': spacing_width,
                    'shr_length': shr_length,
                    'shr_width': shr_width,
                    'fixtures': along_length * across_width,
                    'parity': 'even' if across_width % 2 == 0 else 'odd'
                })
    
    # Remove duplicate arrangements and sort by closest to target fixture count
    unique_arrays = []
    seen = set()
    for arr in sorted(valid_arrays, 
                     key=lambda x: (abs(x['fixtures'] - num_fixtures), x['fixtures'])):
        key = arr['array']
        if key not in seen:
            seen.add(key)
            unique_arrays.append(arr)
    
    # Find one even and one odd arrangement
    even_array = next((a for a in unique_arrays if a['parity'] == 'even'), None)
    odd_array = next((a for a in unique_arrays if a['parity'] == 'odd'), None)
    
    return even_array, odd_array

def calculate_adjusted_light_level(E, num_fixtures, actual_fixtures):
    """
    Calculate actual light level based on how many fixtures are actually used.
    
    Args:
        E: Target illuminance in lux
        num_fixtures: Calculated number of fixtures needed
        actual_fixtures: Number of fixtures in the actual layout
        
    Returns:
        Adjusted illuminance level in lux
    """
    return E * (actual_fixtures / num_fixtures)
# ==============================================
# MAIN CALCULATION FUNCTION
# ==============================================

def calculate_and_display():
    """
    Main function that runs when Calculate button is clicked.
    Performs all calculations and updates the GUI with results.
    """
    try:
        # Get and validate all input values
        room_length = validate_input(room_length_entry.get(), "Room Length", min_value=0.1)
        room_width = validate_input(room_width_entry.get(), "Room Width", min_value=0.1)
        room_height = validate_input(room_height_entry.get(), "Room Height", min_value=0.1)
        working_plane_height = validate_input(
            working_plane_height_entry.get(), 
            "Working Plane Height", 
            min_value=0.1
        )
        suspension_distance = validate_input(
            suspension_distance_entry.get(), 
            "Suspension Distance", 
            min_value=0
        )
        ceiling_reflectance = validate_input(
            ceiling_reflectance_entry.get(), 
            "Ceiling Reflectance", 
            min_value=0, 
            max_value=100
        )
        walls_reflectance = validate_input(
            walls_reflectance_entry.get(), 
            "Walls Reflectance", 
            min_value=0, 
            max_value=100
        )
        floor_reflectance = validate_input(
            floor_reflectance_entry.get(), 
            "Floor Reflectance", 
            min_value=0, 
            max_value=100
        )
        E = validate_input(E_entry.get(), "Required Illuminance", min_value=0)
        MF = validate_input(MF_entry.get(), "Maintenance Factor", min_value=0, max_value=1)

        # Get values from the loaded CSV file
        luminous_flux_value = float(luminous_flux.get().split(":")[1].strip().split()[0])
        wattage_value = float(wattage.get().split(":")[1].strip().rstrip("W"))
        shr_nom_value = metadata['SHRNOM_Modified']  # Using modified value

        # Perform all calculations
        K = calculate_room_cavity_index(
            room_length, 
            room_width, 
            room_height, 
            working_plane_height, 
            suspension_distance
        )
        Uf = interpolate_uf(
            K, 
            ceiling_reflectance, 
            walls_reflectance, 
            floor_reflectance, 
            uf_table
        )
        num_fixtures = calculate_number_of_fixtures(
            E, 
            room_length, 
            room_width, 
            luminous_flux_value, 
            Uf, 
            MF
        )

        # Calculate mounting height (distance from work plane to fixtures)
        mounting_height = (room_height - working_plane_height) - suspension_distance
        if mounting_height <= 0:
            raise ValueError(
                "Invalid mounting height (check room height and suspension distance)"
            )

        # Find valid fixture arrangements
        aspect_ratio = calculate_aspect_ratio(room_length, room_width)
        even_array, odd_array = find_valid_arrays(
            num_fixtures, 
            aspect_ratio, 
            room_length, 
            room_width, 
            mounting_height, 
            shr_nom_value
        )

        def format_array(array_data):
            """Format array information for display in results table."""
            if not array_data:
                return "No valid array found (spacing or SHR constraints not met)"
                
            array = array_data['array']
            spacing_length = array_data['spacing_length']
            spacing_width = array_data['spacing_width']
            actual_fixtures = array_data['fixtures']
            adjusted_E = calculate_adjusted_light_level(E, num_fixtures, actual_fixtures)
            
            # Check spacing against minimum requirements
            spacing_status = []
            if array[0] > 1 and spacing_length < MIN_SPACING:
                spacing_status.append(f"Length spacing < {MIN_SPACING}m")
            if array[1] > 1 and spacing_width < MIN_SPACING:
                spacing_status.append(f"Width spacing < {MIN_SPACING}m")
            
            spacing_note = " | Spacing OK" if not spacing_status else " | Spacing issues: " + ", ".join(spacing_status)
            
            return (
                f"{array[0]} along length, {array[1]} across width | "
                f"Spacing: {spacing_length:.2f}m (L), {spacing_width:.2f}m (W){spacing_note} | "
                f"SHR: {array_data['shr_length']:.2f} (L), {array_data['shr_width']:.2f} (W) | "
                f"Fixtures: {actual_fixtures}, Lux: {adjusted_E:.0f}"
            )

        # Clear previous results from the table
        for widget in result_table.get_children():
            result_table.delete(widget)

        # Prepare all results for display
        results = [
            ("Fixture Name", fixture_name.get().split(":")[1].strip()),
            ("Luminous Flux", f"{luminous_flux_value:.0f} lumens"),
            ("Wattage", f"{wattage_value:.0f} W"),
            ("SHRNOM (CSV)", f"{metadata['SHRNOM']:.2f}"),
            ("SHRNOM (Modified)", f"{metadata['SHRNOM_Modified']:.2f}"),
            ("Minimum Spacing", f"{MIN_SPACING} m (hard-coded)"),
            ("Room Length", f"{room_length:.1f} m"),
            ("Room Width", f"{room_width:.1f} m"),
            ("Room Height", f"{room_height:.1f} m"),
            ("Working Plane Height", f"{working_plane_height:.1f} m"),
            ("Suspension Distance", f"{suspension_distance:.1f} m"),
            ("Mounting Height", f"{mounting_height:.1f} m"),
            ("Ceiling Reflectance", f"{ceiling_reflectance:.0f} %"),
            ("Walls Reflectance", f"{walls_reflectance:.0f} %"),
            ("Floor Reflectance", f"{floor_reflectance:.0f} %"),
            ("Required Lux Level", f"{E:.0f} lux"),
            ("Maintenance Factor", f"{MF:.2f}"),
            ("Room Cavity Index (K)", f"{K:.2f}"),
            ("Utilisation Factor (Uf)", f"{Uf:.2f}"),
            ("Number of Fixtures", f"{num_fixtures}"),
            ("Valid Array (Even)", format_array(even_array)),
            ("Valid Array (Odd)", format_array(odd_array))
        ]

        # Add results to the table
        for row in results:
            result_table.insert("", "end", values=row)

        # Update visualizations
        visualizer.clear_visualizations()
        
        # Draw even array layout if it exists
        if even_array:
            visualizer.draw_room_layout(
                room_length,
                room_width,
                even_array,
                f"Even Array: {even_array['array'][0]}×{even_array['array'][1]} Fixtures"
            )
        
        # Draw odd array layout if it exists
        if odd_array:
            visualizer.draw_room_layout(
                room_length,
                room_width,
                odd_array,
                f"Odd Array: {odd_array['array'][0]}×{odd_array['array'][1]} Fixtures"
            )

        logging.info("Calculation completed successfully.")
        
    except Exception as e:
        logging.error(f"Error during calculation: {e}")
        messagebox.showerror("Error", str(e))
# ==============================================
# CLIPBOARD FUNCTION
# ==============================================

def copy_to_clipboard():
    """Copy the results table contents to system clipboard."""
    try:
        results = []
        
        # Get all results from the table
        for child in result_table.get_children():
            values = result_table.item(child, "values")
            results.append(f"{values[0]}: {values[1]}")

        # Combine into a single string
        results_text = "\n".join(results)
        
        if results_text:
            # Copy to clipboard
            root.clipboard_clear()
            root.clipboard_append(results_text)
            messagebox.showinfo("Copied", "Results copied to clipboard!")
            logging.info("Results copied to clipboard.")
            
    except Exception as e:
        logging.error(f"Error copying to clipboard: {e}")
        messagebox.showerror("Error", str(e))

# ==============================================
# GUI IMPLEMENTATION
# ==============================================

# Create main application window
root = tk.Tk()
root.title("Voltex Highbay Quantity Calculator")
root.geometry("1400x900")  # Wider window for side-by-side layout

# Define font to use throughout the GUI
font = ("Arial", 12)

# Define variables that will show in the GUI
fixture_name = tk.StringVar()  # Will show fixture name
luminous_flux = tk.StringVar()  # Will show luminous flux value
wattage = tk.StringVar()       # Will show wattage
shr_nom = tk.StringVar()       # Will show SHRNOM values

# ==============================================
# MAIN FRAME STRUCTURE
# ==============================================

# Create left panel for inputs and results
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Create right panel for visualizations
right_frame = tk.Frame(root, width=500)  # Fixed width for visualizations
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=10, pady=10)

# ==============================================
# CSV FILE SECTION (LEFT FRAME)
# ==============================================

# Label and entry for CSV file path
csv_file_path_label = tk.Label(left_frame, text="CSV File Path:", font=font)
csv_file_path_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

csv_file_path_entry = tk.Entry(left_frame, width=60, font=font)
csv_file_path_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

# Button to load CSV file
load_csv_button = tk.Button(
    left_frame, 
    text="Load CSV File", 
    command=load_csv_file, 
    font=font
)
load_csv_button.grid(row=0, column=2, sticky="w", padx=10, pady=5)

# ==============================================
# METADATA DISPLAY SECTION (LEFT FRAME)
# ==============================================

# These labels will show the fixture information after loading a CSV
metadata_labels = ["Fixture Name:", "Luminous Flux:", "Wattage:", "SHRNOM:"]
metadata_vars = [fixture_name, luminous_flux, wattage, shr_nom]

# Create labels and value displays in a 4-row grid
for i, (label_text, var) in enumerate(zip(metadata_labels, metadata_vars)):
    tk.Label(left_frame, text=label_text, font=font).grid(
        row=i + 1, column=0, sticky="w", padx=10, pady=2
    )
    tk.Label(left_frame, textvariable=var, font=font).grid(
        row=i + 1, column=1, sticky="w", padx=10, pady=2
    )

# ==============================================
# INPUT FIELDS SECTION (LEFT FRAME)
# ==============================================

# All the input fields the user needs to fill in
input_labels = [
    "Room Length (m):", "Room Width (m):", "Room Height (m):", 
    "Working Plane Height (m):", "Suspension Distance (m):", 
    "Ceiling Reflectance (%):", "Walls Reflectance (%):",
    "Floor Reflectance (%):", "Required Illuminance (lux):", 
    "Maintenance Factor (MF):"
]
input_entries = []  # Will store all the input boxes

# Create labels and input fields in a grid
for i, label_text in enumerate(input_labels):
    tk.Label(left_frame, text=label_text, font=font).grid(
        row=i + 5, column=0, sticky="w", padx=10, pady=2
    )
    entry = tk.Entry(left_frame, font=font)
    entry.grid(row=i + 5, column=1, sticky="w", padx=10, pady=2)
    input_entries.append(entry)

# Give names to each input field for easier reference
(room_length_entry, room_width_entry, room_height_entry, 
 working_plane_height_entry, suspension_distance_entry, 
 ceiling_reflectance_entry, walls_reflectance_entry, 
 floor_reflectance_entry, E_entry, MF_entry) = input_entries

# Set some default values
MF_entry.insert(0, "0.8")  # Default maintenance factor
ceiling_reflectance_entry.insert(0, "50")  # Default ceiling reflectance
walls_reflectance_entry.insert(0, "30")  # Default walls reflectance
floor_reflectance_entry.insert(0, "10")  # Default floor reflectance

# ==============================================
# TOOLTIPS FOR INPUT FIELDS (LEFT FRAME)
# ==============================================

# Help messages that appear when hovering over inputs
tooltips = {
    "Room Length (m):": "Enter the length of the room in meters (must be > 0).",
    "Room Width (m):": "Enter the width of the room in meters (must be > 0).",
    "Room Height (m):": "Enter the height of the room in meters (must be > 0).",
    "Working Plane Height (m):": "Distance from working plane to ceiling (must be > 0).",
    "Suspension Distance (m):": "Distance from ceiling to fixture (must be >= 0).",
    "Ceiling Reflectance (%):": "Ceiling reflectance percentage (0-100).",
    "Walls Reflectance (%):": "Walls reflectance percentage (0-100).",
    "Floor Reflectance (%):": "Floor reflectance percentage (0-100).",
    "Required Illuminance (lux):": "Required illuminance in lux (must be > 0).",
    "Maintenance Factor (MF):": "Maintenance factor (0-1). Default is 0.8.",
}

# Attach tooltips to each input field
for i, label_text in enumerate(input_labels):
    tooltip = tooltips.get(label_text, "")
    if tooltip:
        ToolTip(input_entries[i], tooltip)

# ==============================================
# CALCULATE BUTTON (LEFT FRAME)
# ==============================================

# This button runs the main calculation when clicked
calculate_button = tk.Button(
    left_frame, 
    text="Calculate", 
    command=calculate_and_display, 
    font=font
)
calculate_button.grid(row=15, column=0, columnspan=2, sticky="w", padx=10, pady=10)

# ==============================================
# RESULTS TABLE (LEFT FRAME)
# ==============================================

# This table shows all the calculation results
result_table = ttk.Treeview(
    left_frame, 
    columns=("Parameter", "Value"), 
    show="headings", 
    height=22
)
result_table.heading("Parameter", text="Parameter")
result_table.heading("Value", text="Value")
result_table.column("Parameter", width=300, anchor="w")  # Left-aligned
result_table.column("Value", width=700, anchor="w")
result_table.grid(row=16, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)

# Add scrollbar to results table
scrollbar = ttk.Scrollbar(
    left_frame, 
    orient="vertical", 
    command=result_table.yview
)
scrollbar.grid(row=16, column=3, sticky="ns")
result_table.configure(yscrollcommand=scrollbar.set)

# ==============================================
# COPY TO CLIPBOARD BUTTON (LEFT FRAME)
# ==============================================

copy_button = tk.Button(
    left_frame, 
    text="Copy Results to Clipboard", 
    command=copy_to_clipboard, 
    font=font
)
copy_button.grid(row=17, column=0, columnspan=2, sticky="w", padx=10, pady=10)

# ==============================================
# VISUALIZATION FRAME (RIGHT FRAME)
# ==============================================

# Create a container frame for the entire right panel content
right_content_frame = tk.Frame(right_frame)
right_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# 1. Add title at the very top
viz_label = tk.Label(
    right_content_frame,  # Changed from right_frame to right_content_frame
    text="Suggested Layouts", 
    font=("Arial", 12, "bold"),
    bg="#f0f0f0"  # Match your background color
)
viz_label.pack(side=tk.TOP, pady=(0, 10))  # 10px bottom margin only

# 2. Create visualization frame below the title
visualization_frame = tk.Frame(right_content_frame)
visualization_frame.pack(fill=tk.BOTH, expand=True)

# 3. Initialize the visualizer in the visualization frame
visualizer = LayoutVisualizer(visualization_frame)
visualizer.setup_visualization_area()

# ==============================================
# RUN THE APPLICATION
# ==============================================

# Start the GUI event loop
root.mainloop()
