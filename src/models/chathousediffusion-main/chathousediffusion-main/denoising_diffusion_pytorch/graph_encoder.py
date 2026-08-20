import dgl
from dgl import DGLGraph, shortest_dist
from .graphormer import Graphormer
import pandas as pd
import json
import torch
import torch.nn.functional as F
from torch.nn.utils.rnn import pad_sequence
from .t5 import t5_encode_text
import random
import pickle
import os
import numpy as np

ENCODED_DIM=768
MAX_NUM_NODES=10


room_category = {
    "Unknown": [0],
    "LivingRoom": [1],
    "MasterRoom": [2],
    "Kitchen": [3],
    "Bathroom": [4],
    "DiningRoom": [5],
    "ChildRoom": [6],
    "StudyRoom": [7],
    "SecondRoom": [8],
    "GuestRoom": [9],
    "Balcony": [10],
    "Entrance": [11],
    "Storage": [12],
}
room_location = {
    "north": [0, 1, 0],
    "northwest": [-1, 1, 0],
    "west": [-1, 0, 0],
    "southwest": [-1, -1, 0],
    "south": [0, -1, 0],
    "southeast": [1, -1, 0],
    "east": [1, 0, 0],
    "northeast": [1, 1, 0],
    "center": [0, 0, 0],
    "Unknown": [0, 0, 1],
}
room_size = {
    "Unknown": [0, 1],
    "XS": [-2, 0],
    "S": [-1, 0],
    "M": [0, 0],
    "L": [1, 0],
    "XL": [2, 0],
}


def t5_feature():
    global room_category
    global room_location
    global room_size
    if not os.path.exists("t5_feature.pkl"):
        room_category_keys = [k for k in room_category.keys()]
        room_location_keys = [k for k in room_location.keys()]
        room_size_keys = [k for k in room_size.keys()]
        a = t5_encode_text(room_category_keys).sum(dim=1)
        b = t5_encode_text(room_location_keys).sum(dim=1)
        c = t5_encode_text(room_size_keys).sum(dim=1)
        t5_room_category = {
            key: a[i].cpu().clone().detach().numpy() for i, key in enumerate(room_category_keys)
        }
        t5_room_location = {
            key: b[i].cpu().clone().detach().numpy() for i, key in enumerate(room_location_keys)
        }
        t5_room_size = {
            key: c[i].cpu().clone().detach().numpy() for i, key in enumerate(room_size_keys)
        }
        del a,b,c
        with open("t5_feature.pkl", "wb") as f:
            pickle.dump([t5_room_category, t5_room_location, t5_room_size], f)
    else:
        with open("t5_feature.pkl", "rb") as f:
            [t5_room_category, t5_room_location, t5_room_size] = pickle.load(f)
    room_category = t5_room_category
    room_location = t5_room_location
    room_size = t5_room_size

t5_feature()

class Node:
    ID = 0

    def __init__(
        self,
        name="Unknown",
        link=[],
        location="Unknown",
        size="Unknown",
        category="Unknown",
    ):
        self.name = name if name!="" else "Unknown"
        self.link = link
        self.link_ids = []
        self.location = location if location!="" else "Unknown"
        self.size = size if size!="" else "Unknown"
        self.category = category
        # self.index = int(name.replace(category, "")) if category != "Unknown" else -1
        self.id = Node.ID
        Node.ID += 1

    def __str__(self):
        if hasattr(self, "name"):
            return self.name
        else:
            return "?"

    def __repr__(self):
        if hasattr(self, "name"):
            return self.name
        else:
            return "?"


def get_nodes(text):
    info = json.loads(text) if text != "\n" else {}
    name2node = {}
    node_list = []
    Node.ID = 0
    for key, value in info.items():
        # number=value.get("num")
        # number = len(value.get("rooms"))
        for room in value.get("rooms"):
            name = room.get("name", "Unknown")
            link = room.get("link", [])
            if len(link)>0 and isinstance(link[0],list):
                link = link[0]
            if len(link)>0 and not isinstance(link[0], str):
                link = []
            location = room.get("location", "Unknown")
            size = room.get("size", "Unknown")
            category = key
            node = Node(name, link, location, size, category)
            node_list.append(node)
            name2node[name] = node
        # for _ in range(MAX_ROOMS_PER_TYPE - number):
        #     node_list.append(Node())
    for node in node_list:
        new_link_ids = []
        for name in node.link:
            if name2node.get(name):
                new_link_ids.append(name2node[name].id)
        node.link_ids = list(set(node.link_ids + new_link_ids))
        for n2 in node.link_ids:
            node_list[n2].link_ids = list(set(node_list[n2].link_ids + [node.id]))
    return node_list


def get_dgl(node_list, mask=0):
    dgl_graph: DGLGraph = dgl.graph([])
    for node in node_list:
        dgl_graph.add_nodes(
            1,
            {
                "category": torch.tensor(
                    (
                        np.array([room_category.get(node.category,room_category["Unknown"])])
                        if random.random() >= mask
                        else np.array([room_category["Unknown"]])
                    ),
                    dtype=torch.float,
                ),
                "location": torch.tensor(
                    (
                        np.array([room_location.get(node.location,room_location["Unknown"])])
                        if random.random() >= mask
                        else np.array([room_location["Unknown"]])
                    ),
                    dtype=torch.float,
                ),
                "size": torch.tensor(
                    (
                        np.array([room_size.get(node.size,room_size["Unknown"])])
                        if random.random() >= mask
                        else np.array([room_size["Unknown"]])
                    ),
                    dtype=torch.float,
                ),
            },
        )
    if len(node_list)>10:
        print("too many nodes")
    for node in node_list:
        for j in node.link_ids:
            dgl_graph.add_edges(node.id, j)
    for node in node_list:
        for j in node.link_ids:
            if node.id < j and random.random() < mask:
                dgl_graph.remove_edges(dgl_graph.edge_ids(node.id, j))
                dgl_graph.remove_edges(dgl_graph.edge_ids(j, node.id))
    # erase_list = []
    # for i in range(dgl_graph.num_nodes()):
    #     if random.random() < mask:
    #         erase_list.append(i)
    #         # no zero
    #         if len(erase_list) == dgl_graph.num_nodes() - 1:
    #             break
    # dgl_graph.remove_nodes(erase_list)
    return dgl_graph

def collate(graphs, multi_hop_max_dist=4, max_degree=4):
    # To match Graphormer's input style, all graph features should be
    # padded to the same size. Keep in mind that different graphs may
    # have varying feature sizes since they have different number of
    # nodes, so they will be aligned with the graph having the maximum
    # number of nodes.

    num_graphs = len(graphs)
    num_nodes = [g.num_nodes() for g in graphs]
    max_num_nodes = MAX_NUM_NODES

    # Graphormer adds a virual node to the graph, which is connected to
    # all other nodes and supposed to represent the graph embedding. So
    # here +1 is for the virtual node.
    attn_mask = torch.zeros(num_graphs, max_num_nodes + 1, max_num_nodes + 1)
    node_feat = []
    in_degree, out_degree = [], []
    path_data = []
    # Since shortest_dist returns -1 for unreachable node pairs and padded
    # nodes are unreachable to others, distance relevant to padded nodes
    # use -1 padding as well.
    dist = -torch.ones((num_graphs, max_num_nodes, max_num_nodes), dtype=torch.long)

    for i in range(num_graphs):
        # A binary mask where invalid positions are indicated by True.
        attn_mask[i, :, num_nodes[i] + 1 :] = 1
        if num_nodes[i]==0:
            node_feat_i=torch.zeros(1, ENCODED_DIM*3)
            node_feat.append(node_feat_i)
            in_degree.append(torch.zeros(1,dtype=torch.long))
            out_degree.append(torch.zeros(1,dtype=torch.long))
            path_data.append(torch.zeros(max_num_nodes, max_num_nodes, multi_hop_max_dist, 1))
        else:
        # +1 to distinguish padded non-existing nodes from real nodes
            node_feat_i = torch.cat(
                [
                    graphs[i].ndata["category"],
                    graphs[i].ndata["location"],
                    graphs[i].ndata["size"],
                ],
                dim=-1,
            )
            node_feat.append(node_feat_i)

            in_degree.append(torch.clamp(graphs[i].in_degrees() + 1, min=0, max=max_degree))
            out_degree.append(
                torch.clamp(graphs[i].out_degrees() + 1, min=0, max=max_degree)
            )

            # Path padding to make all paths to the same length "max_len".
            dist_i, path = shortest_dist(graphs[i], return_paths=True)
            path_len = path.size(dim=2)
            # shape of shortest_path: [n, n, max_len]
            if path_len >= multi_hop_max_dist:
                shortest_path = path[:, :, :multi_hop_max_dist]
            else:
                p1d = (0, multi_hop_max_dist - path_len)
                # Use the same -1 padding as shortest_dist for
                # invalid edge IDs.
                shortest_path = F.pad(path, p1d, "constant", -1)
            pad_num_nodes = max_num_nodes - num_nodes[i]
            p3d = (0, 0, 0, pad_num_nodes, 0, pad_num_nodes)
            shortest_path = F.pad(shortest_path, p3d, "constant", -1)
            # shortest_dist pads non-existing edges (at the end of shortest
            # paths) with edge IDs -1, and th.zeros(1, edata.shape[1]) stands
            # for all padded edge features.
            edata = torch.cat(
                [torch.ones((graphs[i].num_edges(), 1)), torch.zeros(1, 1)], dim=0
            )
            path_data.append(edata[shortest_path])

            dist[i, : num_nodes[i], : num_nodes[i]] = dist_i


    # node feat padding
    node_feat = pad_sequence(node_feat, batch_first=True)
    p2d = (0, 0, 0, max_num_nodes - node_feat.shape[1])
    node_feat = F.pad(node_feat, p2d, "constant", 0)

    # degree padding
    in_degree = pad_sequence(in_degree, batch_first=True)
    p1d = (0, max_num_nodes - in_degree.shape[1])
    in_degree = F.pad(in_degree, p1d, "constant", 0)
    out_degree = pad_sequence(out_degree, batch_first=True)
    p1d = (0, max_num_nodes - out_degree.shape[1])
    out_degree = F.pad(out_degree, p1d, "constant", 0)

    return (
        attn_mask,
        node_feat,
        in_degree,
        out_degree,
        torch.stack(path_data),
        dist,
    )

# from tqdm import tqdm
# if __name__ == "__main__":
#     text_path = "../chathousediffusion/data/new/text/json2.csv"
#     texts = pd.read_csv(text_path)
#     texts = [p for p in zip(texts["0"], texts["1"])]
#     texts.sort(
#         key=lambda x: int(x[0].replace(".png", "").replace(".json", "").split("/")[-1])
#     )
#     graphs = []
#     for i in tqdm(range(len(texts))):
#         text = texts[i][1]
#         nodes = get_nodes(text)
#         graph = get_dgl(nodes)
#         graphs.append(graph)

#     attn_mask, node_feat, in_degree, out_degree, path_data, dist = collate(graphs)

#     graphormer = Graphormer()
#     a = graphormer.forward(node_feat, in_degree, out_degree, path_data, dist, attn_mask)
#     print(nodes)
