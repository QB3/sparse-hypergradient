import numpy as np
from joblib import Parallel, delayed
import pandas
from itertools import product
from libsvmdata.datasets import fetch_libsvm
from celer import LogisticRegression


from sparse_ho.ho_dirty import grad_search, grad_search_backtracking_cd_dirty2
from sparse_ho.implicit_forward import ImplicitForward
from sparse_ho.utils_datasets import clean_dataset, get_alpha_max
from sparse_ho.utils import Monitor
from sparse_ho.criterion import LogisticMulticlass
from sparse_ho.hyperopt_wrapper import hyperopt_wrapper


dataset_names = ["aloi"]
# dataset_names = ["mnist"]

# methods = ["random"]
# methods = ["random", "bayesian"]
# methods = ["implicit_forward_cdls"]
methods = ["implicit_forward"]
# methods = ["implicit_forward_cdls", "implicit_forward"]
# methods = ["implicit_forward_cdls", "implicit_forward", "random", "bayesian"]

tols = 1e-7
n_outers = [10]

dict_t_max = {}
dict_t_max["rcv1"] = 50
dict_t_max["real-sim"] = 100
dict_t_max["leukemia"] = 10
dict_t_max["20news"] = 500

dict_subsampling = {}
dict_subsampling["mnist"] = (5_000, 1000)
dict_subsampling["rcv1_train"] = (21_000, 20_000)
dict_subsampling["aloi"] = (5_000, 100)

dict_max_eval = {}
dict_max_eval["mnist"] = 50
dict_max_eval["rcv1_train"] = 20
dict_max_eval["aloi"] = 10


# TODO add dict tmax


def parallel_function(
        dataset_name, method, tol=1e-8, n_outer=15):

    # load data
    X, y = fetch_libsvm(dataset_name)
    # subsample the samples and the features
    # n_samples = 100
    # n_features = 100
    # n_samples = 5_000
    # n_features = 1_000
    n_samples, n_features = dict_subsampling[dataset_name]
    t_max = 1_800
    # t_max = 3600

    X, y = clean_dataset(X, y, n_samples, n_features)
    alpha_max, n_classes = get_alpha_max(X, y)
    log_alpha_max = np.log(alpha_max)  # maybe to change alpha max value

    algo = ImplicitForward(None, n_iter_jac=1000)
    estimator = LogisticRegression(
        C=1, fit_intercept=False, warm_start=True, max_iter=30, verbose=False)
    logit_multiclass = LogisticMulticlass(X, y, algo, estimator)
    monitor = Monitor()
    if method == "implicit_forward":
        log_alpha0 = np.ones(n_classes) * np.log(0.01 * alpha_max)
        grad_search(
            logit_multiclass, log_alpha0, monitor, n_outer=n_outer, tol=tol,
            t_max=t_max)
    if method == "implicit_forward_cdls":
        log_alpha0 = np.ones(n_classes) * np.log(0.01 * alpha_max)
        grad_search_backtracking_cd_dirty2(
            logit_multiclass, log_alpha0, monitor, n_outer=n_outer, tol=tol,
            maxit_ln=10, t_max=t_max)
    elif method.startswith(('random', 'bayesian')):
        log_alpha_min = np.log(alpha_max) - 7
        hyperopt_wrapper(
            logit_multiclass, log_alpha_min, log_alpha_max, monitor,
            max_evals=50, tol=tol, t_max=t_max, method=method,
            size_space=n_classes)

    monitor.times = np.array(monitor.times).copy()
    monitor.objs = np.array(monitor.objs).copy()
    monitor.acc_vals = np.array(monitor.acc_vals).copy()
    monitor.acc_tests = np.array(monitor.acc_tests).copy()
    monitor.log_alphas = np.array(monitor.log_alphas).copy()
    return (
        dataset_name, method, tol, n_outer, monitor.times, monitor.objs,
        monitor.acc_vals, monitor.acc_tests, monitor.log_alphas, log_alpha_max,
        n_samples, n_features)


print("enter parallel")
backend = 'loky'
# n_jobs = 1
n_jobs = len(methods) * len(dataset_names)
results = Parallel(n_jobs=n_jobs, verbose=100, backend=backend)(
    delayed(parallel_function)(
        dataset_name, method, n_outer=n_outer, tol=tols)
    for dataset_name, method, n_outer in product(
        dataset_names, methods, n_outers))
print('OK finished parallel')

df = pandas.DataFrame(results)
df.columns = [
    'dataset', 'method', 'tol', 'n_outer', 'times', 'objs', 'acc_vals',
    'acc_tests', 'log_alphas', "log_alpha_max",
    "n_subsamples", "n_subfeatures"]

for dataset_name in dataset_names:
    for method in methods:
        df[(df['dataset'] == dataset_name) & (df['method'] == method)].to_pickle(
            "results/%s_%s.pkl" % (dataset_name, method))
