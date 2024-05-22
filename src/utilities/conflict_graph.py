from .mod import Mod

class Node: #used only internally within ConflictGraph
    key: int
    value: Mod
    child_count: int
    parent_count: int

    def __init__(self, key, value, child_count = 0, parent_count = 0) -> None:
        self.key = key
        self.value = value
        self.child_count = child_count
        self.parent_count = parent_count


class ConflictGraph:
    nodes: set
    edges: dict
    used_flag: bool

    def __init__(self, loaderder: list) -> None:
        """Initialize the graph based on a list of mod objects.

        Args:
            loaderder (list): arbitraty list of mods
        """
        id = 0
        self.nodes = []
        self.edges = {}
        self.used_flag = False
        modname2id = {}
        # insert all nodes
        for mod in loaderder:
            node = Node(key=id, value = mod, child_count = 0, parent_count = 0)
            self.nodes.append(node)
            modname2id[mod.name] = id
            id += 1
        # create all edges
        for node in self.nodes:
            for mod_late in node.value.overwriting_mods:
                # find its node
                node_late = self.nodes[modname2id[mod_late.name]]
                # store the edge
                if (not node.key in self.edges):
                    self.edges[node.key] = []
                self.edges[node.key].append(node_late)
                node.child_count += 1
                node_late.parent_count += 1


    def to_loadorder(self):
        """
        The graph will be broken after this, so don't reuse the graph!

        Returns:
            A sorted list of mods, based on conflict rules.

        """
        assert self.used_flag == False
        new_order = []
        pop_stack = []
        for node in self.nodes:
            if(node.parent_count == 0):
                # if it's out of the graph, output it first.
                if(node.child_count == 0):
                    new_order.append(node.value)
                # if it's in the graph and has no parent, get ready to pop it.
                else:
                    pop_stack.append(node)
        # remove nodes from the graph 
        while(len(pop_stack) > 0):
            node = pop_stack.pop()
            if (node.key in self.edges):
                for child in self.edges[node.key]:
                    child.parent_count -= 1
                    if (child.parent_count == 0):
                        pop_stack.append(child)
            new_order.append(node.value)
        self.used_flag = True
        return new_order


