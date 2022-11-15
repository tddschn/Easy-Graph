import random
import sys

import easygraph as eg
import numpy as np
import pytest

from matplotlib import pyplot as plt


class TestLocalAssort:
    @classmethod
    def setup_class(self):
        self.G = eg.get_graph_karateclub()
        random_value = [0, 1, 2, 3, 4, 5]
        edgelist = []
        valuelist = []
        node_num = len(self.G.nodes)
        for e in self.G.edges:
            edgelist.append([e[0] - 1, e[1] - 1])
        print("edgelist:", edgelist)
        for i in range(0, node_num):
            valuelist.append(random.choice(random_value))
        self.edgelist = np.int32(edgelist)
        valuelist = np.int32(valuelist)
        self.valuelist = valuelist

    @pytest.mark.skipif(
        sys.version_info < (3, 7), reason="python version should higher than 3.7"
    )
    def test_karateclub(self):
        assortM, assortT, Z = eg.localAssort(
            self.edgelist, self.valuelist, pr=np.arange(0, 1, 0.1)
        )
        print("M:", assortM)
        print("T:", assortT)
        print("Z:", Z)

        _, assortT, Z = eg.functions.basic.localassort.localAssort(
            self.edgelist, self.valuelist, pr=np.array([0.9])
        )
        print("_:", _)
        print("assortT:", assortT)
        print("Z:", Z)

        plt.hist(assortM)
        plt.show()
