// URL = 'http://ec2-34-192-101-140.compute-1.amazonaws.com:5003/'

URL = 'http://localhost:5001/'

previousToast = null;

gameId = null;
newGameButton = document.getElementById('newGameButton');
copyGameIdButton = document.getElementById('copyGameIdButton');

function showToast(message, seconds = 3) {
    const toast = document.createElement('div');

    toast.classList.add('toast');
    toast.textContent = message;

    previousToast?.remove();

    previousToast = toast;

    if (seconds == 0) {
        return;
    }
    document.body.appendChild(toast);

    setTimeout(function () {
        toast.remove();
    }, seconds * 1000);
}

function makeRequestOptions(body, method = 'POST') {
    if (method == 'GET') {
        return {
            method,
            mode: 'cors',
            headers: { 'Content-Type': 'application/json' },
        };
    }

    return {
        method,
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    };
}

function fetchWrapper(url, body, method = 'POST') {
    if (method == 'GET') {
        if (body) {
            url = `${url}?`;
        }
        for (var key in body) {
            url = `${url}${key}=${body[key]}&`;
        }
    }
    return fetch(url, makeRequestOptions(body, method));
}

function newGame() {
    fetchWrapper(URL + 'new_game', {}, 'POST')
        .then((response) => response.json())
        .then((data) => {
            gameId = data['gameId'];
        });

    initBoard();
}

function handleKeyDown(event) {
    if (event.key == 'Enter') {
        if (document.activeElement == key) {
            get(key.value);
        }
        if (document.activeElement == value) {
            set(key, value);
        }
    }
}

newGameButton.addEventListener('click', newGame);

copyGameIdButton.addEventListener('click', () => {
    navigator.clipboard.writeText(gameId);
    showToast(`Copied ${gameId} to clipboard`);
});

document.addEventListener('keydown', handleKeyDown);

var board, game = new Chess();

/* Initialize the board with a configuration object */
function initBoard() {
    var config = {
        draggable: true,
        position: 'start',
        onDragStart: onPickup,
        onDrop: handleMove,
        pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png'
    };
    
    board = Chessboard('board', config);
}

legal_destinations = [];

function onPickup(source) {
    legal_destinations = [];

    fetchWrapper(URL + 'legal_moves', { 'start': source, 'gameId': gameId }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            }
            data['moves'].forEach(move => {
                legal_destinations.push(move);
                console.log(move)
            });
        })
    };

function isLegalMove(to) {
    return legal_destinations.includes(to.toUpperCase());
}

function handleMove(from, to) {
    if (isLegalMove(to)) {
        fetchWrapper(URL + 'move', { 'start': from, 'stop': to, 'gameId': gameId }, 'POST')
    } else {
        return 'snapback';
    }
}

function handleMove2(source, target) {
    // See if the move is legal
    var move = game.move({
        from: source,
        to: target,
        promotion: 'q' // NOTE: Always promote to a queen for simplicity
    });

    // If the move isn't legal, snap back the piece to its source square
    if (move === null) return 'snapback';

    // Else update the game state and continue
    // For example: Check for game over conditions
    if (game.game_over()) {
        alert('Game over');
    }
}

newGame();