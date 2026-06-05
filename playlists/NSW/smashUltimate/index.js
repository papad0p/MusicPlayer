document.querySelectorAll('ul li[data-playlist]').forEach((li) => {
  li.addEventListener('click', () => {
    const key = li.dataset.playlist;
    if (key !== 'NSW/smashUltimate') {
      // For regular playlists, navigate to player.html with the playlist query parameter 
      window.location.href = `player.html?playlist=${encodeURIComponent(key)}`;
    }
  });
});


function backBtn() {
    window.location.href = '../../../index.html';
}