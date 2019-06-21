from enum import Enum
from os import makedirs
from os import system
from sys import exit

import functionUtils as futils
import matplotlib.pyplot as plt
import message_properties as msg
import networkx as nx
import numpy as np
import pandas as pd

PATH_ACTIONS_DATASET = 'datasets/france1819goals.xlsx'
PATH_PLAYERS_DATASET = 'datasets/stats indiv.xlsx'
PATH_GAMES_DATASET = 'datasets/france1819roster.xlsx'
PATH_CONFIG = 'batch_config.txt'
SITUATIONS = ['ES', 'PP']
ONGLET_NODES_ES = pd.DataFrame()
ONGLET_NODES_PP = pd.DataFrame()
ONGLET_EDGES_ES = pd.DataFrame()
ONGLET_EDGES_PP = pd.DataFrame()


class MagnusTeams(Enum):
    ROU = 'Rouen'
    GRE = 'Grenoble'
    BOR = 'Bordeaux'
    CHM = 'Chamonix'
    ANG = 'Angers'
    GAP = 'Gap'
    NIC = 'Nice'
    MUL = 'Mulhouse'
    HOR = 'Anglet'
    LYO = 'Lyon'
    STR = 'Strasbourg'
    AMI = 'Amiens'


def hockey_team_network_analysis(team, magnus_data, strenghtState):
    print(MagnusTeams(team).value, end="")

    magnus_data_by_team = magnus_data.loc[magnus_data['scoringTeam.1'] == MagnusTeams(team).value].reset_index(
        drop=True)

    # work only with 5v5 strength state
    if strenghtState == 'ES':
        data_for_situation = magnus_data_by_team[magnus_data_by_team.strenghtState == '5v5'].reset_index(drop=True)
    elif strenghtState == 'PP':
        data_for_home_situation = magnus_data_by_team[magnus_data_by_team.homeTeam == team]
        data_for_home_situation = data_for_home_situation[data_for_home_situation['strenghtState'].isin(['5v4', '5v3', '6v5', '6v4', '4v3'])]
        data_for_away_situation = magnus_data_by_team[magnus_data_by_team.awayTeam == team]
        data_for_away_situation = data_for_away_situation[data_for_away_situation['strenghtState'].isin(['4v5', '3v5', '5v6', '4v6', '3v4'])]
        data_for_situation = pd.concat([data_for_home_situation, data_for_away_situation]).reset_index(drop=True)

    print('.', end="")

    nodes, edges = hockey_data_manipulation(data_for_situation, team)

    network_analysis(nodes, edges, team, strenghtState)


def string_split(string):
    return str.capitalize(string.split(',').get(0))


def hockey_data_manipulation(data, team):
    # arrange dataFrame to capture only datas of interest for the network's edges
    edges_data = data[["scoringTeam.1", "G", "A1"]]
    edges_data.columns = ['nameTeam', 'scorer', 'firstAssist']

    # arrange dataFrame to capture only datas of interest for the network's nodes
    nodes_data = pd.DataFrame([map(int, pd.unique(data[['G', 'A1']].values.ravel('K'))[
        ~np.isnan(pd.unique(data[['G', 'A1']].values.ravel('K')))])]).T
    nodes_data.columns = ['idPlayer']

    nodes_data['namePlayer'] = None
    nodes_data['nameTeam'] = None
    nodes_data['seasonScore'] = 0

    for i in nodes_data['idPlayer']:
        try:
            index = list(data['G']).index(i)
            column = 'G_fullName'
        except ValueError:
            try:
                index = list(data['A1']).index(i)
                column = 'A1_fullName'
            except ValueError:
                index = Nonedata
                column = None
        if index is not None and column is not None:
            nodes_data.loc[list(nodes_data['idPlayer']).index(i), 'namePlayer'] = data.loc[index, column]
            nodes_data.loc[list(nodes_data['idPlayer']).index(i), 'nameTeam'] = data.loc[index, 'scoringTeam.1']

    for i in range(len(edges_data)):
        nodes_data.loc[nodes_data['idPlayer'] == edges_data.iloc[i].scorer, 'seasonScore'] += 1
        nodes_data.loc[nodes_data['idPlayer'] == edges_data.iloc[i].firstAssist, 'seasonScore'] += 1

    nodes_data = nodes_data.sort_values(by=['nameTeam']).reset_index(drop=True)

    print('.', end="")

    # build nodes from nodes_data
    # ATTENTION : NODELABEL is choosable. (player name or score)
    nodes = [(nodes_data.idPlayer[i],
              {'playerName': nodes_data.namePlayer[i].split(',')[0], 'playerFirstName': nodes_data.namePlayer[i].split(',')[1][1:], 'nodeLabel': str(nodes_data.seasonScore[i])}) for i
             in range(len(nodes_data)) if nodes_data.nameTeam[i] == team]
    nodes.append((1, {'playerName': 'Goal', 'playerFirstName': '', 'nodeLabel': ''}))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DIGRAPH - WEIGHTED EDGES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    digraph_edges = []

    # build edges from edges_data
    # logic : FROM x1.id TO x2.id
    for i in range(len(edges_data)):
        if [int(edges_data.loc[i, 'scorer']), 1] in [dic.get('edge') for dic in digraph_edges
                                                     if dic.get('edge') == [int(edges_data.loc[i, 'scorer']), 1]]:
            digraph_edges[futils.find_dictvalue_in_list(digraph_edges, 'edge',
                                                        [int(edges_data.loc[i, 'scorer']), 1])]['weight'] += 1
        else:
            digraph_edges.append({'edge': [int(edges_data.loc[i, 'scorer']), 1], 'weight': 1})
        if not np.isnan(edges_data.loc[i, 'firstAssist']):
            if [int(edges_data.loc[i, 'firstAssist']), int(edges_data.loc[i, 'scorer'])] in [dic.get('edge') for dic in digraph_edges if dic.get('edge') == [int(edges_data.loc[i, 'firstAssist']), int(edges_data.loc[i, 'scorer'])]]:
                digraph_edges[futils.find_dictvalue_in_list(digraph_edges, 'edge',
                                                            [int(edges_data.loc[i, 'firstAssist']),
                                                             int(edges_data.loc[i, 'scorer'])])]['weight'] += 1
            else:
                digraph_edges.append({'edge': [int(edges_data.loc[i, 'firstAssist']),
                                               int(edges_data.loc[i, 'scorer'])], 'weight': 1})

    digraph_edges = [tuple(dic['edge']) + tuple([dic['weight']]) for dic in digraph_edges]

    print('.', end="")

    return nodes, digraph_edges


def fair_betweenness(node, team, strenghtState):

    player_data = pd.read_excel(PATH_GAMES_DATASET, sheet_name='Sheet1')
    player_data = player_data[player_data['id'] == node[0]]

    magnus_data = pd.read_excel(PATH_ACTIONS_DATASET, sheet_name='Data')

    magnus_data_by_team = magnus_data.loc[magnus_data['scoringTeam.1'] == MagnusTeams.__getattr__(team).value].reset_index(
        drop=True)

    # work only with 5v5 strength state
    if strenghtState == 'ES':
        data_for_situation = magnus_data_by_team[magnus_data_by_team.strenghtState == '5v5'].reset_index(drop=True)
    elif strenghtState == 'PP':
        data_for_home_situation = magnus_data_by_team[magnus_data_by_team.homeTeam == MagnusTeams.__getattr__(team).value]
        data_for_home_situation = data_for_home_situation[
            data_for_home_situation['strenghtState'].isin(['5v4', '5v3', '6v5', '6v4', '4v3'])]
        data_for_away_situation = magnus_data_by_team[magnus_data_by_team.awayTeam == MagnusTeams.__getattr__(team).value]
        data_for_away_situation = data_for_away_situation[
            data_for_away_situation['strenghtState'].isin(['4v5', '3v5', '5v6', '4v6', '3v4'])]
        data_for_situation = pd.concat([data_for_home_situation, data_for_away_situation]).reset_index(drop=True)

    fair_datas = pd.DataFrame()
    for game_id in list(player_data['gameid']):
        game_data = data_for_situation[data_for_situation['gameid'] == game_id]
        fair_datas = pd.concat([fair_datas, game_data])

    nodes, edges = hockey_data_manipulation(fair_datas.reset_index(drop=True), MagnusTeams.__getattr__(team).value)

    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_weighted_edges_from(edges)

    weighted_nodes = nx.betweenness_centrality(G, normalized=False, weight='weight')

    return weighted_nodes[node[0]]


def network_analysis(nodes, edges, team, strenghtState):
    H = nx.DiGraph()
    H.add_nodes_from(nodes)
    H.add_weighted_edges_from(edges)

    weighted_nodes = nx.betweenness_centrality(H, normalized=False, weight='weight')

    players_data = pd.read_excel(PATH_PLAYERS_DATASET, sheet_name='Final')

    for element in MagnusTeams:
        if team == element.value:
            team_acronym = element.name
            break

    players_data = players_data[players_data['Equipe'] == team_acronym]
    for node in nodes:
        if node[1].get('playerName') != 'Goal':
            player = players_data.loc[players_data['Joueur'] == str.capitalize(node[1].get('playerName'))+', '+str.capitalize(node[1].get('playerFirstName'))]
            if not player.empty:
                if players_data.MJ.max() != int(player['MJ']):
                    weighted_nodes[node[0]] = fair_betweenness(node, team_acronym, strenghtState)

    for value in weighted_nodes:
        weighted_nodes[value] *= 1 / ((len(weighted_nodes) - 1)*(len(weighted_nodes) - 2))

    weights = 10000 * pd.Series(list(weighted_nodes.values()))


    goal_fixed_positions = {1: (0, 0)}  # dict with two of the positions set
    goal_fixed_nodes = goal_fixed_positions.keys()
    pos = nx.spring_layout(H, pos=goal_fixed_positions, fixed=goal_fixed_nodes)

    plt.figure(1, figsize=(20, 15))
    plt.plot()
    nx.draw_networkx(H, node_color=range(len(nodes)), font_size=10, pos=pos,
                     node_size=weights, cmap=plt.cm.Reds,
                     labels={player[0]: player[1].get('nodeLabel') for player in nodes}, with_labels=True)

    for i in pos.keys():
        x, y = pos[i]
        plt.text(x, y + 0.04, s=''.join([player[1].get('playerName') for player in nodes if player[0] == i]),
                 bbox=dict(facecolor='red', alpha=0.5), horizontalalignment='center')

    plt.axis('off')
    plt.title(team + " " + strenghtState + " network")

    makedirs("exports", exist_ok=True)

    nodes_export = dict()
    nodes_export['idPlayer'] = [item[0] for item in nodes if item[0] != 1]
    nodes_export['playerName'] = [item[1]['playerName'] for item in nodes if item[1]['playerName'] != 'Goal']
    nodes_export['playerFirstName'] = [item[1]['playerFirstName'] for item in nodes if item[1]['playerFirstName'] != '']
    nodes_export['team'] = [team] * (len(nodes)-1)
    nodes_export['seasonPoints'] = [int(item[1]['nodeLabel']) for item in nodes if item[1]['nodeLabel'] != '']

    weights_export = list(weighted_nodes.values())
    del weights_export[-1]

    nodes_export['betweennessScore'] = weights_export
    nodes_export = pd.DataFrame.from_dict(nodes_export)

    edges_export = dict()
    edges_export['idSource'] = [item[0] for item in edges]
    sourceNames = list()
    for item in edges:
        sourceNames.append(nodes_export[nodes_export.idPlayer == item[0]].reset_index(drop=True).playerName[0])
    edges_export['sourceName'] = sourceNames
    edges_export['idTarget'] = [item[1] for item in edges]
    targetNames = list()
    for item in edges:
        if item[1] == 1:
            targetNames.append('GOAL')
        else:
            targetNames.append(nodes_export[nodes_export.idPlayer == item[1]].reset_index(drop=True).playerName[0])
    edges_export['targetName'] = targetNames
    edges_export['team'] = [team] * (len(edges))
    edges_export['load'] = [item[2] for item in edges]
    edges_export = pd.DataFrame.from_dict(edges_export)

    if strenghtState == 'ES':
        global ONGLET_NODES_ES
        ONGLET_NODES_ES = ONGLET_NODES_ES.append(nodes_export)
        global ONGLET_EDGES_ES
        ONGLET_EDGES_ES = ONGLET_EDGES_ES.append(edges_export)
    elif strenghtState == 'PP':
        global ONGLET_NODES_PP
        ONGLET_NODES_PP = ONGLET_NODES_PP.append(nodes_export)
        global ONGLET_EDGES_PP
        ONGLET_EDGES_PP = ONGLET_EDGES_PP.append(edges_export)

    plt.savefig('exports/' + team + '_' + strenghtState + '_network.png')

    plt.clf()

    print('Done.')


def user_choice_screen(input_value):
    if input_value == 1:
        system('cls')
    elif input_value == 2:
        print(msg.message_error_unkown_functionnality)
        user_choice_screen(futils.input_int_recall(futils.build_message(msg.message_functionnal_launch, msg.message_functionnal_load, msg.message_functionnal_exit)))
    elif input_value == 3:
        exit(msg.message_info_exit)


def magnus_network_choice_screen(input_value):
    if answer == 1:
        print("\n" + msg.message_info_magnusnetwork_fullteam)
        # config file import
        batch_config = None
        try:
            batch_config = open(PATH_CONFIG, 'r')
        except ValueError:
            print(msg.message_error_load_config + PATH_CONFIG)

        if batch_config is not None:
            print('Compute team network...')
            for team in batch_config.read().splitlines():
                for game_situation in SITUATIONS:
                    hockey_team_network_analysis(team, magnus_data_1819, game_situation)
            print('End of program.')
    if answer == 2:
        print(msg.message_info_magnusnetwork_uniqueteam)
        input_team = input('Choose your fighter: ')
        for team in MagnusTeams:
            if team.value == input_team:
                for game_situation in SITUATIONS:
                    hockey_team_network_analysis(team.value, magnus_data_1819, game_situation)
                break
    if answer == 3:
        exit(msg.message_info_exit)


if __name__ == "__main__":
    print(msg.message_info_copyright)
    print(msg.message_info_contact, end='\n\n')
    print(msg.message_info_welcome, end='\n\n')
    print(msg.message_info_input)

    input_value = futils.input_int_recall(
        futils.build_message(
            msg.message_functionnal_launch, msg.message_functionnal_load, msg.message_functionnal_exit))

    user_choice_screen(input_value)

    welcome_screen = open('welcome_screen.txt', 'r')
    for ASCII_line in welcome_screen.read().splitlines():
        print(ASCII_line)

    print('Loading datas...', end="")

    # excel datas import
    try:
        magnus_data_1819 = pd.read_excel(PATH_ACTIONS_DATASET, sheet_name='Data')
    except ValueError:
        print(msg.message_error_load_dataset + PATH_ACTIONS_DATASET)

    print('Done.\n')
    print(msg.message_info_magnusnetwork_welcome)

    answer = futils.input_int_recall(
        futils.build_message(msg.message_functionnal_magnusnetwork_fullteam,
                                           msg.message_functionnal_magnusnetwork_uniqueteam,
                                           msg.message_functionnal_magnusnetwork_exit))

    magnus_network_choice_screen(answer)

    with pd.ExcelWriter('exports/france1819networks.xlsx') as writer:
        ONGLET_NODES_ES.to_excel(writer, sheet_name='NODES_ES')
        ONGLET_EDGES_ES.to_excel(writer, sheet_name='EDGES_ES')
        ONGLET_NODES_PP.to_excel(writer, sheet_name='NODES_PP')
        ONGLET_EDGES_PP.to_excel(writer, sheet_name='EDGES_PP')

    input('Appuyer sur ENTREE pour fermer...')
