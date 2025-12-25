import os
import re
from flask import Flask, request, jsonify
from splitwise import Splitwise
from splitwise.expense import Expense
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

splitwise = Splitwise(
    os.getenv("SPLITWISE_CONSUMER_KEY"),
    os.getenv("SPLITWISE_CONSUMER_SECRET"),
    api_key=os.getenv("SPLITWISE_API_KEY"),
)

DEFAULT_GROUP_ID = int(os.getenv("DEFAULT_GROUP_ID")) if os.getenv("DEFAULT_GROUP_ID") else None

AMOUNT_REGEX = re.compile(
    r"(?:Rs\.?|INR)\s?(\d+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


def extract_amount(message: str) -> float | None:
    if not message:
        return None

    match = AMOUNT_REGEX.search(message)
    return float(match.group(1)) if match else None


@app.route("/add_expense", methods=["POST"])
def add_expense():
    data = request.get_json(silent=True) or {}

    message = data.get("message", "")
    comments = data.get("comments", "").strip()

    amount = extract_amount(message)

    if not amount or amount <= 0:
        return jsonify(
            {"success": False, "error": "Amount not found in message"}
        ), 400

    description = comments if comments else "Auto expense from bank SMS"

    print(f"Adding expense: {amount} - {description}")

    expense = Expense()
    expense.setCost(f"{amount:.2f}")
    expense.setDescription(description)
    expense.setGroupId(DEFAULT_GROUP_ID)
    expense.setCurrencyCode("INR")
    expense.setSplitEqually()

    created, errors = splitwise.createExpense(expense)

    if errors:
        return jsonify({"success": False, "error": errors}), 400

    return jsonify(
        {
            "success": True,
            "expense_id": created.getId(),
            "amount": created.getCost(),
            "description": created.getDescription(),
        }
    ), 200


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

    
