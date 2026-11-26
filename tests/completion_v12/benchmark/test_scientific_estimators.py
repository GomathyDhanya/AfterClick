import numpy as np
from numpy.polynomial.hermite import hermgauss
from scipy.optimize import check_grad

from research_ops.scripts.v12_hierarchical import fit, objective


def test_integrated_random_intercept_gradient_matches_numerical_derivative():
    rng = np.random.default_rng(52111)
    groups = []
    for _ in range(12):
        x = np.column_stack([np.ones(9), rng.normal(size=(9, 3))])
        y = rng.integers(0, 2, size=9)
        groups.append((x, y))
    nodes, weights = hermgauss(21)
    theta = np.array([-.6, .7, -.2, .1, -.4])
    error = check_grad(
        lambda p: objective(p, groups, nodes, weights)[0],
        lambda p: objective(p, groups, nodes, weights)[1],
        theta,
    )
    assert error < 2e-5


def test_zero_success_floor_does_not_produce_finite_treatment_coefficients():
    rows = [dict(policy=policy, clean=False, joint_safe_completion=False)
            for policy in ["P0", "P1", "P2", "P3"]]
    result = fit(rows, {})
    assert result["status"] == "UNIDENTIFIABLE_SEPARATED_OR_ABSENT_ARM"
    assert result["coefficients"] is None
