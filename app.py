from flask import Flask, jsonify, request, send_from_directory
import json
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)


# Load questions from JSON file
def load_questions():
    with open("questions.json", "r") as f:
        return json.load(f)


# Save quiz results to JSON file
def save_results(results):
    try:
        # Try to load existing results
        try:
            with open("quiz_results.json", "r") as f:
                all_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_results = []

        # Add timestamp to results
        results["timestamp"] = datetime.now().isoformat()

        # Append new results
        all_results.append(results)

        # Save updated results
        with open("quiz_results.json", "w") as f:
            json.dump(all_results, f, indent=2)

        return True
    except Exception as e:
        print(f"Error saving results: {e}")
        return False


# Calculate statistics from quiz results
def calculate_statistics():
    try:
        with open("quiz_results.json", "r") as f:
            all_results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"total_attempts": 0, "question_stats": {}}

    # Initialize statistics
    stats = {"total_attempts": len(all_results), "question_stats": {}}

    # Get all questions for reference
    questions = load_questions()
    question_map = {str(q["id"]): q for q in questions["questions"]}

    # Initialize counters for each question
    for q in questions["questions"]:
        q_id = str(q["id"])
        stats["question_stats"][q_id] = {
            "question": q["question"],
            "options": q["options"],
            "correct_answer": q["correct_answer"],
            "answer_counts": defaultdict(int),
            "correct_count": 0,
        }

    # Calculate statistics from all attempts
    for attempt in all_results:
        for result in attempt["results"]:
            q_id = result["id"]
            user_answer = result["user_answer"]

            if user_answer:
                stats["question_stats"][q_id]["answer_counts"][user_answer] += 1

            if result["is_correct"]:
                stats["question_stats"][q_id]["correct_count"] += 1

    return stats


# Get participants data
def get_participants_data():
    try:
        with open("quiz_results.json", "r") as f:
            all_results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "total_participants": 0,
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0,
            "participants": []
        }

    # Process participants data
    participants = []
    total_score_percentage = 0
    highest_score_percentage = 0
    lowest_score_percentage = 100

    for result in all_results:
        user_info = result.get("user_info", {})
        score = result.get("score", 0)
        total = result.get("total", 1)  # Avoid division by zero
        timestamp = result.get("timestamp", "")

        # Calculate score percentage
        score_percentage = (score / total) * 100

        # Update highest and lowest scores
        if score_percentage > highest_score_percentage:
            highest_score_percentage = score_percentage
        if score_percentage < lowest_score_percentage:
            lowest_score_percentage = score_percentage

        # Add to total for average calculation
        total_score_percentage += score_percentage

        # Add participant data
        participants.append({
            "firstName": user_info.get("firstName", "Unknown"),
            "lastName": user_info.get("lastName", "Unknown"),
            "score": score,
            "total": total,
            "timestamp": timestamp
        })

    # Calculate average score
    total_participants = len(participants)
    average_score = total_score_percentage / total_participants if total_participants > 0 else 0

    return {
        "total_participants": total_participants,
        "average_score": average_score,
        "highest_score": highest_score_percentage,
        "lowest_score": lowest_score_percentage,
        "participants": participants
    }


@app.route("/")
def serve_quiz():
    return send_from_directory(".", "index.html")


@app.route("/results")
def serve_results():
    return send_from_directory(".", "results.html")


@app.route("/summary")
def serve_summary():
    return send_from_directory(".", "summary.html")


@app.route("/questions")
def get_questions():
    return jsonify(load_questions())


@app.route("/statistics")
def get_statistics():
    return jsonify(calculate_statistics())


@app.route("/participants")
def get_participants():
    return jsonify(get_participants_data())


@app.route("/check_answers", methods=["POST"])
def check_answers():
    data = request.get_json()
    user_answers = data.get("answers", {})
    user_info = data.get("user_info", {})
    questions = load_questions()

    results = []
    score = 0
    total = len(questions["questions"])

    for question in questions["questions"]:
        question_id = str(question["id"])
        user_answer = user_answers.get(question_id)
        is_correct = user_answer == question["correct_answer"]

        if is_correct:
            score += 1

        results.append(
            {
                "id": question_id,
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
            }
        )

    # Prepare complete results for storage
    complete_results = {
        "user_info": user_info,
        "score": score,
        "total": total,
        "results": results,
    }

    # Save results to file
    save_results(complete_results)

    return jsonify(complete_results)


if __name__ == "__main__":
    app.run(debug=True)
