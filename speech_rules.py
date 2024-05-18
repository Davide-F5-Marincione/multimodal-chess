from __future__ import print_function
from dragonfly import (Grammar, RuleRef, CompoundRule, Choice, Optional, Compound)
import dragonfly 
import logging  

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
    "a": "a","b": "b","c": "c","d": "d","e": "e","f": "f", "g": "g", "h": "h", 
    "alpha" : "a", "bravo" : "b", "charlie" : "c", "delta" : "d", "echo" : "e", "foxtrot" : "f" , 
    "golf" : "g" , "hotel" : "h" 
}

rank_map = { 
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
    "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8"
}


verb_map = {
    "move" : "move", "capture" : "capture", "castle" : "castle"
}

prep_map = {
    "to" : "to", "on" : "on", "with" : "with", "in":"in", "from" : "from"
} 

source_piece = {
    "pawn": "pawn", "knight": "knight", "bishop": "bishop", "rook": "rook", "queen": "queen", "king": "king"
}

target_piece = {
    "pawn": "pawn", "knight": "knight", "bishop": "bishop", "rook": "rook", "queen": "queen", "king": "king"
}

prm_piece = {
    "pawn": "pawn", "knight": "knight", "bishop": "bishop", "rook": "rook", "queen": "queen", "king": "king"
}

# Modelling Move 
class MoveRule(CompoundRule):
    
    spec = "Move ([<src_piece> [<prep> <src_square>][<prep> <tgt_square>]] | [ <src_square> [<prep> <tgt_square>]]) [and promote to <prm_piece>] "
    extras = [
        Choice("prep", prep_map),
        Choice("src_piece", source_piece),
        Choice("tgt_piece", source_piece),
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
        src_square = extras.get("src_square", None)
        tgt_square = extras.get("tgt_square", None) 
        
        print(f"Verb: {verb}")
        print(f"Preposition: {prep}")
        print(f"Source Piece: {src_piece}")
        print(f"Source Square: {src_square}")
        print(f"Target Piece: {tgt_piece}")
        print(f"Target Square: {tgt_square}")
        print(f"Promotion Piece: {prm_piece}")

# Modelling Capture 
class CaptureRule(CompoundRule):  
    spec = "Capture (<tgt_piece> [<prep> <tgt_square>] | <tgt_square>) [with (<src_piece> | <src_square>)] [and promote to <prm_piece>]"
    
    extras = [
        Choice("prep",prep_map),
        Choice("src_piece", source_piece),
        Choice("tgt_piece", source_piece),
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
        src_square = extras.get("src_square", None)
        tgt_square = extras.get("tgt_square", None)
        print(f"Verb: {verb}")
        print(f"Prep: {prep}")
        print(f"Source Piece: {src_piece}")
        print(f"Source Square: {src_square}")
        print(f"Target Piece: {tgt_piece}")
        print(f"Target Square: {tgt_square}") 
        print(f"Promotion Piece: {prm_piece}")
        
     
# Modelling Promotion  
class PromoteRule(CompoundRule):
    
    spec = "Promote [(<src_piece> | <src_square>)] to <prm_piece>"
    extras = [
        Choice("prep", prep_map), 
        Choice("src_piece", source_piece),
        Choice("prm_piece", prm_piece),
        Compound( name = "src_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"]))
    ]

    def _process_recognition(self, node, extras):
        verb = "Promote"
        prep = extras.get("prep", None) 
        src_piece = extras.get("src_piece", None)
        prm_piece = extras.get("prm_piece", None)
        src_square = extras.get("src_square", None)
        print(f"Verb: {verb}")
        print(f"Source Piece: {src_piece}")
        print(f"Source Square: {src_square}")
        print(f"Promotion Piece: {prm_piece}")

# Modelling Castle
class CastleRule(CompoundRule):
    spec = "Castle <direction>"
    extras = [
        Choice("direction", {"King side": "King side", "Queen side": "Queen side"})
    ]

    def _process_recognition(self, node, extras):
        verb = "Castle"
        direction = extras.get("direction", None)
        print(f"Verb: {verb}")
        print(f"Direction: {direction}")
        #re in E1 (bianco) o IN E8 (nero)  -> in G 
        #queen in D1 (bianco) o in         -> in C 


# Modelling Rules that start with Piece
class PieceRule(CompoundRule): 
    spec = "<src_piece> (in <src_square> <verb> [<prep>] ( <tgt_square> | <tgt_piece> [in <tgt_square>] ) | <verb> [<prep> <src_square>]( [<prep>] <tgt_square> | <tgt_piece>  [in <tgt_square>])) [and promote to <prm_piece>]"
    
    extras = [
        Choice("verb", verb_map),
        Choice("prep",prep_map),
        Choice("src_piece", source_piece),
        Choice("tgt_piece", target_piece),
        Choice("prm_piece", prm_piece),
        Compound( name = "src_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"])),
        Compound( name = "tgt_square", spec = "<file> <rank>", extras = [ Choice("file", file_map), Choice("rank", rank_map)], value_func = lambda node, extras: (extras["file"], extras["rank"]))
    ]

    def _process_recognition(self, node, extras):
        verb = extras.get("verb", None)
        src_piece = extras.get("src_piece", None)
        tgt_piece = extras.get("tgt_piece", None)
        prm_piece = extras.get("prm_piece", None)
        src_square = extras.get("src_square", None)
        tgt_square = extras.get("tgt_square", None)
        prep = extras.get("prep", None)
        
        print(f"Verb: {verb}")
        print(f"Prep: {prep}")
        print(f"Source Piece: {src_piece}")
        print(f"Source Square: {src_square}")
        print(f"Target Piece: {tgt_piece}")
        print(f"Target Square: {tgt_square}")
        print(f"Promotion Piece: {prm_piece}") 


# Modelling Example Dictation Rule 
class ExampleDictationRule(dragonfly.MappingRule):
    mapping = {
        "dictate <text>": dragonfly.Function(lambda text: print("I heard %r!" % str(text))),
    }
    extras = [ dragonfly.Dictation("text") ] 
    

# Defining Engine 
engine = dragonfly.get_engine("kaldi",
    model_dir='kaldi_model',
    # tmp_dir='kaldi_tmp',  # default for temporary directory
    # vad_aggressiveness= 3,  # default aggressiveness of VAD
    vad_padding_end_ms=300,  # default ms of required silence surrounding VAD
    # input_device_index=None,  # set to an int to choose a non-default microphone
    # cloud_dictation=None,  # set to 'gcloud' to use cloud dictation
)

# Call connect() now that the engine configuration is set.
engine.connect()


# We may define a context in which the grammar is executed like 
#grammar_context = AppContext(executable="notepad")
#grammar = Grammar("notepad_example", context=grammar_context)

grammar = dragonfly.Grammar(name="Chess Grammar")
move_rule = MoveRule()
capture_rule = CaptureRule()
promotion_rule = PromoteRule()
piece_rule = PieceRule()
castle_rule = CastleRule()
grammar.add_rule(move_rule)
grammar.add_rule(capture_rule)
grammar.add_rule(promotion_rule)
grammar.add_rule(piece_rule)
grammar.add_rule(castle_rule)
grammar.add_rule(ExampleDictationRule())
grammar.load()

#print('Try saying: "I want to eat an apple" or "I want to eat a greasy hamburger" or "dictate this is just a test"')
print("Listening...")
engine.do_recognition()







    
