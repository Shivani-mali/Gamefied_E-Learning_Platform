document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.login-form');
  const nameInput = form.querySelector('input[type="text"]');
  const passwordInput = form.querySelector('input[type="password"]');

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const username = nameInput.value.trim();
    const password = passwordInput.value.trim();

    if (username === '' || password === '') {
      alert("Oops! Please fill out both fields 😊");
      return;
    }

    // Optional: play sound
    const sound = new Audio('click.mp3');
    sound.play();

    // Simulate login success
    setTimeout(() => {
      alert(`Welcome, ${username}! 🎉`);
      // Redirect to next page if needed
      // window.location.href = 'dashboard.html';
    }, 300);
  });
});
