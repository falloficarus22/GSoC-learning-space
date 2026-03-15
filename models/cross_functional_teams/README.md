# Cross-Functional Teams

## What this model does

This is a small organization model with two kinds of group structure:

- permanent departments
- temporary project teams

Each worker always belongs to one department and may also belong to a project
team. That makes it a good first learning model for Mesa's experimental
meta-agent support because the same worker can participate in multiple groups at
once.

The current version adds a few simple behaviors so the model exercises more than
static grouping:

- workers gain workload while assigned to a project
- workers recover energy when they are not on a project
- project teams make progress over time and dissolve when finished
- only workers with enough spare capacity are assigned to new projects

## Why I chose it

I am interested in Mesa's `meta_agents` direction, especially around how group
membership is represented and how that behavior would feel to a modeller using
it for real work. This model gives me a simple way to explore that without
starting with a very large simulation.

## Mesa features used

- core `Model` and `Agent`
- `DataCollector`
- experimental `MetaAgent`
- grouped behavior through permanent and temporary teams
- simple lifecycle changes for temporary groups

## What to look at

- [model.py](./model.py): defines workers, departments, and project teams
- [run.py](./run.py): runs a short smoke test and prints a summary

## Questions this model helps me explore

- How natural is it to model overlapping memberships with `MetaAgent`?
- Are lifecycle operations for temporary groups intuitive?
- How awkward is it to create, complete, and remove temporary teams?
- What happens to worker state when teams are repeatedly created and dissolved?
- Does the API make it clear when to use `meta_agent` vs `meta_agents`?
- What kind of documentation or examples would make this feature easier to use?

## How to run

From this folder:

```bash
python3 run.py
```
