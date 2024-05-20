import objects 
import chess 
import speech_rules
import dragonfly 
from threading import Thread 
from collections import deque 
from timeit import default_timer as timer
import config as cfg 

class SpeechManager():
    def __init__(self, board : objects.Board):
        self.board = board 
        self.t = Thread(target=self.run, args=())
        self.t.daemon = True
        self.commands = deque() 
    
    def push_command(self,command):
        timestamp = int(timer() * 1000)     # Current Time Frame -> each time we execute a command, we get the time 
        self.commands.append((command, timestamp))

    def run(self):
        
        self.speech_engine = dragonfly.get_engine("kaldi",
            model_dir='kaldi_model',
            vad_padding_end_ms=300,
            audio_self_threaded = False)
        self.speech_engine.connect()
        grammar = dragonfly.Grammar(name="Chess Grammar")
        
        # Rules call disambiguator 
        move_rule = speech_rules.MoveRule(self)
        capture_rule = speech_rules.CaptureRule(self)
        promotion_rule = speech_rules.PromoteRule(self)
        piece_rule = speech_rules.PieceRule(self)
        castle_rule = speech_rules.CastleRule(self)
        square_rule = speech_rules.SquareRule(self)
        grammar.add_rule(move_rule)
        grammar.add_rule(capture_rule)
        grammar.add_rule(promotion_rule)
        grammar.add_rule(piece_rule)
        grammar.add_rule(castle_rule)
        grammar.add_rule(square_rule)
        #grammar.add_rule(ExampleDictationRule())
        grammar.load()
        self.speech_engine.do_recognition() 
    
    def start(self):
        self.t.start()
    
    def stop(self):
        self.t.join(0)
        
        
    def resolve_commands(self, curr_time):
        legal_moves = self.board.board.legal_moves
        some_command = False
        
        while len(self.commands) > 0:
            command, timestamp = self.commands.popleft() 

            # Check timeout of command
            if curr_time - timestamp > cfg.VOCAL_COMMANDS_TIMOUT:
                continue

            some_command = True
            
            # Extract command details
            verb = command.verb.lower()
            src_piece = command.src_piece 
            tgt_piece = command.tgt_piece 
            prm_piece = command.prm_piece 
            src_square = command.src_square
            tgt_square = command.tgt_square

            # Do special commands
            if verb == "castle":
                src_piece = chess.KING
                if self.board.board.turn == chess.WHITE:
                    src_square = chess.E1
                    if tgt_square == 6:
                        tgt_square = chess.G1
                    else:
                        tgt_square = chess.C1
                else:
                    src_square = chess.E8
                    if tgt_square == 6:
                        tgt_square = chess.G8
                    else:
                        tgt_square = chess.C8
            
            elif verb == "promote":
                return (None, None, prm_piece), some_command
            

            # Execute generator of legal moves
            moves = list(legal_moves)

            # Filter moves based on the given details
            if src_square is not None:
                moves = [move for move in moves if move.from_square == src_square]
            if tgt_square is not None:
                moves = [move for move in moves if move.to_square == tgt_square]
            if src_piece is not None:
                moves = [move for move in moves if self.board.board.piece_at(move.from_square) is not None and self.board.board.piece_at(move.from_square).piece_type == src_piece]
            if tgt_piece is not None:
                moves = [move for move in moves if self.board.board.piece_at(move.to_square) is not None and self.board.board.piece_at(move.to_square).piece_type == tgt_piece]
            if prm_piece is not None:
                moves = [move for move in moves if move.promotion is not None and move.promotion == prm_piece]

            # If a single move remains... that's it!
            if len(moves) == 1 or (len(moves) == 4 and all(move.promotion is not None for move in moves)):
                # Special case if capture.
                if verb != "capture" or self.board.board.piece_at(moves[0].to_square) is not None:
                    return (moves[0].from_square, moves[0].to_square, prm_piece), some_command

        return None, some_command