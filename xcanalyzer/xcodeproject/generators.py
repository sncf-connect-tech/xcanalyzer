import os

from graphviz import Digraph
from termcolor import cprint

from .models import XcTarget


class XcProjectGraphGenerator():

    def __init__(self, xcode_project):
        self.xcode_project = xcode_project
    
    def generate_targets_dependencies_graph(self,
                                            output_format='pdf',  # 'pdf' or 'png'
                                            dependency_type=None,  # 'build' or 'framework'
                                            preview=False,
                                            display_graph_source=False,
                                            filepath=None,
                                            title=None,
                                            including_types=set()):
        if not filepath:
            raise Exception("Missing filepath.")

        if not title:
            raise Exception("Missing title.")
        
        if output_format not in {'pdf', 'png'}:
            raise Exception("Bad output_format '{}'. Only 'pdf' and 'png' are supported.".format(output_format))
        
        if dependency_type not in {'build', 'linked', 'embed'}:
            raise Exception("Bad dependency_type '{}'. Only 'build', 'linked' and 'embed' are supported.".format(dependency_type))

        graph = Digraph(filename=filepath,
                        format=output_format,
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

        # Target nodes
        for xcode_target in targets:
            if xcode_target.type in {XcTarget.Type.TEST, XcTarget.Type.UI_TEST}:
                style = 'dotted'
            elif xcode_target.type in {XcTarget.Type.APP_EXTENSION, XcTarget.Type.WATCH_EXTENSION}:
                style = 'dashed'
            elif xcode_target.type in {XcTarget.Type.APPLICATION, XcTarget.Type.WATCH_APPLICATION}:
                style = 'diagonals'
            else:
                style = 'solid'
            graph.node(xcode_target.name, style=style)

        # Dependencies edges
        for xcode_target in targets:
            if dependency_type == 'build':
                dependencies = xcode_target.dependencies
            elif dependency_type == 'linked':
                dependencies = xcode_target.linked_frameworks
            elif dependency_type == 'embed':
                dependencies = xcode_target.embed_frameworks
            else:
                raise Exception("Dependency type '{}' not supported.".format(dependency_type))

            dependencies_target = sorted(dependencies, key=lambda t: t.name)  # Sort dependencies by name
            for dependency_target in dependencies_target:
                if including_types and dependency_target.type not in including_types:
                    continue

                graph.edge(xcode_target.name, dependency_target.name)

        # Render the graph
        graph.render(cleanup=True, view=preview)

        # Display graph source if asked
        if display_graph_source:
            print(graph.source)

        return True


class FolderReporter():

    def __init__(self, folder_path, ignored_dirpaths, ignored_dirs):
        self.folder_path = folder_path
        self.ignored_dirpaths = ignored_dirpaths
        self.ignored_dirs = ignored_dirs
    
    def print_empty_dirs(self):
        # Walk to find empty folders
        for (dirpath, dirnames, filenames) in os.walk(self.folder_path):
            relative_dirpath = dirpath[len(self.folder_path):]

            # Filter root folder
            if not relative_dirpath:
                continue

            # Filter folder to ignore by path
            continue_to_next_dirpath = False
            for ignored_dirpath in self.ignored_dirpaths:
                if relative_dirpath.startswith(ignored_dirpath):
                    continue_to_next_dirpath = True
                    break
            if continue_to_next_dirpath:
                continue
                
            # Filter folder to ignore by name
            folder_parts = set(relative_dirpath.split(os.path.sep))
            if self.ignored_dirs & folder_parts:
                continue
            
            # Filter folder containing at least one dir
            if dirnames:
                continue
            
            # Filter folder containing at least an unhidden filename
            unhidden_filenames = set([f for f in filenames if not f.startswith('.')])
            if unhidden_filenames:
                continue
            
            # Hidden files
            hidden_filenames = list(set(filenames) - unhidden_filenames)
            hidden_filenames.sort()

            display = relative_dirpath

            # Display hidden files for folder with only hidden files
            if hidden_filenames:
                hidden_filenames_display = ', '.join([f for f in hidden_filenames])
                display += ' [{}]'.format(hidden_filenames_display)
            
            print(display)


class XcProjReporter():

    def __init__(self, xcode_project):
        self.xcode_project = xcode_project

    def _print_horizontal_line(self):
        print('--------------------')

    def print_targets(self, by_type=True, verbose=False):
        if not by_type:
            target_names = [t.name for t in self.xcode_project.targets]
            target_names.sort()
            for target_name in target_names:
                print(target_name)
        else:
            self.target_type_counts = dict()

            for target_type in XcTarget.Type.AVAILABLES:
                targets = self.xcode_project.targets_of_type(target_type)

                if not targets:
                    self.target_type_counts[target_type] = (None, len(targets))
                    continue

                # Target type
                target_type_display = '{}s'.format(target_type.replace('_', ' ').capitalize())
                cprint('{} ({}):'.format(target_type_display, len(targets)), attrs=['bold'])

                # Targets
                for target in targets:
                    if verbose:
                        text = '- {} => {}'.format(target.name, target.product_name)
                    else:
                        text = '- {}'.format(target.name)
                    print(text)
                
                self.target_type_counts[target_type] = (target_type_display, len(targets))
    
    def print_targets_summary(self):
        # Targets summary
        self._print_horizontal_line()

        for target_type in XcTarget.Type.AVAILABLES:
            if self.target_type_counts[target_type][1]:
                print('{:>2} {}'.format(self.target_type_counts[target_type][1],
                                        self.target_type_counts[target_type][0]))
        cprint('{:>2} Targets in total'.format(len(self.xcode_project.targets)), attrs=['bold'])

    def print_files_by_targets(self):
        for target in self.xcode_project.targets_sorted_by_name:
            counters = [
                '{} source files'.format(len(target.source_files)),
                '{} resource files'.format(len(target.resource_files)),
                '{} header files'.format(len(target.header_files)),
            ]
            target_display = '{} [{}]:'.format(target.name, ', '.join(counters))
            cprint(target_display, attrs=['bold'])

            # Resource and source files of the target
            files = list(target.source_files) + list(target.resource_files) + list(target.header_files)

            filepaths = [f.filepath for f in files]
            filepaths.sort()
            for filepath in filepaths:
                print(filepath)
    
    def print_shared_files(self):
        # key is a file, value is a set of targets
        file_targets = dict()

        # Search targets for shared files
        for target in self.xcode_project.targets:
            for target_file in target.files:
                if target_file in file_targets:
                    file_targets[target_file].add(target)
                else:
                    file_targets[target_file] = set([target])

        # Filter files
        filepath_targets = {f.filepath: targets for (f, targets) in file_targets.items() if len(targets) >= 2}

        # Sort by filepath
        filepaths = [p for p in filepath_targets.keys()]
        filepaths.sort()

        # Sort displays
        for filepath in filepaths:
            targets = filepath_targets[filepath]
            targets_display = ', '.join([t.name for t in targets])
            print('{} [{}]'.format(filepath, targets_display))

    def print_files_summary(self):
        self._print_horizontal_line()

        source_files = set()
        resource_files = set()
        header_files = set()

        for target in self.xcode_project.targets:
            source_files |= target.source_files
            resource_files |= target.resource_files
            header_files |= target.header_files

        # Counter
        source_files_count = len(source_files)
        resource_files_count = len(resource_files)
        header_files_count = len(header_files)

        total_files_count = source_files_count + resource_files_count + header_files_count

        print('{:>2} Source files'.format(source_files_count))
        print('{:>2} Resource files'.format(resource_files_count))
        print('{:>2} Header files'.format(header_files_count))
        cprint('{:>2} Files in total'.format(total_files_count), attrs=['bold'])
    
    def print_groups(self, filter_mode=False):
        groups = self.xcode_project.groups_filtered(filter_mode=filter_mode)
        group_paths = [g.group_path for g in groups]

        group_paths.sort()

        for group_path in group_paths:
            print(group_path)
    
    def print_all_groups_summary(self):
        self._print_horizontal_line()

        groups = self.xcode_project.groups_filtered()

        # Total groups count
        total_groups_count = len(groups)

        # Root groups count
        root_groups_count = len(self.xcode_project.groups)
        variant_root_groups_count = len([g for g in self.xcode_project.groups if g.is_variant])

        # Non root groups count
        variant_groups_count = len([g for g in groups if g.is_variant]) - variant_root_groups_count
        other_groups_count = total_groups_count - root_groups_count - variant_groups_count

        print('{:>2} Root groups (whom {} variant)'.format(root_groups_count, variant_root_groups_count))
        print('{:>2} Variant groups'.format(variant_groups_count))
        print('{:>2} Other groups'.format(other_groups_count))
        cprint('{:>2} Groups in total'.format(total_groups_count), attrs=['bold'])
    
    def print_orphan_files(self, ignored_dirpaths, ignored_dirs, ignore_info_plist=False):
        # Folder's filepaths
        folder_filepaths = set()

        for (dirpath, dirnames, filenames) in os.walk(self.xcode_project.dirpath):
            relative_dirpath = dirpath[len(self.xcode_project.dirpath):]

            # Filter folder to ignore by path
            continue_to_next_dirpath = False
            for ignored_dirpath in ignored_dirpaths:
                if relative_dirpath.startswith(ignored_dirpath):
                    continue_to_next_dirpath = True
                    break
            if continue_to_next_dirpath:
                continue
                
            # Filter folder to ignore by name
            folder_parts = set(relative_dirpath.split(os.path.sep))
            if ignored_dirs & folder_parts:
                continue

            # Filter xcodeproj itself
            if '.xcodeproj' in relative_dirpath:
                continue
            
            # Filter xcworkspace
            if '.xcworkspace' in relative_dirpath:
                continue
            
            # Detect xcassets folders
            if relative_dirpath.endswith('.xcassets'):
                folder_filepaths.add(relative_dirpath)

            elif '.xcassets' in relative_dirpath:
                # Ignore Subfolder of a xcasset folder
                pass

            # Detect xcstickers folders
            elif relative_dirpath.endswith('.xcstickers'):
                folder_filepaths.add(relative_dirpath)

            elif '.xcstickers' in relative_dirpath:
                # Ignore Subfolder of a xcstickers folder
                pass

            else:
                ignored_files = {'.DS_Store'}
                if ignore_info_plist:
                    ignored_files.add('Info.plist')

                for filename in filenames:
                    if filename not in ignored_files:
                        folder_filepaths.add('{}/{}'.format(relative_dirpath, filename))
        
        # Targets' filepaths
        target_filepaths = {target_file.filepath for target_file in self.xcode_project.target_files}

        # Orphan filepaths
        filepaths = list(folder_filepaths - target_filepaths)
        filepaths.sort()

        for filepath in filepaths:
            print(filepath)
