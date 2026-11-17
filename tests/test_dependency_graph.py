import unittest

from src.dependency_graph import GraphError, build_dependency_graph


class DependencyGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D", "E"],
            "D": ["F"],
            "E": [],
            "F": [],
        }

    def get_dependencies(self, package: str) -> list[str]:
        return self.repository[package]

    def test_builds_transitive_graph_in_breadth_first_order(self) -> None:
        graph = build_dependency_graph("A", self.get_dependencies, 3)
        self.assertEqual(list(graph), ["A", "B", "C", "D", "E", "F"])
        self.assertEqual(graph["A"], ["B", "C"])
        self.assertEqual(graph["C"], ["D", "E"])
        self.assertEqual(graph["D"], ["F"])

    def test_zero_depth_keeps_only_root(self) -> None:
        graph = build_dependency_graph("A", self.get_dependencies, 0)
        self.assertEqual(graph, {"A": []})

    def test_depth_one_keeps_direct_dependencies_only(self) -> None:
        graph = build_dependency_graph("A", self.get_dependencies, 1)
        self.assertEqual(
            graph,
            {"A": ["B", "C"], "B": [], "C": []},
        )

    def test_cycle_does_not_cause_infinite_traversal(self) -> None:
        cycle = {"A": ["B"], "B": ["C"], "C": ["A", "D"], "D": []}
        graph = build_dependency_graph("A", cycle.get, 10)
        self.assertEqual(graph["A"], ["B"])
        self.assertEqual(graph["B"], ["C"])
        self.assertEqual(graph["C"], ["A", "D"])
        self.assertEqual(set(graph), {"A", "B", "C", "D"})

    def test_filter_excludes_matching_packages_and_their_edges(self) -> None:
        graph = build_dependency_graph(
            "A",
            self.get_dependencies,
            5,
            package_filter="d",
        )
        self.assertEqual(graph["A"], ["B", "C"])
        self.assertEqual(graph["B"], [])
        self.assertEqual(graph["C"], ["E"])
        self.assertNotIn("D", graph)
        self.assertNotIn("F", graph)

    def test_duplicate_edges_are_removed(self) -> None:
        source = {"A": ["B", "B"], "B": []}
        graph = build_dependency_graph("A", source.get, 2)
        self.assertEqual(graph["A"], ["B"])

    def test_invalid_dependency_name_is_rejected(self) -> None:
        source = {"A": [""]}
        with self.assertRaises(GraphError):
            build_dependency_graph("A", source.get, 2)

    def test_negative_depth_is_rejected(self) -> None:
        with self.assertRaises(GraphError):
            build_dependency_graph("A", self.get_dependencies, -1)


if __name__ == "__main__":
    unittest.main()
