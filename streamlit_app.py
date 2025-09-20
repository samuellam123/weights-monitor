import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from st_supabase_connection import SupabaseConnection
from postgrest.exceptions import APIError

# Initialize connection.
conn = st.connection("supabase", type=SupabaseConnection)

# Use the underlying supabase-py client
supabase = conn.client

st.title("Weight tracker")


# READ (cached)
@st.cache_data(ttl=600)
def get_users():
    return supabase.table("users").select("*").execute()


@st.cache_data(ttl=600)
def get_weights():
    return supabase.table("weight").select("*").execute()


def insert_weight(user_id: int, weight_kg: float, date: datetime.date = None):

    # Build a naive timestamp (no tz) that Postgres 'timestamp' likes
    if date:
        dt = datetime.combine(date, datetime.now().time())  # same day, current time
    else:
        dt = datetime.now()
    dt = dt.replace(tzinfo=None)
    dt_iso = dt.isoformat(timespec="seconds")  # e.g. 2025-09-19T19:29:00

    supabase.table("weight").insert(
        {
            "userid": user_id,
            "weight": weight_kg,
            "datetime": dt_iso,
        }
    ).execute()

    print(f"Insert success: {user_id}, {weight_kg}")


namelist = ["Samuel", "Fabian", "Genee", "Chong Hau", "Zoe"]

with st.form("my_form"):

    name = st.selectbox(
        "Name",
        namelist,
    )

    weight_input_desc = f"Enter weight now ({datetime.now().date()})"

    weight_input = st.number_input(
        weight_input_desc,
        min_value=40.0,
        max_value=120.0,
        value=80.0,
        step=0.1,
        format="%0.1f",
    )

    date_input = st.date_input("Date [Optional]", datetime.now().date())

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit form")

    if submitted:
        name_to_id = {"Samuel": 1, "Fabian": 2, "Genee": 3, "Chong Hau": 4, "Zoe": 5}

        try:
            insert_weight(name_to_id.get(name, 1), float(weight_input), date_input)
            st.write("Database insertion success")
        except APIError as e:
            st.write("API error, please try again later")
        except Exception as e:
            st.write("Insert failed, please try again later")

        st.cache_data.clear()  # refresh cached selects

w = (
    supabase.table("weight")
    .select("userid, weight, datetime")
    .order("datetime")
    .execute()
)
u = supabase.table("users").select("id, name").execute()
df_w = pd.DataFrame(w.data)
df_u = pd.DataFrame(u.data).rename(columns={"id": "userid"})  # join names, parse times
df = df_w.merge(
    df_u, on="userid", how="left"
)  # after you've built df with columns: datetime (str/ts), userid, name, weight

# 1) parse time & clean
# df has: datetime (ISO8601), userid, name, weight
df["datetime"] = pd.to_datetime(df["datetime"], format="mixed", utc=True).dt.tz_convert(
    "Asia/Singapore"
)
df = df.sort_values("datetime")

# pivot to wide for line_chart
wide = df.pivot_table(
    index="datetime", columns="name", values="weight", aggfunc="mean"
).sort_index()

# make index naive for resampling
wide.index = wide.index.tz_localize(None)

# 1 row per day, fill gaps so lines connect
wide_daily = (
    wide.resample("D")
    .mean()  # regular daily grid
    .interpolate(method="time")  # linear over time
    .bfill()  # fill leading NaN
    .ffill()  # (optional) fill trailing NaN
)

st.subheader("Weight vs Date (interpolated)")
st.line_chart(wide_daily)
