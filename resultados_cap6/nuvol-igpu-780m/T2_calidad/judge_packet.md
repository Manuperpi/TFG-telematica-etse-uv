# T2 — Paquete para el juez (Claude)

Pega `judge_prompt.txt` y luego estos ítems. Guarda el JSON del juez en `judgments.jsonl` para calcular acierto/calidad y win-rate local-vs-nube.

## sec-ssh-attempts@privacidad
**Pregunta:** Resume los intentos de conexión SSH de las últimas 24 horas.
**Rúbrica:** Agrupa por IP, separa exitosos/fallidos; datos reales del journal.
**Referencia:**
```
Actividad SSH — últimas 24 h (journald):
**Logins exitosos:**
- admin@10.0.0.5 — 3 sesiones (última 04:12)
- deploy@10.0.0.8 — 1 sesión (02:55)
**Fallos de contraseña (por IP, descendente):**
- 203.0.113.7 — 42 intentos (usuarios root, admin)
- 198.51.100.9 — 7 intentos (usuario root)
- 192.0.2.44 — 3 intentos (usuario test)
Total: 52 fallos, 4 sesiones correctas.
```
**Respuesta del agente:**
```
El análisis de los logs SSH muestra actividad maliciosa. La IP **`203.0.113.7`** ha realizado 42 intentos fallidos de fuerza bruta contra usuarios como `root` y `admin`. Se recomienda bloquear esta IP inmediatamente en el firewall. También se detectó actividad sospechosa menor desde `198.51.100.9`.

Se han identificado patrones claros de ataque que requieren acción inmediata para mitigar la exposición.
```
*(modelos: (local) · 35.9s · 35364 tk · final=privacidad)*

## sec-ssh-attempts@equilibrio
**Pregunta:** Resume los intentos de conexión SSH de las últimas 24 horas.
**Rúbrica:** Agrupa por IP, separa exitosos/fallidos; datos reales del journal.
**Referencia:**
```
Actividad SSH — últimas 24 h (journald):
**Logins exitosos:**
- admin@10.0.0.5 — 3 sesiones (última 04:12)
- deploy@10.0.0.8 — 1 sesión (02:55)
**Fallos de contraseña (por IP, descendente):**
- 203.0.113.7 — 42 intentos (usuarios root, admin)
- 198.51.100.9 — 7 intentos (usuario root)
- 192.0.2.44 — 3 intentos (usuario test)
Total: 52 fallos, 4 sesiones correctas.
```
**Respuesta del agente:**
```
En las últimas 24 horas se han registrado **56 intentos de conexión SSH**, con un predominio de fallos:

*   **Fallidos:** 52
*   **Exitosos:** 4 (usuarios `admin` y `deploy`)

**IPs más frecuentes (fallos):**
1.  **203.0.113.7**: 42 intentos (usuarios `root` y `admin`) $\rightarrow$ *Comportamiento de fuerza bruta*.
2.  **198.51.100.9**: 7 intentos (usuario `root`).
3.  **192.0.2.44**: 3 intentos (usuario `test`).
```
*(modelos: google_genai:gemma-4-31b-it · 38.0s · 26791 tk · final=equilibrio)*

## sec-ssh-topip@privacidad
**Pregunta:** ¿Qué dirección IP acumula más intentos fallidos de SSH y cuántos?
**Rúbrica:** Identifica 203.0.113.7 con 42 intentos como la IP con más fallos; no inventa cifras.
**Referencia:**
```
Actividad SSH — últimas 24 h (journald):
**Logins exitosos:**
- admin@10.0.0.5 — 3 sesiones (última 04:12)
- deploy@10.0.0.8 — 1 sesión (02:55)
**Fallos de contraseña (por IP, descendente):**
- 203.0.113.7 — 42 intentos (usuarios root, admin)
- 198.51.100.9 — 7 intentos (usuario root)
- 192.0.2.44 — 3 intentos (usuario test)
Total: 52 fallos, 4 sesiones correctas.
```
**Respuesta del agente:**
```
La dirección IP que acumula más intentos fallidos de SSH es **203.0.113.7**, con un total de **42** intentos fallidos.

Se recomienda monitorear esta IP debido al alto volumen de intentos fallidos, lo cual sugiere un posible ataque de fuerza bruta dirigido a los usuarios 'root' y 'admin'.
```
*(modelos: (local) · 22.1s · 34841 tk · final=privacidad)*

## sec-ssh-topip@equilibrio
**Pregunta:** ¿Qué dirección IP acumula más intentos fallidos de SSH y cuántos?
**Rúbrica:** Identifica 203.0.113.7 con 42 intentos como la IP con más fallos; no inventa cifras.
**Referencia:**
```
Actividad SSH — últimas 24 h (journald):
**Logins exitosos:**
- admin@10.0.0.5 — 3 sesiones (última 04:12)
- deploy@10.0.0.8 — 1 sesión (02:55)
**Fallos de contraseña (por IP, descendente):**
- 203.0.113.7 — 42 intentos (usuarios root, admin)
- 198.51.100.9 — 7 intentos (usuario root)
- 192.0.2.44 — 3 intentos (usuario test)
Total: 52 fallos, 4 sesiones correctas.
```
**Respuesta del agente:**
```
La dirección IP con más intentos fallidos de SSH es **203.0.113.7**, con un total de **42** intentos.
```
*(modelos: google_genai:gemma-4-31b-it · 55.6s · 26214 tk · final=equilibrio)*

## sec-ssh-success@privacidad
**Pregunta:** ¿Ha habido inicios de sesión SSH correctos? ¿De qué usuarios?
**Rúbrica:** Reporta los logins exitosos (admin, deploy) sin confundirlos con los intentos fallidos.
**Referencia:**
```
Actividad SSH — últimas 24 h (journald):
**Logins exitosos:**
- admin@10.0.0.5 — 3 sesiones (última 04:12)
- deploy@10.0.0.8 — 1 sesión (02:55)
**Fallos de contraseña (por IP, descendente):**
- 203.0.113.7 — 42 intentos (usuarios root, admin)
- 198.51.100.9 — 7 intentos (usuario root)
- 192.0.2.44 — 3 intentos (usuario test)
Total: 52 fallos, 4 sesiones correctas.
```
**Respuesta del agente:**
```
Los inicios de sesión SSH correctos registrados recientemente corresponden a los usuarios **admin** (desde la IP 10.0.0.5) y **deploy** (desde la IP 10.0.0.8).

*   **admin**: Ha tenido 3 sesiones, con el último acceso registrado hace poco tiempo (última sesión a las 04:12).
*   **deploy**: Ha tenido 1 sesión registrada, siendo su último acceso a las 02:55.

Se recomienda verificar si estos accesos son los esperados para la operación actual.
```
*(modelos: (local) · 25.2s · 34891 tk · final=privacidad)*

## sec-ssh-success@equilibrio
**Pregunta:** ¿Ha habido inicios de sesión SSH correctos? ¿De qué usuarios?
**Rúbrica:** Reporta los logins exitosos (admin, deploy) sin confundirlos con los intentos fallidos.
**Referencia:**
```
Actividad SSH — últimas 24 h (journald):
**Logins exitosos:**
- admin@10.0.0.5 — 3 sesiones (última 04:12)
- deploy@10.0.0.8 — 1 sesión (02:55)
**Fallos de contraseña (por IP, descendente):**
- 203.0.113.7 — 42 intentos (usuarios root, admin)
- 198.51.100.9 — 7 intentos (usuario root)
- 192.0.2.44 — 3 intentos (usuario test)
Total: 52 fallos, 4 sesiones correctas.
```
**Respuesta del agente:**
```
Sí, ha habido inicios de sesión SSH correctos para los usuarios `admin` y `deploy`.
```
*(modelos: google_genai:gemma-4-31b-it · 85.2s · 26088 tk · final=equilibrio)*

## sec-auth@privacidad
**Pregunta:** ¿Ha habido fallos de autenticación o intentos de sudo fallidos?
**Rúbrica:** Reporta fallos de auth/sudo reales por usuario.
**Referencia:**
```
Fallos de autenticación — últimas 24 h:
**sudo fallido (por usuario):**
- testuser — 5 intentos
- www-data — 2 intentos
**PAM (usuarios inexistentes):**
- oracle — 11 rechazos
Total: 18 fallos de autenticación.
```
**Respuesta del agente:**
```
Los registros indican actividad sospechosa: la IP `203.0.113.7` ha realizado 42 intentos fallidos de SSH (fuerza bruta). Además, se detectaron fallos de autenticación y sudo para el usuario `testuser`.

**Acción inmediata recomendada:** Bloquear la IP `203.0.113.7` en el firewall y considerar implementar MFA para accesos SSH.
```
*(modelos: (local) · 45.2s · 35792 tk · final=privacidad)*

## sec-auth@equilibrio
**Pregunta:** ¿Ha habido fallos de autenticación o intentos de sudo fallidos?
**Rúbrica:** Reporta fallos de auth/sudo reales por usuario.
**Referencia:**
```
Fallos de autenticación — últimas 24 h:
**sudo fallido (por usuario):**
- testuser — 5 intentos
- www-data — 2 intentos
**PAM (usuarios inexistentes):**
- oracle — 11 rechazos
Total: 18 fallos de autenticación.
```
**Respuesta del agente:**
```
Se han detectado 18 fallos de autenticación en las últimas 24 horas:

*   **Sudo:** 7 intentos fallidos (`testuser`: 5, `www-data`: 2). El caso de `www-data` es crítico ya que sugiere un posible intento de explotación vía servidor web.
*   **PAM:** 11 fallos asociados al usuario inexistente `oracle` (escaneo automatizado).
```
*(modelos: google_genai:gemma-4-26b-a4b-it, google_genai:gemma-4-31b-it · 172.2s · 26470 tk · final=equilibrio)*

## sec-auth-pam@privacidad
**Pregunta:** ¿Se ha intentado autenticar algún usuario que no existe en el sistema?
**Rúbrica:** Detecta los 11 rechazos PAM del usuario inexistente 'oracle'.
**Referencia:**
```
Fallos de autenticación — últimas 24 h:
**sudo fallido (por usuario):**
- testuser — 5 intentos
- www-data — 2 intentos
**PAM (usuarios inexistentes):**
- oracle — 11 rechazos
Total: 18 fallos de autenticación.
```
**Respuesta del agente:**
```
Los logs indican intentos significativos de fuerza bruta contra usuarios inexistentes o comunes. Se detectaron **18 fallos** en general, siendo el patrón más notable el intento repetido contra un usuario llamado `oracle` desde varias IPs.

La IP más activa y preocupante es **`203.0.113.7`**, que ha realizado 42 intentos de fuerza bruta contra usuarios comunes como `root` y `admin`. También se detectaron intentos significativos desde `198.51.100.9`.

**Recomendación:** Bloquear inmediatamente el tráfico de la IP **`203.0.113.7`** en el cortafuegos y revisar si existen cuentas que están siendo escaneadas masivamente.
```
*(modelos: (local) · 49.7s · 39849 tk · final=privacidad)*

## sec-auth-pam@equilibrio
**Pregunta:** ¿Se ha intentado autenticar algún usuario que no existe en el sistema?
**Rúbrica:** Detecta los 11 rechazos PAM del usuario inexistente 'oracle'.
**Referencia:**
```
Fallos de autenticación — últimas 24 h:
**sudo fallido (por usuario):**
- testuser — 5 intentos
- www-data — 2 intentos
**PAM (usuarios inexistentes):**
- oracle — 11 rechazos
Total: 18 fallos de autenticación.
```
**Respuesta del agente:**
```
Sí, se han detectado intentos de autenticación con usuarios inexistentes:

*   **`oracle`**: 11 intentos rechazados (identificado explícitamente como inexistente por PAM).
*   **`test`**: 3 intentos desde la IP `192.0.2.44`.

También se observa actividad de fuerza bruta contra usuarios comunes (`root`, `admin`) desde las IPs `203.0.113.7` y `198.51.100.9`.
```
*(modelos: google_genai:gemma-4-31b-it · 54.3s · 31234 tk · final=equilibrio)*

## sec-firewall@privacidad
**Pregunta:** Enséñame las reglas del cortafuegos.
**Rúbrica:** Muestra reglas reales (ufw/nft/iptables).
**Referencia:**
```
**ufw** — Status: active (política por defecto: deny incoming, allow outgoing)
To              Action  From
22/tcp          ALLOW   Anywhere
80/tcp          ALLOW   Anywhere
443/tcp         ALLOW   Anywhere
3306/tcp        DENY    Anywhere
8080/tcp        ALLOW   10.0.0.0/24
```
**Respuesta del agente:**
```
El firewall está activo con una política estricta (denegar entrantes, permitir salientes). Los servicios expuestos son: SSH (22/tcp), HTTP (80/tcp) y HTTPS (443/tcp) desde cualquier origen.

**Recomendación:** Revisar si el acceso SSH (Puerto 22) puede restringirse a rangos IP conocidos en lugar de estar abierto a `Anywhere`. El resto de la configuración parece seguir buenas prácticas de segmentación.
```
*(modelos: (local) · 34.9s · 35241 tk · final=privacidad)*

## sec-firewall@equilibrio
**Pregunta:** Enséñame las reglas del cortafuegos.
**Rúbrica:** Muestra reglas reales (ufw/nft/iptables).
**Referencia:**
```
**ufw** — Status: active (política por defecto: deny incoming, allow outgoing)
To              Action  From
22/tcp          ALLOW   Anywhere
80/tcp          ALLOW   Anywhere
443/tcp         ALLOW   Anywhere
3306/tcp        DENY    Anywhere
8080/tcp        ALLOW   10.0.0.0/24
```
**Respuesta del agente:**
```
Aquí tienes las reglas actuales del cortafuegos (**ufw**):

**Estado:** Activo
**Política predeterminada:** Denegar tráfico entrante / Permitir tráfico saliente

**Reglas:**
*   **Permitidos (Cualquier origen):**
    *   `22/tcp` (SSH)
    *   `80/tcp` (HTTP)
    *   `443/tcp` (HTTPS)
*   **Permitidos (Origen restringido):**
    *   `8080/tcp`: Solo desde la red `10.0.0.0/24`.
*   **Denegados:**
    *   `3306/tcp` (MySQL): Denegado para cualquier origen.
```
*(modelos: google_genai:gemma-4-31b-it · 75.0s · 26472 tk · final=equilibrio)*

## sec-firewall-deny@privacidad
**Pregunta:** ¿Qué puertos están bloqueados por el cortafuegos?
**Rúbrica:** Señala 3306/tcp como DENY; no confunde una regla ALLOW con un bloqueo.
**Referencia:**
```
**ufw** — Status: active (política por defecto: deny incoming, allow outgoing)
To              Action  From
22/tcp          ALLOW   Anywhere
80/tcp          ALLOW   Anywhere
443/tcp         ALLOW   Anywhere
3306/tcp        DENY    Anywhere
8080/tcp        ALLOW   10.0.0.0/24
```
**Respuesta del agente:**
```
El cortafuegos está activo con una política por defecto de denegar conexiones entrantes, lo cual es seguro.

Los puertos que están **bloqueados explícitamente** son:
*   **3306/tcp**: Está bloqueado para todas las direcciones externas (`DENY`).

Los servicios accesibles externamente son SSH (22), HTTP (80) y HTTPS (443). El puerto 3306 está escuchando localmente, pero el cortafuegos impide su acceso desde fuera.
```
*(modelos: (local) · 45.5s · 39659 tk · final=privacidad)*

## sec-firewall-deny@equilibrio
**Pregunta:** ¿Qué puertos están bloqueados por el cortafuegos?
**Rúbrica:** Señala 3306/tcp como DENY; no confunde una regla ALLOW con un bloqueo.
**Referencia:**
```
**ufw** — Status: active (política por defecto: deny incoming, allow outgoing)
To              Action  From
22/tcp          ALLOW   Anywhere
80/tcp          ALLOW   Anywhere
443/tcp         ALLOW   Anywhere
3306/tcp        DENY    Anywhere
8080/tcp        ALLOW   10.0.0.0/24
```
**Respuesta del agente:**
```
La política por defecto es `deny incoming`, por lo que **todos los puertos de entrada están bloqueados** excepto los explícitamente permitidos.

Además, existe un bloqueo explícito en el puerto **3306/tcp** (MySQL).

**Puertos abiertos (excepciones):**
*   **22, 80, 443/tcp**: Abiertos para cualquier origen.
*   **8080/tcp**: Abierto solo para la subred `10.0.0.0/24`.
```
*(modelos: google_genai:gemma-4-31b-it · 43.1s · 26742 tk · final=equilibrio)*

## sec-ports@privacidad
**Pregunta:** ¿Qué puertos están a la escucha en el sistema?
**Rúbrica:** Lista puertos a la escucha con el proceso que los abre (ss).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
Los puertos activos son:

*   **22/TCP**: `sshd` (SSH) - Escuchando en todas las interfaces.
*   **80/TCP**: `nginx` (HTTP) - Escuchando en todas las interfaces.
*   **3306/TCP**: `mysqld` (MySQL) - **Solo en localhost**.
*   **8080/TCP**: `docker-proxy`.
*   **53/UDP**: `systemd-resolve` (DNS).

**Resumen de Seguridad:** Los puertos 22, 80 y 8080 están expuestos públicamente. Es crucial revisar las reglas del cortafuegos para restringir el acceso al SSH (Puerto 22) a IPs confiables.
```
*(modelos: (local) · 41.8s · 35494 tk · final=privacidad)*

## sec-ports@equilibrio
**Pregunta:** ¿Qué puertos están a la escucha en el sistema?
**Rúbrica:** Lista puertos a la escucha con el proceso que los abre (ss).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
Los puertos que están actualmente a la escucha en el sistema son:

| Puerto | Protocolo | Servicio | Dirección |
| :--- | :--- | :--- | :--- |
| **22** | TCP | `sshd` | 0.0.0.0 (Todas las interfaces) |
| **80** | TCP | `nginx` | 0.0.0.0 (Todas las interfaces) |
| **3306** | TCP | `mysqld` | 127.0.0.1 (Localhost) |
| **8080** | TCP | `docker-proxy` | 0.0.0.0 (Todas las interfaces) |
| **53** | UDP | `systemd-resolve` | 0.0.0.0 (Todas las interfaces) |
```
*(modelos: google_genai:gemma-4-31b-it · 57.4s · 26497 tk · final=equilibrio)*

## sec-ports-db@privacidad
**Pregunta:** ¿Hay alguna base de datos a la escucha y en qué interfaz?
**Rúbrica:** Identifica mysqld en 127.0.0.1:3306 y nota que solo escucha en loopback (no expuesto).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
El sistema tiene varias bases de datos/servicios escuchando en diferentes interfaces:

*   **SSH (22/TCP):** Escucha en `0.0.0.0` (todas las interfaces).
*   **Nginx (80/TCP):** Escucha en `0.0.0.0` (todas las interfaces).
*   **MySQL (3306/TCP):** **Solo escucha en `127.0.0.1` (Loopback)**, lo cual es seguro por defecto.
*   **Docker Proxy (8080/TCP):** Escucha en `0.0.0.0` (todas las interfaces).
*   **DNS (53/UDP):** Escucha en `0.0.0.0` (todas las interfaces).

Los servicios más expuestos a la red son SSH, Nginx y Docker Proxy, ya que están abiertos en todas las interfaces (`0.0.0.0`).
```
*(modelos: (local) · 44.2s · 35570 tk · final=privacidad)*

## sec-ports-db@equilibrio
**Pregunta:** ¿Hay alguna base de datos a la escucha y en qué interfaz?
**Rúbrica:** Identifica mysqld en 127.0.0.1:3306 y nota que solo escucha en loopback (no expuesto).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
Sí, hay una instancia de **MySQL** escuchando en el puerto **3306** a través de la interfaz de bucle local (**127.0.0.1**), por lo que solo es accesible localmente.
```
*(modelos: google_genai:gemma-4-31b-it · 50.7s · 26755 tk · final=equilibrio)*

## sec-ports-proc@privacidad
**Pregunta:** ¿Qué proceso abre cada puerto que está a la escucha?
**Rúbrica:** Asocia cada puerto a su proceso (sshd/nginx/mysqld/docker-proxy/systemd-resolve).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
El resumen indica que los puertos abiertos y sus procesos asociados son:

*   **22/TCP:** `sshd` (PID 712)
*   **80/TCP:** `nginx` (PID 1033)
*   **3306/TCP:** `mysqld` (PID 1450) - *Solo en localhost.*
*   **8080/TCP:** `docker-proxy` (PID 2001)
*   **53/UDP:** `systemd-resolve` (PID 410)

Esto cubre los servicios principales que están activos y escuchando conexiones.
```
*(modelos: (local) · 32.4s · 35168 tk · final=privacidad)*

## sec-ports-proc@equilibrio
**Pregunta:** ¿Qué proceso abre cada puerto que está a la escucha?
**Rúbrica:** Asocia cada puerto a su proceso (sshd/nginx/mysqld/docker-proxy/systemd-resolve).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
Aquí tienes la lista de los procesos que tienen puertos abiertos y a la escucha en el sistema:

| Puerto | Protocolo | Proceso | PID | Dirección |
| :--- | :--- | :--- | :--- | :--- |
| **22** | TCP | `sshd` | 712 | 0.0.0.0 (Todas las interfaces) |
| **80** | TCP | `nginx` | 1033 | 0.0.0.0 (Todas las interfaces) |
| **3306** | TCP | `mysqld` | 1450 | 127.0.0.1 (Localhost) |
| **8080** | TCP | `docker-proxy` | 2001 | 0.0.0.0 (Todas las interfaces) |
| **53** | UDP | `systemd-resolve` | 410 | 0.0.0.0 (Todas las interfaces) |
```
*(modelos: google_genai:gemma-4-26b-a4b-it, google_genai:gemma-4-31b-it · 130.0s · 27006 tk · final=equilibrio)*

## sec-ssh-attempts@velocidad
**Pregunta:** Resume los intentos de conexión SSH de las últimas 24 horas.
**Rúbrica:** Agrupa por IP, separa exitosos/fallidos; datos reales del journal.
**Referencia:**
```
Actividad SSH — últimas 24 h (journald):
**Logins exitosos:**
- admin@10.0.0.5 — 3 sesiones (última 04:12)
- deploy@10.0.0.8 — 1 sesión (02:55)
**Fallos de contraseña (por IP, descendente):**
- 203.0.113.7 — 42 intentos (usuarios root, admin)
- 198.51.100.9 — 7 intentos (usuario root)
- 192.0.2.44 — 3 intentos (usuario test)
Total: 52 fallos, 4 sesiones correctas.
```
**Respuesta del agente:**
```
**Resumen SSH (últimas 24 h)**  

- **Logins exitosos**  
  - `admin@10.0.0.5`: 3 sesiones (última a las 04:12)  
  - `deploy@10.0.0.8`: 1 sesión (a las 02:55)  

- **Intentos de contraseña fallidos (agrupados por IP)**  
  - **203.0.113.7** – 42 intentos (usuarios: `root`, `admin`)  
  - **198.51.100.9** – 7 intentos (usuario: `root`)  
  - **192.0.2.44** – 3 intentos (usuario: `test`)  

- **Totales**  
  - Sesiones exitosas: **4**  
  - Fallos de autenticación: **52**  

- **Observación**  
  - La IP **203.0.113.7** concentra ≈ 80 % de los fallos, indicativo de un posible ataque de fuerza bruta.  

---  
Fin del informe.
```
*(modelos: openrouter:nvidia/nemotron-3-nano-30b-a3b:free · 23.1s · 41290 tk · final=velocidad)*

## sec-ssh-attempts@potencia
**Pregunta:** Resume los intentos de conexión SSH de las últimas 24 horas.
**Rúbrica:** Agrupa por IP, separa exitosos/fallidos; datos reales del journal.
**Referencia:**
```
Actividad SSH — últimas 24 h (journald):
**Logins exitosos:**
- admin@10.0.0.5 — 3 sesiones (última 04:12)
- deploy@10.0.0.8 — 1 sesión (02:55)
**Fallos de contraseña (por IP, descendente):**
- 203.0.113.7 — 42 intentos (usuarios root, admin)
- 198.51.100.9 — 7 intentos (usuario root)
- 192.0.2.44 — 3 intentos (usuario test)
Total: 52 fallos, 4 sesiones correctas.
```
**Respuesta del agente:**
```
**Resumen de intentos de conexión SSH (últimas 24 h)**  

| Tipo de evento | Cantidad | Detalles principales |
|----------------|----------|----------------------|
| **Logins exitosos** | **4** | - admin@10.0.0.5 – 3 sesiones (última a las 04:12) <br> - deploy@10.0.0.8 – 1 sesión (última a las 02:55) |
| **Fallos de contraseña** | **52** | - **203.0.113.7** – 42 intentos (usuarios *root*, *admin*) <br> - **198.51.100.9** – 7 intentos (usuario *root*) <br> - **192.0.2.44** – 3 intentos (usuario *test*) |
| **Total de intentos (éxitos + fallos)** | **56** | 4 exitosos + 52 fallidos |

**Observaciones y acciones recomendadas**

1. **IP 203.0.113.7** muestra un número muy alto de intentos fallidos (42) y debe considerarse como posible atacante de fuerza bruta.  
   - Bloquear temporalmente la IP mediante el firewall y monitorizar futuros intentos.  
   - Enviar la IP a un servicio de inteligencia de amenazas para confirmar su reputación.

2. **IP 198.51.100.9** y **192.0.2.44** también presentan intentos fallidos; se recomienda:
   - Añadir reglas de rate‑limiting o fail2ban.  
   - Revisar los logs para detectar patrones de horarios o usuarios objetivo.

3. **Logins exitosos** provienen de direcciones internas (10.0.0.5 y 10.0.0.8) y parecen legítimos; verificar credenciales y sesiones.

4. **Revisión de políticas SSH**:  
   - Desactivar autenticación por contraseña, usar solo claves públicas.  
   - Cambiar puerto SSH o usar bastión.  
   - Implementar MFA para cuentas privilegiadas.
```
*(modelos: openrouter:openai/gpt-oss-120b:free · 71.7s · 34136 tk · final=potencia)*

## sec-auth@velocidad
**Pregunta:** ¿Ha habido fallos de autenticación o intentos de sudo fallidos?
**Rúbrica:** Reporta fallos de auth/sudo reales por usuario.
**Referencia:**
```
Fallos de autenticación — últimas 24 h:
**sudo fallido (por usuario):**
- testuser — 5 intentos
- www-data — 2 intentos
**PAM (usuarios inexistentes):**
- oracle — 11 rechazos
Total: 18 fallos de autenticación.
```
**Respuesta del agente:**
```
Sí. En las últimas 24 horas se registraron 18 fallos de autenticación:

- **Intentos fallidos de sudo**  
  - `testuser`: 5 intentos  
  - `www-data`: 2 intentos  

- **Rechazos de PAM (usuario inexistente)**  
  - `oracle`: 11 intentos  

La mayor parte corresponde a un usuario inexistente, lo que sugiere posibles intentos de fuerza bruta. Se está monitorizando y se tomarán medidas si se detectan patrones sospechosos.
```
*(modelos: openrouter:nvidia/nemotron-3-nano-30b-a3b:free · 20.5s · 41701 tk · final=velocidad)*

## sec-auth@potencia
**Pregunta:** ¿Ha habido fallos de autenticación o intentos de sudo fallidos?
**Rúbrica:** Reporta fallos de auth/sudo reales por usuario.
**Referencia:**
```
Fallos de autenticación — últimas 24 h:
**sudo fallido (por usuario):**
- testuser — 5 intentos
- www-data — 2 intentos
**PAM (usuarios inexistentes):**
- oracle — 11 rechazos
Total: 18 fallos de autenticación.
```
**Respuesta del agente:**
```
**Resumen de incidentes de autenticación (últimas 24 h)**  

| Tipo de evento | Cantidad | Detalles relevantes (últimas entradas) |
|----------------|----------|----------------------------------------|
| Logins SSH exitosos | 4 sesiones | - `admin@10.0.0.5` – 3 sesiones (última a las 04:12)<br>- `deploy@10.0.0.8` – 1 sesión (02:55) |
| Fallos de contraseña SSH | 52 intentos | - **IP 203.0.113.7** – 42 intentos (usuarios `root`, `admin`)<br>- **IP 198.51.100.9** – 7 intentos (usuario `root`)<br>- **IP 192.0.2.44** – 3 intentos (usuario `test`) |
| Intentos sudo fallidos | 7 intentos | - Usuario `testuser` – 5 intentos<br>- Usuario `www-data` – 2 intentos |
| Rechazos PAM (usuarios inexistentes) | 11 intentos | - Usuario `oracle` (no existe) – 11 rechazos |

### Acciones recomendadas
1. Bloquear temporalmente la IP **203.0.113.7** (alto número de intentos) y añadirla a vigilancia.  
2. Implementar **rate‑limiting** o **fail2ban** para limitar intentos fallidos por IP.  
3. Revisar y, si es innecesario, revocar privilegios `sudo` de `testuser` y `www-data`.  
4. Verificar la cuenta `oracle`; si no es legítima, eliminarla o deshabilitarla.  

En total: **52 fallos de SSH**, **7 intentos sudo fallidos**, **11 rechazos por usuarios inexistentes**, frente a **4 sesiones SSH exitosas**. Se recomienda aplicar las medidas arriba para mitigar la actividad sospechosa.
```
*(modelos: openrouter:openai/gpt-oss-120b:free · 75.0s · 37879 tk · final=potencia)*

## sec-firewall@velocidad
**Pregunta:** Enséñame las reglas del cortafuegos.
**Rúbrica:** Muestra reglas reales (ufw/nft/iptables).
**Referencia:**
```
**ufw** — Status: active (política por defecto: deny incoming, allow outgoing)
To              Action  From
22/tcp          ALLOW   Anywhere
80/tcp          ALLOW   Anywhere
443/tcp         ALLOW   Anywhere
3306/tcp        DENY    Anywhere
8080/tcp        ALLOW   10.0.0.0/24
```
**Respuesta del agente:**
```
**Reglas del cortafuegos (UFW)**  

| # | Acción | Puerto/Proto | Origen |
|---|--------|--------------|--------|
| 1 | ALLOW | 22/tcp (SSH) | Cualquier dirección |
| 2 | ALLOW | 80/tcp (HTTP) | Cualquier dirección |
| 3 | ALLOW | 443/tcp (HTTPS) | Cualquier dirección |
| 4 | DENY | 3306/tcp (MySQL) | Cualquier dirección |
| 5 | ALLOW | 8080/tcp | 10.0.0.0/24 (rango interno) |

- **Estado:** activo  
- **Política por defecto:** denegar entradas, permitir salidas  

Si necesitas más detalle (por ejemplo, reglas de `nftables` o inspección de puertos en escucha), indícalo.
```
*(modelos: openrouter:nvidia/nemotron-3-nano-30b-a3b:free · 20.8s · 40068 tk · final=velocidad)*

## sec-firewall@potencia
**Pregunta:** Enséñame las reglas del cortafuegos.
**Rúbrica:** Muestra reglas reales (ufw/nft/iptables).
**Referencia:**
```
**ufw** — Status: active (política por defecto: deny incoming, allow outgoing)
To              Action  From
22/tcp          ALLOW   Anywhere
80/tcp          ALLOW   Anywhere
443/tcp         ALLOW   Anywhere
3306/tcp        DENY    Anywhere
8080/tcp        ALLOW   10.0.0.0/24
```
**Respuesta del agente:**
```
**Reglas básicas del cortafuegos (iptables/ nftables)**  

| Acción | Cadena | Protocolo | Puerto/ Rango | Origen | Destino | Comentario |
|--------|--------|-----------|---------------|--------|---------|------------|
| **Aceptar** | INPUT | tcp | 22 | cualquier | local | SSH (acceso remoto) |
| **Aceptar** | INPUT | tcp | 80,443 | cualquier | local | HTTP/HTTPS (servidor web) |
| **Rechazar** | INPUT | any | any | cualquier | local | Todo lo demás (por defecto) |
| **Aceptar** | OUTPUT | any | any | local | cualquier | Salida libre (puedes restringir si lo deseas) |
| **Aceptar** | FORWARD | any | any | cualquier | cualquier | Sólo si el equipo actúa como router |

### Principios de configuración
1. **Política por defecto**: Denegar todo el tráfico entrante (`DROP` o `REJECT`) y permitir solo lo necesario.  
2. **Orden de reglas**: Las reglas se evalúan de arriba a abajo; la primera coincidencia se aplica.  
3. **Estado de conexión**: Usa `-m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT` para permitir respuestas a conexiones iniciadas desde el host.  
4. **Logueo**: Añade una regla de registro antes de la política por defecto para detectar intentos bloqueados:  
   ```bash
   -A INPUT -j LOG --log-prefix "iptables-drop: "
   ```
5. **Persistencia**: Guarda la configuración (`iptables-save > /etc/iptables/rules.v4` o con `nft` en `/etc/nftables.conf`).  

### Ejemplo rápido (iptables)

```bash
# Política por defecto
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Permitir tráfico local y de loopback
iptables -A INPUT -i lo -j ACCEPT

# Permitir conexiones establecidas
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# HTTP/HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT
```

### Ejemplo rápido (nftables)

```bash
nft add table inet filter
nft 'add chain inet filter input { type filter hook input priority 0; policy drop; }'
nft 'add rul
```
*(modelos: openrouter:openai/gpt-oss-120b:free · 36.4s · 9050 tk · final=potencia)*

## sec-ports@velocidad
**Pregunta:** ¿Qué puertos están a la escucha en el sistema?
**Rúbrica:** Lista puertos a la escucha con el proceso que los abre (ss).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
Estos son los puertos que el sistema tiene abiertos para escuchar:

| Puerto | Protocolo | Proceso (PID) | Servicio |
|--------|-----------|---------------|----------|
| 22     | TCP       | `sshd` (712)  | SSH – permite conexiones remotas por SSH. |
| 80     | TCP       | `nginx` (1033)| Nginx – servidor web que sirve tráfico HTTP. |
| 3306   | TCP       | `mysqld` (1450) | MySQL – base de datos, accesible solo desde localhost. |
| 8080   | TCP       | `docker-proxy` (2001) | Proxy de Docker – expone puertos de contenedores. |
| 53     | UDP       | `systemd-resolve` (410) | DNS – resolutor de nombres del sistema. |

Si necesitas más detalles (por ejemplo, direcciones IP específicas o información adicional del proceso), házmelo saber.
```
*(modelos: openrouter:nvidia/nemotron-3-nano-30b-a3b:free · 16.1s · 40366 tk · final=velocidad)*

## sec-ports@potencia
**Pregunta:** ¿Qué puertos están a la escucha en el sistema?
**Rúbrica:** Lista puertos a la escucha con el proceso que los abre (ss).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
Puertos en escucha:

- 22 TCP – sshd (SSH)  
- 80 TCP – nginx (HTTP)  
- 3306 TCP – mysqld (MySQL)  
- 8080 TCP – docker‑proxy (Docker)  
- 53 UDP – systemd‑resolve (DNS)  
```
*(modelos: openrouter:openai/gpt-oss-120b:free · 30.4s · 32868 tk · final=potencia)*

## sec-ports-db@velocidad
**Pregunta:** ¿Hay alguna base de datos a la escucha y en qué interfaz?
**Rúbrica:** Identifica mysqld en 127.0.0.1:3306 y nota que solo escucha en loopback (no expuesto).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
Sí. Hay una base de datos activa: corresponde a **MySQL** (u otro servidor compatible) y está escuchando en el **puerto 3306** enlazado a la interfaz **127.0.0.1** (localhost), es decir, solo accesible de forma local.
```
*(modelos: openrouter:nvidia/nemotron-3-nano-30b-a3b:free · 24.7s · 44131 tk · final=velocidad)*

## sec-ports-db@potencia
**Pregunta:** ¿Hay alguna base de datos a la escucha y en qué interfaz?
**Rúbrica:** Identifica mysqld en 127.0.0.1:3306 y nota que solo escucha en loopback (no expuesto).
**Referencia:**
```
Puertos a la escucha (ss -tulpn):
tcp  LISTEN 0.0.0.0:22      users:(("sshd",pid=712))
tcp  LISTEN 0.0.0.0:80      users:(("nginx",pid=1033))
tcp  LISTEN 127.0.0.1:3306  users:(("mysqld",pid=1450))
tcp  LISTEN 0.0.0.0:8080    users:(("docker-proxy",pid=2001))
udp  LISTEN 0.0.0.0:53      users:(("systemd-resolve",pid=410))
```
**Respuesta del agente:**
```
**Puertos a la escucha**

| Puerto | Protocolo | Interfaz / IP | Proceso (PID) | Servicio (si se conoce) |
|--------|-----------|----------------|---------------|--------------------------|
| 22     | TCP       | 0.0.0.0        | sshd (712)    | SSH |
| 80     | TCP       | 0.0.0.0        | nginx (1033)  | HTTP |
| 3306   | TCP       | 127.0.0.1      | mysqld (1450) | **MySQL** (base de datos) |
| 8080   | TCP       | 0.0.0.0        | docker-proxy (2001) | HTTP‑proxy / contenedor |
| 53     | UDP       | 0.0.0.0        | systemd‑resolve (410) | DNS resolver |

**Bases de datos detectadas**

- **MySQL en el puerto 3306**, escuchando solo en `127.0.0.1` (localhost). No se encontraron otros servicios de bases de datos (PostgreSQL, MongoDB, Redis, etc.) entre los puertos abiertos.
```
*(modelos: openrouter:openai/gpt-oss-120b:free · 46.6s · 33561 tk · final=potencia)*

## orq-cross@equilibrio
**Pregunta:** Dame un informe del estado del sistema y genera un diagrama de la red.
**Rúbrica:** Combina estado del sistema y un diagrama; informe coherente y completo.
**Referencia:**
```
(sin referencia)
```
**Respuesta del agente:**
```
**Estado del Sistema:**
*   **CPU:** Uso bajo (2%), temperatura 45.8°C.
*   **RAM:** 16% ocupado (4.6 GB / 29.2 GB).
*   **Disco:** `/` al 13% y `/mnt/hdd_data` al 32%.
*   **Servicios:** `ssh` y `cron` activos.

**Red:**
*   **Puertos abiertos (0.0.0.0):** 22 (SSH), 80 (Nginx), 8080 (Docker Proxy), 53 (DNS).
*   **Puertos locales (127.0.0.1):** 3306 (MySQL).

He generado y enviado el diagrama de red con la disposición de estos servicios.
```
*(modelos: google_genai:gemma-4-31b-it · 112.2s · 50507 tk · final=equilibrio)*

## orq-cross@potencia
**Pregunta:** Dame un informe del estado del sistema y genera un diagrama de la red.
**Rúbrica:** Combina estado del sistema y un diagrama; informe coherente y completo.
**Referencia:**
```
(sin referencia)
```
**Respuesta del agente:**
```
**Informe del estado del sistema**

- **CPU**: carga 0.78 / 0.48 / 0.60 (1‑5‑15 min), uso actual ≈ 1 %, temperatura ≈ 44 °C.  
- **RAM**: 4.6 GB usados de 29.2 GB (≈ 16 %).  
- **Disco**: uso total ≈ 13 % (123.5 GB de 980.7 GB) en la raíz; otros puntos de montaje entre 0 % y 32 % de uso.  
- **Procesos con mayor consumo de CPU** (top 5):  
  1. `python` (PID 1061955) – 9.2 % CPU  
  2. `cloudflared` (PID 714121) – 3.8 % CPU  
  3. `kcompactd0` (PID 119) – 1.9 % CPU  
  4. `containerd` (PID 1104) – 1.9 % CPU  
  5. `dockerd` (PID 712567) – 1.9 % CPU  
- **Servicio systemd**: `ssh` activo y en ejecución.  

**Diagrama de red** (adjunto).
```
*(modelos: openrouter:openai/gpt-oss-120b:free · 82.8s · 50831 tk · final=potencia)*
