import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import pickle

print("🚀 Loading JoSAA Data...")
df = pd.read_csv('complete_data_state.csv')

print("⚙️ Encoding Text to Numbers...")
le_category = LabelEncoder()
le_quota = LabelEncoder()

df['Category_Encoded'] = le_category.fit_transform(df['Category'])
df['Quota_Encoded'] = le_quota.fit_transform(df['Quota'])

# Synthetic Data Generation (Asli ML Dataset Generation)
print("📊 Generating Synthetic Student Profiles for Classifier...")
X_synthetic = []
y_synthetic = []

for idx, row in df.iterrows():
    cat = row['Category_Encoded']
    quota = row['Quota_Encoded']
    cutoff = float(row['Closing_Rank'])
    
    # 1. Safe Zone Students (Rank is better than cutoff -> Label 1)
    for ratio in np.linspace(0.4, 0.95, 15):
        X_synthetic.append([cat, quota, ratio])
        y_synthetic.append(1) 
        
    # 2. Borderline Zone Students (Rank is near or slightly above cutoff)
    for ratio in np.linspace(0.96, 1.15, 10):
        X_synthetic.append([cat, quota, ratio])
        # Jaise-jaise rank cutoff se upar jayegi, seat milne ka chance kam hota jayega
        prob_admit = 1.0 - (ratio - 0.96) / (1.15 - 0.96) * 0.8 
        label = 1 if np.random.rand() < prob_admit else 0
        y_synthetic.append(label)
        
    # 3. Danger Zone Students (Rank is way worse than cutoff -> Label 0)
    for ratio in np.linspace(1.16, 1.6, 10):
        X_synthetic.append([cat, quota, ratio])
        y_synthetic.append(0) 

X_synthetic = np.array(X_synthetic)
y_synthetic = np.array(y_synthetic)

print("🧠 Training Decision Tree Classifier Model...")
# Max depth 5 rakha hai taaki smooth probability probabilities nikal sakein
model = DecisionTreeClassifier(random_state=42, max_depth=5)
model.fit(X_synthetic, y_synthetic)

print("💾 Saving genuine model.pkl...")
with open('model.pkl', 'wb') as f:
    pickle.dump({
        'model': model, 
        'cat_encoder': le_category, 
        'quota_encoder': le_quota
    }, f)

print("✅ Asli ML Classification Model Saved Successfully!")