---STATUS 25.10.22---

...Virtual Environment...
Since I have an M1 mac, I couldn't just use tensorflow out of the box but had to jump through a number of hoops.
the virtual environment used has been installed using conda (miniforge3 or something like that).
It was set up as instructed here: https://caffeinedev.medium.com/how-to-install-tensorflow-on-m1-mac-8e9b91d93706
It can be found (on Tobias' mac) at /Users/tobiasbreuer/miniforge3/envs . Its name is mlp.

...Classes...
There are different files for different purposes.
neuralnetwork1.py - This file houses the code based on Adam Wagner's neural network. The evaluation function of instances
        and the neural network can be found here.
inputreader.py - This file is able to read the input files. This includes the parameter file which contains
        information about all parameters needed to run a specific NN for a specific instance of items, reading a bitstring
        from a file, and potentially more methods.
tests.py - This file contains a number of tests. These have not necessarily been updated, so it might be that, while they should all work,
        the tests to not cover all aspects of the code. As a best practice, the tests should cover all parts of the code.
utils.py - This file contains a number of methods necessary to manipulate the triplet matrices used by the neural network.
        However, it also contains methods to clean up solution files and other utility methods.
control.py - This file contains methods to check the correctness of the neural network. In has methods to read, evaluate and print
        the "pattern bin packing" ILP and LP solution of specific bitstring, and to find an accompanying item-size distribution using
        the corresponding LP.
lpbp.py - This file contains the (Integer) Linear Program to find a solution for the bin packing problem, using the pattern approach.
lpsd.py - This file contains the Linear Program to find a possible item size distribution corresponding to a given selection of
        allowed patterns.