import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from typing import Optional, List

st.set_page_config(layout="wide")

EVENT_LIST_PIPE_URL = "https://api.tinybird.co/v0/pipes/bots_events.json"
EVENT_DATA_PIPE_URL = "https://api.tinybird.co/v0/pipes/example_bots_user_sessions.json"
AUTH_TOKEN = st.secrets['AUTH_TOKEN']


def init() -> None:
    if 'event_id' not in st.session_state:
        st.session_state['event_id'] = 'All'


def run() -> None:
    title = '<p style="color:Black; font-size: 20px;">Chatbot user journey analysis</p>'
    st.markdown(title, unsafe_allow_html=True)

    possible_events = _get_possible_events()
    _select_event(possible_events)

    if st.session_state['event_id'] == 'All':
        steps_before = None
        steps_after = None
    else:
        col1, col2 = st.columns(2)
        steps_before = col1.slider('Steps before', min_value=0, max_value=10,
                                   value=0, step=1, label_visibility="visible")
        steps_after = col2.slider('Steps after', min_value=0, max_value=10,
                                  value=10, step=1, label_visibility="visible")

    event_data = _get_event_data(
        event_id=st.session_state['event_id'], steps_before=steps_before, steps_after=steps_after)
    fig = _get_plot_figure(
        data=event_data, event_id=st.session_state['event_id'])
    st.plotly_chart(fig, use_container_width=True)


@st.experimental_memo
def _get_possible_events() -> List[str]:
    response = requests.get(
        EVENT_LIST_PIPE_URL,
        params={"token": AUTH_TOKEN}
    )
    assert response.status_code == 200
    events = [e['event_id'] for e in response.json()['data']]
    events.sort()
    return ['All'] + events


def _select_event(possible_events: List[str]) -> None:
    with st.form('select_event'):

        event_id = st.selectbox("Choose the step you want to analyze:",
                                possible_events)
        select_button = st.form_submit_button('Run')
        if select_button:
            st.session_state['event_id'] = event_id


def _get_event_data(event_id: str, steps_before: Optional[int], steps_after: Optional[int]) -> pd.DataFrame:
    response = requests.get(EVENT_DATA_PIPE_URL, params={
                            'token': AUTH_TOKEN, 'event_id': event_id, 'steps_before': steps_before, 'steps_after': steps_after})
    return pd.DataFrame.from_records(response.json()['data'])


def _get_plot_figure(data: pd.DataFrame, event_id: str, height: int = 1000) -> go.Figure:
    data = data.dropna()
    labels = pd.unique(data[['source', 'target']].values.ravel('K')).tolist()
    source = []
    target = []
    value = []
    colors = ['#787878']*len(labels)
    lables_without_numbers = []
    for l in labels:
        if l != None:
            list_l = l.split(' - ')
            lables_without_numbers.append(list_l[1])

    if event_id != 'All':
        colors[labels.index(('1 - '+event_id))] = '#6E49FF'
    for _, row in data.iterrows():f
        value.append(int(row['value']))
        source.append(labels.index(row['source']))
        target.append(labels.index(row['target']))
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            label=lables_without_numbers,
            color=colors,
            hovertemplate='%{label} (%{int(value)} users)<br><b>Stats</b><br>Avg. Time: 1m 2s<br>Dropoff: 40%<br>CSAT: 4.32<br><b>Chosen paths</b><br>Feedback 46 (<b>66%</b>)<br> Handoff 21 (<b>30%</b>)<br>Fuera de horario 3 (<b>4%</b>)<br><b>Sources </b><br>Pedidos online 70 (<b>100%</b>)<extra></extra>',
        ),
        link=dict(
            source=source,
            target=target,
            value=value))])

    fig.update_layout(height=height, font=dict(
        size=15), hoverlabel_align='left')
    fig.update_traces(textfont_color="black")
    return fig


if __name__ == "__main__":
    init()
    run()
