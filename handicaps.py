class Handicap():
    def __init__(self, rule):
        self.rule = rule
    
    def filter(self, moves):
        return [move for move in moves if self.rule(move)]

    
    