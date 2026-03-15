"""A small organization model for exploring overlapping group memberships.

Workers belong to a permanent department and may also belong to a temporary
project team. This makes it a useful learning model for Mesa's experimental
meta-agent support because agents can belong to more than one group at once.
"""

from __future__ import annotations

from statistics import mean

from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.experimental.meta_agents.meta_agent import MetaAgent


class WorkerAgent(Agent):
    """A worker with a home department and optional project assignment."""

    def __init__(self, model: "CrossFunctionalTeamsModel", department: str, skill: int):
        super().__init__(model)
        self.department = department
        self.skill = skill
        self.workload = 0
        self.energy = 5
        self.completed_projects = 0
        self.project_name: str | None = None

    def step(self) -> None:
        """Update a worker's state based on project participation."""
        self.workload = max(0, self.workload - 1)

        if self.project_name is not None:
            self.workload += 2
            self.energy = max(0, self.energy - 1)
        else:
            self.workload += 1
            self.energy = min(6, self.energy + 1)

        # Overloaded workers lose a bit of capacity even if they are not
        # currently assigned to a project.
        if self.workload >= 4:
            self.energy = max(0, self.energy - 1)


class Department(MetaAgent):
    """Permanent grouping for workers from the same department."""


class ProjectTeam(MetaAgent):
    """Temporary grouping used for cross-functional work."""

    def __init__(self, model, agents, name: str = "ProjectTeam", target_progress: int = 12):
        super().__init__(model, agents, name=name)
        self.progress = 0.0
        self.target_progress = target_progress
        self.active_steps = 0

    @property
    def department_count(self) -> int:
        return len({worker.department for worker in self.agents})

    def advance(self) -> bool:
        """Advance project work and report whether the team is finished."""
        workers = list(self.agents)
        if not workers:
            return True

        average_skill = mean(worker.skill for worker in workers)
        average_energy = mean(worker.energy for worker in workers)
        collaboration_bonus = 1 + (0.15 * max(0, self.department_count - 1))

        self.progress += (average_skill + average_energy) * collaboration_bonus / 3
        self.active_steps += 1
        return self.progress >= self.target_progress


class CrossFunctionalTeamsModel(Model):
    """Organization model with permanent departments and rotating project teams."""

    def __init__(
        self,
        num_departments: int = 3,
        workers_per_department: int = 4,
        project_team_size: int = 3,
        active_projects: int = 2,
        project_refresh_interval: int = 2,
        rng=None,
    ) -> None:
        super().__init__(rng=rng)
        self.num_departments = num_departments
        self.workers_per_department = workers_per_department
        self.project_team_size = project_team_size
        self.active_projects = active_projects
        self.project_refresh_interval = project_refresh_interval

        self.workers: list[WorkerAgent] = []
        self.departments: list[Department] = []
        self.project_teams: list[ProjectTeam] = []
        self.completed_project_count = 0
        self.project_counter = 0

        self.datacollector = DataCollector(
            model_reporters={
                "workers": lambda m: len(m.workers),
                "department_count": lambda m: len(m.departments),
                "project_team_count": lambda m: len(m.project_teams),
                "completed_project_count": lambda m: m.completed_project_count,
                "workers_with_multiple_groups": lambda m: m.workers_with_multiple_groups,
                "average_workload": lambda m: round(m.average_workload, 2),
                "average_energy": lambda m: round(m.average_energy, 2),
                "overloaded_workers": lambda m: m.overloaded_workers,
                "cross_department_projects": lambda m: m.cross_department_projects,
            }
        )

        self._create_workers()
        self._create_departments()
        self._fill_projects()
        self.datacollector.collect(self)

    def _create_workers(self) -> None:
        for department_idx in range(self.num_departments):
            department_name = f"Department-{department_idx + 1}"
            for _ in range(self.workers_per_department):
                skill = self.random.randint(1, 5)
                self.workers.append(WorkerAgent(self, department_name, skill))

    def _create_departments(self) -> None:
        for department_name in sorted({worker.department for worker in self.workers}):
            members = {worker for worker in self.workers if worker.department == department_name}
            self.departments.append(Department(self, members, name=department_name))

    def _clear_projects(self) -> None:
        for team in self.project_teams:
            members = set(team.agents)
            for worker in members:
                worker.project_name = None
            team.remove_constituting_agents(members)
            team.remove()
        self.project_teams = []

    def _fill_projects(self) -> None:
        if self.project_team_size <= 0 or self.active_projects <= 0:
            return

        available_workers = [
            worker
            for worker in self.workers
            if worker.project_name is None and worker.energy >= 2 and worker.workload <= 3
        ]
        self.random.shuffle(available_workers)

        missing_projects = max(0, self.active_projects - len(self.project_teams))
        for project_idx in range(missing_projects):
            if len(available_workers) < self.project_team_size:
                break

            members: list[WorkerAgent] = []
            departments_used: set[str] = set()

            # Prefer cross-department teams so we can observe overlapping structure.
            for worker in list(available_workers):
                if worker.department in departments_used and len(departments_used) < self.num_departments:
                    continue
                members.append(worker)
                departments_used.add(worker.department)
                available_workers.remove(worker)
                if len(members) == self.project_team_size:
                    break

            if len(members) < self.project_team_size:
                while available_workers and len(members) < self.project_team_size:
                    members.append(available_workers.pop())

            if len(members) < self.project_team_size:
                break

            self.project_counter += 1
            project_name = f"Project-{self.project_counter}"
            for worker in members:
                worker.project_name = project_name

            target_progress = self.random.randint(7, 11)
            self.project_teams.append(
                ProjectTeam(
                    self,
                    set(members),
                    name=project_name,
                    target_progress=target_progress,
                )
            )

    def _complete_project(self, team: ProjectTeam) -> None:
        members = set(team.agents)
        for worker in members:
            worker.completed_projects += 1
            worker.project_name = None
            worker.energy = min(6, worker.energy + 1)

        team.remove_constituting_agents(members)
        team.remove()
        self.project_teams.remove(team)
        self.completed_project_count += 1

    def _advance_projects(self) -> None:
        completed_teams = [team for team in list(self.project_teams) if team.advance()]
        for team in completed_teams:
            self._complete_project(team)

    @property
    def workers_with_multiple_groups(self) -> int:
        return sum(
            1 for worker in self.workers if len(getattr(worker, "meta_agents", set())) > 1
        )

    @property
    def average_workload(self) -> float:
        return mean(worker.workload for worker in self.workers) if self.workers else 0.0

    @property
    def average_energy(self) -> float:
        return mean(worker.energy for worker in self.workers) if self.workers else 0.0

    @property
    def overloaded_workers(self) -> int:
        return sum(1 for worker in self.workers if worker.workload >= 4)

    @property
    def cross_department_projects(self) -> int:
        return sum(
            1
            for team in self.project_teams
            if len({worker.department for worker in team.agents}) > 1
        )

    def step(self) -> None:
        self.agents_by_type[WorkerAgent].shuffle_do("step")
        self._advance_projects()

        if self.project_refresh_interval > 0 and int(self.time) % self.project_refresh_interval == 0:
            self._fill_projects()

        self.datacollector.collect(self)


def model_summary(model: CrossFunctionalTeamsModel) -> dict[str, float | int]:
    """Return a compact summary that is handy in quick smoke tests."""
    latest = model.datacollector.get_model_vars_dataframe().iloc[-1]
    return {
        "workers": int(latest["workers"]),
        "department_count": int(latest["department_count"]),
        "project_team_count": int(latest["project_team_count"]),
        "completed_project_count": int(latest["completed_project_count"]),
        "workers_with_multiple_groups": int(latest["workers_with_multiple_groups"]),
        "average_workload": float(latest["average_workload"]),
        "average_energy": float(latest["average_energy"]),
        "overloaded_workers": int(latest["overloaded_workers"]),
        "cross_department_projects": int(latest["cross_department_projects"]),
    }
