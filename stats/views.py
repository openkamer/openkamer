import plotly
from plotly.graph_objs import Scatter, Layout


def get_plot(request):
    html = plotly.offline.plot(
        figure_or_data={
            "data": [Scatter(x=[1, 2, 3, 4], y=[4, 3, 2, 1])],
            "layout": Layout(title="hello world")
            },
        show_link=False,
        output_type='div',
        include_plotlyjs=True,
        auto_open=False,
    )
    return html
