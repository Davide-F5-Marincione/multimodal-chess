import objects 
import chess 
import speech_rules
import dragonfly 
from threading import Thread 
from collections import deque 
from timeit import default_timer as timer
import audio 
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
        #current_time from main 
        # timestamp from push_command 
        
        legal_moves = self.board.board.legal_moves
        
        while len(self.commands) > 0:
            command, timestamp = self.commands.popleft() 
            #print(speech_rules.command2string(command))
    
            print("old_command", command)
            verb = command.verb 
            src_piece = command.src_piece 
            tgt_piece = command.tgt_piece 
            prm_piece = command.prm_piece 
            src_square = command.src_square
            tgt_square = command.tgt_square
            
            # General Checks 
            # 1st : (board_src_piece == src_piece)
            if src_piece is not None and src_square is not None: 
                print("1.1")
                board_src_piece = self.board.board.piece_at(src_square).piece_type
                if board_src_piece != src_piece:
                    #print("src_piece", src_piece)
                    #print("board_src_piece", board_src_piece)
                    #print("src_square", src_square) 
                    print("1.1 problem")
                    audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
                print("1.1 ok")       
            
            # 2nd : (board_tgt_piece == tgt_piece)         
            if tgt_piece is not None and tgt_square is not None:
                print("1.2")
                board_tgt_piece = self.board.board.piece_at(tgt_square).piece_type
                if board_tgt_piece != tgt_piece:
                    #print("board_tgt_piece", board_tgt_piece)
                    #print("tgt_piece", tgt_piece)
                    #print("tgt_square", tgt_square)
                    print("1.2")
                    audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
                print("1.2 ok")
            
            
            # Check if src_square and tgt_square, MOVE IS NOT LEGAL 
            # 1 
            if src_square is not None and tgt_square is not None:
                print("1")
                action = chess.Move(src_square, tgt_square)
                print("action 1", action)
                if action not in legal_moves:
                    #print("src_square", src_square)
                    #print("tgt_square", tgt_square)
                    print("1 problem")
                    audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
                print(" 1 ok ")

            # 2 
            elif tgt_square is not None and src_piece is None and src_square is None:
                print("2")
                action = [move for move in legal_moves if move.to_square == tgt_square]
                if len(action) == 1 : 
                    print("action 2", action)
                    print("2 ok") 
                    src_square = action[0].from_square 
                    src_piece = self.board.board.piece_at(src_square).piece_type
                    #print(f"Source square: {src_square}, Source piece: {src_piece}")
                else:
                    print("2 problem")
                    audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
            
            # 3 
            elif tgt_square is not None and src_piece is not None and src_square is None:
                print("3")
                action = [move for move in legal_moves if move.to_square == tgt_square and self.board.board.piece_at(move.from_square).piece_type == src_piece]
                if len(action) == 1:
                    print("action 3", action)
                    print("3 ok")
                    src_square = action[0].from_square
                else:
                    print("3 problem")
                    audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
            
            # 4 
            elif tgt_piece is not None and src_square is None and src_piece is None:
                print("4")
                # action = [move for move in legal_moves if self.board.board.piece_at(move.to_square).piece_type == tgt_piece]
                action = [move for move in legal_moves if self.board.board.piece_at(move.to_square) is not None and self.board.board.piece_at(move.to_square).piece_type == tgt_piece]
                print("action 4", action)
                if len(action) == 1:
                    #print("action 4", action) 
                    print("4 ok")
                    src_square = action[0].from_square
                    tgt_square = action[0].to_square 
                    src_piece = self.board.board.piece_at(src_square).piece_type
                    #print(f"Source square: {src_square}, Source piece: {src_piece}") 
                else: 
                    print("4 problem") 
                    audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
            
            # 5 
            elif tgt_piece is not None and src_piece is not None and src_square is None:
                print("5")
                #action = [move for move in legal_moves if self.board.board.piece_at(move.to_square).piece_type == tgt_piece and self.board.board.piece_at(move.from_square).piece_type == src_piece]
                action = [move for move in legal_moves if (self.board.board.piece_at(move.to_square) is not None and self.board.board.piece_at(move.to_square).piece_type == tgt_piece) and 
                (self.board.board.piece_at(move.from_square) is not None and self.board.board.piece_at(move.from_square).piece_type == src_piece)]
                print("action 5", action) 
                if len(action) == 1: 
                    #print("action 5", action)
                    print(" 5 ok")
                    src_square = action[0].from_square
                    tgt_square = action[0].to_square
                    #print(f"Source square: {src_square}")
                else:
                    print("5 problem")
                    audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
            
            # 6 
            elif tgt_piece is not None and src_square is not None:
                print("6")
                action = [move for move in legal_moves if self.board.board.piece_at(move.to_square).piece_type == tgt_piece and move.from_square == src_square]
                print("action 6", action)
                if len(action) == 1:
                    #print("action 6", action)
                    print("6 ok")
                    src_piece = self.board.board.piece_at(src_square).piece_type
                    tgt_square = action[0].to_square
                    #print(f"Source piece: {src_piece}")
                else: 
                    print("6 problem")
                    audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
            
            # "Capture" check       
            if verb == "capture" and self.board.board.piece_at(tgt_square) == None:
                audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
                print("Capture problem")
            print("safe from capture")
            
            
            ''' 
            # Promotion check 
            is_promotion = (src_piece == 1 and  ((src_square[1] == '8' and tgt_square[1] == '7' and prm_piece is not None) or 
                                                      (src_square[1] == '1' and tgt_square[1] == '2' and prm_piece is not None)))
            
            # here we need to check if it is a possible move : check not done yet 
            if not is_promotion and prm_piece is not None:
                audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0) 
                print("promotion problem")
            ''' 
            print("promotion free")
            
                
            command = speech_rules.Command(verb,src_piece,src_square,tgt_piece,tgt_square,prm_piece)
            #return command, legal[0] if len(legal) == 1 else None
            #print("type", type(command))
            print("command_after",command) 
            return command
        return None  

         
                
            
        
        