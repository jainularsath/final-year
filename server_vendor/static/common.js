// Vendor + Admin shared JS utilities
function initTheme() {
    const theme = localStorage.getItem('theme') || 'dark';
    if (theme === 'light') document.body.classList.add('light-mode');

    // Add floating toggle if not exists
    if (!document.getElementById('theme-toggle')) {
        const btn = document.createElement('button');
        btn.id = 'theme-toggle';
        btn.innerHTML = '🌓';
        btn.style.cssText = "position:fixed; bottom:20px; right:20px; z-index:1000; width:45px; height:45px; border-radius:50%; background:var(--clr-gold); border:none; color:#000; cursor:pointer; font-size:20px; box-shadow:0 4px 12px rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center;";
        btn.onclick = () => {
            document.body.classList.toggle('light-mode');
            localStorage.setItem('theme', document.body.classList.contains('light-mode') ? 'light' : 'dark');
        };
        document.body.appendChild(btn);
    }
}
// Initialized via DOMContentLoaded below

function esc(str) {

    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function toast(msg, type = 'info') {
    const tc = document.getElementById('toast-container');
    if (!tc) return;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    const div = document.createElement('div');
    div.className = `toast toast-${type}`;
    div.innerHTML = `<span>${icons[type] || '•'}</span> ${esc(msg)}`;
    tc.appendChild(div);
    setTimeout(() => { div.style.animation = 'none'; div.style.opacity = '0'; div.style.transform = 'translateX(100%)'; div.style.transition = 'all .3s'; setTimeout(() => div.remove(), 300); }, 3500);
}

function openModal(id) { document.getElementById(id)?.classList.add('active'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('active'); }
document.addEventListener('click', e => { if (e.target.classList.contains('modal-overlay')) e.target.classList.remove('active'); });

function statusBadge(status) {
    const map = { pending: 'badge-gold', confirmed: 'badge-green', completed: 'badge-blue', cancelled: 'badge-red', cancelled_no_refund: 'badge-red', active: 'badge-green', inactive: 'badge-red', approved: 'badge-green', rejected: 'badge-red' };
    let display = status;
    if (status === 'confirmed') display = 'Accepted';
    if (status === 'cancelled' || status === 'cancelled_no_refund') display = 'Cancelled';

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
    // Position it differently to not overlap with theme toggle
    btn.style.cssText = "position:fixed; bottom:20px; right:75px; z-index:1000; width:45px; height:45px; border-radius:50%; background:linear-gradient(135deg, #7c5cbf, #4f46e5); color:#fff; cursor:pointer; font-size:20px; box-shadow:0 4px 12px rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; text-decoration:none;";
    btn.href = 'https://mail.google.com/mail/?view=cm&fs=1&to=admin@tnevents.com&su=Support Request - TN Events Vendor';
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
            toast('Password updated successfully!', 'success');
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
    initTheme();
    injectSupportButton();
    injectPasswordModal();
});
function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}
function formatCurrency(n) { return '₹' + Number(n || 0).toLocaleString('en-IN'); }
