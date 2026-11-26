"""Logistic task-random-intercept sensitivity fit by normal quadrature.

Primary inference remains the paired source-cluster contrast. Separated arms
are explicitly unidentifiable rather than assigned fabricated finite estimates.
"""

import numpy as np
from numpy.polynomial.hermite import hermgauss
from scipy.optimize import minimize
from scipy.special import expit, logsumexp


def objective(theta, groups, nodes, weights):
    beta, log_sigma = theta[:-1], theta[-1]
    offsets = np.sqrt(2) * np.exp(log_sigma) * nodes
    value = 0.0
    gradient = np.zeros_like(theta)
    for x, y in groups:
        eta = (x @ beta)[:, None] + offsets[None, :]
        ll = (y[:, None] * eta - np.logaddexp(0, eta)).sum(axis=0) + np.log(
            weights / np.sqrt(np.pi)
        )
        marginal = logsumexp(ll)
        posterior = np.exp(ll - marginal)
        residual = y[:, None] - expit(eta)
        value -= marginal
        gradient[:-1] -= x.T @ (residual @ posterior)
        gradient[-1] -= np.sum(residual.sum(axis=0) * posterior * offsets)
    return value, gradient


def fit(table, contracts):
    data = [
        r
        for r in table
        if not r.get("clean")
        and r["policy"] in {"P0", "P1", "P2", "P3"}
        and r["joint_safe_completion"] is not None
    ]
    arms = {
        a: [int(r["joint_safe_completion"]) for r in data if r["policy"] == a]
        for a in ["P0", "P1", "P2", "P3"]
    }
    separated = [a for a, ys in arms.items() if not ys or len(set(ys)) < 2]
    if separated:
        return dict(
            status="UNIDENTIFIABLE_SEPARATED_OR_ABSENT_ARM",
            arms=separated,
            observed_episodes=len(data),
            coefficients=None,
            reason=(
                "Unpenalized finite treatment effects are not identified; "
                "no zero coefficient substituted"
            ),
        )
    families = sorted({contracts[r["task_id"]]["family"] for r in data})
    columns = (
        ["intercept", "P1-P0", "P2-P0", "P3-P0", "OpsConsole-FlowBoard", "L2-L1", "L3-L1"]
        + [f"family:{f}-{families[0]}" for f in families[1:]]
        + ["intermediate-tight", "generous-tight"]
    )
    grouped = {}
    for row in data:
        contract = contracts[row["task_id"]]
        x = (
            [1.0]
            + [float(row["policy"] == p) for p in ["P1", "P2", "P3"]]
            + [
                float(contract["application"] == "opsconsole"),
                float(contract["complexity"] == "L2"),
                float(contract["complexity"] == "L3"),
            ]
            + [float(contract["family"] == f) for f in families[1:]]
            + [
                float(row["timing_regime"] == "intermediate"),
                float(row["timing_regime"] == "generous"),
            ]
        )
        grouped.setdefault(row["task_id"], []).append((x, int(row["joint_safe_completion"])))
    groups = [
        (np.asarray([r[0] for r in rows]), np.asarray([r[1] for r in rows]))
        for rows in grouped.values()
    ]
    nodes, weights = hermgauss(21)
    initial = np.zeros(len(columns) + 1)
    initial[0] = np.log(
        np.mean([v for ys in arms.values() for v in ys])
        / (1 - np.mean([v for ys in arms.values() for v in ys]))
    )
    initial[-1] = -0.5
    result = minimize(
        objective,
        initial,
        args=(groups, nodes, weights),
        jac=True,
        method="L-BFGS-B",
        bounds=[(-12, 12)] * len(columns) + [(-6, 3)],
        options=dict(maxiter=500, ftol=1e-10, gtol=1e-6),
    )
    hessian = np.zeros((len(initial), len(initial)))
    for index in range(len(initial)):
        perturb = np.zeros(len(initial))
        perturb[index] = 1e-4
        hessian[:, index] = (
            objective(result.x + perturb, groups, nodes, weights)[1]
            - objective(result.x - perturb, groups, nodes, weights)[1]
        ) / 2e-4
    hessian = (hessian + hessian.T) / 2
    eigenvalues = np.linalg.eigvalsh(hessian)
    near_boundary = bool(np.any(np.abs(result.x[:-1]) > 11.9))
    identifiable = result.success and eigenvalues.min() > 1e-6 and not near_boundary
    errors = np.sqrt(np.diag(np.linalg.inv(hessian))) if identifiable else None
    coefficients = [
        dict(
            term=name,
            log_odds=float(beta),
            standard_error=float(errors[i]) if errors is not None else None,
            wald95=[float(beta - 1.96 * errors[i]), float(beta + 1.96 * errors[i])]
            if errors is not None
            else None,
        )
        for i, (name, beta) in enumerate(zip(columns, result.x[:-1]))
    ]
    return dict(
        status="FIT" if identifiable else "UNIDENTIFIABLE_OR_OPTIMIZATION_WARNING",
        episodes=len(data),
        source_tasks=len(groups),
        quadrature_points=21,
        reference_policy="P0",
        reference_family=families[0],
        coefficients=coefficients,
        task_intercept_sigma=float(np.exp(result.x[-1])),
        optimizer_success=bool(result.success),
        optimizer_message=str(result.message),
        negative_log_likelihood=float(result.fun),
        hessian_min_eigenvalue=float(eigenvalues.min()),
        gradient_max=float(np.abs(result.jac).max()),
        caution=(
            "Conditional log-odds sensitivity; Wald intervals depend on model assumptions; "
            "paired cluster contrast is primary"
        ),
    )
