import streamlit as st
import pandas as pd
import os

# File to store poll data
POLL_FILE = "poll_results.csv"

def load_data():
    if os.path.exists(POLL_FILE):
        return pd.read_csv(POLL_FILE)
    else:
        return pd.DataFrame(columns=["Option", "Votes"])

def save_data(data):
    data.to_csv(POLL_FILE, index=False)

def vote(option):
    data = load_data()
    if option in data["Option"].values:
        data.loc[data["Option"] == option, "Votes"] += 1
    else:
        new_row = pd.DataFrame({"Option": [option], "Votes": [1]})
        data = pd.concat([data, new_row], ignore_index=True)
    save_data(data)

def main():
    st.title("Recycling Awareness Poll")
    st.write("Which of the following household plastics do you think can be recycled?")
    
    options = ["Plastic Bottles", "Plastic Bags", "Styrofoam", "Food Containers"]
    selected_option = st.radio("Choose one:", options)
    
    if st.button("Submit Vote"):
        vote(selected_option)
        st.success("Thank you for voting!")
    
    st.subheader("Poll Results")
    poll_data = load_data()
    if not poll_data.empty:
        st.bar_chart(poll_data.set_index("Option"))
    else:
        st.write("No votes yet. Be the first to vote!")

if __name__ == "__main__":
    main()
