document.addEventListener('DOMContentLoaded', () => {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const now = new Date();
    const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    dateInputs.forEach((input) => {
        input.min = today;
    });
});