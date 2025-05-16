import pytest
from fastapi import status

def test_create_user(client):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "department": "Tech"
    }
    response = client.post("/api/users/", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["department"] == user_data["department"]
    assert "id" in data
    assert "password" not in data

def test_create_user_duplicate_email(client):
    # Crear primer usuario
    user_data = {
        "username": "testuser1",
        "email": "test@example.com",
        "password": "testpassword123",
        "department": "Tech"
    }
    client.post("/api/users/", json=user_data)
    
    # Intentar crear segundo usuario con el mismo email
    user_data2 = {
        "username": "testuser2",
        "email": "test@example.com",
        "password": "testpassword123",
        "department": "Tech"
    }
    response = client.post("/api/users/", json=user_data2)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_get_users(client):
    # Crear un usuario primero
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "department": "Tech"
    }
    client.post("/api/users/", json=user_data)
    
    # Obtener lista de usuarios
    response = client.get("/api/users/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["username"] == user_data["username"]

def test_get_user_by_id(client):
    # Crear un usuario
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "department": "Tech"
    }
    create_response = client.post("/api/users/", json=user_data)
    user_id = create_response.json()["id"]
    
    # Obtener usuario por ID
    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["department"] == user_data["department"]

def test_update_user(client):
    # Crear un usuario
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "department": "Tech"
    }
    create_response = client.post("/api/users/", json=user_data)
    user_id = create_response.json()["id"]
    
    # Actualizar usuario
    update_data = {
        "username": "updateduser",
        "email": "updated@example.com",
        "department": "Sales"
    }
    response = client.put(f"/api/users/{user_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == update_data["username"]
    assert data["email"] == update_data["email"]
    assert data["department"] == update_data["department"]

def test_delete_user(client):
    # Crear un usuario
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "department": "Tech"
    }
    create_response = client.post("/api/users/", json=user_data)
    user_id = create_response.json()["id"]
    
    # Eliminar usuario
    response = client.delete(f"/api/users/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    
    # Verificar que el usuario ya no existe
    get_response = client.get(f"/api/users/{user_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND 