URL = CONFIG.URL;

function isLocalhost() {
    return window.location.href.includes('localhost');
}

previousToast = null;

gameId = null;
newGameButton = document.getElementById('newGameButton');
copyGameIdButton = document.getElementById('copyGameIdButton');

holdingPiece = false;

loadGameButton = document.getElementById('loadGameButton');

colorSelector = document.getElementById('colorSelector');
gameIdInput = document.getElementById('gameIdInput');

handicapInfo = document.getElementById('handicapInfo');

howToPlayPopup = document.getElementById('how-to-play-popup');
howToPlayBtnText = document.getElementById('how-to-play-btn-text');

whoseTurn = null;
whoseTurnElement = document.getElementById('whoseTurn');

gameIsOver = false;

highlightedSquares = [];

color = null;

d = { 'white': 'w', 'black': 'b' }

function getSquareElement(square) {
    return document.querySelector(`[data-square="${square.toLowerCase()}"]`);
}

function highlightSquare(square) {
    getSquareElement(square).classList.add('highlight');
    highlightedSquares.push(square);
}

function processGameOver(result) {
    gameIsOver = true;
    showToast(result === 'W' ? 'White wins' : 'Black wins', 5);
}

function unhighlightSquares() {
    highlightedSquares.forEach(square => {
        getSquareElement(square).classList.remove('highlight');
    });
    highlightedSquares = [];
}

// I thought we might want to display this information, but it's not really necessary
// So now this function is just kinda pointless
function setGameId(id) {
    gameId = id;
}

function setWhoseTurn(turn) {
    whoseTurn = turn;
    if (!whoseTurn) {
        whoseTurnElement.textContent = '';
    } else {
        whoseTurnElement.textContent = `${whoseTurn === 'W' ? 'White' : 'Black'} to move`;
    }
}

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

function newGameBody() {
    ret = {};
    if (gameIdInput.value) {
        ret = { 'gameId': gameIdInput.value };
    } if (colorSelector.value != 'random') {
        ret = { ...ret, 'color': colorSelector.value };
    }
    return ret
}

function newGame() {
    fetchWrapper(URL + 'new_game', newGameBody(), 'POST')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast(data['error'], 10);
                return;
            }
            setGameId(data['gameId']);
            color = data['color'];
            board.orientation(color);
            fetchWrapper(URL + 'handicap', { 'gameId': gameId, 'color': color }, 'GET')
                .then((response) => response.json())
                .then((data) => {
                    handicapInfo.textContent = `Your handicap is: ${data['handicap']}`;
                });
        });

    setWhoseTurn('W');
    gameIsOver = false;
    initBoard();
}

function loadGame() {
    if (!gameIdInput.value) {
        showToast('Enter the game ID', 3);
        return;
    }
    fetchWrapper(URL + 'join_game', { 'gameId': gameIdInput.value }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast(data['error'], 3);
                return;
            }
            setGameId(gameIdInput.value);
            gameIsOver = false;
            board.position(data['board']);
            if (data['winner']) {
                processGameOver(data['result']);
            } else {
                color = data['color'];
                board.orientation(color);
                setWhoseTurn(data['whoseTurn']);
            }
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
    return piece.search(whoseTurn.toLowerCase()) !== -1;
}

function onPickup(source, piece) {
    holdingPiece = true;
    unhighlightSquares();
    if (!yourPiece(piece) || !activePiece(piece) || gameIsOver) {
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
                highlightSquare(move);
                legal_destinations.push(move);
            });
        })
}

function isLegalMove(to) {
    return legal_destinations.includes(to.toUpperCase());
}

function handleMove(from, to) {
    holdingPiece = false;
    unhighlightSquares();
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
                    setWhoseTurn(data['whoseTurn']);
                    data['winner'] && processGameOver(data['winner']);
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
    unhighlightSquares();
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
                setWhoseTurn(data['whoseTurn']);
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

function updateState() {
    fetchWrapper(URL + 'board', { 'gameId': gameId }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            } if (data['winner']) {
                processGameOver(data['result']);
            } else {
                board.position(data['board']);
                setWhoseTurn(data['whoseTurn']);
            }
        })
}

setInterval(function () {
    if (retry_move) {
        retry_move();
    }
    if (!holdingPiece) {
        unhighlightSquares();
    }
}, 200);

// This is the stupid constant polling solution
setInterval(function () {
    if (gameIsOver) {
        return;
    } 
    updateState();
}, 1000);

newGame();