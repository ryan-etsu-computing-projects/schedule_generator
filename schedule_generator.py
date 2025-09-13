import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import datetime
from dataclasses import dataclass
from typing import List, Tuple, Dict
import re

@dataclass
class ScheduleEvent:
    """Represents a single scheduled event"""
    title: str
    day: str
    start_time: str
    end_time: str
    location: str
    color: str

class TimeValidator:
    """Handles time parsing and validation"""

    @staticmethod
    def parse_time(time_str: str) -> Tuple[int, int]:
        """Parse time string to hours and minutes"""
        time_str = time_str.strip().upper()
        
        # Handle various time formats
        patterns = [
            # HH:MM AM/PM (e.g., 12:55 AM, 2:55 PM)
            (r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', True),
            # HH:MM in 24-hour format (e.g., 12:55, 14:55)  
            (r'^(\d{1,2}):(\d{2})$', False),
            # H AM/PM (e.g., 2 PM, 12 AM)
            (r'^(\d{1,2})\s*(AM|PM)$', True),
            # HH.MM AM/PM (e.g., 12.55 AM)
            (r'^(\d{1,2})\.(\d{2})\s*(AM|PM)$', True),
            # HH.MM in 24-hour format (e.g., 12.55, 14.55)
            (r'^(\d{1,2})\.(\d{2})$', False)
        ]
        
        for pattern, has_period in patterns:
            match = re.match(pattern, time_str)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                
                # Handle minutes - some patterns don't have minutes
                if len(groups) >= 2 and groups[1] and groups[1].isdigit():
                    minute = int(groups[1])
                else:
                    minute = 0
                
                # Handle AM/PM conversion
                if has_period:
                    period = groups[-1]  # Last group should be AM/PM
                    if period == 'PM' and hour != 12:
                        hour += 12
                    elif period == 'AM' and hour == 12:
                        hour = 0
                
                # Validate ranges
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return (hour, minute)
                else:
                    break  # Invalid time, try next pattern
        
        raise ValueError(f"Invalid time format: {time_str}. Try formats like '12:55 AM', '14:55', '2 PM', etc.")
    @staticmethod
    def time_to_float(time_str: str) -> float:
        """Convert time string to float hours for plotting"""
        hour, minute = TimeValidator.parse_time(time_str)
        return hour + minute / 60.0

class ScheduleGenerator:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Weekly Schedule Generator")
        self.root.geometry("840x800")
        
        # Color presets
        self.color_presets = {
            "ETSU Gold": "#ffc423",
            "ETSU Blue": "#002d62",
            "Blue": "#3498db",
            "Orange": "#e67e22", 
            "Green": "#27ae60",
            "Purple": "#9b59b6",
            "Red": "#e74c3c",
            "Teal": "#1abc9c",
            "Yellow": "#f1c40f",
            "Gray": "#7f8c8d"
        }
        
        self.events = []
        self.setup_ui()
    
    def setup_ui(self):
        """Create the user interface"""
        
        # Main frame with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Weekly Schedule Generator", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Event entry frame
        entry_frame = ttk.LabelFrame(main_frame, text="Add Event", padding=10)
        entry_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Event title
        ttk.Label(entry_frame, text="Event Title:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.title_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.title_var, width=30).grid(row=0, column=1, pady=2)
        
        # Day of week
        ttk.Label(entry_frame, text="Day:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.day_var = tk.StringVar()
        day_combo = ttk.Combobox(entry_frame, textvariable=self.day_var, 
                                values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        day_combo.grid(row=1, column=1, pady=2)
        day_combo.state(['readonly'])
        
        # Time range
        ttk.Label(entry_frame, text="Start Time:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.start_time_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.start_time_var, width=15).grid(row=2, column=1, pady=2)
        
        ttk.Label(entry_frame, text="End Time:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.end_time_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.end_time_var, width=15).grid(row=3, column=1, pady=2)
        
        # Location
        ttk.Label(entry_frame, text="Location:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.location_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.location_var, width=30).grid(row=4, column=1, pady=2)
        
        # Color selection
        ttk.Label(entry_frame, text="Color:").grid(row=5, column=0, sticky=tk.W, pady=2)
        color_frame = ttk.Frame(entry_frame)
        color_frame.grid(row=5, column=1, pady=2)
        
        self.color_var = tk.StringVar(value="Blue")
        color_combo = ttk.Combobox(color_frame, textvariable=self.color_var,
                                  values=list(self.color_presets.keys()), width=10)
        color_combo.pack(side=tk.LEFT)
        color_combo.state(['readonly'])
        
        ttk.Button(color_frame, text="Custom", command=self.choose_custom_color).pack(side=tk.LEFT, padx=(5,0))
        
        # Add event button
        ttk.Button(entry_frame, text="Add Event", command=self.add_event).grid(row=6, column=0, columnspan=2, pady=10)
        
        # Time format help
        help_label = ttk.Label(entry_frame, text="Time formats: 9:30 AM, 14:30, 2 PM, etc.", 
                              font=("Arial", 8), foreground="gray")
        help_label.grid(row=7, column=0, columnspan=2)
        
        # Events list frame
        list_frame = ttk.LabelFrame(main_frame, text="Current Events", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Events treeview
        columns = ("Day", "Time", "Title", "Location", "Color")
        self.events_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.events_tree.heading(col, text=col)
            self.events_tree.column(col, width=120 if col != "Title" else 200)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.events_tree.yview)
        self.events_tree.configure(yscrollcommand=scrollbar.set)
        
        self.events_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Delete button
        ttk.Button(list_frame, text="Delete Selected", command=self.delete_event).pack(pady=(10,0))
        
        # Generation options frame
        options_frame = ttk.LabelFrame(main_frame, text="Generation Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Days selection
        days_label = ttk.Label(options_frame, text="Include Days:")
        days_label.grid(row=0, column=0, sticky=tk.W)
        
        days_frame = ttk.Frame(options_frame)
        days_frame.grid(row=0, column=1, sticky=tk.W)
        
        self.day_vars = {}
        for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]):
            var = tk.BooleanVar(value=True)
            self.day_vars[day] = var
            ttk.Checkbutton(days_frame, text=day[:3], variable=var).grid(row=0, column=i, padx=5)
        
        # Time range
        ttk.Label(options_frame, text="End Time:").grid(row=1, column=0, sticky=tk.W, pady=(10,0))
        self.end_hour_var = tk.StringVar(value="6 PM")
        end_time_combo = ttk.Combobox(options_frame, textvariable=self.end_hour_var,
                                     values=["6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM"])
        end_time_combo.grid(row=1, column=1, sticky=tk.W, pady=(10,0))
        end_time_combo.state(['readonly'])
        
        # Professor name
        ttk.Label(options_frame, text="Name/Title:").grid(row=2, column=0, sticky=tk.W, pady=(10,0))
        self.prof_name_var = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.prof_name_var, width=25).grid(row=2, column=1, pady=(10,0))
        
        # Generate button
        generate_btn = ttk.Button(main_frame, text="Generate PDF Schedule", 
                                 command=self.generate_pdf, style="Accent.TButton")
        generate_btn.pack(pady=20)
        
    def choose_custom_color(self):
        """Open color picker for custom color selection"""
        color = colorchooser.askcolor(title="Choose Color")[1]
        if color:
            self.color_presets["Custom"] = color
            # Update combobox to include custom option
            combo = self.root.nametowidget(self.root.focus_get().master).winfo_children()[0]
            current_values = list(combo['values'])
            if "Custom" not in current_values:
                combo['values'] = current_values + ["Custom"]
            self.color_var.set("Custom")
    
    def add_event(self):
        """Add a new event to the schedule"""
        try:
            title = self.title_var.get().strip()
            day = self.day_var.get()
            start_time = self.start_time_var.get().strip()
            end_time = self.end_time_var.get().strip()
            location = self.location_var.get().strip()
            color_name = self.color_var.get()
            
            if not all([title, day, start_time, end_time]):
                messagebox.showerror("Error", "Please fill in all required fields")
                return
            
            # Validate times
            TimeValidator.parse_time(start_time)
            TimeValidator.parse_time(end_time)
            
            start_float = TimeValidator.time_to_float(start_time)
            end_float = TimeValidator.time_to_float(end_time)
            
            if start_float >= end_float:
                messagebox.showerror("Error", "Start time must be before end time")
                return
            
            color = self.color_presets.get(color_name, "#3498db")
            
            event = ScheduleEvent(title, day, start_time, end_time, location, color)
            self.events.append(event)
            
            # Update treeview
            self.events_tree.insert("", "end", values=(
                day, f"{start_time} - {end_time}", title, location, color_name
            ))
            
            # Clear form
            self.title_var.set("")
            self.start_time_var.set("")
            self.end_time_var.set("")
            self.location_var.set("")
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def delete_event(self):
        """Delete selected event"""
        selection = self.events_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to delete")
            return
        
        # Get the index of the selected item
        item_index = self.events_tree.index(selection[0])
        
        # Remove from events list and treeview
        del self.events[item_index]
        self.events_tree.delete(selection[0])
    
    def generate_pdf(self):
        """Generate PDF schedule"""
        if not self.events:
            messagebox.showwarning("Warning", "Please add at least one event")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save Schedule As"
            )
            
            if not filename:
                return
            
            self.create_schedule_pdf(filename)
            messagebox.showinfo("Success", f"Schedule saved as {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")
    
    def get_text_color(self, hex_color):
        """
        Determine whether to use black or white text on a given background color.
        
        Args:
            hex_color (str): Hex color code (e.g., '#70CCD1' or '70CCD1')
        
        Returns:
            str: Either 'black' or 'white' for optimal contrast
        """
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Calculate perceived luminance using simplified formula
        luminance = (0.299 * r) + (0.587 * g) + (0.114 * b)
        
        # Return black for light colors, white for dark colors
        return 'black' if luminance > 127.5 else 'white'

    def create_schedule_pdf(self, filename: str):
        """Create the actual PDF schedule"""
        # Determine which days to include
        selected_days = [day for day, var in self.day_vars.items() if var.get()]
        
        if not selected_days:
            raise ValueError("Please select at least one day to include")
        
        # Set up time range
        start_hour = 8
        end_time_str = self.end_hour_var.get()
        end_hour = {
            "6 PM": 18, "7 PM": 19, "8 PM": 20, 
            "9 PM": 21, "10 PM": 22, "11 PM": 23
        }[end_time_str]
        
        # Create figure with landscape orientation (11" wide x 8.5" tall)
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(11, 8.5))
        
        # Calculate proportional dimensions for landscape layout
        total_hours = end_hour - start_hour
        num_days = len(selected_days)
        
        # Use wider day columns for landscape orientation
        day_width = 2.0  # Increased width for better text fit
        time_height = total_hours * 0.8  # Proportional height
        
        # Draw day headers at TOP (y = time_height)
        for i, day in enumerate(selected_days):
            x = i * day_width
            
            # Day header at top
            header_rect = patches.Rectangle((x, time_height), day_width, 0.8, 
                                          linewidth=2, edgecolor='black', 
                                          facecolor='#2c3e50')
            ax.add_patch(header_rect)
            ax.text(x + day_width/2, time_height + 0.4, day.upper(), 
                   ha='center', va='center', fontweight='bold', 
                   fontsize=14, color='white')
        
        # DRAW GRID LINES FIRST (so they appear behind events)
        # Draw time grid with ASCENDING order (morning at top, evening at bottom)
        for hour in range(start_hour, end_hour + 1):
            # Invert y-coordinate: early hours get higher y values
            y = time_height - (hour - start_hour) * (time_height / total_hours)
            ax.axhline(y=y, color='lightgray', linewidth=0.5)
            
            # Time labels on the left
            time_12h = self.format_hour_12h(hour)
            ax.text(-0.15, y, time_12h, ha='right', va='center', fontsize=11)
        
        # Draw vertical grid lines
        for i in range(len(selected_days) + 1):
            ax.axvline(x=i * day_width, color='lightgray', linewidth=0.5)
        
        # NOW ADD EVENTS (they will appear on top of grid lines)
        day_positions = {day: i for i, day in enumerate(selected_days)}
        
        for event in self.events:
            if event.day in day_positions:
                x = day_positions[event.day] * day_width
                
                # Calculate y positions (inverted for ascending time)
                start_time_float = TimeValidator.time_to_float(event.start_time)
                end_time_float = TimeValidator.time_to_float(event.end_time)
                
                start_y = time_height - (start_time_float - start_hour) * (time_height / total_hours)
                end_y = time_height - (end_time_float - start_hour) * (time_height / total_hours)
                
                # Height is now end_y to start_y (since end_y < start_y in inverted coords)
                height = start_y - end_y
                
                # Event rectangle (positioned at end_y, with height going up)
                event_rect = patches.Rectangle((x + 0.05, end_y), day_width - 0.1, height,
                                             linewidth=2, edgecolor='darkgray',
                                             facecolor=event.color, alpha=0.8, zorder=2)
                ax.add_patch(event_rect)
                
                # Event text centered vertically
                text_y = end_y + height/2

                text_color = self.get_text_color(event.color)

                # Title
                ax.text(x + day_width/2, text_y + height*0.15, event.title, 
                       ha='center', va='center', fontweight='bold', 
                       fontsize=11, color=text_color, wrap=True)
                
                # Time range
                time_text = f"{event.start_time} - {event.end_time}"
                ax.text(x + day_width/2, text_y - height*0.1, time_text,
                       ha='center', va='center', fontsize=9, color=text_color)
                
                # Location
                if event.location:
                    ax.text(x + day_width/2, text_y - height*0.3, event.location,
                           ha='center', va='center', fontsize=9, color=text_color)
        
        # Set up the plot for landscape orientation
        ax.set_xlim(-0.8, len(selected_days) * day_width + 0.2)
        ax.set_ylim(-0.5, time_height + 1.3)
        
        # Don't force equal aspect ratio - let it use the full landscape space
        ax.set_aspect('auto')
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Add title
        prof_name = self.prof_name_var.get().strip()
        title_text = f"Fall 2025 Schedule"
        if prof_name:
            title_text += f" - {prof_name}"
        
        plt.suptitle(title_text, fontsize=18, fontweight='bold', y=0.95)
        
        # Add footer note
        plt.figtext(0.5, 0.02, "Please knock if door is closed during office hours", 
                   ha='center', fontsize=10, color='gray')
        
        # Save PDF with landscape orientation
        plt.tight_layout()
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches='tight', dpi=300, orientation='landscape')
        
        plt.close(fig)
    
    def format_hour_12h(self, hour: int) -> str:
        """Convert 24-hour format to 12-hour format"""
        if hour == 0:
            return "12:00 AM"
        elif hour < 12:
            return f"{hour}:00 AM"
        elif hour == 12:
            return "12:00 PM"
        else:
            return f"{hour - 12}:00 PM"

def main():
    root = tk.Tk()
    app = ScheduleGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()