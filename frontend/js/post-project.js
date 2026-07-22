/**
 * ============================================================
 * ClipConnect — post-project.js
 * Logic for posting and saving draft editing projects.
 * Handles tag lists, file uploads, pre-filling edit data,
 * and calling /api/projects API endpoints.
 * ============================================================
 */
'use strict';

const API = 'http://localhost:5001/api';

const state = {
  referenceLinks: [],
  requiredSkills: [],
  preferredSoftware: [],
  sampleFiles: [],
  isEditMode: false,
  projectId: null
};

function getToken() { return localStorage.getItem('cc_token'); }
function getUser()  { try { return JSON.parse(localStorage.getItem('cc_user')); } catch { return null; } }

function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = `toast ${type} show`;
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 3500);
}

document.addEventListener('DOMContentLoaded', () => {
  const user = getUser();
  if (!user || user.role !== 'client') {
    toast('Only logged-in clients can post projects.', 'error');
    setTimeout(() => window.location.href = 'login.html', 1500);
    return;
  }

  setupTagInputs();
  setupFileUpload();
  checkEditMode();

  document.getElementById('btn-draft').addEventListener('click', () => submitProject(true));
  document.getElementById('btn-publish').addEventListener('click', () => submitProject(false));
});

function setupTagInputs() {
  // Ref links
  const refBtn = document.getElementById('btn-add-ref');
  const refInp = document.getElementById('inp-ref-link');
  if (refBtn && refInp) {
    refBtn.addEventListener('click', () => {
      const val = refInp.value.trim();
      if (val && !state.referenceLinks.includes(val)) {
        state.referenceLinks.push(val);
        refInp.value = '';
        renderTags('ref-tags', state.referenceLinks);
      }
    });
  }

  // Skills
  const skillBtn = document.getElementById('btn-add-skill');
  const skillInp = document.getElementById('inp-skill');
  if (skillBtn && skillInp) {
    skillBtn.addEventListener('click', () => {
      const val = skillInp.value.trim();
      if (val && !state.requiredSkills.includes(val)) {
        state.requiredSkills.push(val);
        skillInp.value = '';
        renderTags('skill-tags', state.requiredSkills);
      }
    });
  }

  // Software
  const swBtn = document.getElementById('btn-add-sw');
  const swInp = document.getElementById('inp-sw');
  if (swBtn && swInp) {
    swBtn.addEventListener('click', () => {
      const val = swInp.value.trim();
      if (val && !state.preferredSoftware.includes(val)) {
        state.preferredSoftware.push(val);
        swInp.value = '';
        renderTags('sw-tags', state.preferredSoftware);
      }
    });
  }
}

function renderTags(containerId, list) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = list.map((item, idx) => `
    <span class="tag-chip">
      ${item}
      <button type="button" onclick="removeTag('${containerId}', ${idx})">✕</button>
    </span>
  `).join('');
}

window.removeTag = function(containerId, index) {
  if (containerId === 'ref-tags') {
    state.referenceLinks.splice(index, 1);
    renderTags(containerId, state.referenceLinks);
  } else if (containerId === 'skill-tags') {
    state.requiredSkills.splice(index, 1);
    renderTags(containerId, state.requiredSkills);
  } else if (containerId === 'sw-tags') {
    state.preferredSoftware.splice(index, 1);
    renderTags(containerId, state.preferredSoftware);
  }
};

function setupFileUpload() {
  const dropzone = document.getElementById('file-dropzone');
  const fileInp = document.getElementById('file-input');

  if (!dropzone || !fileInp) return;

  dropzone.addEventListener('click', () => fileInp.click());

  fileInp.addEventListener('change', async () => {
    const file = fileInp.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      toast('Uploading sample file...', 'info');
      const res = await fetch(`${API}/projects/upload-sample`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        state.sampleFiles.push({
          filename: data.data.filename,
          url: data.data.url,
          name: file.name
        });
        renderFiles();
        toast('File uploaded successfully!');
      } else {
        toast(data.message || 'Upload failed', 'error');
      }
    } catch (err) {
      toast('Network error uploading file', 'error');
    }
  });
}

function renderFiles() {
  const list = document.getElementById('file-list');
  if (!list) return;
  list.innerHTML = state.sampleFiles.map((f, i) => `
    <div class="file-item">
      <span>📎 ${f.name || f.filename}</span>
      <button type="button" class="btn btn-secondary btn-sm" onclick="removeFile(${i})" style="padding:2px 8px">Remove</button>
    </div>
  `).join('');
}

window.removeFile = function(i) {
  state.sampleFiles.splice(i, 1);
  renderFiles();
};

async function checkEditMode() {
  const params = new URLSearchParams(window.location.search);
  const id = params.get('id');
  if (!id) return;

  state.isEditMode = true;
  state.projectId = id;

  document.getElementById('page-title').textContent = 'Edit Editing Project';

  try {
    const res = await fetch(`${API}/projects/${id}`);
    const data = await res.json();
    if (data.success) {
      const p = data.data.project;
      document.getElementById('inp-title').value = p.title;
      document.getElementById('inp-category').value = p.category;
      document.getElementById('inp-description').value = p.description;
      document.getElementById('inp-budget').value = p.budget;
      document.getElementById('inp-budget-type').value = p.budget_type;
      document.getElementById('inp-visibility').value = p.visibility;
      document.getElementById('inp-editors-count').value = p.editors_required;
      if (p.deadline) {
        document.getElementById('inp-deadline').value = p.deadline.split('T')[0];
      }

      state.referenceLinks = p.reference_links || [];
      state.requiredSkills = p.required_skills || [];
      state.preferredSoftware = p.preferred_software || [];
      state.sampleFiles = p.sample_files || [];

      renderTags('ref-tags', state.referenceLinks);
      renderTags('skill-tags', state.requiredSkills);
      renderTags('sw-tags', state.preferredSoftware);
      renderFiles();
    }
  } catch (err) {
    toast('Failed to load project details', 'error');
  }
}

async function submitProject(isDraft) {
  const title = document.getElementById('inp-title').value.trim();
  const description = document.getElementById('inp-description').value.trim();
  const category = document.getElementById('inp-category').value;
  const budget = document.getElementById('inp-budget').value;
  const budget_type = document.getElementById('inp-budget-type').value;
  const visibility = document.getElementById('inp-visibility').value;
  const editors_required = document.getElementById('inp-editors-count').value;
  const deadline = document.getElementById('inp-deadline').value;

  if (!title || !description) {
    toast('Title and Description are required', 'error');
    return;
  }

  const payload = {
    title,
    description,
    category,
    budget: parseFloat(budget) || 0,
    budget_type,
    visibility,
    editors_required: parseInt(editors_required) || 1,
    deadline: deadline ? new Date(deadline).toISOString() : null,
    reference_links: state.referenceLinks,
    required_skills: state.requiredSkills,
    preferred_software: state.preferredSoftware,
    sample_files: state.sampleFiles,
    is_draft: isDraft
  };

  const url = state.isEditMode ? `${API}/projects/${state.projectId}` : `${API}/projects`;
  const method = state.isEditMode ? 'PUT' : 'POST';

  try {
    const res = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      toast(data.message);
      setTimeout(() => window.location.href = 'dashboard.html', 1500);
    } else {
      toast(data.message || 'Operation failed', 'error');
    }
  } catch (err) {
    toast('Network error saving project', 'error');
  }
}
