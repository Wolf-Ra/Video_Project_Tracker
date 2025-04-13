import streamlit as st
import requests

st.set_page_config(layout="wide")

BACKEND_URL = "http://127.0.0.1:5000"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.email = ""

def auth_page():
    st.markdown("## Video Project Tracker")
    mode = st.radio("Choose Action", ["Login", "Signup", "Reset Password"], horizontal=True)

    col1, col2 = st.columns([1, 1])
    with col2:
        st.image("https://images.pexels.com/photos/1111319/pexels-photo-1111319.jpeg", use_column_width=True)

    with col1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if mode == "Login":
            if st.button("Login"):
                try:
                    response = requests.post(f"{BACKEND_URL}/login", json={"email": email, "password": password})
                    if response.status_code == 200:
                        st.session_state.logged_in = True
                        st.session_state.role = response.json()["role"]
                        st.session_state.email = email
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Login failed.")
                except:
                    st.error("Server connection error.")

        elif mode == "Signup":
            role = st.selectbox("Role", ["editor", "admin"])
            if st.button("Signup"):
                try:
                    response = requests.post(f"{BACKEND_URL}/signup", json={"email": email, "password": password, "role": role})
                    if response.status_code == 201:
                        st.success("Signup successful!")
                    else:
                        st.error("Signup failed.")
                except:
                    st.error("Server connection error.")

        elif mode == "Reset Password":
            new_password = st.text_input("New Password", type="password")
            if st.button("Reset Password"):
                try:
                    response = requests.post(f"{BACKEND_URL}/reset-password", json={"email": email, "new_password": new_password})
                    if response.status_code == 200:
                        st.success("Password reset!")
                    else:
                        st.error("Reset failed.")
                except:
                    st.error("Server connection error.")

def dashboard():
    st.sidebar.title("Navigation")
    nav_options = ["Dashboard"]
    if st.session_state.role == "admin":
        nav_options.append("Create Project")
    choice = st.sidebar.radio("Go to", nav_options)
    st.sidebar.write(f"Logged in as: {st.session_state.email} ({st.session_state.role})")

    if choice == "Dashboard":
        st.title("📋 Project Dashboard")
        response = requests.get(f"{BACKEND_URL}/projects")
        if response.status_code != 200:
            st.error("Failed to fetch projects")
            return
        projects = response.json()

        status_filter = st.selectbox("Filter by Status", ["All"] + list({p['status'] for p in projects}))
        editor_filter = st.selectbox("Filter by Editor", ["All"] + list({p['assigned_editor'] or "Unassigned" for p in projects}))
        client_filter = st.selectbox("Filter by Client", ["All"] + list({p['client_name'] for p in projects}))

        filtered = [p for p in projects if
                    (status_filter == "All" or p['status'] == status_filter) and
                    (editor_filter == "All" or (p['assigned_editor'] or "Unassigned") == editor_filter) and
                    (client_filter == "All" or p['client_name'] == client_filter)]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Projects", len(projects))
        col2.metric("Active Projects", sum(1 for p in projects if p['status'] != "Completed"))
        col3.metric("Completed Projects", sum(1 for p in projects if p['status'] == "Completed"))

        for p in filtered:
            with st.expander(f"📁 {p['title']} | 🎯 {p['status']}"):
                st.write(f"**Editor:** {p['assigned_editor'] or 'Unassigned'}")
                st.write(f"**Client:** {p['client_name']}")
                st.write("### Status Log")
                for log in p.get("logs", []):
                    st.write(f"- `{log['status']}` ➜ {log['comment']} ({log['timestamp']})")

                # Assign editor if unassigned
                if not p['assigned_editor'] and st.session_state.role == "editor":
                    if st.button("Assign to Me", key=f"assign_{p['id']}"):
                        res = requests.post(f"{BACKEND_URL}/assign-editor", json={
                            "project_id": p['id'],
                            "editor_email": st.session_state.email
                        })
                        if res.status_code == 200:
                            st.success("Assigned!")
                            st.rerun()
                        else:
                            st.error("Failed to assign.")

                if st.session_state.role == "admin" or st.session_state.email == p['assigned_editor']:
                    new_status = st.selectbox("Update Status", ["Pending", "Editing", "Review", "Completed"],
                                              index=["Pending", "Editing", "Review", "Completed"].index(p['status']),
                                              key=f"status_{p['id']}")
                    comment = st.text_input("Comment", key=f"comment_{p['id']}")
                    if st.button("Update Status", key=f"update_{p['id']}"):
                        try:
                            res = requests.post(f"{BACKEND_URL}/update-status", json={
                                "project_id": p['id'],
                                "new_status": new_status,
                                "comment": comment
                            })
                            if res.status_code == 200:
                                st.success("Status updated!")
                                st.rerun()
                            else:
                                st.error("Update failed.")
                        except:
                            st.error("Server connection error.")

    elif choice == "Create Project":
        st.title("➕ Create New Project")
        title = st.text_input("Project Title")
        assigned_editor = st.text_input("Assigned Editor (leave blank for unassigned)")
        client_name = st.text_input("Client Name")
        status = st.selectbox("Status", ["Pending", "Editing", "Review", "Completed"])

        if st.button("Create Project"):
            try:
                res = requests.post(f"{BACKEND_URL}/create-project", json={
                    "title": title,
                    "assigned_editor": assigned_editor.strip(),
                    "client_name": client_name,
                    "status": status
                })
                if res.status_code == 201:
                    st.success("Project created!")
                    st.rerun()
                else:
                    st.error("Creation failed.")
            except:
                st.error("Server connection error.")

if st.session_state.logged_in:
    dashboard()
else:
    auth_page()
