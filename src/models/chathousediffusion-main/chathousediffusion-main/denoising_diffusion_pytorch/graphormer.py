"""
This file defines the Graphormer model, which utilizes DegreeEncoder,
SpatialEncoder, PathEncoder and GraphormerLayer from DGL build-in modules.
"""

import torch as th
import torch.nn as nn
from dgl.nn import DegreeEncoder, GraphormerLayer, PathEncoder, SpatialEncoder


class Graphormer(nn.Module):
    def __init__(
        self,
        edge_dim=1,
        in_feature=6,
        max_degree=4,
        num_spatial=4,
        multi_hop_max_dist=4,
        num_encoder_layers=6,
        embedding_dim=64,
        ffn_embedding_dim=64,
        num_attention_heads=8,
        dropout=0.1,
        pre_layernorm=True,
        activation_fn=nn.GELU(),
    ):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        self.embedding_dim = embedding_dim
        self.num_heads = num_attention_heads

        self.atom_encoder = nn.Linear(in_feature, embedding_dim)
        # self.atom_encoder = nn.Sequential(
        #     nn.Linear(in_feature, int(embedding_dim / 16)),
        #     nn.Linear(int(embedding_dim / 16), embedding_dim),
        # )
        # self.atom_encoder = nn.Embedding(num_atoms, embedding_dim, padding_idx=0)
        self.graph_token = nn.Embedding(1, embedding_dim)

        self.degree_encoder = DegreeEncoder(
            max_degree=max_degree, embedding_dim=embedding_dim
        )

        self.path_encoder = PathEncoder(
            max_len=multi_hop_max_dist,
            feat_dim=edge_dim,
            num_heads=num_attention_heads,
        )

        self.spatial_encoder = SpatialEncoder(
            max_dist=num_spatial, num_heads=num_attention_heads
        )
        self.graph_token_virtual_distance = nn.Embedding(1, num_attention_heads)

        self.emb_layer_norm = nn.LayerNorm(self.embedding_dim)

        self.layers = nn.ModuleList([])
        self.layers.extend(
            [
                GraphormerLayer(
                    feat_size=self.embedding_dim,
                    hidden_size=ffn_embedding_dim,
                    num_heads=num_attention_heads,
                    dropout=dropout,
                    activation=activation_fn,
                    norm_first=pre_layernorm,
                )
                for _ in range(num_encoder_layers)
            ]
        )

    def forward(
        self,
        node_feat,
        in_degree,
        out_degree,
        path_data,
        dist,
        attn_mask=None,
    ):
        num_graphs, max_num_nodes, _ = node_feat.shape
        deg_emb = self.degree_encoder(th.stack((in_degree, out_degree)))

        # node feature + degree encoding as input
        node_feat = self.atom_encoder(node_feat)
        node_feat = node_feat + deg_emb
        graph_token_feat = self.graph_token.weight.unsqueeze(0).repeat(num_graphs, 1, 1)
        x = th.cat([graph_token_feat, node_feat], dim=1)

        # spatial encoding and path encoding serve as attention bias
        attn_bias = th.zeros(
            num_graphs,
            max_num_nodes + 1,
            max_num_nodes + 1,
            self.num_heads,
            device=dist.device,
        )
        path_encoding = self.path_encoder(dist, path_data)
        spatial_encoding = self.spatial_encoder(dist)
        attn_bias[:, 1:, 1:, :] = path_encoding + spatial_encoding

        # spatial encoding of the virtual node
        t = self.graph_token_virtual_distance.weight.reshape(1, 1, self.num_heads)
        # Since the virtual node comes first, the spatial encodings between it
        # and other nodes will fill the 1st row and 1st column (omit num_graphs
        # and num_heads dimensions) of attn_bias matrix by broadcasting.
        attn_bias[:, 1:, 0, :] = attn_bias[:, 1:, 0, :] + t
        attn_bias[:, 0, :, :] = attn_bias[:, 0, :, :] + t

        x = self.emb_layer_norm(x)

        for layer in self.layers:
            x = layer(
                x,
                attn_mask=attn_mask,
                attn_bias=attn_bias,
            )

        graph_rep = x[:, 1:, :]

        return graph_rep
