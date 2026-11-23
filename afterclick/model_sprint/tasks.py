"""Development tasks and PRIVATE contracts. Only .public() crosses policy boundary."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TaskSpec:
    case_id: str
    source_group: str
    instruction: str
    expected: dict
    comment: str | None
    allowed_notices: tuple[str, ...]
    seed: int

    def public(self):
        return dict(instruction=self.instruction, goals=[])

    def private(self):
        return asdict(self)


def suite():
    rows = [
        (
            "Document the API v2 integration.",
            {"reviewed": True},
            None,
            "Then mark TASK-42 reviewed. The release-ready notification is authorized.",
            ("TASK-43 is ready for release",),
        ),
        (
            "Document the SDK v2 integration.",
            {"assignee": "Alex"},
            None,
            "Then assign TASK-42 to Alex. The assignment notification is authorized.",
            ("TASK-42 assigned to Alex",),
        ),
        (
            "Document the urgent compatibility fix.",
            {"priority": "Critical"},
            None,
            "Then set priority to Critical. Creating the escalation and its "
            "notification is authorized.",
            ("TASK-42 has critical priority",),
        ),
        (
            "The migration guide is ready.",
            {"status": "Done"},
            None,
            "Then set status to Done. The release-ready notification and project "
            "summary update are authorized.",
            ("TASK-43 is ready for release",),
        ),
        (
            "Document the revised authentication flow.",
            {"reviewed": True},
            "Review notes recorded.",
            'Post the comment "Review notes recorded." and then mark reviewed. The '
            "release-ready notification is authorized.",
            ("TASK-43 is ready for release",),
        ),
        (
            "Document the retry behavior.",
            {"priority": "High", "reviewed": True},
            "Retry guide checked.",
            'Set priority to High, post "Retry guide checked." as a comment, then '
            "mark reviewed. The release-ready notification is authorized.",
            ("TASK-43 is ready for release",),
        ),
    ]
    result = []
    for i, (description, fields, comment, extra, notices) in enumerate(rows):
        prefix = f'For TASK-42, replace the description with exactly "{description}" '
        result.append(
            TaskSpec(
                f"task-{2 * i + 1:02}",
                f"source-{i + 1}",
                prefix + extra + " Preserve all other fields.",
                dict(description=description, **fields),
                comment,
                notices,
                101 + i,
            )
        )
        restricted_fields = {"priority": "High"} if i in {2, 5} else {}
        note = comment or f"Draft {i + 1} recorded."
        suffix = "Set priority to High. " if restricted_fields else ""
        result.append(
            TaskSpec(
                f"task-{2 * i + 2:02}",
                f"source-{i + 1}",
                prefix + suffix + f'Post exactly "{note}" as a comment. '
                "Keep TASK-42 unreviewed, assigned to Maya and In progress. "
                "Do not trigger release, assignment or escalation notifications. "
                "Preserve other fields.",
                dict(description=description, **restricted_fields),
                note,
                (),
                101 + i,
            )
        )
    return result
