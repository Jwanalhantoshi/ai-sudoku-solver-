import tkinter as tk
from tkinter import messagebox, filedialog
import time
import random

import customtkinter as ctk
import cv2
import numpy as np
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def format_time(elapsed_time):
    minutes = int(elapsed_time // 60)
    seconds = elapsed_time % 60
    return f"{minutes:02d}:{seconds:05.2f}"

class SudokuGUI:
    def __init__(self, root):
        self.reset_button = None
        self.pause_button = None
        self.solve_button = None
        self.upload_button = None
        self.speed_selector = None
        self.load_button = None
        self.sps_stat = None
        self.time_stat = None
        self.steps_stat = None
        self.board_canvas = None
        self.right = None
        self.left = None
        self.main = None
        self.root = root
        self.root.title("AI Sudoku Solver")
        self.root.geometry("1180x760")
        self.root.resizable(False, False)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.BG = "#F1DFDD"
        self.PANEL_BG = "#FFF4F2"
        self.CELL = "#FFF8F7"
        self.SOFT_CELL = "#F7DDE2"
        self.GIVEN = "#EEAAC3"
        self.TRYING = "#D86487"
        self.SUCCESS = "#DDF3E4"
        self.ERROR = "#F6B0BD"
        self.DARK = "#4A202A"
        self.ACCENT = "#D86487"
        self.DEEP = "#76172C"
        self.LINE = "#C97991"
        self.GRID_LIGHT = "#E7B5C2"

        self.board_size = 520
        self.cell_size = self.board_size // 9

        self.board_values = [[0 for _ in range(9)] for _ in range(9)]
        self.original_cells = set()
        self.selected_cell = None

        self.start_time = None
        self.steps_count = 0
        self.is_paused = False
        self.is_solving = False
        self.speed_var = tk.StringVar(value="Medium")

        self.puzzles = [
            [
                [0, 0, 8, 9, 2, 0, 0, 0, 0],
                [0, 2, 0, 1, 0, 0, 0, 0, 4],
                [3, 1, 0, 0, 0, 0, 0, 5, 0],
                [1, 0, 9, 0, 0, 0, 0, 6, 0],
                [0, 0, 4, 0, 6, 0, 3, 0, 0],
                [0, 6, 0, 0, 0, 0, 8, 0, 1],
                [0, 3, 0, 0, 0, 0, 0, 1, 5],
                [4, 0, 0, 0, 0, 8, 0, 7, 0],
                [0, 0, 0, 0, 3, 5, 2, 0, 0]
            ],
            [
                [7, 6, 0, 3, 0, 0, 0, 0, 0],
                [5, 0, 0, 0, 0, 6, 4, 0, 0],
                [0, 4, 0, 2, 8, 0, 0, 0, 0],
                [0, 0, 5, 0, 0, 3, 0, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 4],
                [4, 0, 0, 6, 0, 0, 8, 0, 0],
                [0, 0, 0, 0, 1, 2, 0, 6, 0],
                [0, 0, 3, 5, 0, 0, 0, 0, 7],
                [0, 0, 0, 0, 0, 4, 0, 9, 5]
            ]
        ]

        self.root.configure(bg=self.BG)
        self.build_layout()
        self.root.bind("<Key>", self.handle_key)

    def build_layout(self):
        self.main = ctk.CTkFrame(self.root, fg_color=self.BG, corner_radius=0)
        self.main.pack(fill="both", expand=True)

        self.left = ctk.CTkFrame(self.main, fg_color=self.BG, corner_radius=0, width=700)
        self.left.pack(side="left", fill="both", padx=(40, 8), pady=18)

        self.right = ctk.CTkFrame(self.main, fg_color=self.PANEL_BG, corner_radius=28, width=420)
        self.right.pack(side="left", fill="both", expand=True, padx=(8, 28), pady=18)

        self.build_left_panel()
        self.build_right_panel()

    def build_left_panel(self):
        ctk.CTkLabel(
            self.left,
            text="Sudoku Solver",
            font=("Georgia", 42, "bold"),
            text_color=self.DEEP
        ).pack(pady=(0, 0))

        sub_frame = ctk.CTkFrame(self.left, fg_color=self.BG)
        sub_frame.pack(pady=(0, 14))

        ctk.CTkLabel(
            sub_frame,
            text="AI Step-by-Step Visualization",
            font=("Georgia", 17, "bold"),
            text_color=self.ACCENT
        ).pack(side="left", padx=(0, 18))

        ctk.CTkButton(
            sub_frame,
            text="Heuristic Algorithm",
            width=190,
            height=36,
            corner_radius=18,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT,
            text_color="white",
            font=("Georgia", 13, "bold"),
            command=lambda: None
        ).pack(side="left")

        self.board_canvas = tk.Canvas(
            self.left,
            width=self.board_size,
            height=self.board_size,
            bg=self.BG,
            highlightthickness=0
        )
        self.board_canvas.pack(pady=(0, 18))
        self.board_canvas.bind("<Button-1>", self.select_cell)
        self.draw_board()

        stats_bar = ctk.CTkFrame(
            self.left,
            fg_color="#FFF4F2",
            corner_radius=18,
            width=640,
            height=72,
            border_width=1,
            border_color="#E7B5C2"
        )
        stats_bar.pack(pady=(0, 0))
        stats_bar.pack_propagate(False)

        self.steps_stat = self.make_stat_item(stats_bar, "Steps", "0")
        self.time_stat = self.make_stat_item(stats_bar, "Execution Time", "00:00.00")
        self.sps_stat = self.make_stat_item(stats_bar, "Steps Per Second", "0.00")

    def make_stat_item(self, parent, label, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", expand=True, fill="both", padx=10, pady=12)

        ctk.CTkLabel(
            frame,
            text=label,
            font=("Georgia", 12, "bold"),
            text_color=self.DEEP
        ).pack()

        value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=("Georgia", 13, "bold"),
            text_color=self.DEEP
        )
        value_label.pack()

        return value_label

    def build_right_panel(self):
        ctk.CTkLabel(
            self.right,
            text="Heuristic Algorithm",
            font=("Georgia", 27, "bold"),
            text_color=self.DEEP
        ).pack(anchor="w", padx=34, pady=(32, 4))

        tk.Frame(self.right, bg=self.ACCENT, height=3).pack(fill="x", padx=34, pady=(0, 22))

        ctk.CTkLabel(
            self.right,
            text="Heuristic algorithms use smart strategies\n"
                 "to find the best next move by evaluating\n"
                 "available options. They reduce the search\n"
                 "space and solve puzzles more efficiently\n"
                 "than brute force methods.",
            font=("Arial", 18),
            justify="left",
            text_color=self.DARK
        ).pack(anchor="w", padx=34)

        ctk.CTkLabel(
            self.right,
            text="Speed",
            font=("Georgia", 16, "bold"),
            text_color=self.DARK
        ).pack(anchor="w", padx=34, pady=(24, 8))

        self.speed_selector = ctk.CTkSegmentedButton(
            self.right,
            values=["Slow", "Medium", "Fast"],
            variable=self.speed_var,
            width=355,
            height=48,
            corner_radius=16,
            fg_color="#F7DDE2",
            selected_color="#EEAAC3",
            selected_hover_color="#EEAAC3",
            unselected_color="#F7DDE2",
            unselected_hover_color="#EEAAC3",
            text_color=self.DEEP,
            font=("Georgia", 13, "bold")
        )
        self.speed_selector.pack(padx=34, pady=(0, 16))
        self.speed_selector.set("Medium")

        self.load_button = self.side_button("~  Load Random Puzzle", self.load_random_puzzle, light=True)
        self.upload_button = self.side_button("⇧  Upload Sudoku Puzzle", self.upload_sudoku_image, light=True)

        tk.Frame(self.right, bg="#E7B5C2", height=2).pack(fill="x", padx=34, pady=18)

        self.solve_button = self.side_button("▶  Solve", self.start_solving, light=False, height=54)
        self.pause_button = self.side_button("Ⅱ  Pause", self.toggle_pause, light=True)
        self.reset_button = self.side_button("⟳  Reset", self.clear_board, light=True)

    def side_button(self, text, command, light=True, height=50):
        button = ctk.CTkButton(
            self.right,
            text=text,
            command=command,
            width=355,
            height=height,
            corner_radius=20,
            fg_color="#F7DDE2" if light else self.DEEP,
            hover_color="#EEAAC3" if light else self.ACCENT,
            text_color=self.DEEP if light else "white",
            font=("Georgia", 15, "bold"),
            border_width=1,
            border_color="#E7B5C2"
        )
        button.pack(padx=34, pady=7)
        return button

    def draw_board(self):
        self.board_canvas.delete("all")

        for row in range(9):
            for col in range(9):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                if (row, col) in self.original_cells:
                    fill = self.GIVEN
                else:
                    fill = self.CELL if (row + col) % 2 == 0 else self.SOFT_CELL

                self.board_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=fill,
                    outline=self.GRID_LIGHT,
                    width=1
                )

                value = self.board_values[row][col]
                if value != 0:
                    self.board_canvas.create_text(
                        x1 + self.cell_size / 2,
                        y1 + self.cell_size / 2,
                        text=str(value),
                        fill=self.DEEP,
                        font=("Georgia", 24, "bold")
                    )

        for i in range(10):
            position = i * self.cell_size

            if i % 3 == 0:
                width = 2.4
                color = self.DEEP
            else:
                width = 1
                color = self.GRID_LIGHT

            self.board_canvas.create_line(position, 0, position, self.board_size, fill=color, width=width)
            self.board_canvas.create_line(0, position, self.board_size, position, fill=color, width=width)

        self.board_canvas.create_rectangle(
            1, 1, self.board_size - 1, self.board_size - 1,
            outline=self.DEEP,
            width=3
        )

        if self.selected_cell and not self.is_solving:
            row, col = self.selected_cell
            x1 = col * self.cell_size
            y1 = row * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size

            self.board_canvas.create_rectangle(
                x1 + 3, y1 + 3, x2 - 3, y2 - 3,
                outline=self.ACCENT,
                width=3
            )

    def select_cell(self, event):
        if self.is_solving:
            return

        col = event.x // self.cell_size
        row = event.y // self.cell_size

        if 0 <= row < 9 and 0 <= col < 9:
            self.selected_cell = (row, col)
            self.draw_board()

    def handle_key(self, event):
        if self.is_solving or not self.selected_cell:
            return

        row, col = self.selected_cell

        if (row, col) in self.original_cells:
            return

        if event.char in "123456789":
            self.board_values[row][col] = int(event.char)
            self.draw_board()

        elif event.keysym in ["BackSpace", "Delete"]:
            self.board_values[row][col] = 0
            self.draw_board()

    def flash_cell_glow(self, row, col, value, final_color):
        x = col * self.cell_size
        y = row * self.cell_size

        rect_id = self.board_canvas.create_rectangle(
            x + 4, y + 4,
            x + self.cell_size - 4,
            y + self.cell_size - 4,
            fill=self.TRYING,
            outline=self.ACCENT,
            width=3
        )

        text_id = None
        if value != 0:
            text_id = self.board_canvas.create_text(
                x + self.cell_size / 2,
                y + self.cell_size / 2,
                text=str(value),
                fill="white",
                font=("Georgia", 24, "bold")
            )

        self.root.update()
        time.sleep(self.get_delay())

        self.board_canvas.delete(rect_id)
        if text_id:
            self.board_canvas.delete(text_id)

        self.board_values[row][col] = value
        self.draw_board()

        outline_id = self.board_canvas.create_rectangle(
            x + 3, y + 3,
            x + self.cell_size - 3,
            y + self.cell_size - 3,
            outline=final_color,
            width=3
        )

        self.root.update()
        time.sleep(max(self.get_delay() / 2, 0.02))
        self.board_canvas.delete(outline_id)
        self.draw_board()

    def set_solving_visuals(self, active):
        if active:
            self.solve_button.configure(text="▶  Solving...", fg_color=self.DEEP)
        else:
            self.solve_button.configure(text="▶  Solve", fg_color=self.DEEP)

    def update_timer(self):
        if self.start_time is not None and self.is_solving:
            elapsed_time = time.time() - self.start_time
            self.time_stat.configure(text=format_time(elapsed_time))

            if elapsed_time > 0:
                self.sps_stat.configure(text=f"{self.steps_count / elapsed_time:.2f}")

    def clear_board(self):
        if self.is_solving:
            messagebox.showwarning("Solving", "Please pause or wait until solving finishes.")
            return

        self.original_cells.clear()
        self.selected_cell = None
        self.is_paused = False
        self.steps_count = 0
        self.start_time = None
        self.board_values = [[0 for _ in range(9)] for _ in range(9)]

        self.steps_stat.configure(text="0")
        self.time_stat.configure(text="00:00.00")
        self.sps_stat.configure(text="0.00")
        self.set_solving_visuals(False)
        self.draw_board()

    def load_puzzle_to_board(self, puzzle):
        if self.is_solving:
            messagebox.showwarning("Solving", "Please wait until solving finishes.")
            return

        self.clear_board()

        for row in range(9):
            for col in range(9):
                self.board_values[row][col] = puzzle[row][col]

        self.draw_board()

    def load_random_puzzle(self):
        selected_puzzle = random.choice(self.puzzles)
        self.load_puzzle_to_board(selected_puzzle)

    def upload_sudoku_image(self):
        if self.is_solving:
            messagebox.showwarning("Solving", "Please wait until solving finishes.")
            return

        file_path = filedialog.askopenfilename(
            title="Select Sudoku Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )

        if not file_path:
            return

        try:
            puzzle = self.extract_sudoku_from_image(file_path)
            self.load_puzzle_to_board(puzzle)

        except Exception as e:
            messagebox.showerror(
                "OCR Error",
                f"Could not read the Sudoku image.\n\nReason:\n{e}"
            )

    def extract_sudoku_from_image(self, image_path):
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError("Image could not be opened.")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2
        )

        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            raise ValueError("No Sudoku grid found.")

        largest = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, 0.02 * perimeter, True)

        if len(approx) != 4:
            raise ValueError("Could not detect the Sudoku square clearly.")

        points = approx.reshape(4, 2)
        ordered_points = self.order_points(points)

        size = 450
        destination = np.array([
            [0, 0],
            [size - 1, 0],
            [size - 1, size - 1],
            [0, size - 1]
        ], dtype="float32")

        matrix = cv2.getPerspectiveTransform(ordered_points, destination)
        warped = cv2.warpPerspective(gray, matrix, (size, size))

        puzzle = []
        cell_size = size // 9

        for row in range(9):
            current_row = []

            for col in range(9):
                x1 = col * cell_size
                y1 = row * cell_size
                x2 = (col + 1) * cell_size
                y2 = (row + 1) * cell_size

                cell = warped[y1:y2, x1:x2]
                margin = 8
                cell = cell[margin:cell_size - margin, margin:cell_size - margin]

                digit = self.recognize_digit(cell)
                current_row.append(digit)

            puzzle.append(current_row)

        return puzzle

    @staticmethod
    def order_points(points):
        rect = np.zeros((4, 2), dtype="float32")

        points_sum = points.sum(axis=1)
        rect[0] = points[np.argmin(points_sum)]
        rect[2] = points[np.argmax(points_sum)]

        points_diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(points_diff)]
        rect[3] = points[np.argmax(points_diff)]

        return rect

    @staticmethod
    def recognize_digit(cell):
        cell = cv2.resize(cell, (80, 80))
        cell = cv2.GaussianBlur(cell, (3, 3), 0)

        _, cell_thresh = cv2.threshold(
            cell,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        total_pixels = cell_thresh.shape[0] * cell_thresh.shape[1]
        filled_pixels = cv2.countNonZero(cell_thresh)

        if filled_pixels < total_pixels * 0.03:
            return 0

        config = "--psm 10 --oem 3 -c tessedit_char_whitelist=123456789"
        text = pytesseract.image_to_string(cell_thresh, config=config)
        text = text.strip()

        for char in text:
            if char.isdigit() and char != "0":
                return int(char)

        return 0

    def get_delay(self):
        speed = self.speed_var.get()

        if speed == "Slow":
            return 0.25
        if speed == "Medium":
            return 0.08
        return 0.01

    def wait_if_paused(self):
        while self.is_paused:
            self.update_timer()
            self.root.update()
            time.sleep(0.05)

    def toggle_pause(self):
        if self.is_solving:
            self.is_paused = not self.is_paused

            if self.is_paused:
                self.pause_button.configure(text="▶  Resume")
            else:
                self.pause_button.configure(text="Ⅱ  Pause")

    def get_board(self):
        board = []

        for row in range(9):
            current_row = []

            for col in range(9):
                value = self.board_values[row][col]

                if value == 0:
                    current_row.append(0)
                elif 1 <= value <= 9:
                    current_row.append(value)
                else:
                    messagebox.showerror("Invalid Input", "Only numbers from 1 to 9 are allowed.")
                    return None

            board.append(current_row)

        return board

    def lock_original_cells(self):
        self.original_cells.clear()

        for row in range(9):
            for col in range(9):
                if self.board_values[row][col] != 0:
                    self.original_cells.add((row, col))

        self.draw_board()

    @staticmethod
    def is_valid(board, num, row, col):
        for i in range(9):
            if board[row][i] == num:
                return False

        for i in range(9):
            if board[i][col] == num:
                return False

        box_row = (row // 3) * 3
        box_col = (col // 3) * 3

        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if board[i][j] == num:
                    return False

        return True

    def get_candidates(self, board, row, col):
        if board[row][col] != 0:
            return []

        candidates = []

        for num in range(1, 10):
            if self.is_valid(board, num, row, col):
                candidates.append(num)

        return candidates

    def find_heuristic_cell(self, board):
        best_cell = None
        best_candidates = None

        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    candidates = self.get_candidates(board, row, col)

                    if len(candidates) == 0:
                        return (row, col), []

                    if best_candidates is None or len(candidates) < len(best_candidates):
                        best_cell = (row, col)
                        best_candidates = candidates

        return best_cell, best_candidates

    def update_cell(self, row, col, value, final_color):
        self.wait_if_paused()

        if value != 0:
            self.flash_cell_glow(row, col, value, final_color)
        else:
            self.board_values[row][col] = 0
            self.draw_board()
            self.root.update()
            time.sleep(self.get_delay())

    def solve_heuristics(self, board):
        self.wait_if_paused()

        cell, candidates = self.find_heuristic_cell(board)

        if cell is None:
            return True

        row, col = cell

        for num in candidates:
            self.wait_if_paused()

            self.steps_count += 1
            self.steps_stat.configure(text=str(self.steps_count))
            self.update_timer()
            self.root.update()

            board[row][col] = num
            self.update_cell(row, col, num, self.SUCCESS)

            if self.solve_heuristics(board):
                return True

            board[row][col] = 0
            self.update_cell(row, col, 0, self.ERROR)

        return False

    def start_solving(self):
        if self.is_solving:
            return

        board = self.get_board()

        if board is None:
            return

        self.steps_count = 0
        self.is_paused = False
        self.is_solving = True

        self.pause_button.configure(text="Ⅱ  Pause")
        self.steps_stat.configure(text="0")
        self.time_stat.configure(text="00:00.00")
        self.sps_stat.configure(text="0.00")

        self.lock_original_cells()
        self.start_time = time.time()
        self.set_solving_visuals(True)

        if self.solve_heuristics(board):
            self.update_timer()
            self.board_values = board
            self.draw_board()
        else:
            messagebox.showerror("No Solution", "This Sudoku puzzle cannot be solved.")

        self.is_solving = False
        self.is_paused = False
        self.set_solving_visuals(False)


app_root = ctk.CTk()
app = SudokuGUI(app_root)
app_root.mainloop()