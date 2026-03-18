# Portal Cautivo con Google OAuth - Continuación

## Estado actual
- El código está en la rama `feature/captive-portal-google-oauth` (no en main)
- Main está limpio, sin cambios del portal
- Para retomar: `git merge feature/captive-portal-google-oauth`

## Qué ya está hecho (en la rama)
- 3 modelos: AllowedDomain, PortalUser, PortalSession
- 3 blueprints: domains (admin CRUD), portal_users (admin), portal (público OAuth)
- Servicio portal_sync.py (MAC auth en radcheck/radusergroup)
- CLI: `flask portal-cleanup`
- Dashboard con stats del portal
- Sidebar con sección "Portal Cautivo"
- Templates: landing con botón Google, success, error
- Authlib configurado, OAuth con Google registrado
- CSRF exempt en blueprint portal

## Pasos pendientes (en orden)

### 1. Google Cloud Console
- Ir a https://console.cloud.google.com
- Crear proyecto (o usar uno existente)
- Habilitar "Google Identity" o "People API"
- Ir a Credentials → Create OAuth 2.0 Client ID
- Tipo: Web application
- Authorized redirect URI: `http://wifi.apps.grupogaman.com.ar/portal/callback`
- Copiar GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET

### 2. Merge y deploy
```bash
git checkout main
git merge feature/captive-portal-google-oauth
git push origin main
```

### 3. Variables de entorno en Coolify
Agregar en la app (UUID: ks0k004o4ksowogkokcgs8kc):
- `GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com`
- `GOOGLE_CLIENT_SECRET=xxx`
- `PORTAL_SESSION_HOURS=24`

### 4. Migración Alembic
Conectarse al contenedor de la app en Coolify y ejecutar:
```bash
flask db migrate -m "portal cautivo"
flask db upgrade
```
Esto crea las 3 tablas: gaman_allowed_domain, gaman_portal_user, gaman_portal_session

### 5. Crear dominio permitido
Desde el panel admin (http://wifi.apps.grupogaman.com.ar):
- Ir a Dominios → Nuevo Dominio
- Agregar el dominio de Google Workspace del cliente (ej: empresa.com)
- Seleccionar el grupo/VLAN por defecto

### 6. Red - VLAN para SSID guest
- Crear VLAN dedicada (ej: VLAN 50) con subred propia y DHCP
- Asegurar ruta hacia wifi.apps.grupogaman.com.ar (Flask) y 192.168.38.3:1812-1813 (RADIUS)
- DNS funcional (para accounts.google.com)
- En MikroTik: reglas firewall permitiendo tráfico de VLAN guest hacia esas IPs

### 7. Aruba Instant On - SSID guest
- Crear SSID (ej: "WiFi-Guest" o el nombre que quiera el cliente)
- Seguridad: Open (sin WPA)
- Captive Portal: Externo
- URL del portal: `http://wifi.apps.grupogaman.com.ar/portal`
- RADIUS: 192.168.38.3, puerto 1812, secret: GMW6VikovrmXSiHLbOnaLM5B5AYwrroH
- Walled Garden (dominios permitidos sin autenticación):
  - wifi.apps.grupogaman.com.ar
  - accounts.google.com
  - oauth2.googleapis.com
  - fonts.googleapis.com
  - cdn.jsdelivr.net

### 8. Verificar parámetro MAC del AP
- Conectar un dispositivo al SSID guest
- Ver la URL a la que redirige el AP
- Si el parámetro de MAC NO es `mac`, editar `app/blueprints/portal/routes.py:14`:
  ```python
  mac = request.args.get("mac", "")  # cambiar "mac" por el parámetro correcto
  ```

### 9. Pruebas
1. Admin: crear dominio permitido con grupo/VLAN → ver en lista
2. Navegar a /portal → ver landing con botón Google
3. Login con cuenta del dominio → portal_user creado, MAC en radcheck + radusergroup
4. Login con cuenta de dominio NO permitido → error "dominio no autorizado"
5. Admin: cambiar grupo de portal user → verificar radusergroup actualizado
6. Admin: deshabilitar portal user → MAC eliminada de radcheck
7. Dispositivo real: conectar al SSID guest → portal → Google → acceso con VLAN
8. Expiración: ejecutar `flask portal-cleanup` → MAC eliminada
