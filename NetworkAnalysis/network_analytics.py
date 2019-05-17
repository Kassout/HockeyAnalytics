# -*- coding: utf-8 -*-
"""
Created on Wed May  1 10:27:46 2019

@author: Maxime HELIOT
"""    

def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1
    
if __name__ == "__main__":
    
    # Imports
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    import networkx as nx
    
    #STABLE
    # excel datas import
    magnus_data_1819 = pd.read_excel('datasets/france1819goals.xlsx', sheet_name='Data')
    
    # work only with 5v5 strength state
    only_5v5 = magnus_data_1819[magnus_data_1819.strenghtState == '5v5'].reset_index(drop=True)
    
    # teams listing
    teams = list(only_5v5['scoringTeam.1'].unique())
    
    # pick up the team you want to study
    team = "Grenoble"
    
    # arrange dataFrame to capture only datas of interest for the network's edges
    edges_data = only_5v5[["scoringTeam.1","G","A1","A2"]].sort_values(by=['scoringTeam.1']).reset_index(drop=True)
    edges_data.columns = ['nameTeam','scorer','firstAssist','secondAssist']

    # arrange dataFrame to capture only datas of interest for the network's nodes
    nodes_data = pd.DataFrame([map(int,pd.unique(only_5v5[['G','A1','A2']].values.ravel('K'))[~np.isnan(pd.unique(only_5v5[['G','A1','A2']].values.ravel('K')))])]).T
    nodes_data.columns = ['idPlayer']
    
    nodes_data['namePlayer'] = None
    nodes_data['nameTeam'] = None
    nodes_data['seasonScore'] = 0
    
    for i in nodes_data['idPlayer'] :
        try: 
            index = list(only_5v5['G']).index(i)
            column = 'G_fullName'
        except ValueError: 
            try:
                index = list(only_5v5['A1']).index(i)
                column = 'A1_fullName'
            except ValueError:
                try: 
                    index = list(only_5v5['A2']).index(i)
                    column = 'A2_fullName'
                except ValueError:
                    index = None
        if index is not None :
            nodes_data.loc[list(nodes_data['idPlayer']).index(i), 'namePlayer'] = only_5v5.loc[index, column]
            nodes_data.loc[list(nodes_data['idPlayer']).index(i), 'nameTeam'] = only_5v5.loc[index, 'scoringTeam.1']
            
    for i in range(len(edges_data)):
        nodes_data.loc[nodes_data['idPlayer'] == edges_data.iloc[i].scorer, 'seasonScore'] += 1
        nodes_data.loc[nodes_data['idPlayer'] == edges_data.iloc[i].firstAssist, 'seasonScore'] += 1
        nodes_data.loc[nodes_data['idPlayer'] == edges_data.iloc[i].secondAssist, 'seasonScore'] += 1

    nodes_data = nodes_data.sort_values(by=['nameTeam']).reset_index(drop=True)
    
    # build nodes from nodes_data
    ### ATTENTION : NODELABEL is choosable. (player name or score)
    nodes = [(nodes_data.idPlayer[i], {'playerName':nodes_data.namePlayer[i].split(',')[0],'nodeLabel':str(nodes_data.seasonScore[i])}) for i in range(len(nodes_data)) if nodes_data.nameTeam[i] == team]
    nodes.append((1, {'playerName':'Goal','nodeLabel':''}))
   
    ####################################### MULTIDIGRAPH ######################################################
    
    multiDiGraph_edges = []
    
    # build edges from edges_data    
    # logic : FROM x1.id TO x2.id
    edges_data_team = edges_data.loc[edges_data['nameTeam'] == team].reset_index(drop=True)
    for i in range(len(edges_data_team)) :
        multiDiGraph_edges.append((int(edges_data_team.loc[i, 'scorer']), 1))
        if not np.isnan(edges_data_team.loc[i, 'firstAssist']) :
            multiDiGraph_edges.append((int(edges_data_team.loc[i, 'firstAssist']), int(edges_data_team.loc[i, 'scorer'])))
            if not np.isnan(edges_data_team.loc[i, 'secondAssist']) :
                multiDiGraph_edges.append((int(edges_data_team.loc[i, 'secondAssist']), int(edges_data_team.loc[i, 'firstAssist'])))
    
    G = nx.MultiDiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(multiDiGraph_edges)
    weighted_nodes = nx.betweenness_centrality(G, normalized=True)
    weights = 8000*pd.Series(list(weighted_nodes.values()))

    print(weighted_nodes)
    
    plt.figure(1, figsize=(30, 10))
    plt.subplot(121)
    nx.draw(G,k =1,node_color=range(len(nodes)),font_size = 10, pos=nx.spring_layout(G),
            node_size = weights,cmap=plt.cm.Blues,labels={player[0]:player[1].get('nodeLabel') for player in nodes}, with_labels=True)
    
    nx.write_gexf(G, "exports/MultiDiGraph.gexf")
    
    ####################################### DIGRAPH - WEIGHTED EDGES ##########################################
    
    diGraph_edges = []
    
    # build edges from edges_data    
    # logic : FROM x1.id TO x2.id
    for i in range(len(edges_data_team)) :
        if [int(edges_data_team.loc[i, 'scorer']), 1] in [dic.get('edge') for dic in diGraph_edges if dic.get('edge') == [int(edges_data_team.loc[i, 'scorer']), 1]]:
            diGraph_edges[find(diGraph_edges, 'edge', [int(edges_data_team.loc[i, 'scorer']), 1])]['weight'] += 1
        else :
            diGraph_edges.append({'edge':[int(edges_data_team.loc[i, 'scorer']), 1], 'weight': 1})
        if not np.isnan(edges_data_team.loc[i, 'firstAssist']) :
            if [int(edges_data_team.loc[i, 'firstAssist']), int(edges_data_team.loc[i, 'scorer'])] in [dic.get('edge') for dic in diGraph_edges if dic.get('edge') == [int(edges_data_team.loc[i, 'firstAssist']), int(edges_data_team.loc[i, 'scorer'])]]:
                diGraph_edges[find(diGraph_edges, 'edge', [int(edges_data_team.loc[i, 'firstAssist']), int(edges_data_team.loc[i, 'scorer'])])]['weight'] += 1
            else :
                diGraph_edges.append({'edge':[int(edges_data_team.loc[i, 'firstAssist']), int(edges_data_team.loc[i, 'scorer'])], 'weight': 1})
        if not np.isnan(edges_data_team.loc[i, 'secondAssist']) :
            if [int(edges_data_team.loc[i, 'secondAssist']), int(edges_data_team.loc[i, 'firstAssist'])] in [dic.get('edge') for dic in diGraph_edges if dic.get('edge') == [int(edges_data_team.loc[i, 'secondAssist']), int(edges_data_team.loc[i, 'firstAssist'])]]:
                diGraph_edges[find(diGraph_edges, 'edge', [int(edges_data_team.loc[i, 'secondAssist']), int(edges_data_team.loc[i, 'firstAssist'])])]['weight'] += 1
            else :
                diGraph_edges.append({'edge':[int(edges_data_team.loc[i, 'secondAssist']), int(edges_data_team.loc[i, 'firstAssist'])], 'weight': 1})
                    
    diGraph_edges = [tuple(dic['edge']) + tuple([dic['weight']])  for dic in diGraph_edges]
    
    H = nx.DiGraph()
    H.add_nodes_from(nodes)
    H.add_weighted_edges_from(diGraph_edges)
    weighted_nodes = nx.betweenness_centrality(H, normalized=True, weight='weight')
    weights = 8000*pd.Series(list(weighted_nodes.values()))
    
    print(weighted_nodes)
    
    plt.figure(2, figsize=(30, 10))
    plt.subplot(121)
    nx.draw(H,k =1,node_color=range(len(nodes)),font_size = 10,
            node_size = weights,cmap=plt.cm.Blues,labels={player[0]:player[1].get('nodeLabel') for player in nodes}, with_labels=True)
    
    nx.write_gexf(H, "exports/DiGraph.gexf")