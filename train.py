import pandas
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix



dataset = pandas.read_csv("model_dataset.csv")

print(dataset.shape)
print(dataset.head())

drop_cols = ["match_id", "date", "season", "home_team", "away_team", "result"]

feature_cols = [c for c in dataset.columns if c not in drop_cols]


X = dataset[feature_cols]

y = dataset["result"]

train = dataset[dataset["season"] <= 2024]
test = dataset[dataset["season"] == 2025]

X_train = train[feature_cols]
y_train = train["result"]

X_test = test[feature_cols]
y_test = test["result"]

print("Train size:", len(X_train))
print("Test size:", len(X_test))


baseline_acc = (y_test == "w").mean()
print("Baseline (always home win):", baseline_acc)


scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)   # fit + transform on train
X_test_scaled  = scaler.transform(X_test)         # transform only on test


model = LogisticRegression(max_iter=1000, class_weight="balanced")

model.fit(X_train_scaled, y_train)

preds = model.predict(X_test_scaled)

print("Accuracy:", accuracy_score(y_test, preds))
print("\nClassification report:\n", classification_report(y_test, preds))
print("Confusion matrix:\n", confusion_matrix(y_test, preds, labels=["w", "d", "l"]))

