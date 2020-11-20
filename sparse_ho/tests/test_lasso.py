import numpy as np
from scipy.sparse import csc_matrix
from sklearn import linear_model


from sparse_ho.datasets.synthetic import get_synt_data
from sparse_ho.forward import get_beta_jac_iterdiff
from sparse_ho.models import Lasso, WeightedLasso
from sparse_ho.implicit_forward import get_beta_jac_fast_iterdiff
from sparse_ho.implicit import get_beta_jac_t_v_implicit

from sparse_ho.forward import Forward
from sparse_ho.implicit_forward import ImplicitForward
from sparse_ho.implicit import Implicit
from sparse_ho.backward import Backward
from sparse_ho.criterion import CV, SURE

n_samples = 100
n_features = 100
n_active = 5
SNR = 3
rho = 0.1

X_train, y_train, beta_star, noise, sigma_star = get_synt_data(
    dictionary_type="Toeplitz", n_samples=n_samples,
    n_features=n_features, n_times=1, n_active=n_active, rho=rho,
    SNR=SNR, seed=0)
X_train_s = csc_matrix(X_train)

X_test, y_test, beta_star, noise, sigma = get_synt_data(
    dictionary_type="Toeplitz", n_samples=n_samples,
    n_features=n_features, n_times=1, n_active=n_active, rho=rho,
    SNR=SNR, seed=1)
X_test_s = csc_matrix(X_test)

X_val, y_val, beta_star, noise, sigma = get_synt_data(
    dictionary_type="Toeplitz", n_samples=n_samples,
    n_features=n_features, n_times=1, n_active=n_active, rho=rho,
    SNR=SNR, seed=2)
X_test_s = csc_matrix(X_test)


alpha_max = (X_train.T @ y_train).max() / n_samples
p_alpha = 0.9
alpha = p_alpha * alpha_max
log_alpha = np.log(alpha)

log_alphas = np.log(alpha_max * np.geomspace(1, 0.1))
tol = 1e-16

dict_log_alpha = {}
dict_log_alpha["lasso"] = log_alpha
tab = np.linspace(1, 1000, n_features)
dict_log_alpha["wlasso"] = log_alpha + np.log(tab / tab.max())

models = {}
models["lasso"] = Lasso(X_train, y_train, estimator=None)
models["wlasso"] = WeightedLasso(X_train, y_train, estimator=None)


def get_v(mask, dense):
    return 2 * (X_val[:, mask].T @ (
        X_val[:, mask] @ dense - y_val)) / X_val.shape[0]


def test_beta_jac():
    #########################################################################
    # check that the methods computing the full Jacobian compute the same sol
    # maybe we could add a test comparing with sklearn
    for key in models.keys():
        supp1, dense1, jac1 = get_beta_jac_iterdiff(
            X_train, y_train, dict_log_alpha[key], tol=tol,
            model=models[key])
        supp1sk, dense1sk, jac1sk = get_beta_jac_iterdiff(
            X_train, y_train, dict_log_alpha[key], tol=tol,
            model=models[key])
        supp2, dense2, jac2 = get_beta_jac_fast_iterdiff(
            X_train, y_train, dict_log_alpha[key], get_v,
            tol=tol, model=models[key], tol_jac=tol)
        supp3, dense3, jac3 = get_beta_jac_iterdiff(
            X_train_s, y_train, dict_log_alpha[key], tol=tol,
            model=models[key])
        supp4, dense4, jac4 = get_beta_jac_fast_iterdiff(
            X_train_s, y_train, dict_log_alpha[key], get_v,
            tol=tol, model=models[key], tol_jac=tol)

        assert np.all(supp1 == supp1sk)
        assert np.all(supp1 == supp2)
        assert np.allclose(dense1, dense1sk)
        assert np.allclose(dense1, dense2)
        assert np.allclose(jac1, jac2)

        assert np.all(supp2 == supp3)
        assert np.allclose(dense2, dense3)
        assert np.allclose(jac2, jac3)

        assert np.all(supp3 == supp4)
        assert np.allclose(dense3, dense4)
        assert np.allclose(jac3, jac4)

        get_beta_jac_t_v_implicit(
            X_train, y_train, dict_log_alpha[key], get_v,
            model=models[key])


estimator = linear_model.Lasso(
    fit_intercept=False, max_iter=1000, warm_start=True)
models_custom = {}
models_custom["lasso"] = Lasso(X_train, y_train, estimator=estimator)
models_custom["wlasso"] = WeightedLasso(X_train, y_train, estimator=estimator)


def test_beta_jac2():
    #########################################################################
    # check that the methods computing the full Jacobian compute the same sol
    # maybe we could add a test comparing with sklearn
    for key in models.keys():
        supp, dense, jac = get_beta_jac_fast_iterdiff(
            X_train_s, y_train, dict_log_alpha[key], get_v,
            tol=tol, model=models[key], tol_jac=tol)
        supp_custom, dense_custom, jac_custom = get_beta_jac_fast_iterdiff(
            X_train_s, y_train, dict_log_alpha[key], get_v,
            tol=tol, model=models[key], tol_jac=tol)
        assert np.all(supp == supp_custom)
        assert np.allclose(dense, dense_custom)
        assert np.allclose(jac, jac_custom)


def test_val_grad():
    #######################################################################
    # Not all methods computes the full Jacobian, but all
    # compute the gradients
    # check that the gradient returned by all methods are the same
    for key in models.keys():
        log_alpha = dict_log_alpha[key]
        model = models[key]

        criterion = CV(X_val, y_val)
        algo = Forward()
        val_fwd, grad_fwd = criterion.get_val_grad(
            model, log_alpha, algo.get_beta_jac_v, tol=tol)

        criterion = CV(X_val, y_val)
        algo = ImplicitForward(tol_jac=1e-8, n_iter_jac=5000)
        val_imp_fwd, grad_imp_fwd = criterion.get_val_grad(
            model, log_alpha, algo.get_beta_jac_v, tol=tol)

        criterion = CV(X_val, y_val)
        algo = Implicit()
        val_imp, grad_imp = criterion.get_val_grad(
            model, log_alpha, algo.get_beta_jac_v, tol=tol)

        criterion = CV(X_val, y_val)
        algo = Backward()
        val_bwd, grad_bwd = criterion.get_val_grad(
            model, log_alpha, algo.get_beta_jac_v, tol=tol)

        assert np.allclose(val_fwd, val_imp_fwd)
        assert np.allclose(grad_fwd, grad_imp_fwd)
        # assert np.allclose(val_imp_fwd, val_imp)
        assert np.allclose(val_bwd, val_fwd)
        assert np.allclose(val_bwd, val_imp_fwd)
        assert np.allclose(grad_fwd, grad_bwd)
        assert np.allclose(grad_bwd, grad_imp_fwd)

        # for the implcit the conjugate grad does not converge
        # hence the rtol=1e-2
        assert np.allclose(grad_imp_fwd, grad_imp, atol=1e-3)

    for key in models.keys():
        log_alpha = dict_log_alpha[key]
        model = models[key]
        criterion = SURE(X_train, y_train, sigma_star)
        algo = Forward()
        val_fwd, grad_fwd = criterion.get_val_grad(
            model, log_alpha, algo.get_beta_jac_v, tol=tol)

        criterion = SURE(X_train, y_train, sigma_star)
        algo = ImplicitForward(tol_jac=1e-8, n_iter_jac=5000)
        val_imp_fwd, grad_imp_fwd = criterion.get_val_grad(
            model, log_alpha, algo.get_beta_jac_v, tol=tol)

        criterion = SURE(X_train, y_train, sigma_star)
        algo = Implicit(criterion)
        val_imp, grad_imp = criterion.get_val_grad(
            model, log_alpha, algo.get_beta_jac_v, tol=tol)

        criterion = SURE(X_train, y_train, sigma_star)
        algo = Backward()
        val_bwd, grad_bwd = criterion.get_val_grad(
            model, log_alpha, algo.get_beta_jac_v, tol=tol)

        assert np.allclose(val_fwd, val_imp_fwd)
        assert np.allclose(grad_fwd, grad_imp_fwd)
        assert np.allclose(val_imp_fwd, val_imp)
        assert np.allclose(val_bwd, val_fwd)
        assert np.allclose(val_bwd, val_imp_fwd)
        assert np.allclose(grad_fwd, grad_bwd)
        assert np.allclose(grad_bwd, grad_imp_fwd)


if __name__ == '__main__':
    test_beta_jac()
    test_val_grad()
    test_beta_jac2()
