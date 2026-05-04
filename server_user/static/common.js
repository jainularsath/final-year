/** Theme Toggle Logic */
function initTheme() {
  const theme = localStorage.getItem('theme') || 'dark';
  if (theme === 'light') document.body.classList.add('light-mode');
}
function toggleTheme() {
  document.body.classList.toggle('light-mode');
  const isLight = document.body.classList.contains('light-mode');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
});

let _currentUser = null;


/** Escape HTML to prevent XSS */
function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/** Show a toast notification */
function toast(msg, type = 'info') {
  const tc = document.getElementById('toast-container');
  if (!tc) return;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const div = document.createElement('div');
  div.className = `toast toast-${type}`;
  div.innerHTML = `<span>${icons[type] || '•'}</span> ${esc(msg)}`;
  tc.appendChild(div);
  setTimeout(() => { div.style.animation = 'fadeOut .3s ease forwards'; setTimeout(() => div.remove(), 300); }, 3500);
}

/** Open/close modal */
function openModal(id) { document.getElementById(id)?.classList.add('active'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('active'); }

/** Close modal on overlay click */
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
  }
});

/** Initialize navbar based on auth state */
async function initNav() {
  // Add theme toggle button if not exists
  const navAuth = document.getElementById('nav-auth');
  if (navAuth && !document.getElementById('theme-toggle')) {
    const btn = document.createElement('button');
    btn.id = 'theme-toggle';
    btn.className = 'btn btn-secondary btn-sm';
    btn.style.marginRight = '10px';
    btn.innerHTML = '🌓 Mode';
    btn.onclick = toggleTheme;
    navAuth.parentNode.insertBefore(btn, navAuth);
  }

  try {
    const res = await fetch('/api/me');

    if (res.ok) {
      _currentUser = await res.json();
      const navAuth = document.getElementById('nav-auth');
      const navOrders = document.getElementById('nav-orders');
      if (navAuth) {
        navAuth.innerHTML = `
          <div class="nav-user-pill">
            <div class="avatar">${(_currentUser.name || 'U')[0].toUpperCase()}</div>
            <span>${esc(_currentUser.name)}</span>
          </div>
          <button onclick="openModal('pw-modal-overlay')" class="btn btn-secondary btn-sm" title="Account Settings">⚙️</button>
          <a href="/api/logout" class="btn btn-secondary btn-sm">Logout</a>`;
      }
      if (navOrders) navOrders.style.display = '';
    }
  } catch (e) { /* not logged in */ }
}

/** Book a service – redirect to booking page or show login modal */
function bookService(serviceId, serviceType) {
  const target = `/booking.html?service_type=${serviceType}&service_id=${serviceId}`;
  if (_currentUser) {
    window.location.href = target;
  } else {
    // Store redirect target
    sessionStorage.setItem('booking_redirect', target);
    openModal('login-modal');
  }
}

/** Format currency */
function formatCurrency(num) {
  return '₹' + Number(num).toLocaleString('en-IN');
}

/** Format date */
function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

/** Status badge */
function statusBadge(status) {
  const map = {
    pending: 'badge-gold',
    confirmed: 'badge-green',
    completed: 'badge-blue',
    cancelled: 'badge-red',
    cancelled_no_refund: 'badge-red',
    active: 'badge-green',
    inactive: 'badge-red',
  };
  let display = status;
  if (status === 'confirmed') display = 'Accepted';
  if (status === 'cancelled') display = 'Cancelled';
  if (status === 'cancelled_no_refund') display = 'Cancelled';

  let extra = '';
  if (status === 'cancelled') extra = ' <small style="display:block;color:var(--clr-red);font-size:.7rem">(Advance Refunded)</small>';
  if (status === 'cancelled_no_refund') extra = ' <small style="display:block;color:var(--clr-red);font-size:.7rem">(No Refund)</small>';

  return `<span class="badge ${map[status] || ''}">${display}</span>${extra}`;
}

/** Inject Support Button */
function injectSupportButton() {
  if (document.getElementById('support-floating-btn')) return;
  const btn = document.createElement('a');
  btn.id = 'support-floating-btn';
  btn.className = 'support-btn';
  btn.href = 'https://mail.google.com/mail/?view=cm&fs=1&to=admin@tnevents.com&su=Support Request - TN Events';
  btn.target = '_blank';
  btn.innerHTML = '💬';
  btn.title = 'Contact Support';
  document.body.appendChild(btn);
}

/** Inject Password Modal */
function injectPasswordModal() {
  if (document.getElementById('pw-modal-overlay')) return;
  const div = document.createElement('div');
  div.id = 'pw-modal-overlay';
  div.className = 'modal-overlay';
  div.innerHTML = `
    <div class="modal" style="max-width:400px">
      <div class="modal-header">
        <h3>Change Password</h3>
        <button class="modal-close" onclick="closeModal('pw-modal-overlay')">✕</button>
      </div>
      <form id="pw-form" onsubmit="handlePwChange(event)">
        <div class="form-group">
          <label>Current Password</label>
          <input type="password" id="old-pw" class="form-control" required />
        </div>
        <div class="form-group">
          <label>New Password</label>
          <input type="password" id="new-pw" class="form-control" minlength="6" required />
        </div>
        <div class="form-group">
          <label>Confirm New Password</label>
          <input type="password" id="confirm-pw" class="form-control" minlength="6" required />
        </div>
        <button type="submit" class="btn btn-primary" style="width:100%;margin-top:1rem;justify-content:center">Update Password</button>
      </form>
    </div>`;
  document.body.appendChild(div);
}

async function handlePwChange(e) {
  e.preventDefault();
  const oldPw = document.getElementById('old-pw').value;
  const newPw = document.getElementById('new-pw').value;
  const confirmPw = document.getElementById('confirm-pw').value;

  if (newPw !== confirmPw) {
    toast('Passwords do not match', 'error');
    return;
  }

  try {
    const res = await fetch('/api/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_password: oldPw, new_password: newPw })
    });
    const data = await res.json();
    if (res.ok) {
      toast('Password updated! Please use the new password next time.', 'success');
      closeModal('pw-modal-overlay');
      document.getElementById('pw-form').reset();
    } else {
      toast(data.error || 'Update failed', 'error');
    }
  } catch (err) {
    toast('Network error', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  injectSupportButton();
  injectPasswordModal();
});
