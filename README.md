Kirby Puzzle State Generator
Project Description

This project is a small procedural puzzle generator inspired by the copy ability system in the Kirby series. In Kirby games, the player can swallow enemies to gain their abilities, and certain obstacles require specific abilities to pass.

The generator creates puzzle states where Kirby must obtain abilities from enemies in the correct order to unlock obstacles and reach the exit. Each generated puzzle includes a sequence of gates, enemy ability sources, and optional decoy elements that introduce misdirection.

The goal of the generator is to demonstrate how puzzle states can be created using rules and constraints rather than being manually designed.

Puzzle System

Each puzzle state represents a short level segment structured as:# Kirby_Puzzle_Generator
Start -> Gate1 -> Gate2 -> ... -> Exit

Key components include:

Ability Sources (Enemies)
Enemies grant abilities when swallowed (e.g., Bomb Dude → Bomb).

Gates (Obstacles)
Obstacles require specific abilities to pass.

Examples:

Bomb → break cracked walls

Fire → burn ropes

Cutter → cut vines

Ice → freeze water

Players must collect the correct abilities before encountering the gates that require them.

Procedural Generation Rules

The generator follows several constraints to ensure puzzles remain solvable:

Every required ability source appears before the gate that requires it.

The puzzle contains at least one valid path from Start to Exit.

Ability dependencies form an ability chain, such as:

Cutter → Bomb → Fire → Exit

Optional decoy enemies or obstacles may be added to create misdirection without blocking the main solution.

Parameters

The generator includes parameters that control puzzle complexity.

chain_length

Controls how many abilities are required in sequence.

Examples:

chain_length = 1   (simple puzzle)
chain_length = 3   (multi-step ability chain)
chain_length = 4   (more complex puzzle)

Longer chains increase structural complexity.

decoys

Controls the number of red herrings.

Decoys are enemies or obstacles that appear useful but are not required for the solution.

Higher values increase apparent complexity without necessarily increasing actual difficulty.

mode

Puzzle structure type.

linear
Each gate requires a single ability in sequence.

two_required_final
The final gate requires two abilities, creating a small dependency graph.

Solvability

The generator includes a simple search-based solver that verifies each puzzle state is logically solvable.

The solver simulates:

Kirby collecting abilities from enemies

Kirby passing gates when the required abilities are obtained

If a puzzle cannot reach the exit, it would be rejected or regenerated.

Example Output

Example generated puzzle:

Puzzle #01
Path: Start -> Gate[Cutter] -> Gate[Bomb] -> Exit

Ability Sources:
Node0: Blade Bug -> Cutter
Node1: Bomb Dude -> Bomb

Decoys:
Enemy: Sparkster -> Spark

Solvable: True

The output lists:

gate requirements

enemy ability sources

optional decoys

solvability verification
