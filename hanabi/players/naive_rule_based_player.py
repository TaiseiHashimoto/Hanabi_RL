from typing import List, Tuple
import random

from .player import Player, PlayerObservation
from hanabi.objects import Card
from hanabi.actions import Action, GetHintToken, PlayCard, GiveColorHint


def find_playable_card_for_other(observation: PlayerObservation) -> Tuple[int, Card]:
    num_players = len(observation.other_player_hands) + 1
    playable_cards = [Card(color, rank.next_rank) for color, rank in observation.tower_ranks.items()]
    for other_player_id, hands in enumerate(observation.other_player_hands, start=observation.current_player_id + 1):
        other_player_id = other_player_id % num_players
        for playable_card in playable_cards:
            if playable_card in hands:
                return other_player_id, playable_card
    return None, None


class NaiveRuleBasedPlayer(Player):
    def choose_action(self, valid_actions: List[Action], observation: PlayerObservation) -> Action:
        # play a card following hints
        for hand_idx, hint in enumerate(observation.current_player_hints):
            if hint.color is not None and PlayCard(hand_idx) in valid_actions:
                return PlayCard(hand_idx)

        # tell other people playable card
        playable_player_id, playable_card = find_playable_card_for_other(observation)
        # print("playable", playable_card_for_other)
        if playable_player_id is not None:
            desirable_action = GiveColorHint(player_index=playable_player_id, color=playable_card.color)
            if desirable_action in valid_actions:
                return desirable_action

        # can I earn a hint token?
        for action in valid_actions:
            if isinstance(action, GetHintToken):
                return action

        # randomly play a card ¯\_(ツ)_/¯
        return random.choice(valid_actions)
