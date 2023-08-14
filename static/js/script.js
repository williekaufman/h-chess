// URL = 'http://ec2-34-192-101-140.compute-1.amazonaws.com:5003/'

URL = 'http://localhost:5001/'

function isLocalhost() {
    return window.location.href.includes('localhost');
}

previousToast = null;

gameId = null;
newGameButton = document.getElementById('newGameButton');
copyGameIdButton = document.getElementById('copyGameIdButton');

loadGameButton = document.getElementById('loadGameButton');
gameIdInput = document.getElementById('gameIdInput');

handicapInfo = document.getElementById('handicapInfo');

howToPlayPopup = document.getElementById('how-to-play-popup');
howToPlayBtnText = document.getElementById('how-to-play-btn-text');

whose_turn = 'W';

color = Math.random() > 0 ? 'white' : 'black';

d = { 'white': 'w', 'black': 'b' }

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
            fetchWrapper(URL + 'handicap', { 'gameId': gameId , 'color': color }, 'GET')
                .then((response) => response.json())
                .then((data) => {
                    handicapInfo.textContent = `Your handicap is: ${data['handicap']}`;
                });
        });

    whose_turn = 'W';
    initBoard();
}

function loadGame() {
    gameId = gameIdInput.value;

    fetchWrapper(URL + 'board', { 'gameId': gameId }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast('Invalid game ID');
                return;
            }
            board.position(data['board']);
            whose_turn = data['whose_turn'];
        });
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
loadGameButton.addEventListener('click', loadGame);

copyGameIdButton.addEventListener('click', () => {
    navigator.clipboard.writeText(gameId);
    showToast(`Copied ${gameId} to clipboard`);
});

function setSquare(square, piece) {
    board.position({
        ...board.position(),
        [square]: piece,
    }, false)
}

function clearSquare(square) {
    pos = board.position();
    delete pos[square];
    board.position({ ...pos }, false)
}

document.addEventListener('keydown', handleKeyDown);

var board, game = new Chess();

/* Initialize the board with a configuration object */
function initBoard() {
    var config = {
        draggable: true,
        position: 'start',
        orientation: color,
        onDragStart: onPickup,
        onDrop: handleMove,
        moveSpeed: 'fast',
        pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png'
    };

    board = Chessboard('board', config);
}

legal_destinations = [];
on_pickup_in_flight = false;
retry_move = null;

function yourPiece(piece) {
    return piece.search(d[color]) !== -1 || isLocalhost();
}

function activePiece(piece) {
    return piece.search(whose_turn.toLowerCase()) !== -1;
}

function onPickup(source, piece) {
    if (!yourPiece(piece) || !activePiece(piece)) {
            return false;
    }
    
    legal_destinations = [];
    on_pickup_in_flight = true;

    fetchWrapper(URL + 'legal_moves', { 'start': source, 'gameId': gameId }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            }
            on_pickup_in_flight = false;
            data['moves'].forEach(move => {
                legal_destinations.push(move);
            });
        })
}

function isLegalMove(to) {
    return legal_destinations.includes(to.toUpperCase());
}

function handleMove(from, to) {
    if (on_pickup_in_flight) {
        retry_move = () => maybeMove(from, to);
        return 'snapback';
    }
    retry_move = null;
    if (isLegalMove(to)) {
        fetchWrapper(URL + 'move', { 'start': from, 'stop': to, 'gameId': gameId }, 'POST')
            .then((response) => response.json())
            .then((data) => {
                if (!data['success']) {
                    return;
                }
                else {
                    whose_turn = data['whose_turn'];
                    data['extra'].forEach(x => {
                        square = x[0].toLowerCase()
                        piece = x[1]
                        if (piece == '') {
                            clearSquare(square);
                        } else {
                            setSquare(square, piece);
                        }
                    });
                }
            })
    } else {
        return 'snapback';
    }
}

function maybeMove(from, to) {
    retry_move = null;
    if (to == 'offboard') {
        return 'snapback';
    }
    fetchWrapper(URL + 'move', { 'start': from, 'stop': to, 'gameId': gameId }, 'POST')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            }
            else {
                whose_turn = data['whose_turn'];
                board.move(from + '-' + to);
                data['extra'].forEach(x => {
                    square = x[0].toLowerCase()
                    piece = x[1]
                    if (piece == '') {
                        clearSquare(square);
                    } else {
                        setSquare(square, piece);
                    }
                });
            }
        })
}

setInterval(function () {
    if (retry_move) {
        retry_move();
    }}, 200);

newGame();