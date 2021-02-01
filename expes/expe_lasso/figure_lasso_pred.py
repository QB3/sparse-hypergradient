import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sparse_ho.utils_plot import (
    configure_plt, discrete_color, dict_color, dict_color_2Dplot, dict_markers,
    dict_method, dict_title)

save_fig = False
# save_fig = True
fig_dir = "../../../CD_SUGAR/tex/journal/prebuiltimages/"
fig_dir_svg = "../../../CD_SUGAR/tex/journal/images/"


configure_plt()

fontsize = 16

dict_markevery = {}
dict_markevery["news20"] = 1
dict_markevery["finance"] = 10
dict_markevery["rcv1_train"] = 1
dict_markevery["real-sim"] = 1
dict_markevery["leukemia"] = 10

dict_marker_size = {}
dict_marker_size["forward"] = 4
dict_marker_size["implicit_forward"] = 5
dict_marker_size["fast_iterdiff"] = 4
dict_marker_size['implicit'] = 4
dict_marker_size['grid_search'] = 1
dict_marker_size['bayesian'] = 10
dict_marker_size['random'] = 5
dict_marker_size['lhs'] = 4

dict_s = {}
dict_s["implicit_forward"] = 100
dict_s["implicit_forward_approx"] = 40
dict_s['grid_search'] = 5
dict_s['bayesian'] = 20
dict_s['random'] = 5
dict_s['lhs'] = 4

dict_n_feature = {}
dict_n_feature["rcv1_train"] = r"($p=19,959$)"
dict_n_feature["real-sim"] = r"($p=20,958$)"
dict_n_feature["news20"] = r"($p=130,107$)"
dict_n_feature["finance"] = r"($p=1,668,737$)"
dict_n_feature["leukemia"] = r"($p=7129$)"

dict_xmax = {}
dict_xmax["logreg", "rcv1_train"] = 20
dict_xmax["logreg", "real-sim"] = 30
dict_xmax["logreg", "leukemia"] = 5
dict_xmax["logreg", "news20"] = None

dict_xmax["lasso", "rcv1_train"] = 60
dict_xmax["lasso", "real-sim"] = 200
dict_xmax["lasso", "leukemia"] = 5
dict_xmax["lasso", "news20"] = 1200

dict_xticks = {}
dict_xticks["lasso", "rcv1_train"] = (-6, -4, -2, 0)
dict_xticks["lasso", "real-sim"] = (-6, -4, -2, 0)
dict_xticks["lasso", "leukemia"] = (-6, -4, -2, 0)
dict_xticks["lasso", "news20"] = (-8, -6, -4, -2, 0)

dict_xticks["logreg", "rcv1"] = (-8, -6, -4, -2, 0)
dict_xticks["logreg", "real-sim"] = (-8, -6, -4, -2, 0)
dict_xticks["logreg", "leukemia"] = (-8, -6, -4, -2, 0)
dict_xticks["logreg", "news20"] = (-8, -6, -4, -2, 0)

markersize = 8

# dataset_names = ["rcv1"]
# dataset_names = ["rcv1", "news20", "finance"]
# dataset_names = ["rcv1", "real-sim"]
dataset_names = ["rcv1_train", "real-sim", "news20"]
# dataset_names = ["leukemia", "rcv1", "real-sim"]
# dataset_names = ["rcv1", "real-sim", "news20"]


plt.close('all')
fig_val, axarr_val = plt.subplots(
    1, len(dataset_names), sharex=False, sharey=False, figsize=[14, 4],)

fig_test, axarr_test = plt.subplots(
    1, len(dataset_names), sharex=False, sharey=False, figsize=[14, 4],)

fig_grad, axarr_grad = plt.subplots(
    1, len(dataset_names), sharex=False, sharey=False, figsize=[14, 4],)

model_name = "lasso"

for idx, dataset in enumerate(dataset_names):
    df_data = pd.read_pickle("results/%s_%s.pkl" % (model_name, dataset))
    # df_data = pd.read_pickle("%s.pkl" % dataset)

    # df_data = df_data[df_data['tolerance_decrease'] == 'exponential']
    df_data = df_data[df_data['tolerance_decrease'] == 'constant']

    methods = df_data['method']
    times = df_data['times']
    objs = df_data['objs']
    # objs_tests = df_data['objs_test']
    alphas = df_data['alphas']
    # log_alpha_max = df_data['log_alpha_max'][0]
    log_alpha_max = np.log(df_data['alpha_max'].to_numpy()[0])
    tols = df_data['tolerance_decrease']
    # norm_y_vals = df_data['norm y_val']
    norm_val = 0
    # for norm_y_valss in norm_y_vals:
    #     norm_val = norm_y_valss

    min_objs = np.infty
    for obj in objs:
        min_objs = min(min_objs, obj.min())

    lines = []

    axarr_test.flat[idx].set_xlim(0, dict_xmax[model_name, dataset])
    # axarr_test.flat[idx].set_xticks(dict_xticks[model_name, dataset])

    axarr_grad.flat[idx].set_xlabel(
        r"$\lambda - \lambda_{\max}$", fontsize=fontsize)
    axarr_test.flat[idx].set_xlabel("Time (s)", fontsize=fontsize)
    axarr_test.flat[idx].tick_params(labelsize=fontsize)
    axarr_val.flat[idx].tick_params(labelsize=fontsize)

    E0 = df_data.objs[1][0]
    for _, (time, obj, alpha, method, _) in enumerate(
            zip(times, objs, alphas, methods, tols)):
        log_alpha = np.log(alpha)
        marker = dict_markers[method]
        if method != "random":
            # markevery = dict_markevery[dataset]
            s = dict_s[method]
            # axarr_grad.flat[idx].plot(
            axarr_grad.flat[idx].scatter(
                np.array(log_alpha) - log_alpha_max, obj / E0,
                color=discrete_color(len(obj), dict_color_2Dplot[method]),
                label="%s" % (dict_method[method]),
                marker=marker, s=s)
            axarr_grad.flat[idx].set_xticks(dict_xticks[model_name, dataset])

    # plot for objective minus optimum on validation set
    for _, (time, obj, method, _) in enumerate(
            zip(times, objs, methods, tols)):
        marker = dict_markers[method]
        obj = [np.min(obj[:k]) for k in np.arange(len(obj)) + 1]
        lines.append(
            axarr_val.flat[idx].plot(
                time, obj / E0,
                color=dict_color[method], label="%s" % (dict_method[method]),
                marker=marker, markersize=markersize,
                markevery=dict_markevery[dataset]))
    axarr_val.flat[idx].set_xlim(0, dict_xmax[model_name, dataset])
    axarr_val.flat[idx].set_xlabel("Time (s)")

    axarr_grad.flat[idx].set_title("%s %s" % (
        dict_title[dataset], dict_n_feature[dataset]), size=fontsize)

axarr_grad.flat[0].set_ylabel("Cross validation loss", fontsize=fontsize)
axarr_val.flat[0].set_ylabel("Cross validation loss", fontsize=fontsize)
axarr_test.flat[0].set_ylabel("Loss on test set", fontsize=fontsize)

fig_val.tight_layout()
fig_test.tight_layout()
fig_grad.tight_layout()
if save_fig:
    fig_val.savefig(
        fig_dir + "%s_val.pdf" % model_name, bbox_inches="tight")
    fig_val.savefig(
        fig_dir_svg + "%s_val.svg" % model_name, bbox_inches="tight")
    fig_test.savefig(
        fig_dir + "%s_test.pdf" % model_name, bbox_inches="tight")
    fig_test.savefig(
        fig_dir_svg + "%s_test.svg" % model_name, bbox_inches="tight")
    fig_grad.savefig(
        fig_dir + "%s_val_grad.pdf" % model_name, bbox_inches="tight")
    fig_grad.savefig(
        fig_dir_svg + "%s_lasso_val_grad.svg" % model_name,
        bbox_inches="tight")


fig_val.show()
fig_test.show()
fig_grad.show()


#################################################################
# plot legend
labels = []
for method in methods:
    labels.append(dict_method[method])

fig_legend = plt.figure(figsize=[18, 4])
fig_legend.legend(
    [l[0] for l in lines], labels,
    ncol=5, loc='upper center', fontsize=fontsize - 4)
fig_legend.tight_layout()
if save_fig:
    fig_legend.savefig(
        fig_dir + "lasso_pred_legend.pdf", bbox_inches="tight")
fig_legend.show()
