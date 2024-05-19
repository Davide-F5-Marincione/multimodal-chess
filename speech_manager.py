import objects 
import chess 
import speech_rules
import dragonfly 
from threading import Thread 
from collections import deque 
from timeit import default_timer as timer


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
        
        
    def resolve_commands(self, curr_time):
        #current_time from main 
        # timestamp from push_command 
        
        legal_moves = self.board.board.legal_moves 
        
        while len(self.commands) > 0:
            command, timestamp = self.commands.popleft() 
            #print(speech_rules.command2string(command))
            
            verb = command.verb 
            src_piece = command.src_piece 
            tgt_piece = command.tgt_piece 
            prm_piece = command.prm_piece 
            src_square = command.src_square
            tgt_square = command.tgt_square
            
            # General Checks 
            # 1st : (board_src_piece == src_piece)
            if src_piece is not None and src_square is not None: 
                board_src_piece = self.board.board.piece_at(src_square)
                if board_src_piece != src_piece: 
                    print("src_piece not at src_square ")
            
            # 2nd : (board_tgt_piece == tgt_piece)         
            if tgt_square is not None and tgt_square is not None:
                    board_tgt_piece = self.board.board.piece_at(tgt_square) 
                    if board_tgt_piece != tgt_piece:
                        print("src_piece not at src_square and tgt_piece not at tgt_square")
            
            
            # Process command as it is 
            if src_square is not None and tgt_square is not None:
                print("hey")
                
                
             
            
            
            
            
            
             
            
                    
                
                ''' 
                    # 2nd check : src_square in legal_moves 
                    for move in legal_moves:
                        if move.from_square == src_square and move.to_square == tgt_square:
                            # 3rd check : prm_piece in prm_square 
                            if prm_piece is not None:
                                prm_square = chess.square(chess.file_index(tgt_square),chess.rank_index(tgt_square))
                                board_prm_piece = self.board.board.piece_at(prm_square)
                                if board_prm_piece == prm_piece:
                                    return command 
                            else:
                                return command
                ''' 
            
            
        
        