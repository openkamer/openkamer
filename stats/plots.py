import datetime

import numpy as np

from django.utils import timezone
from plotly.offline import plot
from plotly.graph_objs import Layout, Histogram, Histogram2d, Scatter, XAxis
import plotly.figure_factory as ff


def movingaverage(values, window):
    weights = np.repeat([1.0], window)/window
    sma = np.convolve(values, weights, 'full')
    return sma


def movingaverage_from_histogram(bin_values, bin_edges, window):
    x = bin_edges[:-1]
    y = bin_values
    y_moving_avg = movingaverage(y, window)
    return x, y_moving_avg


def bin_datetimes(datetimes, range_years, bin_size_days):
    bin_start = (timezone.now() - datetime.timedelta(days=range_years * 365)).timestamp() * 1000
    bin_end = timezone.now().timestamp() * 1000
    num_bins = (bin_end - bin_start) / (60 * 60 * 24 * bin_size_days * 1000)
    timestamps = []
    for date in datetimes:
        timestamp = datetime.datetime.combine(date, datetime.datetime.min.time()).timestamp()
        timestamps.append(timestamp * 1000)
    bins = np.linspace(
        start=bin_start,
        stop=bin_end,
        num=num_bins,
        endpoint=True
    )
    bin_values, bin_edges = np.histogram(timestamps, bins, density=False)
    return bin_values, bin_edges


def polyfit(x, y, bin_size, deg):
    z = np.polyfit(x, y, deg)
    f = np.poly1d(z)
    x_new = np.linspace(x[0], x[-1], bin_size)
    y_new = f(x_new)

    polyfit_data = Scatter(
        x=x_new,
        y=y_new,
        mode='lines'
    )
    return polyfit_data


def kamervraag_vs_time_plot_html(kamervraag_dates):
    bin_values, bin_edges = bin_datetimes(kamervraag_dates, range_years=7, bin_size_days=7)
    x, y_moving_avg = movingaverage_from_histogram(bin_values, bin_edges, window=8)

    moving_average_scatter = Scatter(
        x=x,
        y=y_moving_avg,
        mode='lines',
        name='lopende trend',
        marker=dict(
            line=dict(
                width=2,
            )
        ),
    )

    hist_data = Histogram(
        x=kamervraag_dates,
        autobinx=False,
        xbins=dict(
            start=(timezone.now() - datetime.timedelta(days=7 * 365)).timestamp() * 1000,
            end=timezone.now().timestamp() * 1000,
            size=60 * 60 * 24 * 7 * 1000
        ),
        marker=dict(
            color='rgb(158,202,225)',
            line=dict(
                color='rgb(8,48,107)',
                width=0,
            )
        ),
        name='vragen per week',
        # showlegend=False
    )
    return plot(
        # figure_or_data=fig,
        figure_or_data={
            "data": [hist_data, moving_average_scatter],
            "layout": Layout(
                title="Kamervragen per Week",
                xaxis=dict(title='Tijd'),
                yaxis=dict(title='Kamervragen per week'),
                legend=dict(
                    x=0.01,
                    y=1,
                    bordercolor='#E2E2E2',
                    bgcolor='#FFFFFF',
                    borderwidth=2
                )
            )
        },
        show_link=False,
        output_type='div',
        include_plotlyjs=False,
        auto_open=False,
    )


def kamervraag_reply_time_histogram_plot_html(kamervraag_durations):
    return plot(
        figure_or_data={
            # "data": [Scatter(x=data_x, y=data_y)],
            "data": [Histogram(
                x=kamervraag_durations,
                autobinx=False,
                xbins=dict(
                    start=0,
                    end=100,
                    size=1
                ),
            )],
            "layout": Layout(
                title="Dagen tot Antwoord",
                xaxis=dict(title='Antwoordtijd [dagen]'),
                yaxis=dict(title='Aantal Kamervragen'),
            ),
        },
        show_link=False,
        output_type='div',
        include_plotlyjs=False,
        auto_open=False,
    )


def kamervraag_reply_time_contour_plot_html(kamervraag_dates, kamervraag_duration):
    data = [
        Histogram2d(
            x=kamervraag_dates,
            y=kamervraag_duration,
            histnorm='',
            autobinx=False,
            xbins=dict(
                start=(timezone.now() - datetime.timedelta(days=7 * 365)).timestamp() * 1000,
                end=timezone.now().timestamp() * 1000,
                size=60 * 60 * 24 * 14 * 1000
            ),
            autobiny=False,
            ybins=dict(
                start=0,
                end=80,
                size=3
            ),
            colorscale='Jet',
            # colorscale='Viridis',
            # colorscale=[[0, 'rgb(12,51,131)'], [0.25, 'rgb(10,136,186)'], [0.5, 'rgb(242,211,56)'],
            #            [0.75, 'rgb(242,143,56)'], [1, 'rgb(217,30,30)']],
            zsmooth='best',
            zauto=False,
            zmin=0,
            zmax=21,
        ),
    ]
    return plot(
        figure_or_data={
            # "data": [Scatter(x=data_x, y=data_y)],
            "data": data,
            "layout": Layout(
                title="Kamervraag Antwoordtijd vs Tijd",
                xaxis=dict(title='Kamervraag Ingediend [tijd]'),
                yaxis=dict(title='Antwoordtijd [dagen]'),
                autosize=False,
                width=1000,
                height=500,
            ),
        },
        show_link=False,
        output_type='div',
        include_plotlyjs=False,
        auto_open=False,
    )


def kamervragen_reply_time_per_party(parties, kamervraag_durations):
    colors = ['#393E46', '#2BCDC1', '#F66095']
    # colors = ['#393E46', '#2BCDC1']
    fig = ff.create_distplot(
        kamervraag_durations,
        parties,
        # colors=colors,
        bin_size=1,
        show_curve=True,
        show_hist=False,
        show_rug=False
    )

    xaxis = XAxis(
        range=[0, 50],
    )

    fig['layout'].update(xaxis=xaxis)
    fig['layout'].update(title="Kamervraag Antwoordtijd per Partij (Probability Distributie)")
    fig['layout'].update(xaxis=dict(title='Antwoordtijd [dagen]'))
    # fig['layout'].update(yaxis=dict(title='Kamervraag Ingediend [tijd]'))
    fig['layout'].update(height=700)
    legend = dict(
        x=0.01,
        y=1,
        bordercolor='#E2E2E2',
        bgcolor='#FFFFFF',
        borderwidth=2
    )
    fig['layout'].update(legend=legend)

    return plot(
        figure_or_data=fig,
        show_link=False,
        output_type='div',
        include_plotlyjs=False,
        auto_open=False,
    )