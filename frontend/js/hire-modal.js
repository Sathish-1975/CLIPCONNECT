/**
 * hire-modal.js — Reusable Hire Editor Modal for ClipConnect
 *
 * Provides a clean modal for clients to hire editors for a project.
 */

async function openHireModal(editorId, editorName) {
  const token = typeof TokenManager !== 'undefined' ? TokenManager.getToken() :
                (localStorage.getItem('cc_token') || localStorage.getItem('token') || localStorage.getItem('clipconnect_token'));
  
  const user  = typeof TokenManager !== 'undefined' ? TokenManager.getUser() :
                (() => { try { return JSON.parse(localStorage.getItem('cc_user') || localStorage.getItem('user') || localStorage.getItem('clipconnect_user')); } catch { return null; } })();

  // Create modal backdrop container
  const backdrop = document.createElement('div');
  backdrop.id = 'hire-modal-backdrop';
  backdrop.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(10, 10, 20, 0.85); backdrop-filter: blur(12px);
    display: flex; align-items: center; justify-content: center;
    z-index: 10000; padding: 20px; animation: fadeIn 0.25s ease-out;
    font-family: 'Inter', sans-serif;
  `;

  if (!token || !user) {
    backdrop.innerHTML = `
      <div style="background: #181826; border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; width: 100%; max-width: 440px; padding: 28px; text-align: center; color: #fff; position: relative;">
        <button id="hire-modal-close" style="position: absolute; top: 16px; right: 16px; background: none; border: none; color: #94a3b8; font-size: 1.3rem; cursor: pointer;">✕</button>
        <div style="font-size: 2.5rem; margin-bottom: 12px;">🔒</div>
        <h3 style="font-size: 1.2rem; font-weight: 700; margin-bottom: 8px;">Login Required</h3>
        <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 24px;">Please log in or sign up to hire ${editorName || 'editors'}.</p>
        <div style="display: flex; gap: 12px;">
          <a href="login.html?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}" class="btn btn-primary" style="flex: 1; text-align: center; text-decoration: none; padding: 10px; border-radius: 8px; font-weight: 600;">Log In</a>
          <a href="register.html" class="btn btn-outline" style="flex: 1; text-align: center; text-decoration: none; padding: 10px; border-radius: 8px; color: #fff; border: 1px solid rgba(255,255,255,0.2); font-weight: 600;">Sign Up</a>
        </div>
      </div>
    `;
    document.body.appendChild(backdrop);
    backdrop.querySelector('#hire-modal-close').addEventListener('click', () => backdrop.remove());
    backdrop.addEventListener('click', (e) => { if (e.target === backdrop) backdrop.remove(); });
    return;
  }

  if (user.role !== 'client') {
    if (typeof toast === 'function') toast('Only client accounts can hire editors.', 'error');
    else alert('Only client accounts can hire editors.');
    return;
  }

  // Remove existing modal if any
  const existing = document.getElementById('hire-modal-backdrop');
  if (existing) existing.remove();

  // Create modal container
  const backdrop = document.createElement('div');
  backdrop.id = 'hire-modal-backdrop';
  backdrop.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(10, 10, 20, 0.85); backdrop-filter: blur(12px);
    display: flex; align-items: center; justify-content: center;
    z-index: 10000; padding: 20px; animation: fadeIn 0.25s ease-out;
    font-family: 'Inter', sans-serif;
  `;

  backdrop.innerHTML = `
    <div style="
      background: #181826; border: 1px solid rgba(255,255,255,0.12);
      border-radius: 16px; width: 100%; max-width: 480px; padding: 28px;
      box-shadow: 0 24px 60px rgba(0,0,0,0.6); position: relative; color: #fff;
    ">
      <button id="hire-modal-close" style="
        position: absolute; top: 18px; right: 18px; background: none; border: none;
        color: #94a3b8; font-size: 1.4rem; cursor: pointer; padding: 4px;
      ">✕</button>

      <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
        ✨ Hire <span style="color: #a78bfa">${editorName}</span>
      </div>
      <div style="color: #94a3b8; font-size: 0.88rem; margin-bottom: 20px;">
        Select one of your projects to send a direct hire request to this editor.
      </div>

      <div id="hire-modal-body">
        <div style="text-align: center; padding: 30px; color: #a78bfa;">Loading your projects...</div>
      </div>
    </div>
  `;

  document.body.appendChild(backdrop);

  // Close handlers
  const closeBtn = backdrop.querySelector('#hire-modal-close');
  closeBtn.addEventListener('click', () => backdrop.remove());
  backdrop.addEventListener('click', (e) => { if (e.target === backdrop) backdrop.remove(); });

  // Fetch client's projects
  const modalBody = backdrop.querySelector('#hire-modal-body');
  try {
    const res = await fetch('/api/projects/my', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const result = await res.json();

    if (!res.ok || !result.success) {
      modalBody.innerHTML = `<div style="color: #f87171; padding: 10px;">Failed to load projects. Please try again.</div>`;
      return;
    }

    const projects = (result.data.projects || []).filter(p => p.status === 'published' || p.status === 'draft');

    if (projects.length === 0) {
      modalBody.innerHTML = `
        <div style="text-align: center; padding: 20px 0;">
          <div style="font-size: 2.5rem; margin-bottom: 10px;">📁</div>
          <div style="font-size: 0.95rem; font-weight: 600; color: #e2e8f0; margin-bottom: 6px;">No Active Projects Found</div>
          <div style="color: #94a3b8; font-size: 0.83rem; margin-bottom: 20px;">You need to create a project first before hiring an editor.</div>
          <a href="post-project.html" class="btn btn-primary" style="
            display: inline-block; background: linear-gradient(135deg, #7c3aed, #6366f1);
            color: #fff; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.9rem;
          ">+ Post a New Project</a>
        </div>
      `;
      return;
    }

    let selectOptions = projects.map(p => `<option value="${p.id}">${p.title} (Budget: ₹${p.budget})</option>`).join('');

    modalBody.innerHTML = `
      <form id="hire-modal-form" style="display: flex; flex-direction: column; gap: 16px;">
        <div>
          <label style="display: block; font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;">Select Project</label>
          <select id="hire-project-id" required style="
            width: 100%; background: #0f172a; border: 1px solid rgba(255,255,255,0.15);
            color: #fff; padding: 10px 12px; border-radius: 8px; font-size: 0.9rem; outline: none;
          ">
            ${selectOptions}
          </select>
        </div>

        <div>
          <label style="display: block; font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;">Message / Note to Editor (Optional)</label>
          <textarea id="hire-message" rows="3" placeholder="Explain your project details, expectations, or timeline..." style="
            width: 100%; background: #0f172a; border: 1px solid rgba(255,255,255,0.15);
            color: #fff; padding: 10px 12px; border-radius: 8px; font-size: 0.88rem; outline: none; resize: vertical;
          "></textarea>
        </div>

        <div style="display: flex; gap: 10px; margin-top: 10px;">
          <button type="button" id="hire-cancel-btn" style="
            flex: 1; background: rgba(255,255,255,0.08); border: none; color: #94a3b8;
            padding: 11px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.88rem;
          ">Cancel</button>
          <button type="submit" id="hire-submit-btn" style="
            flex: 2; background: linear-gradient(135deg, #7c3aed, #6366f1); border: none; color: #fff;
            padding: 11px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.88rem;
            box-shadow: 0 4px 14px rgba(124,58,237,0.4); transition: transform 0.2s;
          ">Send Hire Request ✨</button>
        </div>
      </form>
    `;

    backdrop.querySelector('#hire-cancel-btn').addEventListener('click', () => backdrop.remove());

    backdrop.querySelector('#hire-modal-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const projectId = backdrop.querySelector('#hire-project-id').value;
      const message   = backdrop.querySelector('#hire-message').value;
      const submitBtn = backdrop.querySelector('#hire-submit-btn');

      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending Request...';

      try {
        const hireRes = await fetch('/api/hire', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            project_id: parseInt(projectId),
            editor_id: parseInt(editorId),
            message: message
          })
        });

        const hireResult = await hireRes.json();

        if (hireRes.ok && hireResult.success) {
          modalBody.innerHTML = `
            <div style="text-align: center; padding: 24px 0;">
              <div style="font-size: 3rem; margin-bottom: 10px;">🎉</div>
              <div style="font-size: 1.1rem; font-weight: 700; color: #34d399; margin-bottom: 6px;">Hire Request Sent!</div>
              <div style="color: #94a3b8; font-size: 0.88rem; margin-bottom: 20px; line-height: 1.4;">
                ${editorName} has received your hire request. You'll be notified when they accept or respond.
              </div>
              <button id="hire-success-close" style="
                background: linear-gradient(135deg, #059669, #10b981); border: none; color: #fff;
                padding: 10px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.9rem;
              ">Done</button>
            </div>
          `;
          backdrop.querySelector('#hire-success-close').addEventListener('click', () => backdrop.remove());
        } else {
          alert(hireResult.message || 'Failed to send hire request.');
          submitBtn.disabled = false;
          submitBtn.textContent = 'Send Hire Request ✨';
        }
      } catch (err) {
        console.error('Hire error:', err);
        alert('Network error while sending hire request.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Hire Request ✨';
      }
    });

  } catch (err) {
    console.error('Fetch projects error:', err);
    modalBody.innerHTML = `<div style="color: #f87171; padding: 10px;">Network error loading projects.</div>`;
  }
}
