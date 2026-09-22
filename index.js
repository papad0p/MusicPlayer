document.querySelectorAll('ul li[data-playlist]').forEach((li) => {
  li.addEventListener('click', () => {
    const key = li.dataset.playlist;
    if (key !== 'NSW/smashUltimate') {
      window.location.href = `player.html?playlist=${encodeURIComponent(key)}`;
    }
  });
});
