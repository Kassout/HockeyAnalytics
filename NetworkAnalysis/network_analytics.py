import warnings
from enum import Enum
from os import makedirs
from os import system
from sys import exit

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

import functionUtils as futils
import message_properties as msg

PATH_DATASET = 'datasets/france1819goals.xlsx'
PATH_CONFIG = 'batch_config.txt'


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


def hockey_team_network_analysis(team, magnus_data):
    print(MagnusTeams(team).value, end="")

    magnus_data_by_team = magnus_data.loc[magnus_data['scoringTeam.1'] == MagnusTeams(team).value].reset_index(
        drop=True)

    # work only with 5v5 strength state
    only_5v5 = magnus_data_by_team[magnus_data_by_team.strenghtState == '5v5'].reset_index(drop=True)

    print('.', end="")

    # arrange dataFrame to capture only datas of interest for the network's edges
    edges_data = only_5v5[["scoringTeam.1", "G", "A1"]]
    edges_data.columns = ['nameTeam', 'scorer', 'firstAssist']

    # arrange dataFrame to capture only datas of interest for the network's nodes
    nodes_data = pd.DataFrame([map(int, pd.unique(only_5v5[['G', 'A1']].values.ravel('K'))[
        ~np.isnan(pd.unique(only_5v5[['G', 'A1']].values.ravel('K')))])]).T
    nodes_data.columns = ['idPlayer']

    nodes_data['namePlayer'] = None
    nodes_data['nameTeam'] = None
    nodes_data['seasonScore'] = 0

    for i in nodes_data['idPlayer']:
        try:
            index = list(only_5v5['G']).index(i)
            column = 'G_fullName'
        except ValueError:
            try:
                index = list(only_5v5['A1']).index(i)
                column = 'A1_fullName'
            except ValueError:
                index = None
        if index is not None:
            nodes_data.loc[list(nodes_data['idPlayer']).index(i), 'namePlayer'] = only_5v5.loc[index, column]
            nodes_data.loc[list(nodes_data['idPlayer']).index(i), 'nameTeam'] = only_5v5.loc[index, 'scoringTeam.1']

    for i in range(len(edges_data)):
        nodes_data.loc[nodes_data['idPlayer'] == edges_data.iloc[i].scorer, 'seasonScore'] += 1
        nodes_data.loc[nodes_data['idPlayer'] == edges_data.iloc[i].firstAssist, 'seasonScore'] += 1

    nodes_data = nodes_data.sort_values(by=['nameTeam']).reset_index(drop=True)

    print('.', end="")

    # build nodes from nodes_data
    # ATTENTION : NODELABEL is choosable. (player name or score)
    nodes = [(nodes_data.idPlayer[i],
              {'playerName': nodes_data.namePlayer[i].split(',')[0], 'nodeLabel': str(nodes_data.seasonScore[i])}) for i
             in range(len(nodes_data)) if nodes_data.nameTeam[i] == team]
    nodes.append((1, {'playerName': 'Goal', 'nodeLabel': ''}))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DIGRAPH - WEIGHTED EDGES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

    diGraph_edges = []

    # build edges from edges_data
    # logic : FROM x1.id TO x2.id
    for i in range(len(edges_data)):
        if [int(edges_data.loc[i, 'scorer']), 1] in [dic.get('edge') for dic in diGraph_edges if
                                                     dic.get('edge') == [int(edges_data.loc[i, 'scorer']), 1]]:
            diGraph_edges[futils.find_dictvalue_in_list(diGraph_edges, 'edge',
                                                                      [int(edges_data.loc[i, 'scorer']), 1])][
                'weight'] += 1
        else:
            diGraph_edges.append({'edge': [int(edges_data.loc[i, 'scorer']), 1], 'weight': 1})
        if not np.isnan(edges_data.loc[i, 'firstAssist']):
            if [int(edges_data.loc[i, 'firstAssist']), int(edges_data.loc[i, 'scorer'])] in [dic.get('edge') for dic in
                                                                                             diGraph_edges if
                                                                                             dic.get('edge') == [int(
                                                                                                     edges_data.loc[
                                                                                                         i, 'firstAssist']),
                                                                                                                 int(
                                                                                                                         edges_data.loc[
                                                                                                                             i, 'scorer'])]]:
                diGraph_edges[futils.find_dictvalue_in_list(diGraph_edges, 'edge',
                                                                          [int(edges_data.loc[i, 'firstAssist']),
                                                                           int(edges_data.loc[i, 'scorer'])])][
                    'weight'] += 1
            else:
                diGraph_edges.append(
                    {'edge': [int(edges_data.loc[i, 'firstAssist']), int(edges_data.loc[i, 'scorer'])], 'weight': 1})

    diGraph_edges = [tuple(dic['edge']) + tuple([dic['weight']]) for dic in diGraph_edges]

    print('.', end="")

    H = nx.DiGraph()
    H.add_nodes_from(nodes)
    H.add_weighted_edges_from(diGraph_edges)
    weighted_nodes = nx.betweenness_centrality(H, normalized=True, weight='weight')
    weights = 8000 * pd.Series(list(weighted_nodes.values()))

    goal_fixed_positions = {1: (0, 0)}  # dict with two of the positions set
    goal_fixed_nodes = goal_fixed_positions.keys()
    pos = nx.spring_layout(H, pos=goal_fixed_positions, fixed=goal_fixed_nodes)

    plt.figure(1, figsize=(40, 15))
    plt.subplot(121)
    nx.draw_networkx(H, node_color=range(len(nodes)), font_size=10, pos=pos,
                     node_size=weights, cmap=plt.cm.Reds,
                     labels={player[0]: player[1].get('nodeLabel') for player in nodes}, with_labels=True)

    for i in pos.keys():
        x, y = pos[i]
        plt.text(x, y + 0.04, s=''.join([player[1].get('playerName') for player in nodes if player[0] == i]),
                 bbox=dict(facecolor='red', alpha=0.5), horizontalalignment='center')

    makedirs("exports", exist_ok=True)

    plt.savefig('exports/' + team + '_network.png')
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
        print(msg.message_info_magnusnetwork_fullteam)
        # config file import
        try:
            batch_config = open(PATH_CONFIG, 'r')
        except ValueError:
            print(msg.message_error_load_config + PATH_CONFIG)

        print('Compute team network...')
        for team in batch_config.read().splitlines():
            hockey_team_network_analysis(team, magnus_data_1819)
        print('End of program.')
    if answer == 2:
        print(msg.message_info_magnusnetwork_uniqueteam)
        input_team = input('Choose your fighter: ')
        for team in MagnusTeams:
            if team.value == input_team:
                hockey_team_network_analysis(team.value, magnus_data_1819)
                break
    if answer == 3:
        sys.exit(msg.message_info_exit)


if __name__ == "__main__":

    # warnings.filterwarnings("ignore")

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
        magnus_data_1819 = pd.read_excel(PATH_DATASET, sheet_name='Data')
    except ValueError:
        print(msg.message_error_load_dataset + PATH_DATASET)

    print('Done.\n')
    print(msg.message_info_magnusnetwork_welcome)

    answer = futils.input_int_recall(
        futils.build_message(msg.message_functionnal_magnusnetwork_fullteam,
                                           msg.message_functionnal_magnusnetwork_uniqueteam,
                                           msg.message_functionnal_magnusnetwork_exit))

    magnus_network_choice_screen(answer)

    input('Appuyer sur ENTREE pour fermer...')
