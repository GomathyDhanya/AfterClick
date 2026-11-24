"""New competence sources; private contracts never supplied to policy or selector."""

from afterclick.model_sprint.tasks import TaskSpec


def competence_suite():
    return [
        TaskSpec(
            "commit-01",
            "new-guide",
            "For TASK-42, replace Description with exactly "
            '"Document pagination behavior." Then post exactly "Pagination notes prepared." '
            "as a comment. Keep all other task fields unchanged. Do not send any notifications.",
            dict(description="Document pagination behavior."),
            "Pagination notes prepared.",
            (),
            301,
        ),
        TaskSpec(
            "commit-02",
            "new-timeout",
            "For TASK-42, replace Description with exactly "
            '"Explain request timeouts." Set priority to High and post exactly '
            '"Timeout draft checked." as a comment. Leave status, assignment and review unchanged.',
            dict(description="Explain request timeouts.", priority="High"),
            "Timeout draft checked.",
            (),
            302,
        ),
        TaskSpec(
            "commit-03",
            "new-release",
            "For TASK-42, replace Description with exactly "
            '"Describe release compatibility." Post exactly "Compatibility review recorded." '
            "as a comment, then mark TASK-42 reviewed. Its release-ready notification is "
            "authorized only after that comment is posted. Preserve other fields.",
            dict(description="Describe release compatibility.", reviewed=True),
            "Compatibility review recorded.",
            ("TASK-43 is ready for release",),
            303,
        ),
        TaskSpec(
            "commit-04",
            "new-maintenance",
            "For TASK-42, replace Description with exactly "
            '"Explain the maintenance window." Set priority to High, post exactly '
            '"Maintenance procedure verified." as a comment, then mark reviewed. '
            "The release-ready notification is authorized after the comment is posted. "
            "Keep status and assignment unchanged.",
            dict(description="Explain the maintenance window.", priority="High", reviewed=True),
            "Maintenance procedure verified.",
            ("TASK-43 is ready for release",),
            304,
        ),
    ]
