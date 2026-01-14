import plotly.express as px

def setup_chart(fig):
    fig.update_layout(height=225, xaxis_showgrid=False, yaxis_showgrid=False, xaxis_title=None, yaxis_title=None, dragmode=False)
    fig.update_yaxes(showticklabels=False, fixedrange=True)
    fig.update_traces(cliponaxis=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_layout(hovermode=False)

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
    fig.update_traces(marker_color='rgba(138, 180, 248, 0.5)', marker_line_width=1, marker_line_color='rgba(138, 180, 248, 1)')
    fig.update_traces(texttemplate='%{y}%', textposition='outside')
    fig.update_yaxes(range=[0, 100])
    
    return fig
