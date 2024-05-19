from __future__ import print_function
from dragonfly import (Grammar, RuleRef, CompoundRule, Choice, Optional, Compound)
import dragonfly 
import logging
import chess   
from typing import NamedTuple


if False:
    logging.basicConfig(level=10)
    logging.getLogger('grammar.decode').setLevel(20)
    logging.getLogger('compound').setLevel(20)
    # logging.getLogger('kaldi').setLevel(30)
    logging.getLogger('engine').setLevel(10)
    logging.getLogger('kaldi').setLevel(10)
else:
    # logging.basicConfig(level=20)
    from dragonfly.log import setup_log
    setup_log() 


file_map = { 
    "a" : 0,"b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7, 
    "alpha" : 0 , "bravo" : 1, "charlie" : 2, "delta" : 3, "echo" : 4, "foxtrot" : 5 , 
    "golf" : 6 , "hotel" : 7
}

rank_map = { 
    "one": 0, "two": 1, "three": 2, "four": 3, "five": 4, "six": 5, "seven": 6, "eight": 7,
}


verb_map = {
    "move" : "move", "capture" : "capture"
}

prep_map = {
    "to" : "to", "on" : "on", "with" : "with", "in":"in", "from" : "from"
} 

piece = {
    "pawn": chess.PAWN, "knight": chess.KNIGHT, "bishop": chess.BISHOP, "rook": chess.ROOK, "queen": chess.QUEEN, "king": chess.KING
}

prm_piece = {
    "knight": chess.KNIGHT, "bishop": chess.BISHOP, "rook": chess.ROOK, "queen": chess.QUEEN
}

special_direction = {
    "queen side" : "queenside", "king side" : "kingside", "long side" : "queenside", "short side" : "kingside", "long" : "queenside", "short" : "kingside"
}


# funzione che prende in input il comando e crea una stringa che rappresenta il comando

#def piece_symbol(piece_type: PieceType) -> str:
#    return typing.cast(str, PIECE_SYMBOLS[piece_type])

def command2string(command):
    s = ""
    s+= "verb: " + command.verb if command.verb else ""
    s+= " src_piece: " + chess.piece_symbol(command.src_piece) if command.src_piece else ""
    s+= " src_square: " + chess.square_name(command.src_square) if command.src_square else ""
    s+= " tgt_piece: " + chess.piece_symbol(command.tgt_piece) if command.tgt_piece else  ""
    s+= " tgt_square: " + chess.square_name(command.tgt_square) if command.tgt_square else ""
    s+= " prm_piece: " + chess.piece_symbol(command.prm_piece) if command.prm_piece else ""
    return s 


class Command(NamedTuple):
    verb : str
    src_piece : chess.PieceType
    src_square : chess.Square
    tgt_piece : chess.PieceType
    tgt_square : chess.Square
    prm_piece : chess.PieceType
    

# Modelling Move 
class MoveRule(CompoundRule):
    
    def __init__(self, manager):
        
        super().__init__()
        self.manager = manager
    
    spec = "Move ([<src_piece> [<prep> <src_square>][<prep> <tgt_square>]] | [ <src_square> [<prep> <tgt_square>]]) [and promote to <prm_piece>] "
    extras = [
        Choice("prep", prep_map),
        Choice("src_piece", piece),
        Choice("tgt_piece", piece),
        Choice("prm_piece", prm_piece),
        Compound(name = "src_square",spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"])),
        Compound(name = "tgt_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"])),
        
    ]

    def _process_recognition(self, node, extras):
        verb = "Move"
        prep = extras.get("prep", None)
        src_piece = extras.get("src_piece", None)
        tgt_piece = extras.get("tgt_piece", None)
        prm_piece = extras.get("prm_piece", None) 
        src_square = chess.square(*extras["src_square"]) if "src_square" in extras else None 
        tgt_square = chess.square(*extras["tgt_square"]) if "tgt_square" in extras else None
        
        #print(f"Verb: {verb}")
        #print(f"Preposition: {prep}")
        #print(f"Source Piece: {src_piece}")
        #print(f"Source Square: {src_square}")
        #print(f"Target Piece: {tgt_piece}")
        #print(f"Target Square: {tgt_square}")
        #print(f"Promotion Piece: {prm_piece}")
        
        result = Command(verb, src_piece, src_square, tgt_piece, tgt_square, prm_piece)
        
        #print(f"Result: {command2string(result)}")
        self.manager.push_command(result)  
        

# Modelling Capture 
class CaptureRule(CompoundRule):  
    
    def __init__(self, manager):
        
        super().__init__()
        self.manager = manager
    
    
    spec = "Capture (<tgt_piece> [<prep> <tgt_square>] | <tgt_square>) [with (<src_piece> | <src_square>)] [and promote to <prm_piece>]"
    
    extras = [
        Choice("prep",prep_map),
        Choice("src_piece", piece),
        Choice("tgt_piece", piece),
        Choice("prm_piece", prm_piece),
        Compound( name = "src_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"])),
        Compound( name = "tgt_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"]))
    ]

    def _process_recognition(self, node, extras):
        verb = "Capture"
        prep = extras.get("prep", None)
        src_piece = extras.get("src_piece", None)
        tgt_piece = extras.get("tgt_piece", None)
        prm_piece = extras.get("prm_piece", None) 
        src_square = chess.square(*extras["src_square"]) if "src_square" in extras else None 
        tgt_square = chess.square(*extras["tgt_square"]) if "tgt_square" in extras else None
        
        #print(f"Verb: {verb}")
        #print(f"Prep: {prep}")
        #print(f"Source Piece: {src_piece}")
        #print(f"Source Square: {src_square}")
        #print(f"Target Piece: {tgt_piece}")
        #print(f"Target Square: {tgt_square}") 
        #print(f"Promotion Piece: {prm_piece}")
        
        result = Command(verb, src_piece, src_square, tgt_piece, tgt_square, prm_piece)
        self.manager.push_command(result) 
        
     
# Modelling Promotion  
class PromoteRule(CompoundRule):
    
    def __init__(self, manager):
        
        super().__init__()
        self.manager = manager
    
    
    spec = "Promote [(<src_piece> | <src_square>)] to <prm_piece>"
    extras = [
        Choice("prep", prep_map), 
        Choice("src_piece", piece),
        Choice("prm_piece", prm_piece),
        Compound( name = "src_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"]))
    ]

    def _process_recognition(self, node, extras):
        verb = "Promote"
        prep = extras.get("prep", None) 
        src_piece = extras.get("src_piece", None)
        prm_piece = extras.get("prm_piece", None)
        src_square = chess.square(*extras["src_square"]) if "src_square" in extras else None 
        
         
        #print(f"Verb: {verb}")
        #print(f"Source Piece: {src_piece}")
        #print(f"Source Square: {src_square}")
        #print(f"Promotion Piece: {prm_piece}")
        
        result = Command(verb, src_piece, src_square, None, None, prm_piece)
        self.manager.push_command(result) 

# Modelling Castle
class CastleRule(CompoundRule):
    
    def __init__(self, manager):
        
        super().__init__()
        self.manager = manager
    
    
    spec = "(castle <special_direction> | <special_direction> castle)"
    extras = [
        Choice("special_direction", special_direction),
        #Compound(name = "tgt_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"]))
    ]
    
    def _process_recognition(self, node, extras):
        verb = "Castle"
        special_direction = extras.get("special_direction", None)
        file = 6 if special_direction is "kingside" else 2 
        #print(f"Verb: {verb}")
        #print(f"Special Direction: {special_direction}")
        result = Command(verb, None, None, None, file, None)
        self.manager.push_command(result) 


        
# Modelling Rules that start with Piece
class PieceRule(CompoundRule): 
    
    def __init__(self, manager):
        
        super().__init__()
        self.manager = manager
    
    
    
    
    spec = "<src_piece> (in <src_square> <verb> [<prep>] ( <tgt_square> | <tgt_piece> [in <tgt_square>] ) | <verb> [<prep> <src_square>]( [<prep>] <tgt_square> | <tgt_piece>  [in <tgt_square>])) [and promote to <prm_piece>]"
    
    extras = [
        Choice("verb", verb_map),
        Choice("prep",prep_map),
        Choice("src_piece", piece),
        Choice("tgt_piece", piece),
        Choice("prm_piece", prm_piece),
        Compound( name = "src_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"])),
        Compound( name = "tgt_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"]))
    ]

    def _process_recognition(self, node, extras):
        
        verb = extras.get("verb", None)
        prep = extras.get("prep", None)
        src_piece = extras.get("src_piece", None)
        tgt_piece = extras.get("tgt_piece", None)
        prm_piece = extras.get("prm_piece", None)
        src_square = chess.square(*extras["src_square"]) if "src_square" in extras else None 
        tgt_square = chess.square(*extras["tgt_square"]) if "tgt_square" in extras else None
        
        #print(f"Verb: {verb}")
        #print(f"Prep: {prep}")
        #print(f"Source Piece: {src_piece}")
        #print(f"Source Square: {src_square}")
        #print(f"Target Piece: {tgt_piece}")
        #print(f"Target Square: {tgt_square}")
        #print(f"Promotion Piece: {prm_piece}") 
        
        result = Command(verb, src_piece, src_square, tgt_piece, tgt_square, prm_piece)
        self.manager.push_command(result) 

# Modelling Example Dictation Rule 
class ExampleDictationRule(dragonfly.MappingRule):
    mapping = {
        "dictate <text>": dragonfly.Function(lambda text: print("I heard %r!" % str(text))),
    }
    extras = [ dragonfly.Dictation("text") ] 








        
