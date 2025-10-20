# -*- coding: utf-8 -*-
import math
from copy import deepcopy
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set, TypedDict

# Define a type for the dictionary that represents a route evaluation
class RouteEvaluation(TypedDict):
    score: float
    inputs: Dict[str, float]
    outputs: Dict[str, float]
    byproducts: Dict[str, float]
    available_after_route: Dict[str, float]
    index: int
    children_nodes: List["Node"]
    actual_produced_by_recipe: float
    recipe_inputs: Dict[str, float]
    recipe_outputs: Dict[str, float]
    intermediates: Dict[str, float]


from models import Node
from recipe_manager import RecipeManager, RouteInfo

EPSILON = 1e-9
# Weight for route scoring. Prioritizes routes with fewer base resources over fewer recipe steps.
BASE_RESOURCE_COST_WEIGHT = 1000

class ResourceCalculator:
    """
    Performs the core calculation of resolving a list of required items
    into a list of base resources and intermediate products.
    """
    def __init__(self, recipe_manager: RecipeManager):
        self.recipe_manager = recipe_manager

    def calculate(
        self,
        items: List[Tuple[str, float]],
        initial_available_resources: Dict[str, float]
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float], List[Node]]:
        """
        Calculates the resources needed for a list of items.

        Returns:
            Tuple containing:
            - aggregated_inputs: Total base resources required.
            - aggregated_outputs: Total final products produced (matching requested items).
            - final_available_resources: Resources remaining/produced after calculation.
            - aggregated_intermediates: Intermediate products crafted and consumed.
            - tree_roots: List of root nodes for the recipe trees.
        """
        available_resources: defaultdict[str, float] = defaultdict(float, initial_available_resources)
        aggregated_inputs: defaultdict[str, float] = defaultdict(float)  # Tracks total base resources needed
        aggregated_outputs: defaultdict[str, float] = defaultdict(float) # Tracks successfully produced requested items
        aggregated_intermediates: defaultdict[str, float] = defaultdict(float) # Tracks items crafted and consumed as part of a larger recipe
        tree_roots: List[Node] = []

        current_overall_available_resources: Dict[str, float] = deepcopy(available_resources)
        for item_name, item_qty in items:
            inputs_for_item, outputs_for_item, _, resources_after_item_calc, top_node, intermediates_for_item = self._resolve_item(
                item_name, item_qty, current_overall_available_resources,
                processing=set(), dependency_chain=[], depth=0
            )
            tree_roots.append(top_node)

            current_overall_available_resources = resources_after_item_calc
            for resource, amount in inputs_for_item.items():
                aggregated_inputs[resource] += amount
            for resource, amount in outputs_for_item.items():
                aggregated_outputs[resource] += amount
            for resource, amount in intermediates_for_item.items():
                aggregated_intermediates[resource] += amount

        final_inputs = {k: v for k, v in aggregated_inputs.items() if v > EPSILON}
        final_outputs = {k: v for k, v in aggregated_outputs.items() if v > EPSILON}
        final_available_resources = {k: v for k, v in current_overall_available_resources.items() if v > EPSILON}
        final_intermediates = {k: v for k, v in aggregated_intermediates.items() if v > EPSILON}

        return final_inputs, final_outputs, final_available_resources, final_intermediates, tree_roots

    def _resolve_item(
        self,
        item: str,
        qty: float,
        current_available_resources: Dict[str, float],
        processing: Set[str], # Set of items currently being processed in the recursion stack (for loop detection)
        dependency_chain: List[str], # List of items in the current dependency chain (for debugging/info)
        depth: int = 0
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float], Node, Dict[str, float]]:
        """
        Recursively calculates resources for a given item and quantity.
        """
        current_node = Node(item, qty, depth)
        aggregated_intermediates: defaultdict[str, float] = defaultdict(float)

        if qty <= EPSILON:
            current_node.source = "zero_needed"
            return defaultdict(float), defaultdict(float), defaultdict(float), current_available_resources, current_node, aggregated_intermediates

        if item in processing:
            current_node.source = "unresolved_loop"
            return {item: qty}, defaultdict(float), defaultdict(float), current_available_resources.copy(), current_node, aggregated_intermediates

        # --- Step 1: Use from Stock ---
        qty_after_stock, resources_after_stock_use = self._use_from_stock(item, qty, current_available_resources, current_node, depth)

        # --- Step 2: Crafting / Base Resource ---
        call_inputs: defaultdict[str, float] = defaultdict(float)
        call_outputs: defaultdict[str, float] = defaultdict(float)
        call_byproducts: defaultdict[str, float] = defaultdict(float)

        if qty_after_stock <= EPSILON:
            if not current_node.source or current_node.source == "unknown":
                current_node.source = "stock_only"
            call_outputs[item] += current_node.produced
            return call_inputs, call_outputs, call_byproducts, resources_after_stock_use, current_node, aggregated_intermediates

        new_processing = processing.copy()
        new_processing.add(item)
        new_dependency_chain = dependency_chain + [item]

        best_route_info = self._find_best_route(item, qty_after_stock, resources_after_stock_use, new_processing, new_dependency_chain, depth)

        if best_route_info:
            for res, amount in best_route_info["inputs"].items():
                call_inputs[res] += amount
            for res, amount in best_route_info["outputs"].items():
                call_outputs[res] += amount
            for res, amount in best_route_info["byproducts"].items():
                call_byproducts[res] += amount
            for res, amount in best_route_info["intermediates"].items():
                aggregated_intermediates[res] += amount

            resources_after_fulfillment = defaultdict(float, best_route_info["available_after_route"])

            current_node.source = f"recipe_{best_route_info['index']}"
            current_node.recipe_details = (best_route_info['recipe_inputs'], best_route_info['recipe_outputs'])
            current_node.produced += best_route_info["outputs"].get(item, 0)
            current_node.actual_produced_by_recipe = best_route_info["actual_produced_by_recipe"]
            current_node.children.extend(best_route_info["children_nodes"])

        else: # No viable recipe route found
            if item in self.recipe_manager.get_base_resources():
                current_node.source = "base"
                current_node.produced += qty_after_stock
                current_node.actual_produced_by_recipe = qty_after_stock
                call_inputs[item] += qty_after_stock
                call_outputs[item] += qty_after_stock
                resources_after_fulfillment = defaultdict(float, resources_after_stock_use)
            else:
                current_node.source = "missing_recipe_or_base"
                call_inputs[item] += qty_after_stock
                resources_after_fulfillment = defaultdict(float, resources_after_stock_use)

        if item not in self.recipe_manager.get_base_resources() and \
            current_node.source.startswith("recipe_") and \
            current_node.produced > EPSILON and \
            depth > 0:
            aggregated_intermediates[item] += current_node.produced

        return call_inputs, call_outputs, call_byproducts, dict(resources_after_fulfillment), current_node, aggregated_intermediates

    def _use_from_stock(self, item: str, qty: float, available: Dict[str, float], node: Node, depth: int) -> Tuple[float, Dict[str, float]]:
        """Checks for and uses available items from stock."""
        available_after_use = deepcopy(available)
        available_in_stock = available.get(item, 0)
        used_from_stock = min(available_in_stock, qty)

        if used_from_stock > EPSILON:
            available_after_use[item] -= used_from_stock
            qty -= used_from_stock

            stock_node = Node(item, used_from_stock, depth + 1)
            stock_node.source = "stock"
            stock_node.produced = used_from_stock
            node.add_child(stock_node)
            node.produced += used_from_stock
        
        return qty, available_after_use

    def _find_best_route(self, item: str, qty: float, available_resources: Dict[str, float], processing: Set[str], dependency_chain: List[str], depth: int) -> Optional[RouteEvaluation]:
        possible_routes = self.recipe_manager.find_recipes_for(item)
        if not possible_routes:
            return None

        all_evaluated_route_results: List[RouteEvaluation] = []
        for route_info in possible_routes:
            evaluation = self._evaluate_route(route_info, item, qty, available_resources, processing, dependency_chain, depth)
            if evaluation:
                all_evaluated_route_results.append(evaluation)

        if not all_evaluated_route_results:
            return None

        return min(all_evaluated_route_results, key=lambda x: x["score"])

    def _evaluate_route(self, route_info: RouteInfo, item: str, qty: float, available_resources: Dict[str, float], processing: Set[str], dependency_chain: List[str], depth: int) -> Optional[RouteEvaluation]:
        recipe_index = route_info["index"]
        recipe_inputs_template = route_info["inputs"]
        recipe_outputs_template = route_info["outputs"]

        route_total_inputs_needed: defaultdict[str, float] = defaultdict(float)
        route_total_byproducts_generated: defaultdict[str, float] = defaultdict(float)
        route_children_nodes: List[Node] = []
        num_sub_recipe_steps = 0
        sub_intermediates_agg: defaultdict[str, float] = defaultdict(float)

        if item not in recipe_outputs_template or recipe_outputs_template[item] <= EPSILON:
            return None

        recipe_output_qty_per_run = recipe_outputs_template[item]
        scale_factor = math.ceil(qty / recipe_output_qty_per_run)
        current_resources_for_this_route = deepcopy(available_resources)

        for input_item, input_qty_per_recipe in recipe_inputs_template.items():
            required_qty_for_input_item = input_qty_per_recipe * scale_factor

            sub_inputs, _, sub_byproducts, resources_after_sub_call, sub_node, sub_intermediates = self._resolve_item(
                input_item, required_qty_for_input_item, current_resources_for_this_route,
                processing, dependency_chain, depth + 1
            )
            current_resources_for_this_route = resources_after_sub_call

            if input_item in sub_inputs and input_item not in self.recipe_manager.get_base_resources():
                if sub_inputs[input_item] >= required_qty_for_input_item - EPSILON:
                    return None # Route is not viable

            for res, amount in sub_inputs.items():
                route_total_inputs_needed[res] += amount
            for res, amount in sub_byproducts.items():
                route_total_byproducts_generated[res] += amount
            for res, amount in sub_intermediates.items():
                sub_intermediates_agg[res] += amount
            route_children_nodes.append(sub_node)

            if any(n.source.startswith("recipe_") for n in sub_node.children) or sub_node.source.startswith("recipe_"):
                num_sub_recipe_steps += 1

        actual_produced_target_item_qty = recipe_output_qty_per_run * scale_factor
        used_target_item_qty = qty

        excess_target_item_qty = actual_produced_target_item_qty - used_target_item_qty
        if excess_target_item_qty > EPSILON:
            route_total_byproducts_generated[item] += excess_target_item_qty

        for output_item, output_qty_per_recipe in recipe_outputs_template.items():
            if output_item != item:
                produced_byproduct_qty = output_qty_per_recipe * scale_factor
                if produced_byproduct_qty > EPSILON:
                    route_total_byproducts_generated[output_item] += produced_byproduct_qty

        final_resource_state_for_this_route: defaultdict[str, float] = defaultdict(float, available_resources)

        for res, amount in route_total_inputs_needed.items():
            if res in self.recipe_manager.get_base_resources():
                final_resource_state_for_this_route[res] -= amount
                if final_resource_state_for_this_route[res] < EPSILON:
                    final_resource_state_for_this_route[res] = 0

        for res, amount in route_total_byproducts_generated.items():
            final_resource_state_for_this_route[res] += amount

        final_resource_state_for_this_route = defaultdict(float, {
            k: v for k, v in final_resource_state_for_this_route.items() if v > EPSILON
        })

        route_score = (sum(route_total_inputs_needed.values()) * BASE_RESOURCE_COST_WEIGHT) + num_sub_recipe_steps

        return {
            "score": route_score,
            "inputs": route_total_inputs_needed,
            "outputs": {item: used_target_item_qty},
            "byproducts": route_total_byproducts_generated,
            "available_after_route": dict(final_resource_state_for_this_route),
            "index": recipe_index,
            "children_nodes": route_children_nodes,
            "actual_produced_by_recipe": actual_produced_target_item_qty,
            "recipe_inputs": recipe_inputs_template,
            "recipe_outputs": recipe_outputs_template,
            "intermediates": sub_intermediates_agg
        }
