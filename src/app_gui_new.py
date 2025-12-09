import threading
from tkinter import *
from tkinter import filedialog, messagebox
from Syllabus_Checker_For_GUI import check_syllabus


class SyllabusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Syllabus Analyzer")
        self.root.geometry("800x700")
        self.root.configure(bg="#2b2b2b")

        self.file_path = None

        # Title
        title_label = Label(
            root,
            text="📄 Syllabus Checker",
            font=("Segoe UI", 20, "bold"),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        title_label.pack(pady=20)

        # File Selection Frame
        file_frame = Frame(root, bg="#2b2b2b")
        file_frame.pack(pady=10)

        select_btn = Button(
            file_frame,
            text="Select PDF",
            command=self.select_file,
            font=("Segoe UI", 11),
            bg="#4a9eff",
            fg="white",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        select_btn.pack(side=LEFT, padx=5)

        self.file_label = Label(
            file_frame,
            text="No file selected",
            font=("Segoe UI", 10),
            bg="#3a3a3a",
            fg="#cccccc",
            padx=10,
            pady=8
        )
        self.file_label.pack(side=LEFT, padx=5)

        # Analyze Button
        analyze_btn = Button(
            root,
            text="▶ Analyze Syllabus",
            command=self.run_file_check,
            font=("Segoe UI", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        analyze_btn.pack(pady=10)

        # Output Text Area
        output_frame = Frame(root, bg="#2b2b2b")
        output_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)

        # Scrollbar
        scrollbar = Scrollbar(output_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.output = Text(
            output_frame,
            wrap=WORD,
            font=("Consolas", 14),
            relief="solid",
            bd=1,
            bg="#1e1e1e",
            fg="#d4d4d4",
            yscrollcommand=scrollbar.set
        )
        self.output.pack(fill=BOTH, expand=True)
        scrollbar.config(command=self.output.yview)

        # Status Bar
        self.status = Label(
            root,
            text="Ready to analyze",
            bg="#1e1e1e",
            fg="#4a9eff",
            font=("Segoe UI", 9),
            anchor=W,
            padx=10,
            pady=5
        )
        self.status.pack(side=BOTTOM, fill=X)

    def select_file(self):
        # open file explorer
        path = filedialog.askopenfilename(
            title="Select a Syllabus PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if path:
            self.file_path = path
            filename = path.split("/")[-1]
            self.file_label.config(text=filename, fg="#4CAF50")
            self.log(f"✓ File selected: {filename}\n")
            self.set_status(f"Ready to analyze: {filename}", "#4CAF50")

    def run_file_check(self):
        # validate input and start analyzing in background to keep GUI running
        if not self.file_path:
            messagebox.showwarning("No File Selected", "Please select a PDF file first.")
            return

        # Start analysis in background thread to keep GUI responsive
        threading.Thread(target=self.perform_check, daemon=True).start()

    def perform_check(self):
       # perform check and generate results
        self.set_status("Analyzing syllabus...", "#ffa500")
        self.output.delete(1.0, END)

        try:
            # Run the analysis
            report = check_syllabus(self.file_path)

            # Display results
            self.log(report)
            self.set_status("✓ Analysis complete", "#4CAF50")

        except Exception as e:
            error_msg = f"✗ Error during analysis:\n{str(e)}"
            self.log(error_msg)
            self.set_status("✗ Analysis failed", "#ff4444")
            messagebox.showerror("Analysis Error", f"An error occurred:\n\n{str(e)}")

    def log(self, msg):
      # appemd messages to output but with some new colors
        import re
        color_pattern = r'<color=(#[0-9A-Fa-f]{6})>(.*?)</color>'

        parts = re.split(color_pattern, msg)

        for i, part in enumerate(parts):
            if i % 3 == 0:  # Regular text
                if part:
                    self.output.insert(END, part)
            elif i % 3 == 1:  # Color code
                color = part
            elif i % 3 == 2:  # Colored text
                tag_name = f"color_{color}"
                if tag_name not in self.output.tag_names():
                    self.output.tag_config(tag_name, foreground=color)
                self.output.insert(END, part, tag_name)

        self.output.insert(END, "\n")
        self.output.see(END)

# add color witj status anmd color
    def set_status(self, msg, color="#4a9eff"):
        self.status.config(text=msg, fg=color)
        self.root.update_idletasks()


if __name__ == "__main__":
    root = Tk()
    app = SyllabusApp(root)
    root.mainloop()