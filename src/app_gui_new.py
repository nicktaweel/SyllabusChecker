import threading
from tkinter import *
from tkinter import filedialog, messagebox
from Syllabus_Checker_For_GUI import check_syllabus


class SyllabusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Syllabus Analyzer")
        self.root.geometry("700x600")
        self.root.configure(bg = "white")

        self.file_path = None

        # Title
        Label(root, text = "Syllabus Checker", font = ("Segoe UI", 18, "bold"), bg = "black", fg = "red").pack(pady = 15)

        # File Selection
        file_frame = Frame(root, bg = "black")
        file_frame.pack(pady = 5)

        Button(file_frame, text = "Select PDF",command=self.select_file,font = ("Segoe UI", 10),bg = "gray", fg = "white",relief = "flat", padx = 10, pady = 5).pack(side=LEFT, padx=5)

        self.file_label = Label(file_frame, text="No file selected",font=("Segoe UI", 9), bg="white", fg="black")
        self.file_label.pack(side = LEFT, padx = 5)

        # Input
        query_frame = Frame(root, bg = "black")
        query_frame.pack(pady = 15)
        self.query_entry = Entry(query_frame, width=45,font=("Segoe UI", 10),relief="solid", bd=1)
        self.query_entry.pack(side=LEFT, padx=5, ipady=3)

        Button(query_frame, text="Analyze", command=self.run_file_check, font=("Segoe UI", 10), bg="blue", fg="white", relief="flat", padx=10, pady=5).pack(side=LEFT)

        # Results
        self.output = Text(root, wrap=WORD, font=("Consolas", 10),relief="solid", bd=1, bg="white", fg="black")
        self.output.pack(fill=BOTH, expand=True, padx=20, pady=10)

        # Syllabus Status
        self.status = Label(root, text="Ready", bg="black",fg="white", font=("Segoe UI", 9, "italic"))
        self.status.pack(side=BOTTOM, pady=5)

    # for the actual file selection
    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.file_path = path
            self.file_label.config(text=path.split("/")[-1], fg="white")
            self.log(f"Selected file: {path}")

    def run_file_check(self):
        if not self.file_path:
            messagebox.showwarning("Missing File", "Please select a PDF file first.")
            return
        query = self.query_entry.get().strip()
        threading.Thread(target=self.perform_check, args=(query,), daemon=True).start()

    def perform_check(self, query):
        self.set_status("Reading Syllabus.", "blue")
        self.output.delete(1.0, END)
        try:
            report = check_syllabus(self.file_path, query)
            self.log(report)
            self.set_status("Done", "blue")
        except Exception as e:
            self.log(f"Error: {e}")
            self.set_status("Error", "red")

    def log(self, msg):
        self.output.insert(END, msg + "\n")
        self.output.see(END)

    def set_status(self, msg, color="blue"):
        self.status.config(text=msg, fg=color)
        self.root.update_idletasks()


if __name__ == "__main__":
    root = Tk()
    app = SyllabusApp(root)
    root.mainloop()
