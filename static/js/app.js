console.log("Aula CL loaded");

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    const navLinks = document.getElementById('nav-links');

    if (token && window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        const username = localStorage.getItem('username');
        let adminLink = '';

        // Removed automatic Admin link as per request (moved to left side in dashboard)

        navLinks.innerHTML = `
            ${adminLink}
            <button id="logout-btn" class="btn btn-outline" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Cerrar Sesión</button>
        `;

        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            window.location.href = '/login';
        });
    } else {
        // User is NOT logged in
        // Only show login/register links if NOT on those pages already?
        // For now, simpler is better.
    }
});
