from graphviz import Digraph

from .models import XcTarget


class XcodeProjectGraphGenerator():

    def __init__(self, xcode_project_reader):
        self.xcode_project = xcode_project_reader.xcode_project
    
    def generate_targets_dependencies_graph(self, open_pdf=False, filepath=None, title=None, including_types=set()):
        if not filepath or not title:
            return False

        graph = Digraph(filename=filepath,
                        format='pdf',
                        engine='dot',
                        graph_attr={
                            'fontname': 'Courier',
                            'pack': 'true',
                        },
                        node_attr={
                            'shape': 'box',
                            'fontname': 'Courier',
                        },
                        edge_attr={
                            'fontname': 'Courier',
                        })

        title = "{} - {}\n\n".format(self.xcode_project.name, title)
        graph.attr(label=title)

        graph.attr(labelloc='t')
        graph.attr(fontsize='26')
        graph.attr(rankdir='BT')

        if including_types:
            targets = {t for t in self.xcode_project.targets if t.type in including_types}
        else:
            targets = self.xcode_project.targets

        # Sort nodes by name
        targets = sorted(targets, key=lambda t: t.name)

        # Add nodes
        for xcode_target in targets:
            if xcode_target.type in { XcTarget.Type.TEST, XcTarget.Type.UI_TEST }:
                style = 'dotted'
            elif xcode_target.type == XcTarget.Type.EXTENSION:
                style = 'dashed'
            elif xcode_target.type == XcTarget.Type.APPLICATION:
                style = 'diagonals'
            else:
                style = 'solid'
            graph.node(xcode_target.name, style=style)

        # Add edges
        for xcode_target in targets:
            dependencies_target = sorted(xcode_target.dependencies, key=lambda t: t.name)  # Sort dependencies by name
            for dependency_target in dependencies_target:
                if including_types and dependency_target.type not in including_types:
                    continue

                graph.edge(xcode_target.name, dependency_target.name)

        graph.render(cleanup=True, view=open_pdf)
        # print(graph.source)

        return True
