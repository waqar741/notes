# HFP - Health Priority System (Frontend) 🏥

**HFP** is the user-facing application for the Health First Priority system. It provides an interface for doctors and patients to interact with health data, which is securely stored and managed by a separate backend API.

**Note:** This repository is the **Frontend Client**. It requires the Backend API to be running.

## 🔗 Architecture

This project consists of two parts:
1.  **Frontend (This Repo):** Python/HTML interface for users.
2.  **Backend (API):** Django REST API that stores the data.
    * *Backend Repo:* [https://github.com/waqar741/memo_api](https://github.com/waqar741/memo_api)

## 🚀 Features

* **User Interface:** Clean HTML templates for easy navigation.
* **API Integration:** Fetches and sends health records to the `memo_api` backend.
* **Session Management:** Handles user logins and states.

## 🛠️ Tech Stack

* **Language:** Python
* **Web Framework:** [Flask / Django] *(Update based on your actual code)*
* **Communication:** HTTP Requests (REST)
* **Styling:** HTML / CSS

## ⚙️ Setup & Installation

You must run the **Backend API** first before starting this application.

### Step 1: Start the Backend
1.  Go to the [memo_api repository](https://github.com/waqar741/memo_api).
2.  Follow the instructions there to start the server (usually running on port `8000`).

### Step 2: Start the Frontend (This App)

1.  **Clone this repository**
    ```bash
    git clone [https://github.com/waqar741/notes.git](https://github.com/waqar741/notes.git)
    cd notes
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**
    * Make sure this app is pointing to the correct backend URL (default: `http://127.0.0.1:8000/`).
    * *(If you have a config.py or .env file, mention it here)*.

4.  **Run the App**
    ```bash
    python app.py
    # (Or python manage.py runserver if this is also Django)
    ```

## 🤝 Contributing

1.  Fork the repo.
2.  Create your feature branch.
3.  Submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

---

**Related Repositories:**
* Backend API: [memo_api](https://github.com/waqar741/memo_api)
