# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from annotated_text import annotated_text
from DataModel import Courses, Holes, Scorecard
from load_css import local_css

local_css("style.css")
 
st.markdown(
        f"""
<style>
    .reportview-container .main .block-container{{
        max-width: 900px;
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }}
</style>
""",
        unsafe_allow_html=True,
    )

## Session for querying database
engine = create_engine(f"sqlite:///../Data/GST.db")
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

## Dashboarding elements
st.title("""Golf Score Tracking""")

# Get rounds list
rounds = (
    session.query(
        Courses.name,
        Courses.course_id,
        Scorecard.date
    )
    .select_from(Courses)
    .join(Holes)
    .join(Scorecard)
    .group_by(Courses.name)
    .all()
)

rounds_list = []
rounds_mapping = []
for round_ in rounds:
    round_pretty = f"{round_.name} / {round_.date.strftime('%d %b %Y')}"
    rounds_list.append(round_pretty)
    course_id = f"{round_.course_id}{round_.date.strftime('%d%m%y')}"
    rounds_mapping.append({"round_id": course_id, "round_pretty": round_pretty})


# Display games list
selected_round = st.sidebar.selectbox("select round", rounds_list)
selected_round_id = next(item for item in rounds_mapping if item["round_pretty"] == selected_round)["round_id"]

st.subheader(selected_round)

### Get Scorecard data
scorecard = (
    session.query(
        Holes.number,
        Holes.par,
        Holes.hcp,
        Holes.distance,
        Scorecard.score,
        Scorecard.fairway,
        Scorecard.putts,
    )
    .select_from(Scorecard)
    .join(Holes)
    .filter(Scorecard.scorecard_id == selected_round_id)
    .all()
)
df_scorecard = pd.DataFrame(scorecard).set_index("number").sort_index()
vs_par = df_scorecard.score - df_scorecard.par
gir = df_scorecard.score - df_scorecard.par - df_scorecard.putts
gir = [1 if g == -2 else 0 for g in gir]
fairway_count = [1 if f == 'F' else 0 for f in df_scorecard.fairway]
not_par3_count = [1 if p != 3 else 0 for p in df_scorecard.par]
brut = -vs_par+2
bogey_1_putt = [1 if (p == 1 and g == 0) else 0 for (p, g) in zip(df_scorecard.putts, gir)]

def set_score_color(score):
    if score < 0:
        color = "lightskyblue"
    elif score == 0:
        color = "palegreen"
    elif score == 1:
        color = "cornsilk"
    else:
        color = "pink"
    return color
    
def set_putts_color(putts):
    if putts > 2:
        color = " class='bold indianred'"
    else :
        color = ""
    return color
    
def set_fairways_color(putts):
    if putts == 'F':
        color = " class='bold seagreen'"
    else :
        color = ""
    return color

## SCORE
col1, col2 = st.beta_columns(2)
col1.header(f'{int(df_scorecard.par.sum() + vs_par.fillna(value=3).sum())}  (+{int(vs_par.fillna(value=3).sum())})')
col1.write("Stroke")
col2.header(f'{int(sum(brut[brut>0]))} (+{36-int(sum(brut[brut>0]))})')
col2.write("Brut")


## SCORECARD
st.header("Scorecard")
cols = st.beta_columns(7)
cols[0].subheader("Hole")
cols[1].subheader("Par")
cols[2].subheader("Hcp")
cols[3].subheader("Dist")
cols[4].subheader("Score")
cols[5].subheader("Fairway")
cols[6].subheader("Putts")
for i in range(1, 19):
    cols[0].markdown(f"<div><span>{i}</span></div>", unsafe_allow_html=True)
    cols[1].markdown(f"<div><span>{df_scorecard.par[i]}</span></div>", unsafe_allow_html=True)
    cols[2].markdown(f"<div><span>{df_scorecard.hcp[i]}</span></div>", unsafe_allow_html=True)
    cols[3].markdown(f"<div><span>{df_scorecard.distance[i]}</span></div>", unsafe_allow_html=True)
    score_color = set_score_color(vs_par[i])
    cols[4].markdown(f"<div><span class='highlight {score_color}'>{df_scorecard.fillna('X').score[i]}</span></div>", unsafe_allow_html=True)
    fairways_color = set_fairways_color(df_scorecard.fairway[i])
    cols[5].markdown(f"<div><span{fairways_color}>{df_scorecard.fillna('-').fairway[i]}</span></div>", unsafe_allow_html=True)
    putts_color = set_putts_color(df_scorecard.putts[i])
    cols[6].markdown(f"<div><span{putts_color}>{df_scorecard.fillna('-').putts[i]}</span></div>", unsafe_allow_html=True)


## SCORE EVOLUTION
st.subheader("Score evolution")
cumscore = vs_par.fillna(value=3).cumsum()
df_cumscore = pd.DataFrame(cumscore).reset_index()
df_cumscore.columns = ['thru', 'score']

c = alt.Chart(df_cumscore).mark_area(line={'color':'khaki'},
    color=alt.Gradient(
        gradient='linear',
        stops=[alt.GradientStop(color='dimgray', offset=0),
               alt.GradientStop(color='lemonchiffon', offset=1)],
        x1=1,
        x2=1,
        y1=1,
        y2=0)).encode(
    x="thru:Q",
    y="score:Q",
    tooltip=['score', 'thru']
).properties(width=750, height=350)
st.write(c)

col1, col2 = st.beta_columns(2)

## SCORE REPARTITION
col1.subheader("Score repartition")
df_repartition = pd.DataFrame(vs_par.fillna(10).value_counts().sort_index().reset_index())
df_repartition.columns = ['score', ' ']
df_repartition['colors'] = [set_score_color(s) for s in df_repartition.score]
c = alt.Chart(df_repartition).mark_bar().encode(
    x='score:O',
    y=" :Q",
    # The highlight will be set on the result of a conditional statement
    color=alt.Color('colors:N', scale=None),
    tooltip=['score', ' ']
).properties(width=350)

col1.write(c)


## AVERAGE SCORES
col2.subheader("Average scores")
df_averages = df_scorecard[['par', 'score']].groupby('par').mean().reset_index()
df_averages.columns = ['par', 'avg_score']
df_averages['vs_par'] = df_averages.avg_score - df_averages.par
df_averages['color'] = [set_score_color(int(round(x))) for x in df_averages['vs_par']]

bar = alt.Chart(df_averages).mark_bar().encode(
    x='par:N',
    y='avg_score:Q',
    color=alt.Color('color:N', scale=None),
    tooltip = ['par', 'avg_score']
).properties(width=350)

tick = alt.Chart(df_averages).mark_tick(
    color='firebrick',
    thickness=3,
    size=50 # controls width of tick.
).encode(
    x='par:N',
    y='par:Q'
).properties(width=350)

col2.write(bar+tick)


## OFF THE TEE
st.header("Off the tee")
col1, col2, col3 = st.beta_columns(3)
col1.header(f'{int(sum(fairway_count)/sum(not_par3_count)*100)}%')
col1.write("% Fairways")

df_drives = pd.DataFrame(df_scorecard.fairway.dropna().value_counts()).reset_index()
df_drives['  '] = 1
df_drives.columns = ['drive', ' ', '  ']

c = alt.Chart(df_drives).mark_bar().encode(
    x=alt.X('drive:N', sort=['L', 'F', 'R']),
    y=' ',
    color = alt.condition(
        alt.datum.drive == 'F',
        alt.value('palegreen'),
        alt.value('pink')
    )
).properties(width=200, height=150)

col2.write(c)

st.header("Around the green")
col1, col2, col3 = st.beta_columns(3)
col1.header(f'{int(sum(gir)/18*100)}%')
col1.write("% GIR")
col2.header(f'{int(df_scorecard.putts.sum())}')
col2.write("Nb Putts")

c = alt.Chart(df_drives).mark_bar().encode(
    x='drive:N',
    y=' ',
    color = alt.condition(
        alt.datum.drive == 'F',
        alt.value('palegreen'),
        alt.value('pink')
    )
).properties(width=200, height=150)

col3.header(f'{int(sum(bogey_1_putt)/(18-sum(gir))*100)}%')
col3.write("% Scrambling")
