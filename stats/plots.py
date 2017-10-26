import datetime
import logging

import numpy as np

from django.utils import timezone
from plotly.offline import plot
from plotly import tools
from plotly.graph_objs import Layout, Bar, Histogram, Histogram2d, Scatter, XAxis, Margin
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
            yaxis=dict(title='Kamervragen [per week]'),
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
            yaxis=dict(title='Kamervragen [per maand]'),
            margin=Margin(t=20, b=30),
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
            yaxis=dict(title='Kamervragen per partijzetel [per maand]', range=[0, 6]),
            margin=Margin(t=20, b=30),
            legend=dict(
                # x=0.01,
                # y=1,
                bordercolor='#E2E2E2',
                bgcolor='#FFFFFF',
                borderwidth=2
            )
        )


class PlotKamervraagVsTimePerCategory(object):

    def __init__(self, category_labels, categories, category_kamervragen_dates, kamervraag_dates_all):
        super().__init__()
        self.category_labels = category_labels
        self.category_kamervragen_dates = category_kamervragen_dates
        self.kamervraag_dates_all = kamervraag_dates_all
        self.categories = categories

    def create_plots(self):
        logger.info('BEGIN')
        data_set = self.create_data()
        layout = self.create_layout()
        plots = []
        for i in range(0, len(data_set)):
            layout['title'] = self.category_labels[i]
            plot_config = Plot.create_plot_config([*data_set[i]], layout)
            plots.append(Plot.create_plot_html_default(plot_config))
        return plots, self.categories

    def create_data_hist(self, kamervragen_dates, bin_values_all):
        print('create_data_hist')
        bin_size_days = 365/2
        hist_data = Histogram(
            x=kamervragen_dates,
            autobinx=False,
            xbins=dict(
                start=(timezone.now() - datetime.timedelta(days=7 * 365)).timestamp() * 1000,
                end=timezone.now().timestamp() * 1000,
                size=60 * 60 * 24 * bin_size_days * 1000
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
        return hist_data

    def create_data_bar(self):
        bin_size_days = int(365/12)
        moving_avg_window = 2

        bin_values_all, bin_edges = bin_datetimes(self.kamervraag_dates_all, range_years=7, bin_size_days=bin_size_days)
        # x_all, y_moving_avg_all = movingaverage_from_histogram(bin_values_all, bin_edges, window=moving_avg_window)
        bin_all_average = sum(bin_values_all) / len(bin_values_all)

        data_list = []
        for i in range(0, len(self.category_labels)):
            # histogram = self.create_data_hist(self.category_kamervragen_dates[i], bin_values_all)
            # data_list.append(histogram)
            # if i > 10:
            #     return data_list
            # continue
            bin_values, bin_edges = bin_datetimes(self.category_kamervragen_dates[i], range_years=7, bin_size_days=bin_size_days)
            # bin_values_norm = []
            # for k in range(0, len(bin_values)):
            #     if bin_values_all[k] == 0:
            #         bin_value_relative = 0
            #     else:
            #         bin_value_relative = bin_values[k]/bin_values_all[k]
            #     bin_values_norm.append(bin_value_relative)
            # x, y_moving_avg = movingaverage_from_histogram(bin_values, bin_edges, window=moving_avg_window)

            bin_average = sum(bin_values)/len(bin_values)
            fraction_of_all_average = bin_average/bin_all_average

            y_new = []
            for j in range(0, len(bin_values)):
                if bin_values_all[j] == 0:
                    y_new.append(0)
                else:
                    y_new.append(bin_values[j]/bin_values_all[j] / fraction_of_all_average)

            x_new = []
            for value in bin_edges:
                date = datetime.datetime.fromtimestamp(value / 1000.0)
                x_new.append(date)

            moving_average_scatter = Bar(
                x=x_new,
                y=y_new,
                name=self.category_labels[i],
            )
            data_list.append(moving_average_scatter)
        return data_list

    def create_data(self):
        bin_size_days = int(365/6)
        moving_avg_window = 3

        bin_values_all, bin_edges = bin_datetimes(self.kamervraag_dates_all, range_years=7, bin_size_days=bin_size_days)
        max_y_all = max(bin_values_all)
        min_y_all = min(bin_values_all)
        # x_all, y_moving_avg_all = movingaverage_from_histogram(bin_values_all, bin_edges, window=moving_avg_window)
        bin_all_average = sum(bin_values_all) / len(bin_values_all)
        bin_values_norm_all = []
        fractions_from_average = []
        for k in range(0, len(bin_values_all)):
            diff_from_average = bin_values_all[k] - bin_all_average
            fraction_from_average = diff_from_average/bin_all_average
            print(fraction_from_average)
            fractions_from_average.append(fraction_from_average)

        data_list = []
        for i in range(0, len(self.category_labels)):
            # histogram = self.create_data_hist(self.category_kamervragen_dates[i], bin_values_all)
            # data_list.append(histogram)
            # if i > 10:
            #     return data_list
            # continue
            bin_values, bin_edges = bin_datetimes(self.category_kamervragen_dates[i], range_years=7, bin_size_days=bin_size_days)

            max_y = max(bin_values)
            min_y = min(bin_values)
            bin_values_norm = []
            for k in range(0, len(bin_values)):
                bin_value_norm = (bin_values[k]-min_y) / (max_y-min_y)
                bin_values_norm.append(bin_value_norm)

            bin_avg = sum(bin_values_norm) / len(bin_values_norm)
            bin_values_corrected = []
            for k in range(0, len(bin_values_norm)):
                bin_values_corrected.append(bin_values_norm[k] - (bin_avg*fractions_from_average[k]))
                # bin_values_corrected.append(bin_values_norm[k])

            max_y = max(bin_values_corrected)
            min_y = min(bin_values_corrected)
            bin_values_norm = []
            for k in range(0, len(bin_values_corrected)):
                bin_value_norm = (bin_values_corrected[k]-min_y) / (max_y-min_y)
                bin_values_norm.append(bin_value_norm)

            bin_average = sum(bin_values_norm) / len(bin_values_norm)
            bin_values_norm2 = []
            for k in range(0, len(bin_values_norm)):
                bin_value_norm2 = bin_values_norm[k] - bin_average
                bin_values_norm2.append(bin_value_norm2)

            x, y_moving_avg = movingaverage_from_histogram(bin_values_norm2, bin_edges, window=moving_avg_window)
            #
            # bin_average = sum(y_moving_avg)/len(y_moving_avg)
            # fraction_of_all_average = bin_average/bin_all_average
            #
            # y_new = []
            # for j in range(0, len(y_moving_avg)):
            #     if y_moving_avg_all[j] == 0:
            #         y_new.append(0)
            #     else:
            #         y_new.append(y_moving_avg[j]/y_moving_avg_all[j] / fraction_of_all_average)

            x_new = []
            for value in x:
                date = datetime.datetime.fromtimestamp(value / 1000.0)
                x_new.append(date)

            corrected = Scatter(
                x=x_new,
                y=y_moving_avg,
                mode='lines',
                name=self.category_labels[i],
                line=dict(shape='spline'),
            )
            data_list.append([corrected])
        return data_list

    def create_layout(self):
        return Layout(
            # yaxis=dict(title='Kamervragen [per maand]'), #, range=[self.min_y*2, self.max_y/2]),
            yaxis=dict(title='Kamervragen [per maand]', range=[0.5, "auto"]),
            margin=Margin(t=40, b=30),
            height=300,
            showlegend=False
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
                xaxis=dict(title='Kamervraag ingediend [tijd]'),
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

    xaxis = XAxis(range=[0, 60],)

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
