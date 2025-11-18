import random
import time

class SudokuGenerator:
    def __init__(self, size=9):
        self.size = size

    def generate_puzzle(self, difficulty="Easy"):
        time_i = time.time()
        while True:
            full_board = self.generate_full_solution()
            if full_board:
                puzzle = [row[:] for row in full_board]
                puzzle, check = self.remove_cells_with_unique_check(puzzle, difficulty)
                if check:
                    return puzzle

    def generate_full_solution(self, board=None):
        """
        Generates a full valid Sudoku board using efficient backtracking with candidate tracking.
        """
        board = [[0 for _ in range(9)] for _ in range(9)]
        squares = [(r, c) for r in range(9) for c in range(9)]
        available = { (r, c): list(range(1, 10)) for r in range(9) for c in range(9) }
        idx = 0

        while idx < 81:
            row, col = squares[idx]
            candidates = available[(row, col)]

            if not candidates:
                # Backtrack
                available[(row, col)] = list(range(1, 10))
                board[row][col] = 0
                idx -= 1
                if idx < 0:
                    return None
                continue

            num = random.choice(candidates)
            available[(row, col)].remove(num)

            if self.is_valid_move(board, row, col, num):
                board[row][col] = num
                idx += 1
            else:
                continue

        return board

    def remove_cells_with_unique_check(self, board, difficulty):
        """
        Removes cells from a full board to create a puzzle with a unique solution.
        Difficulty determines how many cells are removed.
        """
        if difficulty.lower() == "easy":
            target_removed = 40
        elif difficulty.lower() == "medium":
            target_removed = 45
        elif difficulty.lower() == "hard":
            target_removed = 50
        elif difficulty.lower() == "god":
            target_removed = 55
        else:
            target_removed = 40

        removed = 0
        removed_cells = set()
        attempts = 0
        max_attempts = 1000
        start_time = time.time()

        while removed < target_removed and attempts < max_attempts:
            r, c = random.randint(0, 8), random.randint(0, 8)
            if (r, c) in removed_cells or board[r][c] == 0:
                attempts += 1
                continue

            backup = board[r][c]
            board[r][c] = 0
            board_copy = [row[:] for row in board]

            if self.solve_sudoku_check_uniqueness(board_copy) == 1:
                removed += 1
                removed_cells.add((r, c))
            else:
                board[r][c] = backup

            attempts += 1
            if time.time() - start_time > 1.5:
                return board, False

        return board, True if removed >= target_removed else False

    def solve_sudoku_check_uniqueness(self, board, found=0):
        """
        Uses backtracking to count solutions (up to 2).
        Returns:
          0 = no solution,
          1 = unique solution,
          2 = more than one solution.
        """
        if found > 1:
            return 2
        pos = self.find_empty(board)
        if not pos:
            return found + 1
        row, col = pos
        for num in range(1, self.size + 1):
            if self.is_valid_move(board, row, col, num):
                board[row][col] = num
                found = self.solve_sudoku_check_uniqueness(board, found)
                board[row][col] = 0
                if found > 1:
                    break
        return found

    def is_valid_move(self, board, row, col, value):
        """
        Checks if placing 'value' at (row, col) is valid according to Sudoku rules.
        """
        if value in board[row]:
            return False
        for r in range(self.size):
            if board[r][col] == value:
                return False
        sub_row = (row // 3) * 3
        sub_col = (col // 3) * 3
        for i in range(3):
            for j in range(3):
                if board[sub_row + i][sub_col + j] == value:
                    return False
        return True

    def find_empty(self, board):
        """
        Finds the first empty cell (with value 0) in the board.
        Returns (row, col) or None if the board is full.
        """
        for i in range(self.size):
            for j in range(self.size):
                if board[i][j] == 0:
                    return (i, j)
        return None
