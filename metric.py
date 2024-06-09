import os
import json
import pandas as pd
import numpy as np


def process_recording(recording_path):
   
    with open(recording_path) as recording_file:
        data = json.load(recording_file)
        player_actions = pd.DataFrame(data["player"])
        #print("player_actions", player_actions)
        ai_moves = data["ai"]
        
        # Defininf Action_Start, Action_End and Action_Duration 
        player_actions['action_start'] = pd.to_datetime(player_actions['action_start'])
        player_actions['action_end'] = pd.to_datetime(player_actions['action_end'])
        player_actions['duration'] = (player_actions['action_end'] - player_actions['action_start']).dt.total_seconds()
        
        
        # Speech Actions Statistics 
        speech_actions = player_actions[player_actions['action_type'] == 'speech']
        #print("speech_actions", speech_actions)
        
        if not speech_actions.empty:
            length_speech_actions = len(speech_actions)  # just the length of the recorded timestamps
            total_utterances = speech_actions['utterances'].sum()   # it is the numer of expression said during a time interval  
            legal_speech_actions = sum(len(action) for action in speech_actions['moves'])
            illegal_speech_actions = total_utterances - legal_speech_actions
            average_speech_duration = speech_actions['duration'].mean()
            total_speech_duration = speech_actions['duration'].sum() / 60 
        else:
            length_speech_actions = 0
            total_utterances = 0
            legal_speech_actions = 0
            illegal_speech_actions = 0
            average_speech_duration = 0
            total_speech_duration = 0
        
        # Hand Actions Statistics 
        hand_actions = player_actions[player_actions['action_type'] == 'hand']
        length_hand_actions = len(hand_actions)   # just the length of the recorded timestamps
        total_hand_down_buttons = hand_actions['down_button'].sum()   # It is the total number of actions performed by the hand 
        legal_hand_actions = sum(len(action) for action in hand_actions['moves'])
        illegal_hand_actions = total_hand_down_buttons - legal_hand_actions
        total_hand_distance = hand_actions['action_dist'].sum()
        average_hand_duration = hand_actions['duration'].mean()
        total_hand_duration = hand_actions['duration'].sum() / 60
        total_hand_up_buttons = hand_actions['up_button'].sum()
        
        # Mouse Actions Statistics 
        mouse_actions =  player_actions[player_actions['action_type'] == 'mouse']
        length_mouse_actions = len(mouse_actions)   # just the length of the recorded timestamps 
        total_mouse_down_buttons = mouse_actions['down_button'].sum()   # It is the total number of actions performed by the mouse
        legal_mouse_actions = sum(len(action) for action in mouse_actions['moves'])
        illegal_mouse_actions = total_mouse_down_buttons - legal_mouse_actions
        total_mouse_distance = mouse_actions['action_dist'].sum()
        total_mouse_duration = mouse_actions['duration'].sum() / 60
        average_mouse_duration = mouse_actions['duration'].mean()
        total_mouse_up_buttons =  mouse_actions['up_button'].sum()
        
        
        # AI Actions Statistics 
        total_ai_moves = len(ai_moves)
        
        # I think these metrics don't have much sense, but they are global metrics 
        total_actions = total_utterances + total_hand_down_buttons + total_mouse_down_buttons
        total_legal_actions = legal_speech_actions + legal_hand_actions + legal_mouse_actions
        total_illegal_actions = total_actions - total_legal_actions
        
    
        return {
            "length_speech_actions": length_speech_actions,
            "total_utterances": total_utterances,
            "legal_speech_actions": legal_speech_actions,
            "illegal_speech_actions": illegal_speech_actions,
            "average_speech_duration": average_speech_duration,
            "total_speech_duration": total_speech_duration,
            "length_hand_actions" : length_hand_actions,
            "total_hand_down_buttons": total_hand_down_buttons,
            "legal_hand_actions": legal_hand_actions,
            "illegal_hand_actions": illegal_hand_actions,
            "total_hand_distance": total_hand_distance,
            "average_hand_duration": average_hand_duration,
            "total_hand_duration": total_hand_duration,
            "total_hand_up_buttons": total_hand_up_buttons,
            "length_mouse_actions" : length_mouse_actions,
            "total_mouse_down_buttons": total_mouse_down_buttons,
            "legal_mouse_actions": legal_mouse_actions,
            "illegal_mouse_actions": illegal_mouse_actions,
            "total_mouse_distance" : total_mouse_distance,
            "total_mouse_duration" : total_mouse_duration,
            "average_mouse_duration" : average_mouse_duration,
            "total_mouse_up_buttons" : total_mouse_up_buttons,
            "total_ai_moves": total_ai_moves,
            "total_actions": total_actions,
            "total_legal_actions": total_legal_actions,
            "total_illegal_actions": total_illegal_actions
        }

def standardize_recording_name(filename):
    # Extracting name up to first _ 
    base_name = filename.split("_")[0]
    return base_name


directory = 'recordings/'
 
all_stats = {}

for filename in os.listdir(directory):
    if filename.endswith(".json"):
        recording_path = os.path.join(directory, filename)
        recording_stats = process_recording(recording_path)
        standardized_name = standardize_recording_name(filename)
        
        if standardized_name not in all_stats:
            all_stats[standardized_name] = recording_stats
        else:
            for key in all_stats[standardized_name]:
                #print(key , (type(all_stats[standardized_name][key])))
                if not key.startswith("average_"):
                    all_stats[standardized_name][key] += recording_stats[key]
                elif key.startswith("average_"):
                    continue
        
        
            # Recomputing averages after summing
            all_stats[standardized_name]['average_speech_duration'] = all_stats[standardized_name]['total_speech_duration'] / all_stats[standardized_name]['length_speech_actions'] if all_stats[standardized_name]['length_speech_actions'] > 0 else 0
            all_stats[standardized_name]['average_hand_duration'] = all_stats[standardized_name]['total_hand_duration'] / all_stats[standardized_name]['length_hand_actions'] if all_stats[standardized_name]['length_hand_actions'] > 0 else 0
            all_stats[standardized_name]['average_mouse_duration'] = all_stats[standardized_name]['total_mouse_duration'] / all_stats[standardized_name]['length_mouse_actions'] if all_stats[standardized_name]['length_mouse_actions'] > 0 else 0


df = pd.DataFrame.from_dict(all_stats, orient='index')

df.index.name = 'recording'

df.reset_index(inplace=True)

#df = df.transpose()

#print(df)

