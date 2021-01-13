import numpy as np
import sklearn
import sklearn.linear_model
from sklearn.model_selection import KFold
from sklearn.linear_model import LassoCV

from sparse_ho.models import Lasso
from sparse_ho.criterion import CrossVal, HeldOutMSE
from sparse_ho.utils import Monitor
from sparse_ho.datasets.synthetic import get_synt_data
from sparse_ho import Forward
from sparse_ho.grid_search import grid_search

n_samples = 100
n_features = 10
n_active = 2
SNR = 3
rho = 0.5

X, y, _, _, _ = get_synt_data(
    dictionary_type="Toeplitz", n_samples=n_samples,
    n_features=n_features, n_times=1, n_active=n_active, rho=rho,
    SNR=SNR, seed=0)

alpha_max = (np.abs(X.T @ y)).max() / n_samples
tol = 1e-8

estimator = sklearn.linear_model.Lasso(
    fit_intercept=False, max_iter=10000, warm_start=True)
model = Lasso(estimator=estimator)

log_alphas = np.log(np.geomspace(alpha_max, alpha_max / 100))


# dict_log_alpha = {}
# dict_log_alpha["lasso"] = log_alpha
# tab = np.linspace(1, 1000, n_features)
# dict_log_alpha["wlasso"] = log_alpha + np.log(tab / tab.max())

# estimator = sklearn.linear_model.Lasso(
#     fit_intercept=False, max_iter=1000, warm_start=True)
# model = Lasso(estimator=estimator)


def test_cross_val_criterion():
    # TODO we also need to add a test for sparse matrices
    alpha_min = alpha_max / 10
    log_alpha_max = np.log(alpha_max)
    log_alpha_min = np.log(alpha_min)
    max_iter = 10000
    n_alphas = 10
    kf = KFold(n_splits=5, shuffle=True, random_state=56)

    monitor_grid = Monitor()
    mse = HeldOutMSE(None, None)
    criterion = CrossVal(mse, cv=kf)
    algo = Forward()
    grid_search(
        algo, criterion, model, X, y, log_alpha_min, log_alpha_max,
        monitor_grid, max_evals=n_alphas)

    reg = LassoCV(
        cv=kf, verbose=True, tol=tol, fit_intercept=False,
        alphas=np.geomspace(alpha_max, alpha_min, num=n_alphas),
        max_iter=max_iter).fit(X, y)
    reg.score(X, y)
    objs_grid_sk = reg.mse_path_.mean(axis=1)
    # these 2 value should be the same
    (objs_grid_sk - np.array(monitor_grid.objs))
    assert np.allclose(objs_grid_sk, monitor_grid.objs)


if __name__ == '__main__':
    test_cross_val_criterion()


# TODO list_criterions = [...]
# test val from get_val_grad === get_val
# verify dtype from criterion, bonne shape


def test_cross_val_criterion():
    kf = KFold(n_splits=5, shuffle=True, random_state=56)
    mse = HeldOutMSE(None, None)
    criterion = CrossVal(mse, cv=kf)
    algo = Forward()

    monitor_get_val = Monitor()
    monitor_get_val_grad = Monitor()

    for log_alpha in log_alphas:
        criterion.get_val(
            model, X, y, log_alpha, tol=tol, monitor=monitor_get_val)
        criterion.get_val_grad(
            model, X, y, log_alpha, algo.get_beta_jac_v,
            tol=tol, monitor=monitor_get_val_grad)

    obj_val = np.array(monitor_get_val.objs)
    obj_val_grad = np.array(monitor_get_val_grad.objs)

    np.testing.assert_allclose(obj_val, obj_val_grad)


if __name__ == '__main__':
    test_cross_val_criterion()
