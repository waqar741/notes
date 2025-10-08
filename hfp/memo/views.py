from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.conf import settings
import requests
from .forms import MemoForm

# API Configuration - DRF API on port 8001
API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://127.0.0.1:8001')
API_TOKEN_URL = f"{API_BASE_URL}/api/token/"
API_REGISTER_URL = f"{API_BASE_URL}/api/register/"
API_MEMOS_URL = f"{API_BASE_URL}/api/memos/"

def get_api_headers(request):
    access_token = request.COOKIES.get("access_token")
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}

def refresh_access_token(request):
    refresh_token = request.COOKIES.get('refresh_token')
    if refresh_token:
        try:
            response = requests.post(f"{API_BASE_URL}/api/token/refresh/", data={
                'refresh': refresh_token
            })
            if response.status_code == 200:
                return response.json().get('access')
        except requests.RequestException:
            pass
    return None

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        print(f"Login attempt for user: {username}")  # Debug print

        try:
            response = requests.post(API_TOKEN_URL, data={
                "username": username,
                "password": password
            })
            
            print(f"API Response Status: {response.status_code}")  # Debug print
            print(f"API Response Content: {response.text}")  # Debug print

            if response.status_code == 200:
                tokens = response.json()
                access_token = tokens["access"]
                refresh_token = tokens["refresh"]
                print(f"Tokens received: Access={access_token[:20]}...")  # Debug print
                
                user, created = User.objects.get_or_create(username=username)
                login(request, user)
                response = redirect("memo:memo_list")
                response.set_cookie("access_token", access_token, httponly=True, samesite="Lax")
                response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="Lax")
                return response
            else:
                error = f"Invalid credentials (API returned {response.status_code})"
                print(f"Login error: {error}")  # Debug print
                
        except requests.RequestException as e:
            error = f"Cannot connect to API server: {str(e)}"
            print(f"Connection error: {error}")  # Debug print

        return render(request, "registration/login.html", {"error": error, "username": username})

    return render(request, "registration/login.html")



def memo_list(request):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return redirect("memo:login")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        res = requests.get(API_MEMOS_URL, headers=headers)
        
        # Token refresh logic
        if res.status_code == 401:
            new_access_token = refresh_access_token(request)
            if new_access_token:
                headers = {"Authorization": f"Bearer {new_access_token}"}
                res = requests.get(API_MEMOS_URL, headers=headers)
                if res.ok:
                    response = render(request, "memo_list.html", {"memos": res.json(), "API_BASE_URL": API_BASE_URL})
                    response.set_cookie("access_token", new_access_token, httponly=True, samesite="Lax")
                    return response
        
        memos = []
        if res.ok:
            memos = res.json()
        else:
            messages.error(request, f"Could not fetch memos. API responded with status {res.status_code}.")
    except requests.RequestException:
        messages.error(request, "Cannot connect to API server.")
        memos = []
    
    return render(request, "memo_list.html", {"memos": memos, "API_BASE_URL": API_BASE_URL})

def memo_create(request):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return redirect("memo:login")
    
    if request.method == "POST":
        form = MemoForm(request.POST, request.FILES)
        if form.is_valid():
            headers = {"Authorization": f"Bearer {access_token}"}
            data = {
                "title": form.cleaned_data["title"],
                "content": form.cleaned_data["content"] or ""
            }
            files = {}
            if form.cleaned_data.get("photo"):
                photo = request.FILES["photo"]
                files = {"photo": (photo.name, photo, photo.content_type)}
            
            try:
                res = requests.post(API_MEMOS_URL, headers=headers, data=data, files=files)
                
                # Token refresh logic
                if res.status_code == 401:
                    new_access_token = refresh_access_token(request)
                    if new_access_token:
                        headers = {"Authorization": f"Bearer {new_access_token}"}
                        res = requests.post(API_MEMOS_URL, headers=headers, data=data, files=files)
                        if res.status_code == 201:
                            response = redirect("memo:memo_list")
                            response.set_cookie("access_token", new_access_token, httponly=True, samesite="Lax")
                            return response
                
                if res.status_code == 201:
                    return redirect("memo:memo_list")
                else:
                    messages.error(request, f"API error: {res.status_code} {res.text}")
            except requests.RequestException:
                messages.error(request, "Cannot connect to API server.")
    else:
        form = MemoForm()
    
    return render(request, "memo_form.html", {"form": form, "action": "Create"})

def memo_update(request, pk):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return redirect("memo:login")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{API_MEMOS_URL}{pk}/"
    
    try:
        res = requests.get(url, headers=headers)
        
        # Handle token expiration for GET
        if res.status_code == 401:
            new_access_token = refresh_access_token(request)
            if new_access_token:
                headers = {"Authorization": f"Bearer {new_access_token}"}
                res = requests.get(url, headers=headers)
                if res.ok:
                    response = render(request, "memo_form.html", {
                        "form": MemoForm(initial={
                            "title": res.json().get("title"), 
                            "content": res.json().get("content")
                        }), 
                        "action": "Update"
                    })
                    response.set_cookie("access_token", new_access_token, httponly=True, samesite="Lax")
                    return response
            messages.error(request, "Session expired. Please login again.")
            return redirect("memo:login")
        
        if not res.ok:
            messages.error(request, "Could not fetch memo to edit.")
            return redirect("memo:memo_list")
        
        memo = res.json()

        if request.method == "POST":
            form = MemoForm(request.POST, request.FILES)
            if form.is_valid():
                data = {
                    "title": form.cleaned_data["title"],
                    "content": form.cleaned_data["content"] or ""
                }
                files = {}
                if form.cleaned_data.get("photo"):
                    photo = request.FILES["photo"]
                    files = {"photo": (photo.name, photo, photo.content_type)}
                
                res2 = requests.put(url, headers=headers, data=data, files=files)
                
                # Handle token expiration for PUT
                if res2.status_code == 401:
                    new_access_token = refresh_access_token(request)
                    if new_access_token:
                        headers = {"Authorization": f"Bearer {new_access_token}"}
                        res2 = requests.put(url, headers=headers, data=data, files=files)
                        if res2.ok:
                            response = redirect("memo:memo_list")
                            response.set_cookie("access_token", new_access_token, httponly=True, samesite="Lax")
                            return response
                
                if res2.ok:
                    return redirect("memo:memo_list")
                else:
                    messages.error(request, f"API update error: {res2.status_code} {res2.text}")
        else:
            form = MemoForm(initial={"title": memo.get("title"), "content": memo.get("content")})
    except requests.RequestException:
        messages.error(request, "Cannot connect to API server.")
        return redirect("memo:memo_list")
    
    return render(request, "memo_form.html", {"form": form, "action": "Update"})

def memo_delete(request, pk):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return redirect("memo:login")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{API_MEMOS_URL}{pk}/"

    if request.method == "POST":
        try:
            response = requests.delete(url, headers=headers)
            
            # Handle token expiration for DELETE
            if response.status_code == 401:
                new_access_token = refresh_access_token(request)
                if new_access_token:
                    headers = {"Authorization": f"Bearer {new_access_token}"}
                    response = requests.delete(url, headers=headers)
                    if response.status_code in [200, 204]:
                        redirect_response = redirect("memo:memo_list")
                        redirect_response.set_cookie("access_token", new_access_token, httponly=True, samesite="Lax")
                        return redirect_response
            
            if response.status_code in [200, 204]:
                return redirect("memo:memo_list")
            else:
                error = response.text
                return render(request, "memo_confirm_delete.html", {"error": error})
        except requests.RequestException:
            messages.error(request, "Cannot connect to API server.")
            return redirect("memo:memo_list")

    return render(request, "memo_confirm_delete.html")

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
            })

            if response.status_code == 201:
                return redirect("memo:login")
            else:
                error = response.json().get("error", "Registration failed")
        except requests.RequestException:
            error = "Cannot connect to API server"

        return render(request, "registration/register.html", {"error": error})

    return render(request, "registration/register.html")

def logout_view(request):
    logout(request)
    response = redirect("memo:login")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response