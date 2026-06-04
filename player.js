
let playlist = [];
let playlistMeta = {};
let currentIndex = 0;
let loopMode = 0; // 0 = off, 1 = autoplay next, 2 = loop current
// Reads playlist key from URL `?playlist=...` first then falls back to localStorage if needed
const urlParams = new URLSearchParams(window.location.search);
const playlistKey = urlParams.get('playlist') || localStorage.getItem('playlist');
const playlistFile = playlistKey ? `playlists/${playlistKey}.json` : null;

const gameTitleEl = document.getElementById("game-title");
const artEl = document.getElementById("album-art");
const descEl = document.getElementById("desc");

const audio = document.getElementById("audio-player");

const titleEl = document.getElementById("song-title");
// const artistEl = document.getElementById("song-artist");
const playBtn = document.getElementById("play-pause");
const listEl = document.getElementById("playlist");



// 1. Get the reference
const seekBar = document.getElementById("seek-bar");

// 2. When a song loads, set the max value of the slider to the song duration
audio.addEventListener("loadedmetadata", () => {
    seekBar.max = audio.duration;
});

// 3. As the song plays, update the slider's value
audio.addEventListener("timeupdate", () => {
    seekBar.value = audio.currentTime;
});

audio.addEventListener("ended", () => {
    if (loopMode === 1) {
        nextTrack();
    }
});

// 4. When the user moves the slider, update the audio's time
seekBar.addEventListener("input", () => {
    audio.currentTime = seekBar.value;
});


function backBtn() {
    window.location.href = 'index.html';
}


// 2. INITIALIZATION
function initPlaylist() {

    gameTitleEl.innerText = playlistMeta.game_title;
    artEl.src = playlistMeta.art;
    descEl.innerText = playlistMeta.desc;

    listEl.innerHTML = "";
    playlist.forEach((song, index) => {
        const span = document.createElement("span");
        span.className = "song-bar"; // Add the class here
        span.innerHTML = `${index+1}. &nbsp; ${song.title}`;
        span.onclick = () => loadTrack(index);
        listEl.appendChild(span);
    });
}

async function loadPlaylistData() {
    try {
        if (!playlistFile) {
            console.error('No playlist specified in URL or localStorage');
            listEl.innerHTML = "<p class='error-message'>No playlist selected. Open the player from the index page.</p>";
            return;
        }
        const response = await fetch(`./${playlistFile}`);
        if (!response.ok) {
            throw new Error(`Failed to load JSON: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        playlistMeta = data.meta || {};
        playlist = data.songs || [];
        initPlaylist();
    } catch (error) {
        console.error("Failed to load playlist JSON:", error);
        listEl.innerHTML = "<p class='error-message'>Unable to load playlist data.</p>";
    }
}


// 3. LOGIC
function togglePlay() {
    if (audio.paused) {
        audio.play();
        playBtn.innerHTML = "<i class='fa-solid fa-pause'></i>";
    } else {
        audio.pause();
        playBtn.innerHTML = "<i class='fa-solid fa-play'></i>";
    }
}

function toggleLoop() {
    loopMode = (loopMode + 1) % 3;
    audio.loop = loopMode === 2;
    const loopBtn = document.getElementById("loop-btn");
    if (!loopBtn) return;
    
    // Set color based on mode
    let bgColor = "";
    if (loopMode === 1) {
        bgColor = "#00bceb"; // Blue for autoplay next
    } else if (loopMode === 2) {
        bgColor = "#af69ee"; // Purple for loop current
    }
    
    loopBtn.style.background = bgColor;
    loopBtn.classList.toggle("active-loop", loopMode !== 0);
    loopBtn.setAttribute("aria-pressed", (loopMode !== 0).toString());
}



function loadTrack(index) {
    currentIndex = index;
    audio.src = playlist[index].src;
    titleEl.innerText = playlist[index].title;

    const bars = document.querySelectorAll(".song-bar");
    bars.forEach(b => b.classList.remove("active-song"));
    bars[index].classList.add("active-song");

    audio.play();
    playBtn.innerHTML = "<i class='fa-solid fa-pause'></i>"
}

function nextTrack() {
    currentIndex = (currentIndex + 1) % playlist.length;
    loadTrack(currentIndex);
}

function prevTrack() {
    currentIndex = (currentIndex - 1 + playlist.length) % playlist.length;
    loadTrack(currentIndex);
}



loadPlaylistData();