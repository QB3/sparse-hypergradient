import numpy as np
from joblib import Parallel, delayed
import pandas
from itertools import product
from sparse_ho.models import Lasso
from sparse_ho.criterion import HeldOutMSE
from sparse_ho import ImplicitForward, Implicit
from sparse_ho import Forward, Backward
from sparse_ho.utils import Monitor
from celer import Lasso as Lasso_celer
from libsvmdata import fetch_libsvm
from sklearn.model_selection import StratifiedShuffleSplit


tol = 1e-16
methods = ["forward", "implicit_forward", "celer"]
p_alpha_max = 0.01
dict_algo = {}
dict_algo["forward"] = Forward()
dict_algo["implicit_forward"] = ImplicitForward(
    tol_jac=1e-8, n_iter_jac=100000, max_iter=1000)
dict_algo["implicit"] = Implicit(max_iter=1000)
dict_algo["backward"] = Backward()
dataset_names = ["leukemia", "rcv1_train", "real-sim", "news20"]
dict_maxits = {}
dict_maxits["leukemia"] = np.floor(np.geomspace(5, 70, 15)).astype(int)
dict_maxits["rcv1_train"] = np.floor(np.geomspace(5, 70, 15)).astype(int)
dict_maxits["real-sim"] = np.floor(np.geomspace(5, 70, 15)).astype(int)
dict_maxits["news20"] = np.floor(np.geomspace(5, 70, 15)).astype(int)

maxits = np.floor(np.geomspace(5, 60, 15)).astype(int)
dataset_name = "real-sim"


def parallel_function(
        dataset_name, p_alpha_max, method="forward", maxit=10,
        random_state=42):
    X, y = fetch_libsvm(dataset_name)
    n_samples = len(y)
    sss1 = StratifiedShuffleSplit(n_splits=2, test_size=0.3333, random_state=0)
    idx_train, idx_val = sss1.split(X, y)
    idx_train = idx_train[0]
    idx_val = idx_val[0]

    for i in range(2):
        alpha_max = np.max(np.abs(X.T.dot(y))) / n_samples
        log_alpha = np.log(alpha_max * p_alpha_max)
        monitor = Monitor()
        if method == "celer":
            clf = Lasso_celer(
                alpha=np.exp(log_alpha), fit_intercept=False, warm_start=True,
                tol=1e-12, max_iter=maxit)
            model = Lasso(estimator=clf, max_iter=maxit)
            criterion = HeldOutMSE(idx_train, idx_val)
            algo = ImplicitForward(
                tol_jac=1e-8, n_iter_jac=maxit)
            algo = dict_algo["implicit_forward"]
            algo.max_iter = maxit
            val, grad = criterion.get_val_grad(
                    model, X, y, log_alpha, algo.get_beta_jac_v, tol=1e-12,
                    monitor=monitor, max_iter=maxit)
        else:
            model = Lasso(max_iter=maxit)
            criterion = HeldOutMSE(idx_train, idx_val)
            algo = dict_algo[method]
            algo.max_iter = maxit
            val, grad = criterion.get_val_grad(
                    model, X, y, log_alpha, algo.get_beta_jac_v, tol=tol,
                    monitor=monitor, max_iter=maxit)

        true_monitor = Monitor()
        clf = Lasso_celer(
                alpha=np.exp(log_alpha), fit_intercept=False, warm_start=True,
                tol=1e-14, max_iter=10000)
        criterion = HeldOutMSE(idx_train, idx_val)
        algo = Implicit(criterion)
        model = Lasso(estimator=clf, max_iter=10000)
        true_val, true_grad = criterion.get_val_grad(
                model, X, y, log_alpha, algo.get_beta_jac_v, tol=1e-14,
                monitor=true_monitor)

    return (
        dataset_name, p_alpha_max, method, maxit,
        val, grad, monitor.times[0], true_val, true_grad,
        true_monitor.times[0])

# dict_all = {}
# for n_features, n_samples, rho, method, maxit in product(
#         list_n_features, list_n_samples, list_rho, methods, maxits):

#     res = parallel_function(
#         n_features=n_features, n_samples=n_samples, rho=rho,
#         method=method, maxit=maxit)
#     dict_all = {**dict_all, **res}

print("enter parallel")
backend = 'loky'
#
# n_jobs = len(maxits)
# n_jobs = len(methods) * len(maxits) * len(list_rho)
n_jobs = 1
results = Parallel(n_jobs=n_jobs, verbose=100, backend=backend)(
    delayed(parallel_function)(
        dataset_name, p_alpha_max,
        method=method, maxit=maxit)
    for method, maxit in product(
        methods, maxits))
print('OK finished parallel')

df = pandas.DataFrame(results)
df.columns = [
    'dataset',
    'p_alpha', 'method', 'maxit', 'criterion value',
    'criterion grad',  'time',
    'criterion true value', 'criterion true grad', 'true time']

# df.to_pickle("results.pkl")

for dataset_name in dataset_names:
    df[df['dataset'] == dataset_name].to_pickle(
        "%s.pkl" % dataset_name)