async function fetchJson(path) {
    const response = await fetch(path);

    if (!response.ok) {
        throw new Error(`Failed to load ${path}: ${response.status}`);
    }

    const text = await response.text();
    const jsonWithoutTrailingCommas = text.replace(/,\s*([}\]])/g, "$1");
    return JSON.parse(jsonWithoutTrailingCommas);
}

async function getGameArt(system, game) {
    if (!game.id) return "";

    const directory = system.dir ? system.dir : "";
    const playlistPath = `playlists/${directory}${game.id}.json`;

    try {
        const playlistData = await fetchJson(playlistPath);
        return playlistData.meta && playlistData.meta.art ? playlistData.meta.art : "";
    } catch (error) {
        console.warn(`Could not load art from ${playlistPath}`, error);
        return "";
    }
}

function createCover(game, art) {
    const img = document.createElement('img');
    img.src = art;
    img.alt = `${game.title} cover`;
    img.loading = "lazy";
    img.decoding = "async";
    img.style.width = "100px";
    img.style.height = "100px";
    img.style.objectFit = "cover";
    img.style.borderRadius = "5px";
    img.style.flex = "0 0 auto";
    return img;
}

async function createGameItem(system, game) {
    const li = document.createElement('li');
    const div = document.createElement('div');
    div.classList.add('game-item');
    div.style.display = "grid";
    div.style.alignItems = "center";
    div.style.justifyContent = "center";
    // li.style.gridTemplateColumns = "1fr 1fr"

    li.style.gap = "1em";

    const art = await getGameArt(system, game);
    if (art) {
        li.appendChild(createCover(game, art));
    }

    const title = document.createElement('span');
    title.textContent = game.title;
    title.style.textAlign = "center";
    // title.style.fontSize = "1.2em";
    li.appendChild(title);

    if (game.status === 'new') li.classList.add('new-playlist');
    if (game.status === 'leaving') li.classList.add('leaving-soon');
    if (game.status === 'broken') li.classList.add('broken');

    if (game.url) {
        const a = document.createElement('a');
        a.href = game.url;
        a.appendChild(li);
        return a;
    }

    const directory = system.dir ? system.dir : "";
    li.dataset.playlist = directory + game.id;
    return li;
}

async function loadLibrary() {
    try {
        const libraryData = await fetchJson('playlist.json');
        const container = document.getElementById('game-playlists');

        for (const system of libraryData) {
            const h2 = document.createElement('h2');
            h2.textContent = system.platform;
            container.appendChild(h2);

            const ul = document.createElement('ul');
            const gameItems = await Promise.all(
                system.games.map(game => createGameItem(system, game))
            );

            gameItems.forEach(item => ul.appendChild(item));
            container.appendChild(ul);
        }

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

loadLibrary();
