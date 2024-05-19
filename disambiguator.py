import objects 
import chess 
import speech_rules
import dragonfly 
from threading import Thread 


class Disambiguator:
    def __init__(self, board : objects.Board):
        self.board = board 
    
        self.t = Thread(target=self.run, args=())
        self.t.daemon = True

    def run(self):
        
        self.speech_engine = dragonfly.get_engine("kaldi",
            model_dir='kaldi_model',
            vad_padding_end_ms=300,
            audio_self_threaded = False)
        self.speech_engine.connect()
        grammar = dragonfly.Grammar(name="Chess Grammar")
        move_rule = speech_rules.MoveRule(self)
        capture_rule = speech_rules.CaptureRule(self)
        promotion_rule = speech_rules.PromoteRule(self)
        piece_rule = speech_rules.PieceRule(self)
        castle_rule = speech_rules.CastleRule(self)
        grammar.add_rule(move_rule)
        grammar.add_rule(capture_rule)
        grammar.add_rule(promotion_rule)
        grammar.add_rule(piece_rule)
        grammar.add_rule(castle_rule)
        #grammar.add_rule(ExampleDictationRule())
        grammar.load()
        self.speech_engine.do_recognition() 
    
    def start(self):
        self.t.start()
    
    def stop(self):
    
        self.t.join(0)
        
        
    def disambiguate(self, command:speech_rules.Command):

        legal_moves = self.board.board.legal_moves 
        # tutto il resto 
        
        print(speech_rules.command2string(command)) 
        
        