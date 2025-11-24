import threading
import os
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
from Syllabus_Checker_For_GUI import check_syllabus
from reportlab.pdfgen import canvas


def save_report_as_pdf(text, filepath):
    c = canvas.Canvas(filepath)
    y = 800
    for line in text.split("\n"):
        c.drawString(40, y, line)
        y -= 14
        if y < 40:
            c.showPage()
            y = 800
    c.save()


class PennStateSyllabusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Penn State Syllabus Checker")
        self.root.geometry("1200x800")
        self.root.minsize(900, 650)

        # MAIN COLORS
        self.BG_BLUE = "#74AADD"      # page background
        self.WHITE = "#FFFFFF"
        self.PSU_BLUE = "#002D72"
        self.PSU_NAV = "#003B8E"
        self.ACCENT = "#FFCC00"

        self.file_path = None

        # save file as a PDF
        def save_report_as_pdf(text, filepath):
            c = canvas.Canvas(filepath)
            y = 800
            for line in text.split("\n"):
                c.drawString(40, y, line)
                y -= 14
                if y < 40:
                    c.showPage()
                    y = 800
            c.save()

        # Root background
        self.root.configure(bg=self.BG_BLUE)

        #                         HEADER
        header = Frame(self.root, bg=self.PSU_BLUE, height=130)
        header.pack(side=TOP, fill=X)

        # Lion logo (left)
        self.lion_icon = None
        lion_holder = Frame(header, bg=self.PSU_BLUE)
        lion_holder.pack(side=LEFT, padx=20, pady=10)

        if os.path.exists("lion.png"):
            img = Image.open("lion.png")
            img = img.resize((110, 110), Image.LANCZOS)
            self.lion_icon = ImageTk.PhotoImage(img)
            Label(lion_holder, image=self.lion_icon, bg=self.PSU_BLUE).pack()
        else:
            Label(lion_holder, text="🦁", font=("Segoe UI", 48), bg=self.PSU_BLUE, fg=self.WHITE).pack()

        # Title & subtitle (center)
        title_frame = Frame(header, bg=self.PSU_BLUE)
        title_frame.pack(side=LEFT, expand=True)

        Label(
            title_frame,
            text="Penn State Syllabus Checker",
            font=("Segoe UI", 24, "bold"),
            bg=self.PSU_BLUE,
            fg=self.WHITE
        ).pack(anchor="w", pady=(20, 0))

        Label(
            title_frame,
            text="CMPSC 487W — Penn State Abington",
            font=("Segoe UI", 13),
            bg=self.PSU_BLUE,
            fg="#D0E4FF"
        ).pack(anchor="w", pady=(4, 10))

        # Top-right nav (About / Help)
        nav_frame = Frame(header, bg=self.PSU_BLUE)
        nav_frame.pack(side=RIGHT, padx=30)

        about_btn = Label(
            nav_frame, text="About",
            fg=self.WHITE, bg=self.PSU_BLUE,
            font=("Segoe UI", 14, "bold"), cursor="hand2"
        )
        help_btn = Label(
            nav_frame, text="Help",
            fg=self.WHITE, bg=self.PSU_BLUE,
            font=("Segoe UI", 14, "bold"), cursor="hand2"
        )

        about_btn.pack(side=LEFT, padx=15)
        help_btn.pack(side=LEFT, padx=15)

        # Hover effect for nav labels
        self._add_hover_label(about_btn, self.WHITE, "#FFEE88")
        self._add_hover_label(help_btn, self.WHITE, "#FFEE88")

        about_btn.bind("<Button-1>", lambda e: messagebox.showinfo(
            "About",
            "Penn State Syllabus Checker\n\n"
            "Developed by:\n"
            "• Jack Demtshuk\n"
            "• Ishaq Halimi\n"
            "• Joscelin Montoya-Rojas\n"
            "• Rebecca Nanayakkara\n"
            "• Nicholas Taweel\n"
            "\nCMPSC 487W — Penn State Abington\n© 2025"
        ))

        help_btn.bind("<Button-1>", lambda e: messagebox.showinfo(
            "Help",
            "1) Select a syllabus PDF\n"
            "2) Click Analyze\n"
            "3) Review the content and readability report\n"
            "4) Save the report if needed\n\n"
            "Faculty Handbook:\nhttps://senate.psu.edu/faculty/syllabus-requirements/"
        ))

        #                         MAIN AREA
        main_frame = Frame(self.root, bg=self.BG_BLUE)
        main_frame.pack(fill=BOTH, expand=True, padx=30, pady=25)

        # -------------------- CONTROL CARD ------------------------
        control_card = Frame(main_frame, bg=self.WHITE, bd=0, relief="flat")
        control_card.pack(fill=X, pady=(0, 15))

        # Card top border (fake rounded look with padding)
        control_inner = Frame(control_card, bg=self.WHITE)
        control_inner.pack(fill=X, padx=18, pady=18)

        Label(
            control_inner,
            text="Upload and Analyze Your Syllabus",
            font=("Segoe UI", 18, "bold"),
            bg=self.WHITE,
            fg=self.PSU_BLUE
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        Label(
            control_inner,
            text="Select a PDF syllabus file, then click Analyze to generate a report.",
            font=("Segoe UI", 11),
            bg=self.WHITE,
            fg="#444444"
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 15))

        # Buttons row
        btn_row = Frame(control_inner, bg=self.WHITE)
        btn_row.grid(row=2, column=0, columnspan=3, sticky="w")

        self.select_btn = Button(
            btn_row,
            text="📂  Select PDF",
            font=("Segoe UI", 16, "bold"),
            bg=self.PSU_BLUE,
            fg=self.WHITE,
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.select_file
        )
        self.select_btn.pack(side=LEFT, padx=(0, 10))

        self.analyze_btn = Button(
            btn_row,
            text="▶  Analyze",
            font=("Segoe UI", 16, "bold"),
            bg="#0E8044",
            fg=self.WHITE,
            relief="flat",
            padx=22,
            pady=8,
            cursor="hand2",
            command=self.run_file_check
        )
        self.analyze_btn.pack(side=LEFT, padx=10)

        self.save_btn = Button(
            btn_row,
            text="💾  Save Report",
            font=("Segoe UI", 16, "bold"),
            bg="#F5F5F5",
            fg="#333333",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.save_report
        )
        self.save_btn.pack(side=LEFT, padx=10)

        # Hover styling for buttons
        self._add_hover_button(self.select_btn, self.PSU_BLUE, "#1D4E9E", self.WHITE, self.WHITE)
        self._add_hover_button(self.analyze_btn, "#0E8044", "#0A5C31", self.WHITE, self.WHITE)
        self._add_hover_button(self.save_btn, "#F5F5F5", "#E2E2E2", "#333333", "#000000")

        # File label
        self.file_label = Label(
            control_inner,
            text="No file selected",
            font=("Segoe UI", 11),
            bg=self.WHITE,
            fg="#666666",
            anchor="w"
        )
        self.file_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(12, 0))

        #                    OUTPUT / REPORT CARD
        output_card = Frame(main_frame, bg=self.WHITE, bd=0, relief="flat")
        output_card.pack(fill=BOTH, expand=True)

        output_inner = Frame(output_card, bg=self.WHITE)
        output_inner.pack(fill=BOTH, expand=True, padx=18, pady=18)

        Label(
            output_inner,
            text="Syllabus Analysis Report",
            font=("Segoe UI", 15, "bold"),
            bg=self.WHITE,
            fg=self.PSU_BLUE
        ).pack(anchor="w", pady=(0, 8))

        # Output Text + Scrollbar
        text_frame = Frame(output_inner, bg=self.WHITE)
        text_frame.pack(fill=BOTH, expand=True, pady=(5, 0))

        self.output = Text(
            text_frame,
            wrap=WORD,
            font=("Consolas", 11),
            bg="#FAFAFA",
            fg="#111111",
            relief="flat",
            bd=0
        )
        self.output.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = Scrollbar(text_frame, command=self.output.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.output.config(yscrollcommand=scrollbar.set)

        #                    STATUS + PROGRESS
        status_frame = Frame(main_frame, bg=self.BG_BLUE)
        status_frame.pack(fill=X, pady=(10, 0))

        self.status = Label(
            status_frame,
            text="Ready",
            font=("Segoe UI", 11),
            bg=self.BG_BLUE,
            fg=self.PSU_BLUE,
            anchor="w"
        )
        self.status.pack(side=LEFT, padx=(2, 10))

        self.progress = ttk.Progressbar(
            status_frame,
            mode="indeterminate",
            length=220
        )
        self.progress.pack(side=RIGHT, padx=5)
        self.progress.stop()

    #                       HELPER METHODS
    def _add_hover_button(self, btn, bg_normal, bg_hover, fg_normal, fg_hover):
        def on_enter(e):
            btn.config(bg=bg_hover, fg=fg_hover)

        def on_leave(e):
            btn.config(bg=bg_normal, fg=fg_normal)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def _add_hover_label(self, lbl, fg_normal, fg_hover):
        def on_enter(e):
            lbl.config(fg=fg_hover)

        def on_leave(e):
            lbl.config(fg=fg_normal)

        lbl.bind("<Enter>", on_enter)
        lbl.bind("<Leave>", on_leave)

    def _set_status(self, text, color=None):
        if color is None:
            color = self.PSU_BLUE
        self.status.config(text=text, fg=color)
        self.root.update_idletasks()

    def _insert_rich_text(self, msg):
        """
        Parse <color=#RRGGBB>...</color> tags and insert with tags.
        Everything else is plain text.
        """
        import re
        pattern = r'<color=(#[0-9A-Fa-f]{6})>(.*?)</color>'
        pos = 0
        for match in re.finditer(pattern, msg, flags=re.S):
            start, end = match.span()
            # plain chunk
            if start > pos:
                self.output.insert(END, msg[pos:start])

            color = match.group(1)
            text = match.group(2)

            tag_name = f"color_{color}"
            if tag_name not in self.output.tag_names():
                self.output.tag_config(tag_name, foreground=color, font=("Consolas", 11, "bold"))

            self.output.insert(END, text, tag_name)
            pos = end

        if pos < len(msg):
            self.output.insert(END, msg[pos:])

        self.output.insert(END, "\n")
        self.output.see(END)

    # MAIN ACTIONS
    def select_file(self):
        path = filedialog.askopenfilename(
            title="Select a Syllabus PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if path:
            self.file_path = path
            self.file_label.config(
                text=f"✓ {os.path.basename(path)}",
                fg="#1D4E9E"
            )
            self._set_status("Ready to analyze", self.PSU_BLUE)

    def run_file_check(self):
        if not self.file_path:
            messagebox.showwarning("No File Selected", "Please select a PDF file first.")
            return

        self.output.delete("1.0", END)
        self._set_status("Analyzing syllabus...", self.ACCENT)
        self.progress.start(10)

        # Disable buttons during analysis
        self.analyze_btn.config(state=DISABLED)
        self.select_btn.config(state=DISABLED)
        self.save_btn.config(state=DISABLED)

        def worker():
            try:
                report = check_syllabus(self.file_path)
                self.root.after(0, lambda: self._display_report(report))
            except Exception as e:
                self.root.after(0, lambda err=e: self._display_error(err))

        threading.Thread(target=worker, daemon=True).start()

    def _display_report(self, report):
        self.progress.stop()
        self._set_status("✓ Analysis complete", "#0E8044")

        self.output.delete("1.0", END)
        self._insert_rich_text(report)

        # Re-enable buttons
        self.analyze_btn.config(state=NORMAL)
        self.select_btn.config(state=NORMAL)
        self.save_btn.config(state=NORMAL)

    def _display_error(self, error):
        self.progress.stop()
        self._set_status("✗ Analysis failed", "#CC0000")

        self.output.delete("1.0", END)
        self.output.insert(END, f"Error during analysis:\n\n{error}")

        # Re-enable buttons
        self.analyze_btn.config(state=NORMAL)
        self.select_btn.config(state=NORMAL)
        self.save_btn.config(state=NORMAL)

    def save_report(self):
        text = self.output.get("1.0", END).strip()
        if not text:
            messagebox.showerror("Error", "No report to save.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF File", "*.pdf")]
        )
        if save_path:
            save_report_as_pdf(text, save_path)
            self._set_status("✓ Report saved as PDF", "#0E8044")


if __name__ == "__main__":
    root = Tk()
    app = PennStateSyllabusApp(root)
    root.mainloop()
