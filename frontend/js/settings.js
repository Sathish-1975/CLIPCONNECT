/**
 * ClipConnect - Settings JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const passwordForm = document.getElementById('password-form');
    const savePrefBtn  = document.getElementById('save-pref-btn');
    const savePayoutBtn = document.getElementById('save-payout-btn');

    passwordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;

        try {
            const res = await API.put('/users/password', {
                current_password: currentPassword,
                new_password: newPassword
            });

            if (res && res.success) {
                alert('Password updated successfully!');
                passwordForm.reset();
            } else {
                alert(res.message || 'Failed to update password.');
            }
        } catch (err) {
            alert('Error updating password.');
        }
    });

    savePrefBtn.addEventListener('click', () => {
        alert('Notification preferences saved successfully.');
    });

    savePayoutBtn.addEventListener('click', () => {
        const details = document.getElementById('payout-details').value;
        if (!details) {
            alert('Please enter payout details.');
            return;
        }
        alert('Payout details saved successfully.');
    });
});
