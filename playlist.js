async function loadLibrary() {
    try {
        // 1. Fetch the data from the JSON file
        const response = await fetch('playlist.json');
        
        if (!response.ok) {
            throw new Error(`Failed to load library: ${response.status}`);
        }
        
        const libraryData = await response.json();
        const container = document.getElementById('game-playlists');

        // 2. Loop through the data to build the elements
        libraryData.forEach(system => {
            const h2 = document.createElement('h2');
            h2.textContent = system.platform;
            container.appendChild(h2);

            const ul = document.createElement('ul');

            system.games.forEach(game => {
                const li = document.createElement('li');
                li.textContent = game.title;
                
                if (game.status === 'new') li.classList.add('new-playlist');
                if (game.status === 'leaving') li.classList.add('leaving-soon');

                if (game.url) {
                    const a = document.createElement('a');
                    a.href = game.url;
                    a.appendChild(li);
                    ul.appendChild(a);
                } else {
                    // Prepend the directory if it exists, otherwise just use the id
                    const directory = system.dir ? system.dir : ""; 
                    li.dataset.playlist = directory + game.id;
                    ul.appendChild(li);
                }
            });

            container.appendChild(ul);
        });

        // 3. Attach click event listeners AFTER the elements exist
        document.querySelectorAll('ul li[data-playlist]').forEach((li) => {
            li.addEventListener('click', () => {
                const key = li.dataset.playlist;
                window.location.href = `player.html?playlist=${encodeURIComponent(key)}`;
            });
        });

    } catch (error) {
        console.error("Error loading the game library:", error);
        document.getElementById('game-playlists').innerHTML = "<p>Error loading the playlist library.</p>";
    }
}

// Run the function when the script loads
loadLibrary();