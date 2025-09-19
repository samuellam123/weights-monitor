import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.title("Weight tracker")

namelist = ['Samuel', 'Fabian', 'Genee']

option = st.selectbox(
    "Name",
    namelist,
)

st.write("You selected:", option)

text_input = f"Enter weight now ({datetime.now().date()}, {datetime.now().time().strftime("%H:%M")})"
weight_input = st.text_input(text_input)
st.write("Your weight is: ", weight_input)

from numpy.random import default_rng as rng

df = pd.DataFrame(rng(0).standard_normal((20, 3)), columns=["a", "b", "c"])

st.line_chart(df)