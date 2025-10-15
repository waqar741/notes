from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import requests

API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://127.0.0.1:8001')
API_TOKEN_URL = f"{API_BASE_URL}/api/token/"
API_REFRESH_URL = f"{API_BASE_URL}/api/token/refresh/"
API_MEMOS_URL = f"{API_BASE_URL}/api/memos/"
API_ME_URL = f"{API_BASE_URL}/api/me/"
API_REGISTER_URL = f"{API_BASE_URL}/api/register/"

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            response = requests.post(API_TOKEN_URL, data={
                "username": username,
                "password": password
            }, timeout=5)

            if response.status_code == 200:
                tokens = response.json()
                access_token = tokens["access"]
                refresh_token = tokens["refresh"]

                res = redirect("memo:memo_list")
                res.set_cookie("access_token", access_token, httponly=True, samesite="Lax")
                res.set_cookie("refresh_token", refresh_token, httponly=True, samesite="Lax")
                return res
            else:
                messages.error(request, "Invalid username or password.")
        except requests.RequestException:
            messages.error(request, "Error connecting to API.")

    return render(request, "registration/login.html")

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")

        try:
            response = requests.post(API_REGISTER_URL, data={
                "username": username,
                "password": password,
                "email": email
            }, timeout=5)

            if response.status_code == 201:
                messages.success(request, "Registration successful! Please login.")
                return redirect("memo:login")
            else:
                error_msg = response.json().get('error', 'Registration failed')
                messages.error(request, error_msg)
        except requests.RequestException:
            messages.error(request, "Error connecting to API.")

    return render(request, "registration/register.html")

def refresh_access_token(request):
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return None
    try:
        response = requests.post(API_REFRESH_URL, data={"refresh": refresh_token}, timeout=5)
        if response.status_code == 200:
            return response.json()["access"]
    except requests.RequestException:
        pass
    return None

def get_current_user_info(request):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return None
    try:
        res = requests.get(API_ME_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=5)
        if res.status_code == 200:
            return res.json()
    except requests.RequestException:
        pass
    return None

def memo_list(request):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return redirect("memo:login")

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        res = requests.get(API_MEMOS_URL, headers=headers, timeout=5)
        if res.status_code == 401:
            new_access = refresh_access_token(request)
            if new_access:
                headers = {"Authorization": f"Bearer {new_access}"}
                res = requests.get(API_MEMOS_URL, headers=headers)
                response = render(request, "memo_list.html", {
                    "memos": res.json() if res.ok else [],
                    "current_user": get_current_user_info(request),
                    "API_BASE_URL": API_BASE_URL
                })
                response.set_cookie("access_token", new_access, httponly=True, samesite="Lax")
                return response
            else:
                return redirect("memo:login")

        memos = res.json() if res.ok else []
    except requests.RequestException:
        memos = []

    return render(request, "memo_list.html", {
        "memos": memos,
        "current_user": get_current_user_info(request),
        "API_BASE_URL": API_BASE_URL
    })

def memo_create(request):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return redirect("memo:login")

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        photo = request.FILES.get("photo")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"title": title, "content": content}
        files = {}
        
        if photo:
            files = {"photo": photo}
        
        try:
            if files:
                res = requests.post(API_MEMOS_URL, headers=headers, data=data, files=files)
            else:
                res = requests.post(API_MEMOS_URL, headers=headers, data=data)
                
            if res.status_code == 201:
                messages.success(request, "Note created successfully!")
                return redirect("memo:memo_list")
            else:
                messages.error(request, "Error creating note. Please try again.")
        except requests.RequestException:
            messages.error(request, "Error connecting to API.")

    return render(request, "memo_form.html", {
        "current_user": get_current_user_info(request),
        "API_BASE_URL": API_BASE_URL
    })

def memo_update(request, pk):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return redirect("memo:login")

    headers = {"Authorization": f"Bearer {access_token}"}
    memo_url = f"{API_MEMOS_URL}{pk}/"

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        photo = request.FILES.get("photo")
        
        data = {"title": title, "content": content}
        files = {}
        
        if photo:
            files = {"photo": photo}
        
        try:
            if files:
                res = requests.put(memo_url, headers=headers, data=data, files=files)
            else:
                res = requests.patch(memo_url, headers=headers, data=data)
                
            if res.status_code in (200, 204):
                messages.success(request, "Note updated successfully!")
                return redirect("memo:memo_list")
            else:
                messages.error(request, "Error updating note. Please try again.")
        except requests.RequestException:
            messages.error(request, "Error connecting to API.")

    try:
        res = requests.get(memo_url, headers=headers)
        memo = res.json() if res.ok else None
    except requests.RequestException:
        memo = None

    return render(request, "memo_form.html", {
        "memo": memo, 
        "current_user": get_current_user_info(request),
        "API_BASE_URL": API_BASE_URL
    })

def memo_delete(request, pk):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return redirect("memo:login")

    headers = {"Authorization": f"Bearer {access_token}"}
    memo_url = f"{API_MEMOS_URL}{pk}/"

    if request.method == "POST":
        try:
            res = requests.delete(memo_url, headers=headers)
            if res.status_code in (200, 204):
                messages.success(request, "Note deleted successfully!")
                return redirect("memo:memo_list")
            else:
                messages.error(request, "Error deleting note. Please try again.")
        except requests.RequestException:
            messages.error(request, "Error connecting to API.")

    try:
        res = requests.get(memo_url, headers=headers)
        memo = res.json() if res.ok else None
    except requests.RequestException:
        memo = None

    return render(request, "memo_confirm_delete.html", {
        "memo": memo, 
        "current_user": get_current_user_info(request),
        "API_BASE_URL": API_BASE_URL
    })

def logout_view(request):
    res = redirect("memo:login")
    res.delete_cookie("access_token")
    res.delete_cookie("refresh_token")
    messages.success(request, "You have been logged out successfully.")
    return res