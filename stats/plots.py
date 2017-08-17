import datetime
from django.utils import timezone
from plotly.offline import plot
from plotly.graph_objs import Layout, Histogram, Histogram2d


def kamervraag_vs_time_plot_html(kamervraag_dates):
    return plot(
        figure_or_data={
            "data": [Histogram(
                x=kamervraag_dates,
                autobinx=False,
                xbins=dict(
                    start=(timezone.now() - datetime.timedelta(days=7 * 365)).timestamp() * 1000,
                    end=timezone.now().timestamp() * 1000,
                    size=60 * 60 * 24 * 7 * 1000
                ),
            )],
            "layout": Layout(
                title="Kamervragen per Week",
                xaxis=dict(title='Tijd'),
                yaxis=dict(title='Kamervragen per week'),
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
