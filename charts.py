import plotly.express as px

def temperature_line_chart(df, x, y):
    
    fig = px.line(df, x=x, y=y)

    fig.update_traces(fill='tozeroy', line=dict(color='#d2a906'), fillcolor='rgba(210,169,6,0.3)')
    fig.update_traces(mode='lines+text', text=[round(t) for t in df[y]], textposition='top center')

    fig.update_xaxes(
        type='category', 
        categoryorder='array', 
        categoryarray=df[x]
    )
    fig.update_xaxes(range=[-0.5, len(df[x]) - 0.5])

    fig.update_yaxes(showticklabels=False)
    fig.update_yaxes(range=[df[y].min() - 1, df[y].max() + 5])

    fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    fig.update_layout(height=225)
    fig.update_layout(xaxis_fixedrange=True, yaxis_fixedrange=True)
    fig.update_layout(hovermode=False)
    fig.update_layout(
        title_text='',
        margin=dict(t=0),
    )
    return fig
