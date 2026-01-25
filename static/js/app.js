console.log("Aula CL loaded");

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    const navLinks = document.getElementById('nav-links');

    if (token && window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        // Fetch User Info to get License Data
        axios.defaults.headers.common['Authorization'] = 'Bearer ' + token;

        axios.get('/auth/me').then(response => {
            const user = response.data;
            const username = user.username || "Usuario";
            let licenseInfoHTML = '';

            // Update role flags based on server data
            const isTeacher = !!user.is_teacher;
            const isSubUser = !user.username;

            localStorage.setItem('is_teacher', isTeacher);
            localStorage.setItem('is_subuser', isSubUser);

            // Update Dynamic Nav Title
            const titleContainer = document.getElementById('dynamic-nav-title');
            if (titleContainer && window.location.pathname === '/dashboard') {
                if (isTeacher) {
                    titleContainer.innerText = 'Panel de profesorado';
                } else {
                    titleContainer.innerText = '';
                }
            }

            if (user.username !== 'admin') {
                if (user.access_expires_at && new Date(user.access_expires_at) > new Date()) {
                    const date = new Date(user.access_expires_at).toLocaleDateString();
                    licenseInfoHTML = `
                        <div class="dropdown-header">Licencia</div>
                        <div class="dropdown-item" style="cursor: default; pointer-events: none;">
                            <div class="license-info-active">Premium Activo</div>
                            <div style="font-size: 0.8rem; color: var(--text-secondary);">Caduca: ${date}</div>
                        </div>
                        <div class="dropdown-divider"></div>
                    `;
                } else {
                    licenseInfoHTML = `
                        <div class="dropdown-header">Licencia</div>
                        <div class="dropdown-item" style="cursor: default; pointer-events: none;">
                            <div class="license-info-inactive">Modo Gratuito</div>
                        </div>
                        <a href="#" class="dropdown-item" id="add-license-action">Añadir Licencia</a>
                        <div class="dropdown-divider"></div>
                    `;
                }
            }

            // Custom Navigation Logic based on User Role (Teacher vs Parent)
            let menuItemsHTML = '';

            // "Añadir Licencia" is for everyone EXCEPT admin
            if (user.username !== 'admin') {
                menuItemsHTML += `<a href="#" class="dropdown-item" id="add-license-action">Añadir Licencia</a>`;
            }

            // "Mis alumnos" is ONLY for Teachers
            if (user.is_teacher) {
                menuItemsHTML += `<a href="/my-subusers" class="dropdown-item">Mis Alumnos/as</a>`;
            }

            // "Cambiar Contraseña" and "Cerrar Sesión" for everyone
            menuItemsHTML += `
                <a href="#" class="dropdown-item" id="change-password-action">Cambiar Contraseña</a>
                <div class="dropdown-divider"></div>
                <div class="dropdown-item" id="logout-action" style="color: var(--danger);">Cerrar Sesión</div>
            `;

            // Dropdown HTML
            const dropdownHTML = `
                <div class="dropdown" id="user-dropdown">
                    <button class="btn btn-outline" id="user-menu-btn" style="padding: 0.4rem 0.8rem; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem;">
                        <span>${username}</span>
                        <span style="font-size: 1.1rem; line-height: 1;">≡</span>
                    </button>
                    <div class="dropdown-menu">
                        ${menuItemsHTML}
                    </div>
                </div>
            `;

            const isStudent = localStorage.getItem('is_subuser') === 'true';

            if (isStudent) {
                navLinks.innerHTML = `
                    <button id="logout-btn-simple" class="btn btn-outline" style="padding: 0.4rem 0.8rem; font-size: 0.9rem;">
                        Cerrar Sesión
                    </button>
                `;
                document.getElementById('logout-btn-simple').onclick = () => {
                    localStorage.removeItem('token');
                    localStorage.removeItem('username');
                    localStorage.removeItem('is_subuser');
                    // Clear Cookie
                    document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; SameSite=Lax";
                    window.location.href = '/login';
                };
                return; // Stop here for students
            }

            navLinks.innerHTML = dropdownHTML;

            // Event Listeners
            const dropdown = document.getElementById('user-dropdown');
            const btn = document.getElementById('user-menu-btn');

            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropdown.classList.toggle('active');
            });

            // Close on click outside
            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target)) {
                    dropdown.classList.remove('active');
                }
            });

            // Logout Logic
            document.getElementById('logout-action').addEventListener('click', () => {
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                localStorage.removeItem('is_subuser');
                // Clear Cookie
                document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; SameSite=Lax";
                window.location.href = '/login';
            });

            // Change Password Logic
            document.getElementById('change-password-action').addEventListener('click', (e) => {
                e.preventDefault();
                openChangePasswordModal();
                dropdown.classList.remove('active');
            });

            // Add License Logic
            const addLicBtn = document.getElementById('add-license-action');
            if (addLicBtn) {
                addLicBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    openUnlockModal();
                    // Close dropdown
                    dropdown.classList.remove('active');
                });
            }

        }).catch(err => {
            console.error("Error fetching user info for navbar", err);
            // Fallback to simple logout if API fails
            navLinks.innerHTML = `
                <button id="logout-btn" class="btn btn-outline" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Cerrar Sesión</button>
            `;
            document.getElementById('logout-btn').addEventListener('click', () => {
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                localStorage.removeItem('is_subuser');
                // Clear Cookie
                document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; SameSite=Lax";
                window.location.href = '/login';
            });
        });
    }
});

// --- GLOBAL UNLOCK MODAL LOGIC ---
function openUnlockModal() {
    document.getElementById('unlock-modal').style.display = 'flex';
}

function closeUnlockModal() {
    document.getElementById('unlock-modal').style.display = 'none';
}

// --- GLOBAL CHANGE PASSWORD MODAL LOGIC ---
function openChangePasswordModal() {
    document.getElementById('change-password-modal').style.display = 'flex';
}

function closeChangePasswordModal() {
    document.getElementById('change-password-modal').style.display = 'none';
    document.getElementById('change-password-form').reset();
}

// Ensure modals close on outside click & Handle Forms
document.addEventListener('DOMContentLoaded', () => {
    // Unlock Modal
    const unlockModal = document.getElementById('unlock-modal');
    if (unlockModal) {
        unlockModal.addEventListener('click', (e) => {
            if (e.target === unlockModal) closeUnlockModal();
        });

        const unlockForm = document.getElementById('unlock-form');
        if (unlockForm) {
            unlockForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = unlockForm.querySelector('button[type="submit"]');
                const originalText = btn.innerText;
                btn.innerText = "⏳ Verificando...";
                btn.disabled = true;

                const code = document.getElementById('unlock-code').value;
                const token = localStorage.getItem('token');

                try {
                    const response = await axios.post('/auth/unlock',
                        { access_code: code },
                        { headers: { 'Authorization': 'Bearer ' + token } }
                    );

                    alert(response.data.message);
                    closeUnlockModal();
                    window.location.reload();

                } catch (error) {
                    console.error(error);
                    if (error.response) {
                        alert(error.response.data.detail || "Código incorrecto");
                    } else {
                        alert("Error de conexión");
                    }
                } finally {
                    btn.innerText = originalText;
                    btn.disabled = false;
                }
            });
        }
    }

    // Change Password Modal
    const pwModal = document.getElementById('change-password-modal');
    if (pwModal) {
        pwModal.addEventListener('click', (e) => {
            if (e.target === pwModal) closeChangePasswordModal();
        });

        const pwForm = document.getElementById('change-password-form');
        if (pwForm) {
            pwForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const currentPw = document.getElementById('current-password').value;
                const newPw = document.getElementById('new-password').value;
                const confirmPw = document.getElementById('confirm-new-password').value;

                if (newPw !== confirmPw) {
                    alert("Las nuevas contraseñas no coinciden");
                    return;
                }

                if (newPw.length < 6) {
                    alert("La nueva contraseña debe tener al menos 6 caracteres");
                    return;
                }

                const btn = pwForm.querySelector('button[type="submit"]');
                const originalText = btn.innerText;
                btn.innerText = "⏳ Guardando...";
                btn.disabled = true;

                const token = localStorage.getItem('token');

                try {
                    await axios.post('/auth/change-password',
                        { current_password: currentPw, new_password: newPw },
                        { headers: { 'Authorization': 'Bearer ' + token } }
                    );

                    alert("¡Contraseña actualizada con éxito!");
                    closeChangePasswordModal();

                } catch (error) {
                    console.error(error);
                    alert('Error: ' + (error.response?.data?.detail || "Error al actualizar contraseña"));
                } finally {
                    btn.innerText = originalText;
                    btn.disabled = false;
                }
            });
        }
    }
});
