URL = CONFIG.URL;

previousToast = null;

gameId = null;

usernameInputElement = document.getElementById('usernameInput');
username = null;

addFriendInputElement = document.getElementById('addFriendInput');
addFriendButton = document.getElementById('addFriendButton');

newGameButton = document.getElementById('newGameButton');
newGameModal = document.getElementById('newGameModal');
newGameModalOverlay = document.getElementById('newGameModalOverlay');
createGameButton = document.getElementById('createGameButton');
copyGameIdButton = document.getElementById('copyGameIdButton');

holdingPiece = false;

loadGameButton = document.getElementById('loadGameButton');

gameIdInput = document.getElementById('gameIdInput');

promotionSelector = document.getElementById('promotionSelector');
promotionPiece = null;
displayPromotionOptionsElement = document.getElementById('displayPromotionOptions');

handicapInfo = document.getElementById('handicapInfo');

howToPlayPopup = document.getElementById('how-to-play-popup');
howToPlayBtnText = document.getElementById('how-to-play-btn-text');

whoseTurn = null;
whoseTurnElement = document.getElementById('whoseTurn');

gameIsOver = false;
gameResultElement = document.getElementById('game-result');

colorSelection = 'random';
whiteKingElement = document.getElementById('whiteKing');
blackKingElement = document.getElementById('blackKing');

timeSelection = null;

highlightedSquares = [];

// Colors should try to be 'White' or 'Black' (capitalization matters sometimes!) unless something else
// is required to interact with chessboard.js, e.g. in the charAt(0) stuff below
color = null;

timesElement = document.getElementById('times');

ignoreOtherPlayerCheck = document.getElementById('ignoreOtherPlayerCheck');

function getSquareElement(square) {
    return document.querySelector(`[data-square="${square.toLowerCase()}"]`);
}

function highlightSquare(square) {
    getSquareElement(square).classList.add('highlight');
    highlightedSquares.push(square);
}

function processGameOver(result) {
    setWhoseTurn('');
    gameIsOver = true;
    gameResultElement.textContent = `${result} wins`;
    gameResultElement.style.color = result === color ? 'green' : 'red';
}

function unhighlightSquares() {
    highlightedSquares.forEach(square => {
        getSquareElement(square).classList.remove('highlight');
    });
    highlightedSquares = [];
}

function formatTime(seconds, bold = false) {
    if (typeof (seconds) == 'string') {
        return bold ? `<b>${seconds}</b>` : seconds;
    }
    if (seconds <= 0) {
        return '0:00';
    }
    ret = `${Math.floor(seconds / 60)}:${seconds % 60 < 10 ? '0' : ''}${Math.floor(seconds % 60)}`;
    if (bold) {
        ret = `<b>${ret}</b>`;
    }
    return ret;
}

function updateTimes(white, black) {
    if (gameIsOver || !white || !black) {
        return;
    }
    whiteTime = formatTime(white, whoseTurn === 'White');
    blackTime = formatTime(black, whoseTurn === 'Black');
    timesElement.innerHTML = `${whiteTime} - ${blackTime}`
}

// I thought we might want to display this information, but it's not really necessary
// Too lazy to refactor
function setGameId(id) {
    gameId = id;
}

// Used to be used to populate a textbox with whose turn it was, but 
// no longer necessary since the time controls stuff handles that. 
// Too lazy to refactor
function setWhoseTurn(turn) {
    whoseTurn = turn;
}

function setUsername() {
    username = usernameInputElement.value;
    localStorage.setItem('handicap-chess-username', username);
    populateFriendsList();

}

displayPromotionOptionsElement.addEventListener('change', function () {
    promotionSelector.style.display = displayPromotionOptionsElement.checked ? 'flex' : 'none';
});

promotionElements = document.querySelectorAll('.promotion-piece');

promotionElements.forEach(element => {
    element.addEventListener('click', function () {
        if (element.classList.contains('selected')) {
            element.classList.remove('selected');
            promotionPiece = null;
            return;
        }
        promotionElements.forEach(element => {
            element.classList.remove('selected');
        });
        promotionPiece = element.getAttribute('piece');
        element.classList.add('selected');
    });
});

function setOrientation(orientation) {
    color = orientation;
    board.orientation(orientation.toLowerCase());
    promotionElements.forEach(element => {
        element.src = element.src.replace(/w(.)\.png/, `${orientation.charAt(0).toLowerCase()}$1.png`);
    });
}

usernameInputElement.addEventListener('blur', function () {
    setUsername();
    document.addEventListener('keydown', handleKeyDown);
});

usernameInputElement.addEventListener('focus', function () {
    document.removeEventListener('keydown', handleKeyDown);
});

usernameInputElement.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
        setUsername();
    }
    if (e.key === 'Escape') {
        usernameInputElement.blur();
    }
});

if (localStorage.getItem('handicap-chess-username')) {
    usernameInputElement.value = localStorage.getItem('handicap-chess-username');
    username = usernameInputElement.value;
}

gameIdInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
        console.log('asdf asdf'); 
        loadGame();
    }
});

whiteKingElement.addEventListener('click', function () {
    if (colorSelection == 'White') {
        colorSelection = 'random';
        whiteKingElement.classList.remove('selected');
    } else {
        colorSelection = 'White';
        whiteKingElement.classList.add('selected');
        blackKingElement.classList.remove('selected');
    }
});

blackKingElement.addEventListener('click', function () {
    if (colorSelection == 'Black') {
        colorSelection = 'random';
        blackKingElement.classList.remove('selected');
    } else {
        colorSelection = 'Black';
        blackKingElement.classList.add('selected');
        whiteKingElement.classList.remove('selected');
    }
});

timeSelectionElements = document.querySelectorAll('.time-selection');

timeSelectionElements.forEach(element => {
    element.addEventListener('click', function () {
        if (element.classList.contains('selected')) {
            element.classList.remove('selected');
            timeSelection = null;
            return;
        }
        timeSelectionElements.forEach(element => {
            element.classList.remove('selected');
        });
        element.classList.add('selected');
        timeSelection = element.getAttribute('seconds');
    });
});

addFriendInputElement.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
        addFriendButton.click();
    } else if (e.key === 'Escape') {
        addFriendInputElement.blur();
    }
});

addFriendButton.addEventListener('click', function () {
    if (!username) {
        showToast('Please enter a username');
        return;
    }
    if (!addFriendInputElement.value) {
        showToast('Please enter a friend to add');
        return;
    }
    friend = addFriendInputElement.value;
    fetchWrapper(URL + 'add_friend', { 'username': username, friend })
        .then((response) => response.json())
        .then((data) => {
            showToast(data.success ? `Successfully added ${friend} as a friend` : data.error);
            populateFriendsList();
        });
    addFriendInputElement.value = '';
});

function removeFriend(friend) {
    fetchWrapper(URL + 'remove_friend', { 'username': username, friend })
        .then((response) => response.json())
        .then((data) => {
            showToast(data.success ? `Successfully removed ${friend} as a friend` : data.error);
            populateFriendsList();
        });
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
        ret['gameId'] = gameIdInput.value;
    } if (colorSelection != 'random') {
        ret['color'] = colorSelection;
    } if (timeSelection) {
        ret['timeControl'] = timeSelection;
    } if (username) {
        ret['username'] = username;
    }
    return ret
}

function getHandicap() {
    fetchWrapper(URL + 'handicap', { 'gameId': gameId, 'color': color }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            handicapInfo.textContent = `Your handicap is: ${data['handicap']}`;
        });
}

function newGame() {
    gameResultElement.textContent = '';
    fetchWrapper(URL + 'new_game', newGameBody(), 'POST')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast(data['error'], 10);
                return;
            }
            setGameId(data['gameId']);
            setOrientation(data['color']);
            getHandicap();
        });

    setWhoseTurn('White');
    gameIsOver = false;
    initBoard();
}

function loadGame(game = null) {
    game = game || gameIdInput.value;
    if (!game) {
        showToast('Enter the game ID', 3);
        return;
    }
    gameResultElement.textContent = '';
    fetchWrapper(URL + 'join_game', { 'gameId': game }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast(data['error'], 3);
                return;
            }
            setGameId(game);
            gameIsOver = false;
            board.position(data['board']);
            if (data['winner']) {
                processGameOver(data['winner']);
            } else {
                setOrientation(data['color']);
                setWhoseTurn(data['whoseTurn']);
                getHandicap();
                gameIdInput.value = '';
                showToast('Game loaded', 3);
            }
        });
}

function openModal() {
    newGameModal.style.display = 'flex';
    newGameModalOverlay.style.display = 'block';
}

function closeModal() {
    newGameModal.style.display = 'none';
    newGameModalOverlay.style.display = 'none';
}

function handleKeyDown(event) {
    if (event.ctrlKey) {
        if (event.key == 'c') {
            copyGameId();
        }
    } else if (event.key == 'Escape') {
        closeModal();
    } else if (event.key == 'Enter' && newGameModal.style.display == 'flex') {
        event.preventDefault();
        createGameButton.click();
    }
}

document.addEventListener("click", function (event) {
    if (event.target === newGameModalOverlay) {
        closeModal();
    }
});

newGameButton.addEventListener('click', () => {
    openModal();
});

createGameButton.addEventListener('click', () => {
    newGame();
    closeModal();
});

loadGameButton.addEventListener('click', () => loadGame());

function copyToClipboard(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
}

function copyGameId() {
    copyToClipboard(gameId);
    showToast(`Copied ${gameId} to clipboard`);
}

copyGameIdButton.addEventListener('click', () => {
    copyGameId();
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

function imgUrl(piece) {
    return `https://chessboardjs.com/img/chesspieces/wikipedia/${piece}.png`
}

/* Initialize the board with a configuration object */
function initBoard() {
    var config = {
        draggable: true,
        position: 'start',
        orientation: (color && color.toLowerCase()) || 'white',
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
    return color && piece.search(color.charAt(0).toLowerCase()) !== -1 || ignoreOtherPlayerCheck.checked;
}

function activePiece(piece) {
    return piece.search(whoseTurn.charAt(0).toLowerCase()) !== -1;
}

function onPickup(source, piece) {
    holdingPiece = true;
    unhighlightSquares();
    if (!yourPiece(piece) || !activePiece(piece) || gameIsOver) {
        return false;
    }

    legal_destinations = [];
    on_pickup_in_flight = true;

    fetchWrapper(URL + 'legal_moves', { 'start': source, 'gameId': gameId, 'ignoreOtherPlayerCheck': ignoreOtherPlayerCheck.checked }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                if (data['error'] === 'Other player has not joined') {
                    showToast("Can't move until other player joins", 3);
                }
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

function sendMove(from, to) {
    fetchWrapper(URL + 'move', { 'start': from, 'stop': to, 'gameId': gameId, 'ignoreOtherPlayerCheck': ignoreOtherPlayerCheck.checked, 'promotion': promotionPiece || 'Q' }, 'POST')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            }
            else {
                board.move(`${from}-${to}`, false); // this should be unnecessary except in a retry but it doesn't hurt anyway
                data['whoseTurn'] && setWhoseTurn(data['whoseTurn']);
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
        });
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
        sendMove(from, to);
    } else {
        return 'snapback';
    }
}

function maybeMove(from, to) {
    unhighlightSquares();
    retry_move = null;
    if (to == 'offboard') {
        return
    }
    sendMove(from, to);
}

function updateState() {
    fetchWrapper(URL + 'board', { 'gameId': gameId }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            }
            board.position(data['board']);
            if (data['winner']) {
                processGameOver(data['winner']);
            } else {
                setWhoseTurn(data['whoseTurn']);
                updateTimes(data['whiteTime'], data['blackTime']);
            }
        })
}

setInterval(function () {
    retry_move && retry_move();
    !holdingPiece && unhighlightSquares();
}, 200);

// This is the stupid constant polling solution
setInterval(function () {
    if (gameIsOver) {
        return;
    }
    updateState();
}, 1000);

function populateFriendsList() {
    fetchWrapper(URL + 'active_games', { 'username': username }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            }
            displayActiveGames(data['games']);
        })
}

setInterval(function () {
    if (!username) {
        return;
    } else {
        populateFriendsList();
    }
}, 10000);

activeGamesWrapper = document.createElement('div');
activeGamesWrapper.id = 'active-games-wrapper';

activeGamesWrapper.classList.add('active-games-wrapper');

function displayActiveGames(activeGames) {
    activeGamesWrapper.innerHTML = `<h4> Friends list </h4>`;
    activeGames.forEach(game => {
        id = game['gameId'];
        display_username = game['username'].slice(0, 9);
        if (id) {
            content = `<button class="active-game-button" onclick="loadGame('${id}')">Challenge ${display_username}</button>`;
        } else {
            content = `<button class="dead-button">Challenge ${display_username}</button>`;
        }
        activeGamesWrapper.innerHTML += `
                <div class="friend">
                    ${content}
                    <button class="remove-friend-button" onClick="removeFriend('${game['username']}')">Remove friend</button>
                </div>
            `;
    });

    document.body.appendChild(activeGamesWrapper);
}

if (localStorage.getItem('hchess-testing-mode')) {
    whiteKingElement.click();
    ignoreOtherPlayerCheck.checked = true;
}

newGame();
populateFriendsList();