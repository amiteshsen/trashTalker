import streamlit as st
import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# File to store poll data
POLL_FILE = "poll_results.csv"

# Sample dataset for classification (simulated)
data = pd.DataFrame({
    "Plastic Type": ["Plastic Bottles", "Plastic Bags", "Styrofoam", "Food Containers"],
    "Recyclable": [1, 0, 0, 1]
})

# Encoding labels
label_encoder = LabelEncoder()
data["Plastic Type"] = label_encoder.fit_transform(data["Plastic Type"])

# Splitting data
X = data[["Plastic Type"]]
y = data["Recyclable"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train classifier
clf = RandomForestClassifier(n_estimators=10, random_state=42)
clf.fit(X_train, y_train)

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

def classify_plastic(option):
    encoded_option = label_encoder.transform([option])[0]
    prediction = clf.predict([[encoded_option]])[0]
    return "Recyclable" if prediction == 1 else "Not Recyclable"

def main():
    st.title("Recycling Awareness Poll")
    st.write("Which of the following household plastics do you think can be recycled?")
    
    options = ["Plastic Bottles", "Plastic Bags", "Styrofoam", "Food Containers"]
    selected_option = st.radio("Choose one:", options)
    
    if st.button("Submit Vote"):
        classification_result = classify_plastic(selected_option)
        vote(selected_option)
        
        if classification_result == "Recyclable":
            st.success(f"Thank you for voting! According to our model, '{selected_option}' is {classification_result}.")
        else:
            st.error(f"Thank you for voting! According to our model, '{selected_option}' is {classification_result}.", icon="🚨")
    
    st.subheader("Poll Results")
    poll_data = load_data()
    if not poll_data.empty:
        st.bar_chart(poll_data.set_index("Option"))
    else:
        st.write("No votes yet. Be the first to vote!")

if __name__ == "__main__":
    main()
