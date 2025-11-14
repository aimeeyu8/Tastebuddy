import json
from llm_engine import extract_preferences
from sklearn.metrics import precision_score, recall_score, f1_score

# Helper: turn extracted lists into sets (avoids ordering issues)
def to_set(x):
    if x is None:
        return set()
    if isinstance(x, list):
        return set([str(i).lower() for i in x])
    return set([str(x).lower()])

def compare_attr(pred, gold):
    """Returns (TP, FP, FN) for one attribute."""
    pred = to_set(pred)
    gold = to_set(gold)

    TP = len(pred.intersection(gold))
    FP = len(pred - gold)
    FN = len(gold - pred)

    return TP, FP, FN

# Load test dataset
with open("tests/preference_eval.json", "r") as f:
    data = json.load(f)

total_TP = {"cuisine": 0, "price": 0, "allergies": 0, "location": 0}
total_FP = {"cuisine": 0, "price": 0, "allergies": 0, "location": 0}
total_FN = {"cuisine": 0, "price": 0, "allergies": 0, "location": 0}

print("\n LLM Preference Extraction Evaluation \n")

# Evaluate each prompt
for example in data:
    text = example["text"]
    gold = example["expected"]
    pred = extract_preferences(text)

    print(f"Input: {text}")
    print(f"Predicted: {pred}")
    print(f"Expected:  {gold}\n")

    # Compare each attribute
    for attr in ["cuisine", "price", "allergies", "location"]:
        TP, FP, FN = compare_attr(pred.get(attr), gold.get(attr))

        total_TP[attr] += TP
        total_FP[attr] += FP
        total_FN[attr] += FN

# Compute metrics
def compute_metrics(TP, FP, FN):
    precision = TP / (TP + FP + 1e-9)
    recall = TP / (TP + FN + 1e-9)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)
    return precision, recall, f1

print("\n=== Summary Metrics ===\n")

for attr in ["cuisine", "price", "allergies", "location"]:
    P, R, F1 = compute_metrics(total_TP[attr], total_FP[attr], total_FN[attr])
    print(f"{attr.upper()}:")
    print(f"  Precision: {P:.2f}")
    print(f"  Recall:    {R:.2f}")
    print(f"  F1 Score:  {F1:.2f}\n")
