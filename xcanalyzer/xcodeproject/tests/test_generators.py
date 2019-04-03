from unittest import TestCase

import os
import shutil

from .fixtures import XcModelsFixture, XcProjectGraphGeneratorFixture

from ..generators import XcProjectGraphGenerator
from ..models import XcTarget


class XcProjectGraphGeneratorTests(TestCase):

    fixture = XcProjectGraphGeneratorFixture()

    def tearDown(self):
        path = self.fixture.test_build_folder
        if os.path.exists(path):
            shutil.rmtree(path)

    # __init__

    def test_init_xc_project_graph_generator(self):
        project = XcModelsFixture().any_project()
        
        generator = XcProjectGraphGenerator(project)

        self.assertEqual(generator.xcode_project, project)
    
    # generate_targets_dependencies_graph

    def test_generate_targets_dependencies_graph__for_dependency_type_build(self):
        project = XcModelsFixture().any_project()
        generator = XcProjectGraphGenerator(project)
        filepath = self.fixture.any_graph_filepath('pdf_target_dependencies')

        generated = generator.generate_targets_dependencies_graph(filepath=filepath, title='title', dependency_type='build')

        graph_filepath = '{}.pdf'.format(filepath)
        self.assertEqual(generated, True)
        self.assertTrue(os.path.exists(graph_filepath))

    def test_generate_targets_dependencies_graph__for_dependency_type_linked(self):
        project = XcModelsFixture().any_project()
        generator = XcProjectGraphGenerator(project)
        filepath = self.fixture.any_graph_filepath('pdf_target_dependencies')

        generated = generator.generate_targets_dependencies_graph(filepath=filepath, title='title', dependency_type='linked')

        graph_filepath = '{}.pdf'.format(filepath)
        self.assertEqual(generated, True)
        self.assertTrue(os.path.exists(graph_filepath))

    def test_generate_targets_dependencies_graph__for_dependency_type_embed(self):
        project = XcModelsFixture().any_project()
        generator = XcProjectGraphGenerator(project)
        filepath = self.fixture.any_graph_filepath('pdf_target_dependencies')

        generated = generator.generate_targets_dependencies_graph(filepath=filepath, title='title', dependency_type='linked')

        graph_filepath = '{}.pdf'.format(filepath)
        self.assertEqual(generated, True)
        self.assertTrue(os.path.exists(graph_filepath))

    def test_generate_targets_dependencies_graph__for_png_format(self):
        project = XcModelsFixture().any_project()
        generator = XcProjectGraphGenerator(project)
        filepath = self.fixture.any_graph_filepath('png_target_dependencies')

        generated = generator.generate_targets_dependencies_graph(filepath=filepath, title='title', dependency_type='linked', output_format='png')

        graph_filepath = '{}.png'.format(filepath)
        self.assertEqual(generated, True)
        self.assertTrue(os.path.exists(graph_filepath))

    def test_generate_targets_dependencies_graph__only_for_a_target_type(self):
        project = XcModelsFixture().any_project()
        generator = XcProjectGraphGenerator(project)
        filepath = self.fixture.any_graph_filepath('png_framework_target_dependencies')
        including_types = {XcTarget.Type.FRAMEWORK}

        generated = generator.generate_targets_dependencies_graph(filepath=filepath, title='title', dependency_type='linked', including_types=including_types)

        graph_filepath = '{}.pdf'.format(filepath)
        self.assertEqual(generated, True)
        self.assertTrue(os.path.exists(graph_filepath))
