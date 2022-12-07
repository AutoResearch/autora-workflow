from itertools import product
from typing import List, Sequence, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from autora.cycle import Cycle


def parse_dv_iv(
    cycle: Cycle, iv_names: Union[str, List[str]] = None, dv_name: str = None
):
    """
    Selects the independent (IV) and dependent (DV) variables defined in cycle based from optional
    user input. Returns a list of IV tuples (index, IV) single DV tuple (index, Variable). The index
    is in reference to the column in which the variable appears in the cycle's observed data
    structures.

    Args:
        cycle: AER Cycle object that has been run
        iv_names: List of up to 2 independent variable names. Names should match the names
                    instantiated in the cycle object. Default will select up to the first two.
        dv_name: Single DV name. Name should match the names instantiated in the cycle object.
                    Default will select the first DV

    Returns: List of independent variable tuples (index, Variable) and single dependent variable
    tuple (index, Variable).

    """

    l_iv = cycle.data.metadata.independent_variables
    l_dv = cycle.data.metadata.dependent_variables
    n_iv = len(l_iv)

    # Input conversion
    if isinstance(iv_names, str):
        iv_names = [iv_names]

    # Select independent variables to plot
    if iv_names:  # If user supplies names
        # TODO deal with order of ivs if specified, currently plots x1,x2 in the order
        #  specified in the cycle metadata.
        assert (
            len(iv_names) <= 2
        ), f"Cannot plot more than two IVs; got {len(iv_names)}."
        l_iv_to_plot = [(i, s) for i, s in enumerate(l_iv) if s.name in iv_names]
        assert len(l_iv_to_plot) == len(iv_names), (
            "Invalid IV name(s) detected. "
            "Check that iv_names keyword matches model IV "
            "names."
        )
    else:  # If not specified take up to the first 2 IVs
        l_iv_to_plot = [(i, s) for i, s in enumerate(l_iv[:2])]

    # Select dependent variable to plot
    # In the data structure DVs are after IVs. The number of IVs is added to get the DV index.
    if dv_name:
        try:
            dv_to_plot = [
                (i + n_iv, s) for i, s in enumerate(l_dv) if s.name == dv_name
            ][0]
        except IndexError:
            raise IndexError(
                f'Dependent variable "{dv_name}" was not found in the model. '
                f"Check DV name."
            )

    else:
        dv_to_plot = (n_iv, l_dv[0])

    return l_iv_to_plot, dv_to_plot


def observed_to_df(cycle: Cycle):
    """
    Concatenates observation data of cycles into a single dataframe with a field "cycle" with the
    cycle index.
    Args:
        cycle: AER Cycle object that has been run

    Returns: Dataframe

    """
    l_observations = cycle.data.observations
    l_agg = []

    for i, data in enumerate(l_observations):
        l_agg.append(pd.DataFrame(data).assign(cycle=i))

    return pd.concat(l_agg)


def generate_condition_space(cycle: Cycle, steps: int = 50):
    """
    Generates condition space based on the minimum and maximum of all observed data in AER Cycle.
    Args:
        cycle: AER Cycle object that has been run
        steps: Number of steps to define the condition space

    Returns:

    """
    iv_index = range(len(cycle.data.metadata.independent_variables))
    l_observations = cycle.data.observations
    l_space = []

    # Get min and max of observation data
    # Min and max by cycle - All IVs
    l_mins = [np.min(s, axis=0) for s in l_observations]  # Arrays by columns
    l_maxs = [np.max(s, axis=0) for s in l_observations]
    # Min and max for all cycles by IVs
    for idx in iv_index:
        glob_min = np.min([s[idx] for s in l_mins])
        glob_max = np.max([s[idx] for s in l_maxs])
        l_space.append(np.linspace(glob_min, glob_max, steps))

    if len(l_space) > 1:
        # TODO Check if this outputs the correct shape
        return np.array(list(product(*l_space)))
    else:
        return l_space[0].reshape(-1, 1)


def theory_predict(cycle: Cycle, conditions: Sequence):
    """
    Gets theory predictions over conditions space and saves results of each cycle to a dictionary.
    Args:
        cycle: AER Cycle object that has been run
        conditions: Condition space. Should be an array of grouped conditions.

    Returns:

    """
    d_predictions = {}
    for i, theory in enumerate(cycle.data.theories):
        d_predictions[i] = theory.predict(conditions)

    return d_predictions


def plot_results_panel(
    cycle: Cycle,
    iv_names: Union[str, List[str]] = None,
    dv_name: str = None,
    steps: int = 50,
    wrap: int = 4,
    **kwargs,
):
    """
    Generates a multi-panel plot with each panel showing results of an AER cycle. Observed data
    is plotted as a scatter plot with the current cycle colored differently than observed data from
    previous cycles. The current cycle's theory is plotted as a line over the range of the observed
    data.
    Args:
        cycle: AER Cycle object that has been run
        iv_names: List of up to 2 independent variable names. Names should match the names
                    instantiated in the cycle object. Default will select up to the first two.
        dv_name: Single DV name. Name should match the names instantiated in the cycle object.
                    Default will select the first DV
        steps: Number of steps to define the condition space to plot the theory.
        wrap: Number of panels to appear in a row. Example: 9 panels with wrap=3 results in a
                3x3 grid.
        **kwargs:

        TODO: 1. 3D Plotting - Plotting with 2 IVs
              2. Ability to supply different optional kwargs for matplotlib subplot (subplot_kw,
                 gridspec_kw, fig_kw) so user can better tune figure layout paramters.
              3. Optional keywords to plotting calls to adjust appearance of points, lines/planes.
              4. Save to file feature.

    Returns: matplotlib figure

    """
    n_cycles = len(cycle.data.theories)
    threedim = False

    # Extract IVs and DV metadata and indexes
    ivs, dv = parse_dv_iv(cycle, iv_names, dv_name)
    if len(ivs) > 1:
        threedim = True
    iv_labels = [f"{s[1].name} {s[1].units}" for s in ivs]
    dv_label = f"{dv[1].name} {dv[1].units}"

    # Create a dataframe of observed data from cycle
    df_observed = observed_to_df(cycle)

    # Generate IV space
    condition_space = generate_condition_space(cycle, steps=steps)
    # Get theory predictions over space
    d_predictions = theory_predict(cycle, condition_space)

    # Subplot configurations
    if n_cycles < wrap:
        shape = (1, n_cycles)
    else:
        shape = (int(np.ceil(n_cycles / wrap)), wrap)
    if threedim:
        kwargs["projection"] = "3d"
    fig, axs = plt.subplots(*shape, **kwargs)

    # Loop by panel
    for i, ax in enumerate(axs.flat):
        if i + 1 <= n_cycles:
            ax.set_title(f"Cycle {i}")

            # ---Plot observed data---
            # Independent variable values
            l_x = [df_observed.loc[:, s[0]] for s in ivs]
            # Dependent values masked by current cycle vs previous data
            dv_previous = np.ma.masked_where(
                df_observed["cycle"] >= i, df_observed[dv[0]]
            )
            dv_current = np.ma.masked_where(
                df_observed["cycle"] != i, df_observed[dv[0]]
            )
            # Plotting scatter
            ax.scatter(*l_x, dv_previous, s=2, marker="x", label="Previous Data")
            ax.scatter(*l_x, dv_current, c="orange", s=2, alpha=0.6, label="New Data")

            # ---Plot Theory---
            if not threedim:
                ax.plot(condition_space, d_predictions[i], label="Theory")
            else:  # 3D Plotting
                ax.plot_surface(
                    *condition_space, d_predictions[i], alpha=0.5, label="Theory"
                )
                # Axis labels
                ax.set_xlabel(iv_labels[0])
                ax.set_ylabel(iv_labels[1])
                ax.set_zlabel(dv_label)

        else:
            ax.axis("off")

    # Super Labels for 2D Plots
    if not threedim:
        fig.supxlabel(iv_labels[0])
        fig.supylabel(dv_label)

    # Legend
    fig.legend(
        ["Previous Data", "New Data", "Theory"],
        ncols=3,
        bbox_to_anchor=(0.5, -0.025),
        loc="center",
    )

    return fig
