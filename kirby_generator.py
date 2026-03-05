#!/usr/bin/env python3
"""
Kirby Puzzle State Generator (Tiny Generator)

Generates starting states for a Kirby-inspired "ability chain" puzzle:
- Kirby can swallow enemies to copy abilities.
- Obstacles ("gates") require specific abilities to pass.
- The puzzle is solved by collecting abilities in the right order to reach Exit.

Run:
  python kirby_generator.py --count 12 --chain 3 --decoys 2 --mode linear
  python kirby_generator.py --count 10 --chain 3 --decoys 1 --mode two_required_final
"""

from __future__ import annotations
import argparse
import random
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional


# --- Ability / Gate mapping (edit freely) ------------------------------------

ABILITY_TO_GATE: Dict[str, str] = {
    "Bomb": "Cracked Wall",
    "Fire": "Rope / Wooden Block",
    "Cutter": "Vine / Distant Switch",
    "Ice": "Water Patch",
    "Spark": "Conductor Gate",
    "Stone": "Heavy Press Plate",
}

# Optional decoy "visual bait" obstacles that look meaningful but aren't on the main path
DECOY_OBSTACLES = [
    "Optional cracked wall (side path)",
    "Optional rope (side path)",
    "Optional vine (side path)",
    "Optional water patch (side path)",
    "Optional conductor panel (side path)",
    "Optional heavy plate (side path)",
]

# Flavor enemies that grant abilities (1:1)
ABILITY_TO_ENEMY: Dict[str, str] = {
    "Bomb": "Bomb Dude",
    "Fire": "Flame Buddy",
    "Cutter": "Blade Bug",
    "Ice": "Chilly",
    "Spark": "Sparkster",
    "Stone": "Rocky",
}


# --- Data model --------------------------------------------------------------

@dataclass(frozen=True)
class Gate:
    """A requirement to move forward."""
    requires: frozenset[str]  # ability set required
    obstacle_name: str        # visual label


@dataclass
class PuzzleState:
    """Abstract puzzle state: a path graph with gates and ability sources."""
    chain: List[str]                 # ordered abilities (linear chain) e.g. ["Cutter","Bomb","Fire"]
    final_requires: Set[str]         # what the final gate requires (usually {A_final} or two abilities)
    gates: List[Gate]                # gates along main path, in order
    ability_sources: Dict[int, str]  # node index -> ability granted at node
    decoy_enemies: List[str]
    decoy_obstacles: List[str]
    mode: str                        # "linear" or "two_required_final"


# --- Generator ---------------------------------------------------------------

def pick_ability(rng: random.Random, exclude: Set[str]) -> str:
    pool = [a for a in ABILITY_TO_GATE.keys() if a not in exclude]
    if not pool:
        raise ValueError("No abilities left to pick (expand ABILITY_TO_GATE).")
    return rng.choice(pool)


def generate_puzzle(
    rng: random.Random,
    chain_length: int,
    decoy_count: int,
    mode: str,
) -> PuzzleState:
    """
    Build a puzzle that is guaranteed solvable in the abstract model:
    - Ability source for each required gate appears before that gate.
    - Main path is Start -> Gate1 -> ... -> GateK -> Exit
    """
    if chain_length < 1:
        raise ValueError("chain_length must be >= 1")

    # 1) Choose abilities for the chain
    used: Set[str] = set()
    chain: List[str] = []
    for _ in range(chain_length):
        a = pick_ability(rng, used)
        chain.append(a)
        used.add(a)

    # 2) Determine final requirement
    if mode == "linear":
        final_requires = {chain[-1]}
    elif mode == "two_required_final":
        # Require last + one earlier ability (small DAG-ish dependency)
        if chain_length < 2:
            # If chain too short, fall back to linear
            final_requires = {chain[-1]}
            mode = "linear"
        else:
            final_requires = {chain[-1], rng.choice(chain[:-1])}
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # 3) Build main path gates
    # We'll create gates for each step that "teaches" moving forward:
    # - For i in [0..chain_length-2], gate requires chain[i] (to reach the next ability)
    # - Final gate requires final_requires (to reach Exit)
    gates: List[Gate] = []
    for i in range(chain_length - 1):
        req = frozenset([chain[i]])
        gates.append(Gate(requires=req, obstacle_name=ABILITY_TO_GATE[chain[i]]))

    # Final gate
    # If two_required_final, show a combined obstacle label for readability
    if len(final_requires) == 1:
        only = next(iter(final_requires))
        obstacle_name = ABILITY_TO_GATE[only] + " (Final)"
    else:
        # Combine two obstacle labels for the final gate
        parts = [ABILITY_TO_GATE[a] for a in sorted(final_requires)]
        obstacle_name = " + ".join(parts) + " (Final)"
    gates.append(Gate(requires=frozenset(final_requires), obstacle_name=obstacle_name))

    # 4) Place ability sources (guarantee solvable):
    # Node indices: 0 = Start room, 1 = after Gate1, 2 = after Gate2, ...
    # Put chain[0] at node 0; chain[1] at node 1; ...
    ability_sources: Dict[int, str] = {i: chain[i] for i in range(chain_length)}

    # 5) Add decoys (enemies + obstacles), not required for the main path
    decoy_pool = [a for a in ABILITY_TO_GATE.keys() if a not in used]
    rng.shuffle(decoy_pool)
    chosen_decoys = decoy_pool[:max(0, decoy_count)]

    decoy_enemies = [ABILITY_TO_ENEMY[a] + f" -> {a}" for a in chosen_decoys]
    rng.shuffle(DECOY_OBSTACLES)
    decoy_obstacles = DECOY_OBSTACLES[:max(0, decoy_count)]

    return PuzzleState(
        chain=chain,
        final_requires=set(final_requires),
        gates=gates,
        ability_sources=ability_sources,
        decoy_enemies=decoy_enemies,
        decoy_obstacles=decoy_obstacles,
        mode=mode,
    )


# --- Solver (Optional Challenge A: solvability proof) -------------------------

def is_solvable(p: PuzzleState) -> Tuple[bool, Optional[List[int]]]:
    """
    Abstract BFS solver on the main path.
    State: (node_index, abilities_owned)
    - At each node, Kirby can swallow the ability source (if present) and gain that ability.
    - Kirby can traverse gate i from node i to node i+1 if abilities_owned includes gate.requires.

    Returns (solvable, path_nodes) where path_nodes is a list of node indices visited.
    """
    # nodes: 0..len(gates)  (after final gate you are at Exit node)
    exit_node = len(p.gates)

    def apply_pickup(node: int, abilities: frozenset[str]) -> frozenset[str]:
        if node in p.ability_sources:
            return frozenset(set(abilities) | {p.ability_sources[node]})
        return abilities

    start_abilities = apply_pickup(0, frozenset())
    start = (0, start_abilities)

    queue: List[Tuple[int, frozenset[str]]] = [start]
    parent: Dict[Tuple[int, frozenset[str]], Optional[Tuple[int, frozenset[str]]]] = {start: None}

    while queue:
        node, abilities = queue.pop(0)
        if node == exit_node:
            # reconstruct node path (ignore ability set changes for brevity)
            rev: List[int] = []
            cur = (node, abilities)
            while cur is not None:
                rev.append(cur[0])
                cur = parent[cur]
            rev.reverse()
            return True, rev

        # Try to pass gate at this node (gate index == node)
        gate = p.gates[node]
        if gate.requires.issubset(set(abilities)):
            next_node = node + 1
            next_abilities = apply_pickup(next_node, abilities)
            nxt = (next_node, next_abilities)
            if nxt not in parent:
                parent[nxt] = (node, abilities)
                queue.append(nxt)

    return False, None


# --- Difficulty tags (Optional Challenge B) ----------------------------------

def difficulty_tag(p: PuzzleState, chain_length: int, decoy_count: int) -> str:
    """
    Simple heuristic: longer chains and two-required final gates are harder.
    Decoys increase apparent complexity; we reflect that slightly.
    """
    score = chain_length
    if p.mode == "two_required_final" and len(p.final_requires) >= 2:
        score += 1
    if decoy_count >= 2:
        score += 1

    if score <= 2:
        return "Easy"
    if score <= 4:
        return "Medium"
    return "Hard"


# --- Pretty printing ---------------------------------------------------------

def format_puzzle(p: PuzzleState, idx: int, chain_length: int, decoy_count: int) -> str:
    solvable, path_nodes = is_solvable(p)
    diff = difficulty_tag(p, chain_length, decoy_count)

    lines: List[str] = []
    lines.append(f"Puzzle #{idx:02d}  |  mode={p.mode}  |  chain_length={chain_length}  |  decoys={decoy_count}  |  tag={diff}")
    lines.append("-" * 78)
    # Path description
    path = ["Start"]
    for i, g in enumerate(p.gates, start=1):
        req = " + ".join(sorted(g.requires))
        path.append(f"Gate{i}[{req}]")
    path.append("Exit")
    lines.append("Path: " + " -> ".join(path))

    # Gate detail
    lines.append("Gates:")
    for i, g in enumerate(p.gates, start=1):
        req = ", ".join(sorted(g.requires))
        lines.append(f"  - Gate{i}: requires {{{req}}}  |  obstacle='{g.obstacle_name}'")

    # Ability sources
    lines.append("Ability Sources (node index -> enemy -> ability):")
    for node in sorted(p.ability_sources.keys()):
        a = p.ability_sources[node]
        enemy = ABILITY_TO_ENEMY.get(a, "Enemy")
        lines.append(f"  - Node {node}: {enemy} -> {a}")

    # Decoys
    if p.decoy_enemies or p.decoy_obstacles:
        lines.append("Decoys (red herrings):")
        for d in p.decoy_enemies:
            lines.append(f"  - Decoy Enemy: {d}")
        for o in p.decoy_obstacles:
            lines.append(f"  - Decoy Obstacle: {o}")

    # Solvability proof result
    lines.append(f"Solvable (BFS on abstract graph): {solvable}")
    if solvable and path_nodes is not None:
        lines.append(f"One solution path (nodes): {path_nodes}")

    lines.append("")  # blank line between puzzles
    return "\n".join(lines)


# --- Main --------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Kirby Ability-Chain Puzzle State Generator")
    parser.add_argument("--count", type=int, default=10, help="How many puzzle states to generate (>=10 recommended).")
    parser.add_argument("--chain", type=int, default=3, help="Ability chain length (>=1). Controls structure complexity.")
    parser.add_argument("--decoys", type=int, default=1, help="Number of decoy enemies/obstacles (>=0). Controls misdirection.")
    parser.add_argument("--mode", choices=["linear", "two_required_final"], default="linear",
                        help="Puzzle structure mode. 'two_required_final' creates a final gate needing 2 abilities (DAG-ish).")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible output.")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    # Generate + print
    for i in range(1, args.count + 1):
        p = generate_puzzle(
            rng=rng,
            chain_length=args.chain,
            decoy_count=args.decoys,
            mode=args.mode,
        )
        print(format_puzzle(p, i, args.chain, args.decoys))


if __name__ == "__main__":
    main()