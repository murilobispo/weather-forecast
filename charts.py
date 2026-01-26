import plotly.express as px
import plotly.graph_objects as go

def setup_chart(fig):
    fig.update_layout(height=225, xaxis_showgrid=False, yaxis_showgrid=False, xaxis_title=None, yaxis_title=None, dragmode=False, hovermode=False)
    fig.update_yaxes(showticklabels=False, fixedrange=True)
    fig.update_traces(cliponaxis=False)
    fig.update_xaxes(fixedrange=True)

    return fig

def temperature_chart(df, x, y):
    fig = px.line(df, x=x, y=y)
    fig = setup_chart(fig)
    fig.update_traces(fill='tozeroy', line=dict(color='#d2a906'), fillcolor='rgba(210,169,6,0.3)')
    fig.update_traces(mode='lines+text', text=df[y], textposition='top center', line_shape='spline')
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=df[x])
    fig.update_xaxes(range=[-0.5, len(df[x]) - 0.5])
    fig.update_yaxes(range=[df[y].min() - 1, df[y].max() + 5])
    fig.update_layout(margin=dict(t=0))

    return fig

def rain_chart(df, x, y):
    fig = px.bar(df, x=x, y=y)
    fig = setup_chart(fig)
    fig.update_traces(marker_color='rgba(31, 119, 180, 0.5)', marker_line_width=2, marker_line_color='rgba(31, 119, 180, 1)')
    fig.update_traces(texttemplate='%{y}%', textposition='outside')
    fig.update_yaxes(range=[0, 100])
    
    return fig

def wind_chart(df, x, y, z):
    fig = go.Figure(go.Scatter(
        x=df[x],
        y=df[y],
        mode="markers",
        marker=dict(
            symbol="arrow",
            size=18,
            color=df[y],
            colorscale="Viridis",
            cmin=df[y].min(),
            cmax=df[y].max(),
            showscale=True,
            angle = (df[z] + 180) % 360,
            angleref="up",
            opacity=0.85,
            colorbar=dict(
                title="km/h",
                tickvals=[df[y].min(), df[y].max()],
                ticktext=[f"{df[y].min():.0f}", f"{df[y].max():.0f}"],
                thickness=8,
                len=1,
                outlinewidth=0
            )
        ),
        hoverinfo="skip"
    ))
    fig.update_layout(template="plotly", margin=dict(t=0))
    fig = setup_chart(fig)

    return fig
