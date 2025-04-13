from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

users = []
projects = []
project_id_counter = 1

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    if any(u['email'] == data['email'] for u in users):
        return jsonify({"error": "User already exists"}), 409
    users.append({"email": data['email'], "password": data['password'], "role": data['role']})
    return jsonify({"message": "Signup successful"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = next((u for u in users if u['email'] == data['email'] and u['password'] == data['password']), None)
    if user:
        return jsonify({"role": user['role']}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    user = next((u for u in users if u['email'] == data['email']), None)
    if user:
        user['password'] = data['new_password']
        return jsonify({"message": "Password reset successful"}), 200
    return jsonify({"error": "User not found"}), 404

@app.route("/create-project", methods=["POST"])
def create_project():
    global project_id_counter
    data = request.json
    project = {
        "id": project_id_counter,
        "title": data['title'],
        "assigned_editor": data['assigned_editor'],
        "client_name": data['client_name'],
        "status": data['status'],
        "logs": [{
            "status": data['status'],
            "comment": "Project created",
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    project_id_counter += 1
    projects.append(project)
    return jsonify(project), 201

@app.route("/projects", methods=["GET"])
def get_projects():
    return jsonify(projects), 200

@app.route("/update-status", methods=["POST"])
def update_status():
    data = request.json
    for p in projects:
        if p["id"] == data["project_id"]:
            p["status"] = data["new_status"]
            p.setdefault("logs", []).append({
                "status": data["new_status"],
                "comment": data["comment"],
                "timestamp": datetime.utcnow().isoformat()
            })
            return jsonify({"message": "Status updated"}), 200
    return jsonify({"error": "Project not found"}), 404

@app.route("/assign-editor", methods=["POST"])
def assign_editor():
    data = request.json
    for p in projects:
        if p["id"] == data["project_id"] and not p["assigned_editor"]:
            p["assigned_editor"] = data["editor_email"]
            p.setdefault("logs", []).append({
                "status": p["status"],
                "comment": f"Editor {data['editor_email']} assigned themselves",
                "timestamp": datetime.utcnow().isoformat()
            })
            return jsonify({"message": "Editor assigned"}), 200
    return jsonify({"error": "Project not found or already assigned"}), 400

if __name__ == "__main__":
    app.run(debug=True)
