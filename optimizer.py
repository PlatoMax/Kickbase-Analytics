import pulp
from pulp import PULP_CBC_CMD


def run_optimizer(market_players, squad_players, budget, predictions):
        # Umwandeln da ursprüngliches Format Liste von Dictionaries war
        market_players = {p["player_id"]: {**p, "points": predictions.get(p["player_id"],0.0)} for p in market_players}
        squad_players = {p["player_id"]: {**p, "points": predictions.get(p["player_id"],0.0)} for p in squad_players}

        prob = pulp.LpProblem("Kickbase_Optimizer", pulp.LpMaximize)

        buy = pulp.LpVariable.dicts("Buy", market_players.keys(), cat="Binary")
        keep = pulp.LpVariable.dicts("Keep", squad_players.keys(), cat="Binary")
        sell = pulp.LpVariable.dicts("Sell", squad_players.keys(), cat="Binary")

        prob += pulp.lpSum([market_players[p]["points"] * buy[p] for p in market_players]) + \
                pulp.lpSum([squad_players[p]["points"] * keep[p] for p in squad_players])

        # Budget
        prob += pulp.lpSum([market_players[p]["player_price"] * buy[p] for p in market_players]) - \
                pulp.lpSum([squad_players[p]["player_price"] * sell[p] for p in squad_players]) <= budget

        for s in squad_players:
                prob += keep[s] + sell[s] == 1

        # max 1 Torwart
        gk_sum = pulp.lpSum([buy[p] for p in market_players if market_players[p]["player_pos"] == 1]) + \
                pulp.lpSum([keep[p] for p in squad_players if squad_players[p]["player_pos"] == 1])
        prob += gk_sum == 1

        # Abwehr 3 - 5
        def_sum = pulp.lpSum([buy[p] for p in market_players if market_players[p]["player_pos"] == 2]) + \
                pulp.lpSum([keep[p] for p in squad_players if squad_players[p]["player_pos"] == 2])
        prob += def_sum >= 3
        prob += def_sum <= 5

        # Mittelfeld 2 - 6
        mf_sum = pulp.lpSum([buy[p] for p in market_players if market_players[p]["player_pos"] == 3]) + \
                pulp.lpSum([keep[p] for p in squad_players if squad_players[p]["player_pos"] == 3])
        prob += mf_sum >= 2
        prob += mf_sum <= 6

        # Angriff 1 - 4
        st_sum = pulp.lpSum([buy[p] for p in market_players if market_players[p]["player_pos"] == 4]) + \
                pulp.lpSum([keep[p] for p in squad_players if squad_players[p]["player_pos"] == 4])
        prob += st_sum >= 1
        prob += st_sum <= 4

        # Kadergröße gesamt == 11
        new_squad_sum = pulp.lpSum([buy[p] for p in market_players]) + \
                pulp.lpSum([keep[p] for p in squad_players])
        prob += new_squad_sum == 11

        prob.solve(PULP_CBC_CMD(msg=False))

        
        status = pulp.LpStatus[prob.status]
        hold = [squad_players[player] for player in squad_players if keep[player].varValue == 1.0]
        buy = [market_players[player] for player in market_players if buy[player].varValue == 1.0]
        sell = [squad_players[player] for player in squad_players if sell[player].varValue == 1.0]

        return {
            "status": status,
            "buy": buy,
            "sell": sell,
            "hold": hold
        }
       

            