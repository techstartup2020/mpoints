import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn
import statsmodels.tsa.stattools as stattools
from matplotlib.colors import ListedColormap
import copy
import bisect

def qq_plot(residuals, shape=None, path='', fig_name='qq_plot.pdf', log=False, q_min=0.01, q_max=0.99,
            number_of_quantiles=100, title=None, labels=None, model_labels=None, palette=None, figsize=(12, 6),
            size_labels=16, size_ticks=14, legend_size=16, bottom=0.12, top=0.93, left=0.08, right=0.92, savefig=False,
            leg_pos=0):
    """
    Qq-plot of residuals.

    :param residuals: list of lists (one list of residuals per event type) or list of lists of lists when multiple models are compared (one list of lists per model).
    :param shape: 2D-tuple (number of columns, number of rows), shape of the array of figures.
    :param path: string, where the figure is saved.
    :param fig_name: string, name of the file.
    :param log: boolean, set to True for qq-plots with log-scale.
    :param q_min: float, smallest quantile to plot (e.g., 0.01 for 1%).
    :param q_max: float, largest quantile to plot.
    :param number_of_quantiles: int.
    :param title: string, suptitle.
    :param labels: list of strings, labels of the event types.
    :param model_labels: list of strings, names of the different considered models.
    :param palette: color palette (list of colors), one color per model.
    :param figsize: tuple (width, height).
    :param size_labels: int, fontsize of labels.
    :param size_ticks: int, fontsize of tick labels.
    :param legend_size: int, fontsize of the legend.
    :param bottom: float between 0 and 1, adjusts the bottom margin, see matplotlib subplots_adjust.
    :param top: float between 0 and 1, adjusts the top margin, see matplotlib subplots_adjust.
    :param left: float between 0 and 1, adjusts the left margin, see matplotlib subplots_adjust.
    :param right: float between 0 and 1, adjusts the right margin, see matplotlib subplots_adjust.
    :param savefig: boolean, set to True to save the figure.
    :param leg_pos: int, position of the legend in the array of figures.
    :return: figure, array of figures.
    """
    quantile_levels = np.linspace(q_min, q_max, number_of_quantiles)
    quantiles_theoretical = np.zeros(number_of_quantiles)
    for i in range(number_of_quantiles):
        q = quantile_levels[i]
        x = - np.log(1 - q)  # standard exponential distribution
        quantiles_theoretical[i] = x
    # find number of models given and number of event types (dim)
    n_models = 1
    dim = len(residuals)
    if type(residuals[0][0]) in [list, np.ndarray]:  # case when there is more than one model
        n_models = len(residuals)
        dim = len(residuals[0])
    # set empty model labels if no labels provided
    if model_labels==None:
        model_labels = [None]*n_models
    v_size = shape[0]
    h_size = shape[1]
    seaborn.set()
    if palette==None:
        palette = seaborn.color_palette('husl', n_models)
    f, fig_array = plt.subplots(v_size, h_size, figsize=figsize, sharex='col', sharey='row')
    if title != None:
        f.suptitle(title)
    for i in range(v_size):
        for j in range(h_size):
            n = j + h_size * i
            if n < dim:  # the shape of the subplots might be bigger than dim, i.e. 3 plots on a 2x2 grid.
                axes = None
                if v_size == 1 and h_size == 1:
                    axes = fig_array
                elif v_size == 1:
                    axes = fig_array[j]
                elif h_size == 1:
                    axes = fig_array[i]
                else:
                    axes = fig_array[i, j]
                axes.tick_params(axis='both', which='major', labelsize=size_ticks)  # font size for tick labels
                if n_models == 1:
                    quantiles_empirical = np.zeros(number_of_quantiles)
                    for k in range(number_of_quantiles):
                        q = quantile_levels[k]
                        x = np.percentile(residuals[n], q * 100)
                        quantiles_empirical[k] = x
                    axes.plot(quantiles_theoretical, quantiles_empirical, color=palette[0])
                    axes.plot(quantiles_theoretical, quantiles_theoretical, color='k', linewidth=0.8, ls='--')
                else:
                    for m in range(n_models):
                        quantiles_empirical = np.zeros(number_of_quantiles)
                        for k in range(number_of_quantiles):
                            q = quantile_levels[k]
                            x = np.percentile(residuals[m][n], q * 100)
                            quantiles_empirical[k] = x
                        axes.plot(quantiles_theoretical, quantiles_empirical, color=palette[m],
                                     label=model_labels[m])
                        if m == 0:
                            axes.plot(quantiles_theoretical, quantiles_theoretical, color='k', linewidth=0.8,
                                      ls='--')
                    if n == leg_pos :  # add legend in the specified subplot
                        legend = axes.legend(frameon=1, fontsize=legend_size)
                        legend.get_frame().set_facecolor('white')
                if log:
                    axes.set_xscale('log')
                    axes.set_yscale('log')
                if labels != None:
                    axes.set_title( labels[n], fontsize=size_labels)
    plt.tight_layout()
    if bottom!=None:
        plt.subplots_adjust(bottom=bottom, top=top, left=left, right=right)
    f.text(0.5, 0.02, 'Quantile (standard exponential distribution)', ha='center', fontsize=size_labels)
    f.text(0.02, 0.5, 'Quantile (empirical)', va='center', rotation='vertical', fontsize=size_labels)
    if savefig:
        entire_path = os.path.join(path, fig_name)
        plt.savefig(entire_path)
    return f, fig_array

def correlogram(residuals, path=os.getcwd(), fig_name='correlogram.pdf', title=None, labels=None, model_labels=None,
                palette=None, n_lags=50, figsize=(8, 6), size_labels=16, size_ticks=14, size_legend=16, bottom=None,
                top=None, left=None, right=None,savefig=True):
    """
    Correlogram of residuals.

    :param residuals: list of lists (one list of residuals per event type) or list of lists of lists when multiple models are compared (one list of lists per model).
    :param path: string, where the figure is saved.
    :param fig_name: string, name of the file.
    :param title: string, suptitle.
    :param labels: list of strings, labels of the event types.
    :param model_labels: list of strings, names of the different considered models.
    :param palette: color palette (list of colors), one color per model.
    :param n_lags: int, number of lags to plot.
    :param figsize: tuple (width, height).
    :param size_labels: int, fontsize of labels.
    :param size_ticks: int, fontsize of tick labels.
    :param size_legend: int, fontsize of the legend.
    :param bottom: float between 0 and 1, adjusts the bottom margin, see matplotlib subplots_adjust.
    :param top: float between 0 and 1, adjusts the top margin, see matplotlib subplots_adjust.
    :param left: float between 0 and 1, adjusts the left margin, see matplotlib subplots_adjust.
    :param right: float between 0 and 1, adjusts the right margin, see matplotlib subplots_adjust.
    :param savefig: boolean, set to True to save the figure.
    :return:
    """
    # find number of models given and number of event types (dim)
    n_models = 1
    dim = len(residuals)
    if type(residuals[0][0]) in [list, np.ndarray]:  # case when there is more than one model
        n_models = len(residuals)
        dim = len(residuals[0])
    # set empty model labels if no labels provided
    if model_labels == None:
        model_labels = [None] * n_models
    v_size = dim
    h_size = dim
    seaborn.set()
    # seaborn.set_style('dark')  # no grid for good-looking small subplots
    if palette == None:
        palette = seaborn.color_palette('husl', n_models)
    f, fig_array = plt.subplots(v_size, h_size, figsize=figsize, sharex='col', sharey='row')
    if title != None:
        f.suptitle(title)
    for i in range(v_size):
        for j in range(h_size):
            axes = None
            if v_size == 1 and h_size == 1:
                axes = fig_array
            elif v_size == 1:
                axes = fig_array[j]
            elif h_size == 1:
                axes = fig_array[i]
            else:
                axes = fig_array[i, j]
            axes.tick_params(axis='both', which='major', labelsize=size_ticks)  # font size for tick labels
            if n_models == 1:
                max_length = min(len(residuals[i]), len(residuals[j]))
                ccf = stattools.ccf(np.array(residuals[i][0:max_length]),
                                    np.array(residuals[j][0:max_length]),
                                    unbiased=True)
                axes.plot(ccf[0:n_lags+1], color=palette[0])
                axes.set_xlim(xmin=0, xmax=n_lags)
            else:
                for m in range(n_models):
                    max_length = min(len(residuals[m][i]), len(residuals[m][j]))
                    ccf = stattools.ccf(np.array(residuals[m][i][0:max_length]),
                                        np.array(residuals[m][j][0:max_length]),
                                        unbiased=True)
                    axes.plot(ccf[0:n_lags + 1], color=palette[m], label=model_labels[m])
                    axes.set_xlim(xmin=0, xmax=n_lags)
                if i+j==0:  # only add legend in the first subplot
                    legend = axes.legend(frameon=1, fontsize=size_legend)
                    legend.get_frame().set_facecolor('white')
            if labels != None:
                axes.set_title(labels[i] + r'$\rightarrow$' + labels[j], fontsize=size_labels)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    if bottom!=None:
        plt.subplots_adjust(left=left, right=right, bottom=bottom, top=top)
    f.text(0.5, 0.025, 'Lag', ha='center', fontsize=size_labels)
    f.text(0.015, 0.5, 'Correlation', va='center', rotation='vertical', fontsize=size_labels)
    if savefig:
        entire_path = os.path.join(path, fig_name)
        plt.savefig(entire_path)

def transition_probabilities(probabilities, shape=None, path=os.getcwd(), fig_name='transition_probabilities.pdf',
                             events_labels=None, states_labels=None, title=None, color_map=None, fig_size=(12, 6),
                             size_labels=16, size_values=14, bottom=0.1, top=0.95, left=0.08, right=0.92,
                             wspace=0.2, hspace=0.2,
                             savefig=False, usetex=False):
    if color_map == None:
        color_map = seaborn.cubehelix_palette(as_cmap=True, reverse=False, start=0.5, rot=-.75)
    number_of_states = np.shape(probabilities)[0]
    number_of_event_types = np.shape(probabilities)[1]
    if shape == None:
        v_size = 1
        h_size = number_of_event_types
    else:
        v_size = shape[0]
        h_size = shape[1]
    f, fig_array = plt.subplots(v_size, h_size, figsize=fig_size)
    if title != None:
        f.suptitle(title)
    for i in range(v_size):
        for j in range(h_size):
            n = i*h_size + j
            if n < number_of_event_types:  # we could have more subplots than event types
                axes = None
                if v_size == 1 and h_size == 1:
                    axes = fig_array
                elif v_size == 1:
                    axes = fig_array[j]
                elif h_size == 1:
                    axes = fig_array[i]
                else:
                    axes = fig_array[i, j]
                axes.tick_params(axis='both', which='major', labelsize=size_labels)  # font size for tick labels
                # Create annotation matrix
                annot = np.ndarray((number_of_states, number_of_states), dtype=object)
                for x1 in range(number_of_states):
                    for x2 in range(number_of_states):
                        p = probabilities[x1, n, x2]
                        if p == 0:
                            if usetex:
                                annot[x1, x2] = r'$0$\%'
                            else:
                                annot[x1, x2] = r'0%'
                        elif p < 0.01:
                            if usetex:
                                annot[x1, x2] = r'$<1$\%'
                            else:
                                annot[x1, x2] = r'<1%'
                        else:
                            a = str(int(np.floor(100 * p)))
                            if usetex:
                                annot[x1, x2] = r'$' + a + r'$\%'
                            else:
                                annot[x1, x2] = a + r'%'
                seaborn.heatmap(probabilities[:, n, :], ax=axes,
                                xticklabels=states_labels, yticklabels=states_labels, annot=annot, cbar=False,
                                cmap=color_map, fmt='s', square=True, annot_kws={'size': size_values})
                axes.set_yticklabels(states_labels, va='center')
                if not usetex:
                    axes.set_title(r'$\phi_{' + events_labels[n] + '}$', fontsize=size_labels)
                else:
                    axes.set_title(r'$\bm{\phi}_{' + events_labels[n] + '}$', fontsize=size_labels)
    if bottom!=None:
        plt.subplots_adjust(bottom=bottom, top=top, left=left, right=right, wspace=wspace, hspace=hspace)
    f.text(0.5, 0.02, 'Next state', ha='center', fontsize=size_labels)
    f.text(0.02, 0.5, 'Previous state', va='center', rotation='vertical', fontsize=size_labels)
    if savefig:
        entire_path = os.path.join(path, fig_name)
        plt.savefig(entire_path)

def discrete_distribution(probabilities, path=os.getcwd(), fig_name='distribution_events_states.pdf', v_labels=None,
                          h_labels=None, title=None, color_map=None, figsize=(12, 6), size_labels=16, size_values=14,
                          bottom=None, top=None, left=None, right=None, savefig=False, usetex=False):
    if color_map == None:
        color_map = seaborn.cubehelix_palette(as_cmap=True, reverse=False, start=0.5, rot=-.75)
    v_size = np.shape(probabilities)[0]
    h_size = np.shape(probabilities)[1]
    # Create annotation matrix
    annot = np.ndarray((v_size, h_size), dtype=object)
    for x1 in range(v_size):
        for x2 in range(h_size):
            p = probabilities[x1, x2]
            if p == 0:
                if usetex:
                    annot[x1, x2] = r'$0$\%'
                else:
                    annot[x1, x2] = r'0%'
            elif p < 0.01:
                if usetex:
                    annot[x1, x2] = r'$<1$\%'
                else:
                    annot[x1, x2] = r'<1%'
            else:
                a = str(int(np.floor(100 * p)))
                if usetex:
                    annot[x1, x2] = r'$' + a + r'$\%'
                else:
                    annot[x1, x2] = a + r'%'
    plt.figure(figsize=figsize)
    ax = seaborn.heatmap(probabilities, xticklabels=h_labels, yticklabels=v_labels, annot=annot, cbar=False,
                    cmap=color_map, fmt='s', square=True, annot_kws={'size': size_values})
    ax.tick_params(axis='both', which='major', labelsize=size_labels)  # font size for tick labels
    ax.set_yticklabels(v_labels, va='center')
    if title != None:
        plt.title(title)
    plt.tight_layout()
    if bottom != None:
        plt.subplots_adjust(bottom=bottom, top=top, left=left, right=right)
    if savefig:
        entire_path = os.path.join(path, fig_name)
        plt.savefig(entire_path)

def kernels_exp(impact_coefficients, decay_coefficients, events_labels=None, states_labels=None, path=os.getcwd(),
                fig_name='kernels.pdf', title=None, palette=None, figsize=(9, 7), size_labels=16,
                size_values=14, size_legend=16, bottom=None, top=None, left=None, right=None, savefig=False,
                fig_array=None, fig=None,
                tmin=None, tmax=None, npoints=500, ymax=None, alpha=1, legend_pos=0):
    s = np.shape(impact_coefficients)
    number_of_event_types = s[0]
    number_of_states = s[1]
    beta_min = np.min(decay_coefficients)
    beta_max = np.max(decay_coefficients)
    t_max = tmax
    if tmax == None:
        t_max = -np.log(0.1) / beta_min
    t_min = tmin
    if tmin == None:
        t_min = -np.log(0.9) / beta_max
    order_min = np.floor(np.log10(t_min))
    order_max = np.ceil(np.log10(t_max))
    tt = np.logspace(order_min, order_max, num=npoints)
    norm_max = ymax
    if ymax is None:
        norm_max = np.max(np.divide(impact_coefficients, decay_coefficients)) * 1.05
    if palette is None:
        palette = seaborn.color_palette('husl', n_colors=number_of_states)
    if fig_array is None:
        fig, fig_array = plt.subplots(number_of_event_types, number_of_event_types, sharex='col', sharey='row',
                                figsize=figsize)
    for e1 in range(number_of_event_types):
        for e2 in range(number_of_event_types):
            axes = None
            if number_of_event_types == 1:
                axes = fig_array
            else:
                axes = fig_array[e1, e2]
            for x in range(number_of_states):  # mean
                a = impact_coefficients[e1, x, e2]
                b = decay_coefficients[e1, x, e2]
                yy = a / b * (1 - np.exp(-b * tt))
                l = None
                if np.shape(states_labels) != ():
                    l = states_labels[x]
                axes.plot(tt, yy, color=palette[x], label=l, alpha=alpha)
            axes.tick_params(axis='both', which='major', labelsize=size_values)  # font size for tick labels
            axes.set_xscale('log')
            axes.set_ylim(ymin=0, ymax=norm_max)
            axes.set_xlim(xmin=t_min, xmax=t_max)
            if np.shape(events_labels) != ():
                axes.set_title(events_labels[e1] + r' $\rightarrow$ ' + events_labels[e2], fontsize=size_labels)
            pos = e2 + number_of_event_types*e1
            if pos == legend_pos and np.shape(states_labels) != () :
                legend = axes.legend(frameon=1, fontsize=size_legend)
                legend.get_frame().set_facecolor('white')
    if title != None:
        fig.suptitle(title, fontsize=size_labels)
    plt.tight_layout()
    if bottom != None:
        plt.subplots_adjust(bottom=bottom, top=top, left=left, right=right)
    if savefig:
        entire_path = os.path.join(path, fig_name)
        plt.savefig(entire_path)
    return fig, fig_array

def sample_path(times, events, states, model, time_start, time_end, color_palette=None, labelsize=16, ticksize=14,
                legendsize=16, num=1000, s=12, savefig=False, path='', fig_name='sample_path.pdf'):
    if color_palette is None:
        color_palette = seaborn.color_palette('husl', n_colors=model.number_of_event_types)
    'Compute the intensities - this may require all the event times prior to start_time'
    compute_times = np.linspace(time_start, time_end, num=num)
    aggregated_times, intensities = model.intensities_of_events_at_times(compute_times, times, events, states)
    'We can now discard the times outside the desired time period'
    index_start = bisect.bisect_left(times, time_start)
    index_end = bisect.bisect_right(times, time_end)
    initial_state = 0
    if index_start > 0:
        initial_state = states[index_start-1]
    times = copy.copy(times[index_start:index_end])
    events = copy.copy(events[index_start:index_end])
    states = copy.copy(states[index_start:index_end])
    seaborn.set(style='darkgrid')
    plt.figure()
    f, fig_array = plt.subplots(2, 1, sharex='col')
    'Plot the intensities'
    ax = fig_array[1]
    ax.tick_params(axis='both', which='major', labelsize=ticksize)
    # intensity_max = intensities.max() * 1.01
    for n in range(model.number_of_event_types):
        ax.plot(aggregated_times, intensities[n], linewidth=1, color=color_palette[n], label=model.events_labels[n])
    ax.set_ylim(ymin=0)
    ax.set_ylabel('Intensity', fontsize=labelsize)
    ax.set_xlabel('Time', fontsize=labelsize)
    legend = ax.legend(frameon=1, fontsize=legendsize)
    legend.get_frame().set_facecolor('white')
    'Plot the state process and the events'
    ax = fig_array[0]
    ax.tick_params(axis='both', which='major', labelsize=ticksize)
    # Plot the event times and types, one color per event type, y-coordinate corresponds to new state of the system
    color_map = ListedColormap(color_palette)
    ax.scatter(times, states, c=events, cmap=color_map, s=s, alpha=1, edgecolors='face',
               zorder=10)
    ax.set_xlim(xmin=time_start, xmax=time_end)
    ax.set_ylim(ymin=-0.1, ymax=model.number_of_states - 0.9)
    ax.set_yticks(range(model.number_of_states))
    ax.set_yticklabels(model.states_labels, fontsize=ticksize)
    ax.set_ylabel('State', fontsize=labelsize)
    # Plot the state process
    times.insert(0, time_start)
    states.insert(0, initial_state)
    times.append(time_end)
    states.append(states[-1])  # these two appends are required to plot until `time_end'
    ax.step(times, states, where='post', linewidth=1, color='grey', zorder=1)
    # Save the figure
    plt.tight_layout()
    plt.subplots_adjust(left=0.1, right=0.9)
    if savefig:
        entire_path = os.path.join(path, fig_name)
        plt.savefig(entire_path)
    return f, fig_array