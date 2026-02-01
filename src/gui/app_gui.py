import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os
from pathlib import Path
import threading
from src.core.converter import process_images_to_pdf # Import the core conversion function


class PNGtoPDFConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("PNG to PDF Converter")
        self.root.geometry("900x600")
        self.root.configure(bg="#F5F5DC")  # Beige background
        
        self.files_to_convert = []  # List of dicts: {'path': '...', 'frame': ..., 'label': ..., 'remove_btn': ..., 'thumbnail': ..., 'status_label': ...}
        self.output_path_manually_set = False # New flag to track if user has manually set output path
        self.pdf_output_mode = tk.StringVar(value="single") # Default to single PDF
        self.dragged_item_path = None
        self.dragged_item_frame = None
        self.drag_start_y = 0
        self.drag_offset_y = 0
        self.placeholder_frame = None # Visual placeholder for drop position
        
        # Title Label
        title = tk.Label(
            root,
            text="PNG to PDF Converter",
            font=("Helvetica", 20, "bold"),
            bg="#F5F5DC",
            fg="#2F4F4F"
        )
        title.pack(pady=20)
        
        # Drop Zone
        self.drop_frame = tk.Frame(
            root,
            bg="#ADD8E6",  # Light blue
            width=500,
            height=200,
            relief="solid",
            borderwidth=2
        )
        self.drop_frame.pack(pady=20)
        self.drop_frame.pack_propagate(False)
        
        self.drop_label = tk.Label(
            self.drop_frame,
            text="Drag & Drop PNG files here\nor click Browse",
            font=("Helvetica", 14),
            bg="#ADD8E6",
            fg="#2F4F4F"
        )
        self.drop_label.place(relx=0.5, rely=0.5, anchor="center")

        # Scrollable Frame for file list
        self.canvas = tk.Canvas(self.drop_frame, bg="#ADD8E6", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.drop_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ADD8E6")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind('<Enter>', self._bound_to_mousewheel)
        self.canvas.bind('<Leave>', self._unbound_to_mousewheel)
        
        # Hide scrollable frame initially
        self.canvas.pack_forget()
        self.scrollbar.pack_forget()
        
        # Enable drag and drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)

        # Frame for buttons
        btn_frame = tk.Frame(root, bg="#F5F5DC")
        btn_frame.pack(pady=10)
        
        # Browse Button
        self.browse_btn = tk.Button(
            btn_frame,
            text="Browse Files",
            command=self.browse_files,
            font=("Helvetica", 12),
            bg="#90EE90",  # Light green
            fg="#2F4F4F",
            padx=20,
            pady=10,
            relief="raised",
            cursor="hand2"
        )
        self.browse_btn.pack(side="left", padx=10)

        # Convert Button
        self.convert_btn = tk.Button(
            btn_frame,
            text="Convert to PDF",
            command=self.start_conversion,
            font=("Helvetica", 12),
            bg="#FFD700",  # Gold
            fg="#2F4F4F",
            padx=20,
            pady=10,
            relief="raised",
            cursor="hand2",
            state=tk.DISABLED  # Initially disabled
        )
        self.convert_btn.pack(side="left", padx=10)

        # Clear All Button
        self.clear_btn = tk.Button(
            btn_frame,
            text="Clear All",
            command=self.clear_all_files,
            font=("Helvetica", 12),
            bg="#FF6347",  # Tomato
            fg="#FFFFFF",
            padx=20,
            pady=10,
            relief="raised",
            cursor="hand2",
            state=tk.DISABLED  # Initially disabled
        )
        self.clear_btn.pack(side="left", padx=10)

        btn_frame.pack(pady=10)

        # PDF Output Mode (Radio Buttons) - Moved up
        mode_frame = tk.Frame(root, bg="#F5F5DC")
        mode_frame.pack(pady=5)

        single_pdf_radio = tk.Radiobutton(
            mode_frame,
            text="Combine into Single PDF",
            variable=self.pdf_output_mode,
            value="single",
            bg="#F5F5DC",
            fg="#2F4F4F",
            font=("Helvetica", 10)
        )
        single_pdf_radio.pack(side="left", padx=10)

        separate_pdf_radio = tk.Radiobutton(
            mode_frame,
            text="Separate PDFs for Each Image",
            variable=self.pdf_output_mode,
            value="separate",
            bg="#F5F5DC",
            fg="#2F4F4F",
            font=("Helvetica", 10)
        )
        separate_pdf_radio.pack(side="left", padx=10)

        # Output Directory Selector - Moved below radio buttons
        output_frame = tk.Frame(root, bg="#F5F5DC")
        output_frame.pack(pady=10)

        self.output_path = tk.StringVar(value=os.getcwd()) # Default to current working directory

        output_label = tk.Label(output_frame, text="Output Folder:", font=("Helvetica", 10), bg="#F5F5DC", fg="#2F4F4F")
        output_label.pack(side="left", padx=5)

        self.output_path_entry = tk.Entry(output_frame, textvariable=self.output_path, width=40, state="readonly")
        self.output_path_entry.pack(side="left", padx=5)

        browse_output_btn = tk.Button(
            output_frame,
            text="Browse",
            command=self.browse_output_directory,
            font=("Helvetica", 10),
            bg="#B0C4DE",  # Light steel blue
            fg="#2F4F4F",
            relief="raised",
            cursor="hand2"
        )
        browse_output_btn.pack(side="left", padx=5)

        # Completion Message Label - Replaces progress_frame
        self.completion_message_label = tk.Label(
            root,
            text="",
            font=("Helvetica", 10, "bold"),
            bg="#F5F5DC",
            fg="#2F4F4F"
        )
        self.completion_message_label.pack(pady=5)
    
    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def browse_output_directory(self):
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_path.get()
        )
        if directory:
            self.output_path.set(directory)
            self.output_path_manually_set = True

    def _on_drag_start(self, event, file_path):
        # Record the item being dragged
        self.dragged_item_path = file_path
        for file_info in self.files_to_convert:
            if file_info['path'] == file_path:
                self.dragged_item_frame = file_info['frame']
                self.drag_start_y = event.y_root
                self.drag_offset_y = event.y_root - self.dragged_item_frame.winfo_y()
                break

        # Hide the original frame being dragged temporarily
        self.dragged_item_frame.pack_forget()

        # Create a placeholder for visual feedback during drag
        # Create a transparent rectangle as a placeholder on the canvas
        self.placeholder_frame_id = self.canvas.create_rectangle(
            0, self.dragged_item_frame.winfo_y(),
            self.canvas.winfo_width(), self.dragged_item_frame.winfo_y() + self.dragged_item_frame.winfo_height(),
            outline="gray", width=2, dash=(5, 5)
        )

    def _on_drag_motion(self, event):
        if self.dragged_item_frame and self.placeholder_frame:
            # Calculate new Y position relative to the canvas
            new_y_on_canvas = self.canvas.canvasy(event.y_root - self.drag_offset_y)
            
            # Move the placeholder based on the mouse position
            self.canvas.coords(self.placeholder_frame_id, 0, new_y_on_canvas)

            # Update the scrollbar if dragging near the edges
            if event.y < 20:
                self.canvas.yview_scroll(-1, "units")
            elif event.y > self.canvas.winfo_height() - 20:
                self.canvas.yview_scroll(1, "units")


    def _on_drop(self, event):
        if self.dragged_item_path and self.dragged_item_frame:
            # Determine the new position for the dropped item
            drop_y = self.canvas.canvasy(event.y_root - self.drag_offset_y) # Y-coordinate on canvas

            # Find the index of the file that the dragged item was dropped over
            new_index = 0
            for i, file_info in enumerate(self.files_to_convert):
                if not file_info['removed'] and file_info['frame']:
                    frame_y_start = file_info['frame'].winfo_y()
                    frame_y_end = frame_y_start + file_info['frame'].winfo_height()
                    if drop_y > frame_y_start:
                        new_index = i + 1
                    else:
                        break
            
            # Find the original index of the dragged item
            original_index = -1
            for i, file_info in enumerate(self.files_to_convert):
                if file_info['path'] == self.dragged_item_path:
                    original_index = i
                    break

            if original_index != -1 and original_index != new_index:
                # Adjust new_index if dropping before the original position
                if new_index > original_index:
                    new_index -= 1

                # Reorder the internal list
                item = self.files_to_convert.pop(original_index)
                self.files_to_convert.insert(new_index, item)
        
        # Clean up drag state and refresh display
        self.dragged_item_path = None
        self.dragged_item_frame = None
        if self.placeholder_frame_id:
            self.canvas.delete(self.placeholder_frame_id)
            self.placeholder_frame_id = None

        self._refresh_file_list_display()

    
    def handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        png_files = [f for f in files if f.lower().endswith('.png')]
        
        if png_files:
            self.add_files_to_list(png_files)
        else:
            messagebox.showwarning("No PNG Files", "Please drop PNG files only.")
    
    def browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select PNG files",
            filetypes=[("PNG files", "*.png")]
        )
        
        if files:
            self.add_files_to_list(list(files))

    def add_files_to_list(self, new_files):
        self.drop_label.pack_forget() # Hide the drop label
        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.scrollbar.pack(side="right", fill="y")

        for file_path in new_files:
            if file_path not in [f['path'] for f in self.files_to_convert if not f.get('removed', False)]:
                # Set output path if it hasn't been manually set and this is the first active file
                if not self.output_path_manually_set and not any(f for f in self.files_to_convert if not f.get('removed', False)):
                    first_file_dir = Path(file_path).parent
                    self.output_path.set(str(first_file_dir))

                # Store enough information to reconstruct the visual element later
                self.files_to_convert.append({
                    'path': file_path,
                    'thumbnail': None, # Will be generated in _refresh_file_list_display
                    'frame': None, # Will be generated in _refresh_file_list_display
                    'label': None, # Will be generated in _refresh_file_list_display
                    'remove_btn': None, # Will be generated in _refresh_file_list_display
                    'removed': False,
                    'status_label': None # For post-conversion status
                })
        self._refresh_file_list_display()
        self.update_convert_button_state()
        self.completion_message_label.config(text="") # Clear completion message on new files

    def _refresh_file_list_display(self):
        # Clear existing widgets from the scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        temp_files_info = [] # To rebuild self.files_to_convert with new widget references

        for file_info in self.files_to_convert:
            if file_info['removed']:
                temp_files_info.append(file_info)
                continue

            file_frame = tk.Frame(self.scrollable_frame, bg="#E0FFFF") # Light cyan
            file_frame.pack(fill="x", pady=2, padx=5)

            # Bind drag-and-drop events to the file_frame
            file_frame.bind("<Button-1>", lambda e, p=file_info['path']: self._on_drag_start(e, p))
            file_frame.bind("<B1-Motion>", self._on_drag_motion)
            file_frame.bind("<ButtonRelease-1>", self._on_drop)

            # Thumbnail
            tk_img = None
            try:
                img = Image.open(file_info['path'])
                img.thumbnail((30, 30)) # Small thumbnail size
                tk_img = ImageTk.PhotoImage(img)
                thumb_label = tk.Label(file_frame, image=tk_img, bg="#E0FFFF")
                thumb_label.image = tk_img # Keep a reference!
                thumb_label.pack(side="left", padx=5)
            except Exception:
                thumb_label = tk.Label(file_frame, text="[IMG]", bg="#E0FFFF", fg="#2F4F4F")
                thumb_label.pack(side="left", padx=5)
            file_info['thumbnail'] = tk_img # Update thumbnail reference

            file_label = tk.Label(file_frame, text=file_info['path'], bg="#E0FFFF", fg="#2F4F4F", anchor="w")
            file_label.pack(side="left", fill="x", expand=True)
            file_info['label'] = file_label # Update label reference

            remove_btn = tk.Button(
                file_frame,
                text="X",
                fg="red",
                font=("Helvetica", 10, "bold"),
                command=lambda p=file_info['path']: self.remove_file(p)
            )
            remove_btn.pack(side="right")
            file_info['remove_btn'] = remove_btn # Update button reference

            status_label = tk.Label(file_frame, text="", bg="#E0FFFF", fg="#2F4F4F")
            status_label.pack(side="right", padx=5)
            file_info['status_label'] = status_label

            file_info['frame'] = file_frame # Update frame reference

            # Reapply grayed-out style if removed
            if file_info['removed']:
                file_frame.config(bg="#D3D3D3")
                file_label.config(bg="#D3D3D3", fg="#A9A9A9")
                remove_btn.config(state=tk.DISABLED, fg="#A9A9A9")
            
            temp_files_info.append(file_info)
        
        self.files_to_convert = temp_files_info # Reassign the updated list
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_convert_button_state(self):
        active_files = [f for f in self.files_to_convert if not f.get('removed', False)]
        if active_files:
            self.convert_btn.config(state=tk.NORMAL)
            self.clear_btn.config(state=tk.NORMAL)
        else:
            self.convert_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.DISABLED)
            # If no files, show the drop label again
            self.canvas.pack_forget()
            self.scrollbar.pack_forget()
            self.drop_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def remove_file(self, file_path):
        for file_info in self.files_to_convert:
            if file_info['path'] == file_path and not file_info['removed']:
                file_info['removed'] = True
                file_info['frame'].config(bg="#D3D3D3")  # Light gray
                file_info['label'].config(bg="#D3D3D3", fg="#A9A9A9") # Light gray, darker text
                file_info['remove_btn'].config(state=tk.DISABLED, fg="#A9A9A9")
                break
        self.update_convert_button_state()

    def clear_all_files(self):
        for file_info in self.files_to_convert:
            file_info['frame'].destroy()  # Destroy the file's frame
        self.files_to_convert = []
        self.output_path.set(os.getcwd()) # Reset output path to default
        self.output_path_manually_set = False # Reset manual override flag
        self.completion_message_label.config(text="") # Clear completion message on clear all
        self.update_convert_button_state()

    def start_conversion(self):
        active_files_paths = [f['path'] for f in self.files_to_convert if not f['removed']]
        if not active_files_paths:
            messagebox.showwarning("No Files Selected", "Please select PNG files to convert.")
            return

        # Run conversion in separate thread to keep UI responsive
        thread = threading.Thread(target=self.process_conversion, args=(active_files_paths,))
        thread.start()

    def process_conversion(self, files_to_convert_paths):
        self.completion_message_label.config(text="") # Clear previous completion message
        self.root.update_idletasks()

        # Reset all status labels
        for file_info in self.files_to_convert:
            if not file_info['removed'] and file_info['status_label']:
                file_info['status_label'].config(text="", fg="#2F4F4F")

        output_dir = Path(self.output_path.get())
        output_mode = self.pdf_output_mode.get()

        # Call the core conversion logic
        converted, skipped = process_images_to_pdf(
            png_paths=files_to_convert_paths,
            output_dir=output_dir,
            output_mode=output_mode,
            ask_overwrite_callback=self.ask_overwrite,
            get_new_name_callback=self.get_new_name,
            update_status_callback=self._update_file_status_label,
            update_overall_progress_callback=self._update_overall_progress
        )

        # Show completion message in the app window
        message = f"Conversion complete!  Converted: {converted}  Skipped: {skipped}"
        self.completion_message_label.config(text=message)

    def _update_file_status_label(self, file_path, status_text, color):
        for file_info in self.files_to_convert:
            if file_info['path'] == file_path and not file_info['removed'] and file_info['status_label']:
                file_info['status_label'].config(text=status_text, fg=color)
        self.root.update_idletasks()

    def _update_overall_progress(self, message, current, total):
        # For now, we only have a completion message, so this will update that or be empty during process
        # This callback can be expanded to update a progress bar if reintroduced
        pass # As per request, progress bar is removed

    def ask_overwrite(self, png_path, pdf_path):
        result = messagebox.askyesnocancel(
            "File Exists",
            f"'{Path(pdf_path).name}' already exists.\n\nYes = Overwrite\nNo = Rename\nCancel = Skip"
        )
        
        if result is True:
            return "overwrite"
        elif result is False:
            return "rename"
        else:
            return "skip"
    
    def get_new_name(self, original_path):
        new_name = simpledialog.askstring(
            "Rename File",
            f"Enter new name for PDF:",
            initialvalue=Path(original_path).stem
        )
        
        if new_name:
            new_path = Path(original_path).parent / f"{new_name}.pdf"
            return new_path
        return None


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = PNGtoPDFConverter(root)
    root.mainloop()