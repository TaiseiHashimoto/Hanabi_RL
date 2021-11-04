from typing import List
from hanabi.objects import (
    FailureTokensOnField,
    HintTokensOnField,
    Deck,
    Card,
    Color,
    Rank,
)
from hanabi.hanabi_field import HanabiField
from hanabi.players import HumanPlayer, RandomPlayer
from .actions import Action, PlayCard, GetHintToken, GiveColorHint, GiveRankHint


class GameField:
    def __init__(self, num_players: int):

        self.deck = Deck()
        self.players = [HumanPlayer(index) for index in range(num_players)]
        self.failure_tokens = FailureTokensOnField()
        self.hint_tokens = HintTokensOnField(
            initial_num_hint_tokens=8, max_num_hint_tokens=8
        )
        self.hanabi_field = HanabiField()
        self.discard_pile: List[Card] = []
        self.turn = 0

        self.turn_since_deck_is_empty = 0

    def distribute_cards(self, num_initial_cards: int = 5):
        for _ in range(num_initial_cards):
            for player in self.players:
                player.draw_card(self.deck)

    def get_valid_actions(self, player: Player) -> List[Action]:
        valid_actions = [PlayCard(card_index) for card_index in range(len(player.hand))]

        if self.hint_tokens.is_able_to_add_token() and len(player.hand) > 0:
            valid_actions += [
                GetHintToken(card_index) for card_index in range(len(player.hand))
            ]

        for other_player in self.players:
            if other_player == player:
                continue
            for color in list(Color):
                if other_player.has_color(color):
                    valid_actions.append(
                        GiveColorHint(player_index=other_player.index, color=color)
                    )
            for rank in list(Rank):
                if other_player.has_rank(rank):
                    valid_actions.append(
                        GiveRankHint(player_index=other_player.index, rank=rank)
                    )

        return valid_actions

    def is_terminal(self) -> bool:
        if self.failure_tokens.is_failed():
            return True

        if self.hanabi_field.is_completed():
            return True

        if self.turn_since_deck_is_empty == len(self.players):
            return True

        return False

    def start_game(self):
        self.distribute_cards()

        print(self)

        max_num_rounds = (len(self.deck) + len(self.hint_tokens) + 1) // len(
            self.players
        ) + 2

        for current_round in range(max_num_rounds):
            for current_player_id, player in enumerate(self.players):

                valid_actions = self.get_valid_actions(player)
                action = player.choose_action(valid_actions)

                if isinstance(action, PlayCard):
                    card = player.use_card(action.played_card_index)
                    if self.hanabi_field.is_able_to_add(card):
                        color_field_is_completed = self.hanabi_field.add_card(card)
                        if (
                            color_field_is_completed
                            and self.hint_tokens.is_able_to_add_token()
                        ):
                            self.hint_tokens.add_token()
                    else:
                        self.failure_tokens.add_token()
                        self.discard_pile.append(card)
                    player.draw_card(self.deck)

                elif isinstance(action, GetHintToken):
                    assert self.hint_tokens.is_able_to_add_token()
                    discarded_card = player.use_card(action.discard_card_index)
                    self.discard_pile.append(discarded_card)
                    self.hint_tokens.add_token()
                    player.draw_card(self.deck)
                elif isinstance(action, GiveColorHint):
                    assert action.player_index != current_player_id
                    assert self.hint_tokens.is_able_to_use_token()
                    self.hint_tokens.use_token()
                    self.players[action.player_index].get_color_hint(action.color)
                elif isinstance(action, GiveRankHint):
                    assert action.player_index != current_player_id
                    assert self.hint_tokens.is_able_to_use_token()
                    self.hint_tokens.use_token()
                    self.players[action.player_index].get_rank_hint(action.rank)
                else:
                    raise RuntimeError(f"Invalid action: {action}")

                self.turn += 1
                self.turn_since_deck_is_empty += int(self.deck.is_empty())

                print(self)

                if self.is_terminal():
                    return self.hanabi_field.get_score()

    def __str__(self):
        string = ""
        string += "==============================\n"
        string += f"Deck: {len(self.deck)}" + "\n"
        string += f"Hint Tokens: [" + "○" * len(self.hint_tokens) + "]\n"
        string += f"Failure Tokens: [" + "●" * len(self.failure_tokens) + "]\n"
        string += "\n"

        string += "Hanabi Field:" + "\n"
        string += str(self.hanabi_field) + "\n"

        string += "Hand: \n"
        for player in self.players:
            string += f"Player {player.index}: \n"
            string += str([str(c) for c in player.hand]) + "\n"
            string += "\n"
        string += "==============================\n"

        return string
