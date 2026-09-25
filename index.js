const indexInfoBtn = document.getElementById('index-info-btn');
const indexInfoDiv = document.getElementById('index-info');
indexInfoBtn.addEventListener('click', () => {
    if (indexInfoDiv.style.display === 'block') {
        indexInfoDiv.style.display = 'none';
    } else {
        indexInfoDiv.style.display = 'block';
    }

});

document.querySelectorAll('ul li[data-playlist]').forEach((li) => {
  li.addEventListener('click', () => {
    const key = li.dataset.playlist;
    if (key !== 'NSW/smashUltimate') {
      window.location.href = `player.html?playlist=${encodeURIComponent(key)}`;
    }
  });
});
