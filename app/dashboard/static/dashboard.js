const { userId, baseUrl } = window.BOTNUTRI_CONFIG;

async function loadDashboard() {
  const res = await fetch(`${baseUrl}/api/users/${userId}/dashboard-data`);
  const data = await res.json();

  document.getElementById('calories').innerText = `${data.today.calories} / ${data.today.calorie_target} kcal`;
  document.getElementById('score').innerText = `Daily progress score: ${data.today.score}%`;

  document.getElementById('friends').innerHTML = data.friend_leaderboard
    .map((row) => `<li>${row.name} — ${row.score}%</li>`)
    .join('');

  new Chart(document.getElementById('weeklyChart'), {
    type: 'line',
    data: {
      labels: data.weekly_calories.map((x) => x.date),
      datasets: [{ label: 'Calories', data: data.weekly_calories.map((x) => x.calories), borderColor: '#38bdf8' }],
    },
  });

  new Chart(document.getElementById('macroChart'), {
    type: 'doughnut',
    data: {
      labels: ['Protein', 'Carbs', 'Fats'],
      datasets: [{
        data: [data.macro_distribution.protein, data.macro_distribution.carbs, data.macro_distribution.fats],
        backgroundColor: ['#22c55e', '#f59e0b', '#ef4444'],
      }],
    },
  });
}

loadDashboard();
