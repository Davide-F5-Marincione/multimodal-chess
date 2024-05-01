from __future__ import print_function
import logging, os

import dragonfly

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


# VERB SRC_PIECE TGT_SQUARE
# VERB SRC_PIECE SRC_SQUARE TGT_SQUARE
# SRC_PIECE SRC_SQUARE VERB TGT_SQUARE

# Move Queen to H7
# Move Queen on H8 to H7
# Queen on H8 move to H7


# SRC_PIECE VERB TGT_SQUARE
# SRC_PIECE VERB TGT_PIECE
# SRC_PIECE SRC_SQUARE VERB TGT_SQUARE
# SRC_PIECE SRC_SQUARE VERB TGT_PIECE TGT_SQUARE
# VERB TGT_PIECE TGT_SQUARE SRC_PIECE

# Queen capture E4
# Queen capture Bishop
# Queen on H8 capture E4
# Queen on H8 capture Bishop on E4
# Capture Bishop on E4 with Queen


# VERB TGT_PIECE
# Capture bishop


# VERB SRC_PIECE PRM_PIECE
# VERB SRC_SQUARE TGT_SQUARE VERB PRM_PIECE

# Promote Pawn to Queen
# Move E7 to E8 and promote to Queen

# SRC_PIECE VERB TGT_PIECE VERB PRM_PIECE
# Pawn capture Knight and promote to Queen

# VERB PRM_PIECE
# Promote to Queen

# When PIECE and SQUARE are together, the order is PIECE SQUARE
# There must be a VERB in the command
# VERBs either come at the start or after the first PIECE/SQUARE
# VERBs must always have a target (not necessarily a source)
# When promotion is given with another command, it comes at the end of the sentence.
# Promotion always needs a PRM_PIECE



class ExampleCustomRule(dragonfly.CompoundRule):

    spec = ""
    extras = [
        dragonfly.Choice(
            "food", {"(an | a juicy) apple": "good", "a [greasy] hamburger": "bad"}
        )
    ]

    def _process_recognition(self, node, extras):
        good_or_bad = extras["food"]
        print("That is a %s idea!" % good_or_bad)


# Load engine before instantiating rules/grammars!
# Set any configuration options here as keyword arguments.
engine = dragonfly.get_engine("kaldi",
    model_dir='kaldi_model',
    # tmp_dir='kaldi_tmp',  # default for temporary directory
    # vad_aggressiveness=3,  # default aggressiveness of VAD
    # vad_padding_ms=300,  # default ms of required silence surrounding VAD
    # input_device_index=None,  # set to an int to choose a non-default microphone
    # cloud_dictation=None,  # set to 'gcloud' to use cloud dictation
)
# Call connect() now that the engine configuration is set.
engine.connect()

grammar = dragonfly.Grammar(name="mygrammar")
rule = ExampleCustomRule()
grammar.add_rule(rule)
grammar.load()

engine.do_recognition()