from enum import Enum
from color import Color

class Rank(Enum):
    First = '1'
    Second = '2'
    Third = '3'
    Fourth = '4'
    Fifth = '5'
    Sixth = '6'
    Seventh = '7'
    Eighth = '8'

    def to_index(self):
        return int(self.value) - 1
    
    def of_index(index):
        try:
            return Rank(str(index + 1))
        except:
            return None

    def shift(self, shift):
        return Rank.of_index(self.to_index() + shift)
    
    def flip(self):
        return Rank.of_index(7 - self.to_index())

    def more_agg_than(self, rank, color):
        if color.value == 'White':
            return self.to_index() > rank.to_index()
        else:
            return self.to_index() < rank.to_index()
    
    def equals(self, rank):
        return self.to_index() == rank.to_index()

    def more_agg_or_equal(self, rank, color):
        return self.more_agg_than(rank, color) or self.equals(rank)

    def less_agg_than(self, rank, color):
        return not self.more_agg_or_equal(rank, color)
    
    def less_agg_or_equal(self, rank, color):
        return not self.more_agg_than(rank, color)

class File(Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'
    F = 'F'
    G = 'G'
    H = 'H'

    def to_index(self):
        return ord(self.name) - 65

    def of_index(index):
        try:
            return File(chr(index + 65))
        except:
            return None

    def shift(self, shift):
        return File.of_index(self.to_index() + shift)
    

class Square(Enum):
    A1 = 'A1'
    A2 = 'A2'
    A3 = 'A3'
    A4 = 'A4'
    A5 = 'A5'
    A6 = 'A6'
    A7 = 'A7'
    A8 = 'A8'
    B1 = 'B1'
    B2 = 'B2'
    B3 = 'B3'
    B4 = 'B4'
    B5 = 'B5'
    B6 = 'B6'
    B7 = 'B7'
    B8 = 'B8'
    C1 = 'C1'
    C2 = 'C2'
    C3 = 'C3'
    C4 = 'C4'
    C5 = 'C5'
    C6 = 'C6'
    C7 = 'C7'
    C8 = 'C8'
    D1 = 'D1'
    D2 = 'D2'
    D3 = 'D3'
    D4 = 'D4'
    D5 = 'D5'
    D6 = 'D6'
    D7 = 'D7'
    D8 = 'D8'
    E1 = 'E1'
    E2 = 'E2'
    E3 = 'E3'
    E4 = 'E4'
    E5 = 'E5'
    E6 = 'E6'
    E7 = 'E7'
    E8 = 'E8'
    F1 = 'F1'
    F2 = 'F2'
    F3 = 'F3'
    F4 = 'F4'
    F5 = 'F5'
    F6 = 'F6'
    F7 = 'F7'
    F8 = 'F8'
    G1 = 'G1'
    G2 = 'G2'
    G3 = 'G3'
    G4 = 'G4'
    G5 = 'G5'
    G6 = 'G6'
    G7 = 'G7'
    G8 = 'G8'
    H1 = 'H1'
    H2 = 'H2'
    H3 = 'H3'
    H4 = 'H4'
    H5 = 'H5'
    H6 = 'H6'
    H7 = 'H7'
    H8 = 'H8'

    def to_coordinates(self):
        return (int(self.name[1]) - 1, ord(self.name[0]) - 65)

    def of_coordinates(file, rank):
        try:
            return Square(chr(file + 65) + str(rank + 1))
        except:
            return None

    def of_rank_and_file(file, rank):
        try:
            return Square(file.name + rank.name)
        except:
            return None

    def of_rank(rank):
        return [square for square in Square if square.name[1] == rank.name]

    def of_file(file):
        return [square for square in Square if square.name[0] == file.name]

    def rank(self):
        return Rank(self.name[1])
    
    def file(self):
        return File(self.name[0])

    def shift(self, rank_shift, file_shift):
        rank, file = self.to_coordinates()
        return Square.of_coordinates(file + file_shift, rank + rank_shift)
    
    def distance(self, other_square):
        return abs(self.rank().to_index() - other_square.rank().to_index()) + abs(self.file().to_index() - other_square.file().to_index())
    
    # Returns a string and not a color object because there's a circular import if we reference Color here
    def color(self):
        r, f = self.to_coordinates()
        if (r + f) % 2 == 0:
            return 'B'
        else:
            return 'W'
        