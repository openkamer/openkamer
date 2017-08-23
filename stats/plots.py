import datetime
import logging

import numpy as np

from django.utils import timezone
from plotly.offline import plot
from plotly.graph_objs import Layout, Histogram, Histogram2d, Scatter, XAxis, Margin
import plotly.figure_factory as ff


logger = logging.getLogger(__name__)

COLOR_PRIMARY = '#4582ec'
COLOR_INFO = '#5bc0de'
COLOR_SUCCESS = '#3fad46'
COLOR_WARNING = '#f0ad4e'
COLOR_DANGER = '#d9534f'


def movingaverage(values, window):
    weights = np.repeat([1.0], window)/window
    sma = np.convolve(values, weights, 'valid')
    return sma


def movingaverage_from_histogram(bin_values, bin_edges, window):
    x = bin_edges[:-1]
    y = bin_values
    y_moving_avg = movingaverage(y, window)
    return x, y_moving_avg


def bin_datetimes(datetimes, range_years, bin_size_days, weights=None):
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
    bin_values, bin_edges = np.histogram(timestamps, bins, density=False, weights=weights)
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


class Plot(object):
    plot_title = None

    def __init__(self):
        super().__init__()
        logger.info('create plot')

    def create_data(self):
        raise NotImplementedError

    def create_layout(self):
        raise NotImplementedError

    def create_plot(self):
        logger.info('BEGIN')
        plot_data = self.create_data()
        assert isinstance(plot_data, list)
        plot_layout = self.create_layout()
        assert plot_layout is not None
        plot_config = self.create_plot_config(plot_data, plot_layout)
        assert plot_config is not None
        logger.info('END')
        return Plot.create_plot_html_default(plot_config)

    @staticmethod
    def create_plot_config(data, layout):
        return {"data": data, "layout": layout}

    @staticmethod
    def create_plot_html_default(figure_or_data):
        return plot(
            figure_or_data=figure_or_data,
            show_link=False,
            output_type='div',
            include_plotlyjs=False,
            auto_open=False,
        )


class PlotKamervraagVsTime(Plot):

    def __init__(self, kamervraag_dates):
        super().__init__()
        self.kamervraag_dates = kamervraag_dates

    def create_data(self):
        bin_values, bin_edges = bin_datetimes(self.kamervraag_dates, range_years=7, bin_size_days=7)
        x, y_moving_avg = movingaverage_from_histogram(bin_values, bin_edges, window=8)

        moving_average_scatter = Scatter(
            x=x,
            y=y_moving_avg,
            mode='lines',
            name='lopende trend',
            line=dict(
                color=COLOR_WARNING,
                width=3,
            ),
        )

        hist_data = Histogram(
            x=self.kamervraag_dates,
            autobinx=False,
            xbins=dict(
                start=(timezone.now() - datetime.timedelta(days=7 * 365)).timestamp() * 1000,
                end=timezone.now().timestamp() * 1000,
                size=60 * 60 * 24 * 7 * 1000
            ),
            marker=dict(
                color=COLOR_INFO,
                line=dict(
                    color=COLOR_PRIMARY,
                    width=1,
                )
            ),
            name='vragen per week',
        )

        return [hist_data, moving_average_scatter]

    def create_layout(self):
        return Layout(
            title=self.plot_title,
            xaxis=dict(title='Tijd'),
            yaxis=dict(title='Kamervragen per week'),
            margin=Margin(t=20),
            legend=dict(
                x=0.01,
                y=1,
                bordercolor='#E2E2E2',
                bgcolor='#FFFFFF',
                borderwidth=2
            )
        )


class PlotKamervraagVsTimePerParty(Plot):

    def __init__(self, party_labels, party_kamervragen_dates):
        super().__init__()
        self.party_labels = party_labels
        self.party_kamervragen_dates = party_kamervragen_dates

    def create_data(self):
        data = []
        for i in range(0, len(self.party_labels)):
            bin_values, bin_edges = bin_datetimes(self.party_kamervragen_dates[i], range_years=7, bin_size_days=30)
            x, y_moving_avg = movingaverage_from_histogram(bin_values, bin_edges, window=3)

            x_new = []
            for value in x:
                date = datetime.datetime.fromtimestamp(value / 1000.0)
                x_new.append(date)

            moving_average_scatter = Scatter(
                x=x_new,
                y=y_moving_avg,
                mode='lines',
                name=self.party_labels[i],
                line=dict(shape='spline'),
            )
            data.append(moving_average_scatter)
        return data

    def create_layout(self):
        return Layout(
            xaxis=dict(title='Tijd'),
            yaxis=dict(title='Kamervragen per maand'),
            margin=Margin(t=20),
            legend=dict(
                # x=0.01,
                # y=1,
                bordercolor='#E2E2E2',
                bgcolor='#FFFFFF',
                borderwidth=2
            )
        )


class PlotKamervraagVsTimePerPartySeat(Plot):

    def __init__(self, party_labels, party_kamervragen_dates, party_seats):
        super().__init__()
        self.party_labels = party_labels
        self.party_kamervragen_dates = party_kamervragen_dates
        self.party_seats = party_seats

    def create_data(self):
        data = []
        for i in range(0, len(self.party_labels)):
            weights = []
            for seat in self.party_seats[i]:
                weights.append(1 / seat)
            bin_values, bin_edges = bin_datetimes(self.party_kamervragen_dates[i], range_years=7, bin_size_days=30,
                                                  weights=weights)

            x, y_moving_avg = movingaverage_from_histogram(bin_values, bin_edges, window=3)

            x_new = []
            for value in x:
                date = datetime.datetime.fromtimestamp(value / 1000.0)
                x_new.append(date)

            moving_average_scatter = Scatter(
                x=x_new,
                y=y_moving_avg,
                mode='lines',
                name=self.party_labels[i],
                line=dict(shape='spline'),
            )
            data.append(moving_average_scatter)
        return data

    def create_layout(self):
        return Layout(
            yaxis=dict(title='Kamervragen per kamerzetel per maand', range=[0, 6]),
            margin=Margin(t=20, b=20),
            legend=dict(
                # x=0.01,
                # y=1,
                bordercolor='#E2E2E2',
                bgcolor='#FFFFFF',
                borderwidth=2
            )
        )


class PlotKamervraagReplyTimeHistogram(Plot):

    def __init__(self, kamervraag_durations):
        super().__init__()
        self.kamervraag_durations = kamervraag_durations

    def create_data(self):
        return [Histogram(
            x=self.kamervraag_durations,
            autobinx=False,
            xbins=dict(start=0, end=100, size=1),
            marker=dict(
                color=COLOR_INFO,
                line=dict(
                    color=COLOR_PRIMARY,
                    width=2,
                )
            ),
        )]

    def create_layout(self):
        return Layout(
            # title="Dagen tot Antwoord",
            xaxis=dict(title='Antwoordtijd [dagen]'),
            yaxis=dict(title='Aantal Kamervragen'),
            margin=Margin(t=20)
        )


class PlotKamervraagReplyTimeContour(Plot):

    def __init__(self, kamervraag_dates, kamervraag_durations):
        super().__init__()
        self.kamervraag_dates = kamervraag_dates
        self.kamervraag_durations = kamervraag_durations

    def create_data(self):
        return [Histogram2d(
            x=self.kamervraag_dates,
            y=self.kamervraag_durations,
            histnorm='',
            autobinx=False,
            xbins=dict(
                start=(timezone.now() - datetime.timedelta(days=7 * 365)).timestamp() * 1000,
                end=timezone.now().timestamp() * 1000,
                size=60 * 60 * 24 * 14 * 1000
            ),
            autobiny=False,
            ybins=dict(start=0, end=80, size=3),
            colorscale='Jet',
            # colorscale='Viridis',
            # colorscale=[[0, 'rgb(12,51,131)'], [0.25, 'rgb(10,136,186)'], [0.5, 'rgb(242,211,56)'],
            #            [0.75, 'rgb(242,143,56)'], [1, 'rgb(217,30,30)']],
            zsmooth='best',
            zauto=False,
            zmin=0,
            zmax=21,
        )]

    def create_layout(self):
        return Layout(
                # title="Kamervraag Antwoordtijd vs Tijd",
                xaxis=dict(title='Kamervraag Ingediend [tijd]'),
                yaxis=dict(title='Antwoordtijd [dagen]'),
                autosize=False,
                width=1000,
                height=500,
                margin=Margin(t=20)
            )


class PlotPartySeatsVsTime(Plot):

    def __init__(self, party_labels, dates, seats):
        super().__init__()
        self.party_labels = party_labels
        self.dates = dates
        self.seats = seats

    def create_data(self):
        data = []
        for i in range(0, len(self.party_labels)):
            party_data = Scatter(
                x=self.dates[i],
                y=self.seats[i],
                mode='lines',
                name=self.party_labels[i],
                line=dict(shape='hv')
                # line=dict(shape='spline'),
            )
            data.append(party_data)
        return data

    def create_layout(self):
        return Layout(
            # title="Kamervragen per Week",
            xaxis=dict(title='Tijd'),
            yaxis=dict(title='Zetels per partij'),
            margin=Margin(t=20),
            legend=dict(
                # x=0.01,
                # y=1,
                bordercolor='#E2E2E2',
                bgcolor='#FFFFFF',
                borderwidth=2
            )
        )


def kamervragen_reply_time_per_party(parties, kamervraag_durations):
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
        range=[0, 60],
    )

    fig['layout'].update(xaxis=xaxis)
    # fig['layout'].update(title="Kamervraag Antwoordtijd per Partij (probability distributie)")
    fig['layout'].update(xaxis=dict(title='Antwoordtijd [dagen]'))
    # fig['layout'].update(yaxis=dict(title='Kamervraag Ingediend [tijd]'))
    fig['layout'].update(height=700)
    legend = dict(
        # x=0.01,
        # y=1,
        bordercolor='#E2E2E2',
        bgcolor='#FFFFFF',
        borderwidth=2
    )
    fig['layout'].update(legend=legend)
    fig['layout'].update(margin=Margin(t=20))

    return Plot.create_plot_html_default(figure_or_data=fig)


def kamervragen_reply_time_per_ministry(ministries, kamervraag_durations):
    fig = ff.create_distplot(
        kamervraag_durations,
        ministries,
        # colors=colors,
        bin_size=1,
        show_curve=True,
        show_hist=False,
        show_rug=False
    )

    xaxis = XAxis(range=[0, 70])

    fig['layout'].update(xaxis=xaxis)
    # fig['layout'].update(title="Kamervraag Antwoordtijd per Ministerie tijdens Rutte-II (KDE probability distributie)")
    fig['layout'].update(xaxis=dict(title='Antwoordtijd [dagen]'))
    # fig['layout'].update(yaxis=dict(title=''))
    fig['layout'].update(height=700)
    fig['layout'].update(margin=Margin(t=20))
    legend = dict(
        # x=0.01,
        # y=1,
        bordercolor='#E2E2E2',
        bgcolor='#FFFFFF',
        borderwidth=2
    )
    fig['layout'].update(legend=legend)

    return Plot.create_plot_html_default(figure_or_data=fig)


def kamervragen_reply_time_per_year(years, kamervraag_durations):
    fig = ff.create_distplot(
        kamervraag_durations,
        years,
        # colors=colors,
        bin_size=1,
        show_curve=True,
        show_hist=False,
        show_rug=False
    )

    xaxis = XAxis(range=[0, 60])

    fig['layout'].update(xaxis=xaxis)
    # fig['layout'].update(title="Kamervraag Antwoordtijd per Ministerie tijdens Rutte-II (KDE probability distributie)")
    fig['layout'].update(xaxis=dict(title='Antwoordtijd [dagen]'))
    # fig['layout'].update(yaxis=dict(title=''))
    fig['layout'].update(height=700)
    fig['layout'].update(margin=Margin(t=20))
    legend = dict(
        # x=0.01,
        # y=1,
        bordercolor='#E2E2E2',
        bgcolor='#FFFFFF',
        borderwidth=2
    )
    fig['layout'].update(legend=legend)

    return Plot.create_plot_html_default(figure_or_data=fig)
