import utils

class Node(object):
    def __init__(self, name, creator=None):
        self.raw_name = name
        self.creator = creator

    @property
    def is_source(self):
        return self.creator is None

    def filename(self, env):
        return self.raw_name

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.raw_name)
        )

class Directory(Node):
    pass

class Edge(object):
    def __init__(self, target, deps=None):
        target.creator = self
        self.target = target
        self.deps = utils.objectify_list(deps, Node)

class InstallInputs(object):
    def __init__(self):
        self.files = []
        self.directories = []

    def __nonzero__(self):
        return bool(self.files or self.directories)

class BuildInputs(object):
    def __init__(self):
        self.edges = []
        self.default_targets = []
        self.fallback_default = None
        self.install_targets = InstallInputs()
        self.global_options = {}

    def add_edge(self, edge):
        self.edges.append(edge)

    def get_default_targets(self):
        if self.default_targets:
            return self.default_targets
        elif self.fallback_default:
            return [self.fallback_default]
        else:
            return []
