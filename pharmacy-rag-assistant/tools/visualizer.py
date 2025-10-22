import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional


def create_visualization(
    data: List[Dict[str, Any]],
    chart_type: str,
    title: str,
    x_column: str,
    y_column: str,
    color_column: Optional[str] = None
) -> go.Figure:
    if not data:
        raise ValueError("Нету данных")

    if chart_type == "bar":
        fig = px.bar(
            data,
            x=x_column,
            y=y_column,
            color=color_column,
            title=title,
            labels={x_column: x_column.capitalize(), y_column: y_column.capitalize()}
        )

    elif chart_type == "line":
        fig = px.line(
            data,
            x=x_column,
            y=y_column,
            color=color_column,
            title=title,
            labels={x_column: x_column.capitalize(), y_column: y_column.capitalize()},
            markers=True
        )

    elif chart_type == "pie":
        fig = px.pie(
            data,
            names=x_column,
            values=y_column,
            title=title
        )

    elif chart_type == "scatter":
        fig = px.scatter(
            data,
            x=x_column,
            y=y_column,
            color=color_column,
            title=title,
            labels={x_column: x_column.capitalize(), y_column: y_column.capitalize()}
        )

    else:
        raise ValueError(f"Неизвестный тип графика: {chart_type}. Доступные: bar, line, pie, scatter")

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        font=dict(size=12),
        title_font_size=16
    )

    return fig


def create_grouped_bar_chart(
    data: List[Dict[str, Any]],
    title: str,
    x_column: str,
    y_column: str,
    group_column: str
) -> go.Figure:
    fig = px.bar(
        data,
        x=x_column,
        y=y_column,
        color=group_column,
        title=title,
        barmode='group',
        labels={x_column: x_column.capitalize(), y_column: y_column.capitalize()}
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        font=dict(size=12),
        title_font_size=16
    )

    return fig


def create_multi_line_chart(
    data: List[Dict[str, Any]],
    title: str,
    x_column: str,
    y_column: str,
    group_column: str
) -> go.Figure:
    fig = px.line(
        data,
        x=x_column,
        y=y_column,
        color=group_column,
        title=title,
        markers=True,
        labels={x_column: x_column.capitalize(), y_column: y_column.capitalize()}
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        font=dict(size=12),
        title_font_size=16
    )

    return fig
