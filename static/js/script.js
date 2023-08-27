URL = CONFIG.URL;

previousToast = null;
toastElement = document.getElementById('toast');

gameId = null;

currentThemeIsDark = document.body.classList.contains('dark');

whiteboard = document.getElementById('whiteboard');
whiteboard_messages = []

usernameInputElement = document.getElementById('usernameInput');
username = null;

addFriendInputElement = document.getElementById('addFriendInput');
addFriendButton = document.getElementById('addFriendButton');

activeGamesWrapper = document.getElementById('activeGamesWrapper');

shiftKeyIsDown = false;
newGameModal = document.getElementById('newGameModal');
newGameModalOverlay = document.getElementById('newGameModalOverlay');

newGameButton = document.getElementById('newGameButton');
offerDrawButton = document.getElementById('offerDrawButton');
copyGameIdButton = document.getElementById('copyGameIdButton');
toggleThemeButton = document.getElementById('toggleThemeButton');
displayFriendsListButton = document.getElementById('displayFriendsListButton');
displayPromotionOptionsButton = document.getElementById('displayPromotionOptionsButton');
ignoreOtherPlayerCheckButton = document.getElementById('ignoreOtherPlayerCheckButton');

holdingPiece = false;

joinGameButton = document.getElementById('joinGameButton');

gameIdInput = document.getElementById('gameIdInput');

promotionSelector = document.getElementById('promotionSelector');
promotionPiece = null;

ignoreOtherPlayerCheck = false;
lastIgnoreOtherPlayerCheck = false;

mostRecentFrom = null;
mostRecentTo = null;

handicapInfo = document.getElementById('handicapInfo');

howToPlayPopup = document.getElementById('how-to-play-popup');
howToPlayBtnText = document.getElementById('how-to-play-btn-text');

whoseTurn = null;
whoseTurnElement = document.getElementById('whoseTurn');

stateToastElement = document.getElementById('stateToast');

gameIsOver = false;
gameResultToastElement = document.getElementById('gameResult');
drawToastElement = document.getElementById('drawToast');
confirmDrawElement = document.getElementById('confirmDrawToast');

colorSelection = 'random';
whiteKingElement = document.getElementById('whiteKing');
blackKingElement = document.getElementById('blackKing');


untimedString = 'No time controls';
whiteTime = untimedString;
blackTime = untimedString;

firstMove = false;

currentWidth = window.innerWidth;
currentHeight = window.innerHeight;

yourTimeElement = document.getElementById('yourTime');
opponentTimeElement = document.getElementById('opponentTime');

timeSelection = null;

highlightedSquares = [];

// Colors should try to be 'White' or 'Black' (capitalization matters sometimes!) unless something else
// is required to interact with chessboard.js, e.g. in the charAt(0) stuff below
color = null;

timesElement = document.getElementById('times');

const socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('message', (data) => {
    if (data['color'] === 'both' || data['color'] === color) {
        showToast(data['message'], 5);
    }
});

socket.on('update', (data) => {
    firstMove = false;
    if (data['color'] === 'both' || data['color'] === color) {
        updateState();
    }
});

socket.on('whiteboard', (data) => {
    if (data['color'] == 'both' || data['color'] == color) {
        addToWhiteboard(data['message']);
    }
})

socket.on('draw_offer', (data) => {
    if (data['color'] == color) {
        showToast('Your opponent offered a draw', 10);
        opponentOfferedDraw();
    }  
})

socket.on('draw_offer_rescinded', (data) => {
    if (data['color'] == color) {
        drawToastElement.style.display = 'none';
    }
})

drawButton = document.getElementById('drawButton');
noDrawButton = document.getElementById('noDrawButton');

confirmDrawButton = document.getElementById('confirmDrawButton');
cancelDrawButton = document.getElementById('cancelDrawButton');

drawButton.addEventListener('click', () => {
    fetchWrapper(URL + 'accept_draw', { 'gameId': gameId, 'color': color }, 'POST')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast(data['error'], 5)
                return;
            }
        });
    drawToastElement.style.display = 'none';
});

noDrawButton.addEventListener('click', () => {
    drawToastElement.style.display = 'none';
});

confirmDrawButton.addEventListener('click', () => {
    offerDraw();
    confirmDrawElement.style.display = 'none';
});

cancelDrawButton.addEventListener('click', () => {
    confirmDrawElement.style.display = 'none';
});

function opponentOfferedDraw() {
    drawToastElement.style.display = 'inline-block';
}

function offerDraw() {
    fetchWrapper(URL + 'offer_draw', { 'gameId': gameId, 'color': color }, 'POST')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast(data['error'], 5)
                return;
            }
            else {
                showToast('You offered a draw', 5);
            }
        });
}

whiteboard.addEventListener('click', (e) => {
    if (e.target.classList.contains('whiteboard-message')) {
        whiteboard_messages.splice(e.target.dataset.index, 1);
        updateWhiteboard();
    }
});

for (var i = 0; i < 10; i++) {
    e = document.createElement('div');
    e.classList.add('whiteboard-message');

    if (i == 0) {
        e.classList.add('most-recent-message');
    }

    e.dataset.index = i;

    whiteboard.appendChild(e);
}

updateWhiteboard();

function updateWhiteboard(flash=false) {
    for (var i = 0; i < whiteboard_messages.length; i++) {
        whiteboard.children[i].innerHTML = `${whiteboard_messages[i]}`;
        whiteboard.children[i].style.display = 'block';
    } 
    for (var i = whiteboard_messages.length; i < 10; i++) {
        whiteboard.children[i].innerHTML = '';
        whiteboard.children[i].style.display = 'none';
    }
    if (flash) {
        whiteboard.children[0].classList.add('flash');
        setTimeout(() => {
            whiteboard.children[0].classList.remove('flash');
        }, 2000);
    }
}

function addToWhiteboard(message) {
    if (whiteboard_messages.length >= 10) {
        whiteboard_messages.pop();
    }

    whiteboard_messages.unshift(message);

    updateWhiteboard(true);
}

function admin() {
    return localStorage.getItem('hchess-testing-mode');
}

function toggleOtherPlayerCheck() {
    ignoreOtherPlayerCheck = !ignoreOtherPlayerCheck;
    if (ignoreOtherPlayerCheck) {
        stateToastElement.textContent = `Can move opponent's pieces`;
        stateToastElement.style.display = 'inline-block';
    } else {
        stateToastElement.style.display = 'none';
    }
}

function getSquareElement(square) {
    return document.querySelector(`[data-square="${square.toLowerCase()}"]`);
}

function highlightSquare(square) {
    getSquareElement(square).classList.add('highlight');
    highlightedSquares.push(square);
}

function updateMostRecentMove(from, to) {
    mostRecentFrom && getSquareElement(mostRecentFrom).classList.remove('recent-move');
    mostRecentTo && getSquareElement(mostRecentTo).classList.remove('recent-move');
    getSquareElement(from).classList.add('recent-move');
    getSquareElement(to).classList.add('recent-move');
    mostRecentFrom = from;
    mostRecentTo = to;
}

function highlightMostRecentMove() {
    if (!mostRecentFrom || !mostRecentTo) {
        return;
    }
    getSquareElement(mostRecentFrom).classList.add('recent-move');
    getSquareElement(mostRecentTo).classList.add('recent-move');
}

function processGameOver(result) {
    setWhoseTurn('');
    gameIsOver = true;
    gameResultToastElement.classList.remove('win', 'loss', 'draw');
    gameResultToastElement.style.display = 'inline-block';
    result_string = result === 'White' ? 'White wins' : result === 'Black' ? 'Black wins' : result;
    result_class = result === color ? 'win' : (result === 'Black' || result == 'White') ? 'loss' : 'draw'; 
    gameResultToastElement.textContent = result_string;
    gameResultToastElement.classList.add(result_class);
}

function unhighlightSquares() {
    highlightedSquares.forEach(unhighlightSquare);
    highlightedSquares = [];
}

function unhighlightSquare(square, removeRecent = false) {
    if (removeRecent) {
        getSquareElement(square).classList.remove('recent');
    }
    ['highlight'].forEach(className => {
        getSquareElement(square).classList.remove(className);
    });
}

function formatTime(seconds) {
    if (typeof (seconds) == 'string') {
        return untimedString;
    }
    if (seconds <= 0) {
        return '0:00';
    }
    ret = `${Math.floor(seconds / 60)}:${seconds % 60 < 10 ? '0' : ''}${Math.floor(seconds % 60)}`;
    return ret;
}

function setBold(element, bold) {
    if (bold) {
        element.classList.add('bold');
    } else {
        element.classList.remove('bold');
    }
}

function updateTimes(white, black) {
    if (gameIsOver || !white || !black) {
        return;
    }
    if (white < -1 || black < -1) {
        updateState();
        return;
    }
    whiteTime = white;
    blackTime = black;

    whiteTimeStr = formatTime(white);
    blackTimeStr = formatTime(black);
    setBold(yourTimeElement, color == whoseTurn);
    setBold(opponentTimeElement, color != whoseTurn);
    yourTimeElement.innerHTML = color === 'White' ? whiteTimeStr : blackTimeStr;
    opponentTimeElement.innerHTML = color === 'White' ? blackTimeStr : whiteTimeStr;
}

setInterval(() => {
    if (gameIsOver || firstMove) {
        return;
    }
    whiteTime = (typeof (whiteTime) != 'string' && whoseTurn === 'White') ? whiteTime - 1 : whiteTime;
    blackTime = (typeof (blackTime) != 'string' && whoseTurn === 'Black') ? blackTime - 1 : blackTime;
    updateTimes(whiteTime, blackTime);
}, 1000);


function setGameId(id) {
    gameId && socket.emit('leave', { room: gameId })
    gameId = id;
    socket.emit('join', { room: id });
}

// No longer necessary but too lazy to refactor
function setWhoseTurn(turn) {
    whoseTurn = turn;
}

function setUsername() {
    username && socket.emit('leave', { room: username });
    username = usernameInputElement.value;
    localStorage.setItem('handicap-chess-username', username);
    socket.emit('join', { room: username });
    populateFriendsList();

}

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
        // Sets the image to the correct color
        element.src = element.src.replace(/.(.)\.png/, `${orientation.charAt(0).toLowerCase()}$1.png`);
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
    setUsername();
}

gameIdInput.addEventListener('focus', function () {
    document.removeEventListener('keydown', handleKeyDown);
});

gameIdInput.addEventListener('blur', function () {
    document.addEventListener('keydown', handleKeyDown);
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
        if (element.classList.contains('selected-time')) {
            element.classList.remove('selected-time');
            timeSelection = null;
            return;
        }
        timeSelectionElements.forEach(element => {
            element.classList.remove('selected-time');
        });
        element.classList.add('selected-time');
        timeSelection = element.getAttribute('seconds');
    });
});

addFriendInputElement.addEventListener('focus', function () {
    document.removeEventListener('keydown', handleKeyDown);
});

addFriendInputElement.addEventListener('blur', function () {
    document.addEventListener('keydown', handleKeyDown);
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
    if (seconds == 0) {
        toastElement.style.display = 'none';
        return;
    }

    toastElement.textContent = message;
    toastElement.style.display = 'inline-block';

    setTimeout(function () {
        toastElement.style.display = 'none';
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
            handicapInfo.textContent = data['handicap'];
        });
}

function newGame(toast = true) {
    gameResultToastElement.style.display = 'none';
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
            toast && showToast('Successfully created game', 5);
            updateState();
            firstMove = true;
        });
    closeModal();
    setWhoseTurn('White');
    gameIsOver = false;
    whiteboard_messages = [];
    updateWhiteboard();
    initBoard();
}

function loadGame(game = null) {
    game = game || gameIdInput.value;
    if (!game) {
        showToast('Enter the game ID', 3);
        return;
    }
    closeModal();
    gameResultToastElement.style.display = 'none';
    fetchWrapper(URL + 'join_game', { 'gameId': game }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast(data['error'], 3);
                return;
            }
            setGameId(game);
            gameIsOver = false;
            if (data['winner']) {
                board.position(data['board']);
                processGameOver(data['winner']);
            } else {
                setOrientation(data['color']);
                board.position(data['board']);
                setWhoseTurn(data['whoseTurn']);
                getHandicap();
                gameIdInput.value = '';
                showToast('Game loaded', 3);
                firstMove = true;
            }
            updateState();
        });
}

function openModal() {
    newGameModal.style.display = 'flex';
    newGameModalOverlay.style.display = 'block';
}

function confirmDraw() {
    confirmDrawElement.style.display = 'inline-block';
}

function closeModal() {
    newGameModal.style.display = 'none';
    newGameModalOverlay.style.display = 'none';
}

function flipVisibility(element) {
    element.style.visibility = element.style.visibility == 'hidden' ? 'visible' : 'hidden';
}

function handleKeyDown(event) {
    k = event.key.toLowerCase();
    if (event.shiftKey) {
        shiftKeyIsDown = true;
    }
    if (k == 'c') {
        if (admin() && event.ctrlKey) {
            showOpponentsHandicap();
        } else {
            copyGameIdButton.click();
        }
    } else if (k == 'escape') {
        closeModal();
    } else if (k == 'enter' && newGameModal.style.display == 'flex') {
        event.preventDefault();
        createGameButton.click();
    } else if (k == 'd') {
        displayPromotionOptionsButton.click();
    } else if (k == 'f') {
        displayFriendsListButton.click();
    } else if (k == 'a') {
        ignoreOtherPlayerCheckButton.click();
    } else if (k == 'n') {
        newGameButton.click();
    } else if (k == 't') {
        toggleThemeButton.click();
    } else if (k == 'o') {
        offerDrawButton.click();
    }
}

function handleKeyUp(event) {
    k = event.key.toLowerCase();
    if (event.key == 'Shift') {
        shiftKeyIsDown = false;
    }
}

document.addEventListener("click", function (event) {
    if (event.target === newGameModalOverlay) {
        closeModal();
    }
});

newGameButton.addEventListener('click', () => {
    shiftKeyIsDown ? newGame() : openModal();
});

offerDrawButton.addEventListener('click', () => {
    if (gameIsOver || drawToastElement.style.display == 'inline-block') {
        showToast('Respond to your opponent\'s draw offer first', 5);
        return ;
    }
    shiftKeyIsDown ? offerDraw() : confirmDraw();
});

toggleThemeButton.addEventListener('click', () => {
    toggleTheme();
});

createGameButton.addEventListener('click', () => {
    newGame();
});

joinGameButton.addEventListener('click', () => loadGame());

function copyToClipboard(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
}

function showOpponentsHandicap() {
    fetchWrapper(URL + 'handicap', { 'gameId': gameId, 'color': color == 'White' ? 'Black' : 'White' }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            showToast(data['handicap'], 10);
        });
}

function copyGameId() {
    copyToClipboard(gameId);
    showToast(`Copied game id to clipboard`);
}

copyGameIdButton.addEventListener('click', () => {
    copyGameId();
});

displayFriendsListButton.addEventListener('click', () => {
    flipVisibility(activeGamesWrapper);
});

displayPromotionOptionsButton.addEventListener('click', () => {
    flipVisibility(promotionSelector);
});

ignoreOtherPlayerCheckButton.addEventListener('click', () => {
    toggleOtherPlayerCheck();
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
document.addEventListener('keyup', handleKeyUp);

var board, game = new Chess();

function imgUrl(piece) {
    return `https://chessboardjs.com/img/chesspieces/wikipedia/${piece}.png`
}

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
    lastIgnoreOtherPlayerCheck = ignoreOtherPlayerCheck;
    return (color && piece.search(color.charAt(0).toLowerCase()) !== -1) || ignoreOtherPlayerCheck;
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

    fetchWrapper(URL + 'legal_moves', { 'start': source, 'gameId': gameId, ignoreOtherPlayerCheck }, 'GET')
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
    if (lastIgnoreOtherPlayerCheck && !ignoreOtherPlayerCheck) {
        showToast("Can't move until other player joins", 3);
        return false;
    }
    return lastIgnoreOtherPlayerCheck === ignoreOtherPlayerCheck && legal_destinations.includes(to.toUpperCase());
}

function sendMove(from, to) {
    fetchWrapper(URL + 'move', { 'start': from, 'stop': to, 'gameId': gameId, ignoreOtherPlayerCheck, 'promotion': promotionPiece || 'Q' }, 'POST')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            }
            else {
                board.move(`${from}-${to}`, false); // this should be unnecessary except in a retry but it doesn't hurt anyway
                updateMostRecentMove(from, to);
                data['whoseTurn'] && setWhoseTurn(data['whoseTurn']);
                data['winner'] && processGameOver(data['winner']);
                data['extra'].forEach(x => {
                    square = x[0].toLowerCase()
                    piece = x[1]
                    if (piece == '') {
                        clearSquare(square);
                    } else {
                        setSquare(square, piece.charAt(0).toLowerCase() + piece.charAt(piece.length - 1));
                    }
                });
            }
        });
}

function handleMove(from, to) {
    holdingPiece = false;
    unhighlightSquares();
    if (on_pickup_in_flight && lastIgnoreOtherPlayerCheck === ignoreOtherPlayerCheck) {
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
            updateTimes(data['whiteTime'], data['blackTime']);
            if (data['winner']) {
                processGameOver(data['winner']);
            } else {
                setWhoseTurn(data['whoseTurn']);
            }
        })
}

setInterval(function () {
    retry_move && retry_move();
    !holdingPiece && unhighlightSquares();
}, 200);

// // This is the stupid constant polling solution
// setInterval(function () {
//     if (gameIsOver) {
//         return;
//     }
// updateState();
// }, 1000);

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
}, 3000);

function toggleGameButtons() {
    document.querySelectorAll('.game-button').forEach(element => {
        element.classList.toggle('dark');
    });
    document.querySelectorAll('.remove-friend-button').forEach(element => {
        element.classList.toggle('dark');
    });
}

function toggleTheme() {
    document.body.classList.toggle('dark');
    currentThemeIsDark = document.body.classList.contains('dark');
    localStorage.setItem('hchess-dark-mode', currentThemeIsDark);
}


function displayActiveGames(activeGames) {
    activeGamesWrapper.innerHTML = '<h4> Friends </h4>';
    activeGames.forEach(game => {
        id = game['gameId'];
        f = id ? `loadGame('${id}')` : '';
        content = `<button class="game-button ${id ? "active" : "dead"} ${currentThemeIsDark ? 'dark' : ''}" onclick="${f}">Challenge ${game['username']}</button>`
        activeGamesWrapper.innerHTML += `
                <div class="friend">
                    ${content}
                    <button class="remove-friend-button ${currentThemeIsDark ? 'dark' : ''}" onClick="removeFriend('${game['username']}')">
                        X
                    </button>
                </div>
            `;
    });
}

admin() && (whiteKingElement.click() || toggleOtherPlayerCheck());

setInterval(() => {
    if (currentWidth != window.innerWidth || currentHeight != window.innerHeight) {
        currentWidth = window.innerWidth;
        currentHeight = window.innerHeight;
        !holdingPiece && board.resize();
        highlightMostRecentMove();
    }
}, 100);

if (localStorage.getItem('hchess-dark-mode') == 'true') {
    toggleTheme();
}

newGame(false);
populateFriendsList();