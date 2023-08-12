from enum import Enum

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
        return (ord(self.name[0]) - 65, int(self.name[1]) - 1)

    def of_coordinates(file, rank):
        try:
            return Square(chr(file + 65) + str(rank + 1))
        except:
            return None

    def shift(self, file_shift, rank_shift):
        file, rank = self.to_coordinates()
        return Square.of_coordinates(file + file_shift, rank + rank_shift)