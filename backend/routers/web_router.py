from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
import os
import json
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import bcrypt
from dotenv import load_dotenv

from auth import verify_token, get_current_user
from db import get_db_connection, execute_read, execute_write
from models import UserCreate, UserLogin, UserResponse

load_dotenv()

router = APIRouter(prefix="/app", tags=["web"])

# ========== PÁGINA PRINCIPAL ==========
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return HTMLResponse(content=generate_dashboard_html())

# ========== PÁGINA DE TICKETS ==========
@router.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request):
    html_content = generate_tickets_html()
    return HTMLResponse(content=html_content)

# ========== FUNCIÓN GENERADORA DE HTML DE TICKETS ==========
def generate_tickets_html():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Tickets - Carrier Transicold</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #f5f7fa; color: #1e293b; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: white; border-radius: 16px; padding: 20px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; font-weight: 700; color: #0f3b5c; }
        .btn-primary { background: #0f3b5c; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s; }
        .btn-primary:hover { background: #1e4d6f; transform: translateY(-1px); }
        .btn-danger { background: #dc2626; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; }
        .btn-danger:hover { background: #b91c1c; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: white; padding: 30px; border-radius: 16px; width: 500px; max-width: 90%; }
        .modal-content h3 { margin-bottom: 20px; font-size: 20px; }
        .modal-content input, .modal-content select, .modal-content textarea { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 14px; }
        .modal-content button { margin-right: 10px; }
        .ticket-card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 6px solid; transition: all 0.2s; }
        .ticket-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .ticket-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .ticket-title { font-size: 18px; font-weight: 700; }
        .ticket-status { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .ticket-body { margin-top: 12px; }
        .ticket-footer { margin-top: 16px; display: flex; gap: 10px; justify-content: flex-end; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
        .section-title { font-size: 20px; font-weight: 700; margin: 24px 0 16px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Gestión de Tickets</h1>
            <button class="btn-primary" onclick="abrirModalCrear()">+ Nuevo Ticket</button>
        </div>
        <div id="ticketsList" class="grid"></div>
    </div>

    <!-- Modal Crear Ticket -->
    <div id="modalCrear" class="modal">
        <div class="modal-content">
            <h3>Crear Nuevo Ticket</h3>
            <select id="unidad" required>
                <option value="">Seleccionar Unidad</option>
            </select>
            <input type="text" id="vin" placeholder="VIN (opcional)">
            <textarea id="descripcion" placeholder="Descripción del problema" rows="4" required></textarea>
            <select id="tecnico" required>
                <option value="">Seleccionar Técnico</option>
            </select>
            <div style="margin-top: 20px; text-align: right;">
                <button class="btn-primary" onclick="crearTicket()">Guardar</button>
                <button onclick="cerrarModal()">Cancelar</button>
            </div>
        </div>
    </div>

    <script>
        // ========== FUNCIONES DE AUTENTICACIÓN ==========
        window.fetchAuth = async (url, options = {}) => {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = '/';
                throw new Error('No token');
            }
            const res = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                    'Authorization': `Bearer ${token}`
                }
            });
            if (res.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            return res;
        };

        // ========== CARGAR DATOS INICIALES ==========
        async function cargarTickets() {
            try {
                const res = await fetchAuth('/api/tickets/');
                const tickets = await res.json();
                const grid = document.getElementById('ticketsList');
                
                if (!tickets || tickets.length === 0) {
                    grid.innerHTML = '<p style="text-align:center; padding:40px;">No hay tickets.</p>';
                    return;
                }
                
                let html = '';
                tickets.forEach(t => {
                    const color = t.atendido ? '#10b981' : '#f59e0b';
                    const estadoText = t.atendido ? 'Completado' : 'Pendiente';
                    html += `
                        <div class="ticket-card" style="border-left-color: ${color}">
                            <div class="ticket-header">
                                <span class="ticket-title">Ticket #${t.ticket_num}</span>
                                <span class="ticket-status" style="background: ${color}20; color: ${color}">
                                    ${estadoText}
                                </span>
                            </div>
                            <div class="ticket-body">
                                <p><strong>Unidad:</strong> ${t.unit_number || 'N/A'} | <strong>VIN:</strong> ${t.vin_number || 'N/A'}</p>
                                <p><strong>Descripción:</strong> ${t.descripcion || 'Sin descripción'}</p>
                                <p><strong>Creado por:</strong> ${t.creado_por || 'N/A'} · ${new Date(t.fecha_creacion).toLocaleString()}</p>
                                <p><strong>Técnico:</strong> ${t.tecnico_asig || 'No asignado'}</p>
                            </div>
                            <div class="ticket-footer">
                                ${!t.atendido ? `<button class="btn-primary" onclick="marcarCompletado(${t.id})">Marcar Completado</button>` : ''}
                                <button class="btn-danger" onclick="eliminarTicket(${t.id})">Eliminar</button>
                            </div>
                        </div>
                    `;
                });
                grid.innerHTML = html;
            } catch (error) {
                console.error('Error cargando tickets:', error);
            }
        }

        // ========== FUNCIÓN CORREGIDA: CREAR TICKET ==========
        async function crearTicket() {
            const unidad = document.getElementById('unidad').value;
            const vin = document.getElementById('vin').value;
            const descripcion = document.getElementById('descripcion').value;
            const tecnico = document.getElementById('tecnico').value;
            
            if (!unidad || !descripcion || !tecnico) {
                alert('Completa los campos obligatorios');
                return;
            }
            
            try {
                const res = await fetchAuth('/api/tickets/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        unit_number: unidad,      // ← CAMPO CORRECTO
                        vin_number: vin,
                        descripcion: descripcion,
                        tecnico: tecnico
                    })
                });
                
                const data = await res.json();
                
                if (res.ok) {
                    alert('✅ Ticket creado exitosamente');
                    cerrarModal();
                    cargarTickets();
                } else {
                    alert('Error: ' + JSON.stringify(data.detail));
                }
            } catch (error) {
                console.error('Error creando ticket:', error);
                alert('Error al crear el ticket');
            }
        }

        async function marcarCompletado(id) {
            if (confirm('¿Marcar este ticket como completado?')) {
                try {
                    const res = await fetchAuth(`/api/tickets/${id}/complete`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    if (res.ok) {
                        alert('Ticket completado');
                        cargarTickets();
                    } else {
                        alert('Error al completar');
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }
        }

        async function eliminarTicket(id) {
            if (confirm('¿Eliminar este ticket permanentemente?')) {
                try {
                    const res = await fetchAuth(`/api/tickets/${id}`, {
                        method: 'DELETE'
                    });
                    if (res.ok) {
                        alert('Ticket eliminado');
                        cargarTickets();
                    } else {
                        alert('Error al eliminar');
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }
        }

        async function cargarUnidades() {
            try {
                const res = await fetchAuth('/api/unidades/');
                const unidades = await res.json();
                const select = document.getElementById('unidad');
                if (Array.isArray(unidades)) {
                    unidades.forEach(u => {
                        const option = document.createElement('option');
                        option.value = u.unit_number;
                        option.textContent = `${u.unit_number} - ${u.vin_number || 'Sin VIN'}`;
                        select.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error cargando unidades:', error);
            }
        }

        async function cargarTecnicos() {
            try {
                const res = await fetchAuth('/api/usuarios/');
                const usuarios = await res.json();
                const select = document.getElementById('tecnico');
                if (Array.isArray(usuarios)) {
                    usuarios.forEach(u => {
                        if (u.role === 'tecnico' || u.role === 'admin') {
                            const option = document.createElement('option');
                            option.value = u.username;
                            option.textContent = u.username;
                            select.appendChild(option);
                        }
                    });
                }
            } catch (error) {
                console.error('Error cargando técnicos:', error);
            }
        }

        function abrirModalCrear() {
            document.getElementById('modalCrear').style.display = 'flex';
            document.getElementById('unidad').value = '';
            document.getElementById('vin').value = '';
            document.getElementById('descripcion').value = '';
            document.getElementById('tecnico').value = '';
        }

        function cerrarModal() {
            document.getElementById('modalCrear').style.display = 'none';
        }

        // Inicializar
        cargarUnidades();
        cargarTecnicos();
        cargarTickets();
    </script>
</body>
</html>
    """

# Función para generar el dashboard principal
def generate_dashboard_html():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Carrier Transicold</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #f5f7fa; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #0f3b5c; color: white; padding: 20px; border-radius: 12px; margin-bottom: 30px; }
        .menu { display: flex; gap: 15px; margin-top: 15px; flex-wrap: wrap; }
        .menu a { background: rgba(255,255,255,0.2); color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; transition: 0.2s; }
        .menu a:hover { background: rgba(255,255,255,0.3); }
        .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .btn { background: #0f3b5c; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚛 Carrier Transicold - Dashboard</h1>
            <div class="menu">
                <a href="/app/tickets">🎫 Tickets</a>
                <a href="/app/unidades">📸 Unidades</a>
                <a href="/app/usuarios">👥 Usuarios</a>
            </div>
        </div>
        <div class="card">
            <h2>Bienvenido al Sistema</h2>
            <p>Selecciona una opción del menú para comenzar.</p>
        </div>
    </div>
</body>
</html>
    """
 
 
