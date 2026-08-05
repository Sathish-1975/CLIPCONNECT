/**
 * project-details.js — Project details page frontend script
 */

const API_BASE = window.location.port === '5000' ? 'http://localhost:5000/api' : 'http://localhost:5000/api';

document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const projectId = urlParams.get('id') || urlParams.get('project_id');

  if (!projectId) {
    document.getElementById('project-title').textContent = 'Project Not Found';
    document.getElementById('project-description').textContent = 'No project ID provided in URL parameters.';
    return;
  }

  const token = localStorage.getItem('jwt_token') || localStorage.getItem('token');
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(`${API_BASE}/projects/${projectId}`, { headers });
    const result = await res.json();

    if (!res.ok || !result.success) {
      document.getElementById('project-title').textContent = 'Project Not Found';
      document.getElementById('project-description').textContent = result.message || 'Unable to fetch project details.';
      return;
    }

    const project = result.data.project;

    // Render title & basic info
    document.getElementById('project-title').textContent = project.title || 'Untitled Project';
    document.getElementById('project-description').textContent = project.description || 'No description provided.';
    
    // Save button state
    const saveBtn = document.getElementById('save-btn');
    if (token) {
      saveBtn.style.display = 'inline-block';
      let isSaved = !!project.is_saved;

      const updateSaveBtn = () => {
        saveBtn.textContent = isSaved ? '★ Saved' : '⭐ Save Project';
        saveBtn.classList.toggle('btn-primary', isSaved);
        saveBtn.classList.toggle('btn-secondary', !isSaved);
      };
      updateSaveBtn();

      saveBtn.addEventListener('click', async () => {
        try {
          const method = isSaved ? 'DELETE' : 'POST';
          const saveRes = await fetch(`${API_BASE}/projects/${projectId}/save`, {
            method,
            headers: { 'Authorization': `Bearer ${token}` }
          });
          const saveResult = await saveRes.json();
          if (saveRes.ok && saveResult.success) {
            isSaved = !isSaved;
            updateSaveBtn();
          } else {
            alert(saveResult.message || 'Failed to update saved status.');
          }
        } catch (err) {
          console.error('Save error:', err);
          alert('Error saving project.');
        }
      });
    }

    // Render meta fields
    const budgetStr = project.budget_min && project.budget_max 
      ? `₹${project.budget_min} - ₹${project.budget_max}` 
      : (project.budget ? `₹${project.budget}` : 'Negotiable');
    document.getElementById('project-budget').textContent = budgetStr;
    
    document.getElementById('project-deadline').textContent = project.deadline || project.timeline || 'Flexible';
    document.getElementById('project-status').textContent = project.status ? project.status.toUpperCase() : 'OPEN';

    // Proposal count
    const count = project.proposal_count || 0;
    document.getElementById('proposal-count').textContent = `${count} proposal${count === 1 ? '' : 's'} submitted`;

    // Client info
    const clientDiv = document.getElementById('client-info');
    if (project.client) {
      clientDiv.innerHTML = `<strong>Posted by:</strong> ${project.client.name || 'Client'} (${project.client.email || ''})`;
    } else if (project.client_name) {
      clientDiv.innerHTML = `<strong>Posted by:</strong> ${project.client_name}`;
    }

    // Skills
    const skillContainer = document.getElementById('skill-tags');
    const skills = Array.isArray(project.skills_required) ? project.skills_required : (project.skills || []);
    if (skills.length > 0) {
      skillContainer.innerHTML = skills.map(s => `<span class="tag">${s}</span>`).join('');
    } else {
      skillContainer.innerHTML = '<span>Any video editing skills</span>';
    }

    // Software
    const softwareContainer = document.getElementById('software-tags');
    const software = Array.isArray(project.software_required) ? project.software_required : (project.software || []);
    if (software.length > 0) {
      softwareContainer.innerHTML = software.map(s => `<span class="tag">${s}</span>`).join('');
    } else {
      softwareContainer.innerHTML = '<span>Premiere Pro / After Effects / DaVinci</span>';
    }

    // Attachments
    const attachmentList = document.getElementById('attachment-list');
    if (project.attachments && project.attachments.length > 0) {
      attachmentList.innerHTML = project.attachments.map(att => 
        `<li><a href="${att.url || att}" target="_blank">${att.name || 'Attachment Link'}</a></li>`
      ).join('');
    }

    // Apply button handler
    const applyBtn = document.getElementById('apply-btn');
    applyBtn.addEventListener('click', async () => {
      if (!token) {
        alert('Please log in as an Editor to apply for this project.');
        window.location.href = 'login.html';
        return;
      }

      try {
        const applyRes = await fetch(`${API_BASE}/projects/${projectId}/apply`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
        const applyData = await applyRes.json();

        if (applyRes.ok && applyData.success) {
          alert('Application submitted successfully!');
          location.reload();
        } else {
          alert(applyData.message || 'Failed to submit application.');
        }
      } catch (err) {
        console.error('Apply error:', err);
        alert('Error connecting to backend server.');
      }
    });

  } catch (err) {
    console.error('Error loading project details:', err);
    document.getElementById('project-title').textContent = 'Error Loading Project';
    document.getElementById('project-description').textContent = 'Could not connect to backend server.';
  }
});
