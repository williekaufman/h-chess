URL = CONFIG.URL;

previousToast = null;
toastElement = document.getElementById('toast');

gameId = null;
lastGameId = null;
inviteId = null;

currentThemeIsDark = document.body.classList.contains('dark');

whiteboard = document.getElementById('whiteboard');
whiteboard_messages = []

usernameInputElement = document.getElementById('usernameInput');
username = null;

addFriendInputElement = document.getElementById('addFriendInput');
addFriendButton = document.getElementById('addFriendButton');

activeGamesWrapper = document.getElementById('activeGamesWrapper');
publicGamesWrapper = document.getElementById('publicGamesWrapper');

shiftKeyIsDown = false;
newGameModal = document.getElementById('newGameModal');
newGameModalOverlay = document.getElementById('newGameModalOverlay');

hotkeysElement = document.getElementById('hotkeys');
hotkeysVisibilityButton = document.getElementById('hotkeysVisibilityButton');

rulesButton = document.getElementById('rulesButton');
newGameButton = document.getElementById('newGameButton');
openJoinDialogButton = document.getElementById('openJoinDialogButton');
offerDrawButton = document.getElementById('offerDrawButton');
resignButton = document.getElementById('resignButton');
copyGameIdButton = document.getElementById('copyGameIdButton');
toggleThemeButton = document.getElementById('toggleThemeButton');
displayFriendsListButton = document.getElementById('displayFriendsListButton');
displayPromotionOptionsButton = document.getElementById('displayPromotionOptionsButton');
ignoreOtherPlayerCheckButton = document.getElementById('ignoreOtherPlayerCheckButton');

publicCheckbox = document.getElementById('publicCheckbox');

unlimitedTimeCheckbox = document.getElementById('unlimitedTimeCheckbox');
timeControlMinutes = document.getElementById('timeControlMinutes');
timeControlSeconds = document.getElementById('timeControlSeconds');
incrementMinutes = document.getElementById('incrementMinutes');
incrementSeconds = document.getElementById('incrementSeconds');

holdingPiece = false;

joinGameButton = document.getElementById('joinGameButton');
joinGameModal = document.getElementById('joinGameModal')
joinGameModalOverlay = document.getElementById('joinGameModalOverlay');

rulesModal = document.getElementById('rulesModal');
rulesModalOverlay = document.getElementById('rulesModalOverlay');

publicGamesModalOverlay = document.getElementById('publicGamesModalOverlay');
publicGamesModal = document.getElementById('publicGamesModal');

gameIdInput = document.getElementById('gameIdInput');

promotionSelector = document.getElementById('promotionSelector');
promotionPiece = null;

ignoreOtherPlayerCheck = false;
lastIgnoreOtherPlayerCheck = false;

mostRecentFrom = null;
mostRecentTo = null;

handicapInfo = document.getElementById('handicapInfo');

whoseTurn = null;
whoseTurnElement = document.getElementById('whoseTurn');

stateToastElement = document.getElementById('stateToast');

// Very few of these things with toast in the name are really toast related anymore...so it goes

gameIsOver = false;
gameResultToastElement = document.getElementById('gameResult');
showOpponentsHandicapButton = document.getElementById('showOpponentsHandicapButton');
drawToastElement = document.getElementById('drawToast');
confirmDrawElement = document.getElementById('confirmDrawToast');
confirmResignElement = document.getElementById('confirmResignToast');
inviteToastElement = document.getElementById('inviteToast');
acceptInviteButton = document.getElementById('acceptInviteButton');
declineInviteButton = document.getElementById('declineInviteButton');


colorSelection = 'random';
whiteKingElement = document.getElementById('whiteKing');
blackKingElement = document.getElementById('blackKing');


untimedString = 'No time controls';
whiteTime = untimedString;
blackTime = untimedString;

// For tracking if the clocks should be counting down
// Strictly frontend, we don't sync the times up except in a move so this just controls the loop
// that decrements the active player's time
ticking = null;

currentWidth = window.innerWidth;
currentHeight = window.innerHeight;

yourTimeElement = document.getElementById('yourTime');
opponentTimeElement = document.getElementById('opponentTime');

yourHandicapSelection = null;
theirHandicapSelection = null;

highlightedSquares = [];

// Colors should try to be 'White' or 'Black' (capitalization matters sometimes!) unless something else
// is required to interact with chessboard.js, e.g. in the charAt(0) stuff below
color = null;

timesElement = document.getElementById('times');

const socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('message', (data) => {
    // No need for color checking here
    showToast(data['message'], 10);
});

socket.on('update', (data) => {
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

socket.on('invite', (data) => {
    makeInvite(data);
})

function removeOnClickEventListener(element) {
  const clone = element.cloneNode(true);
  element.parentNode.replaceChild(clone, element);
}

declineInviteButton.addEventListener('click', () => {
    inviteToastElement.style.display = 'none';
});

acceptInviteButton.addEventListener('click', () => {
    acceptInvite(inviteId);
});

function acceptInvite(id) {
    loadGame(id);
    inviteToastElement.style.display = 'none';
}

function makeInvite(data) {
    inviteId = data['gameId'];
    inviteToastElement.style.display = 'inline-block';
    showToast(`You were invited to a game by ${data['username']}`, 5);
}

drawButton = document.getElementById('drawButton');
noDrawButton = document.getElementById('noDrawButton');

confirmDrawButton = document.getElementById('confirmDrawButton');
cancelDrawButton = document.getElementById('cancelDrawButton');

confirmResignButton = document.getElementById('confirmResignButton');
cancelResignButton = document.getElementById('cancelResignButton');



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

confirmResignButton.addEventListener('click', () => {
    resign();
    confirmResignElement.style.display = 'none';
});

cancelResignButton.addEventListener('click', () => {
    confirmResignElement.style.display = 'none';
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
    cancelDrawButton.click();
}

function resign() {
    fetchWrapper(URL + 'resign', { 'gameId': gameId, 'color': color }, 'POST')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast(data['error'], 5)
                return;
            }
        });
    cancelResignButton.click();
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
    showOpponentsHandicapButton.style.display = 'inline-block';
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
    if (gameIsOver || !ticking) {
        return;
    }
    whiteTime = (typeof (whiteTime) != 'string' && whoseTurn === 'White') ? whiteTime - .2 : whiteTime;
    blackTime = (typeof (blackTime) != 'string' && whoseTurn === 'Black') ? blackTime - .2 : blackTime;
    updateTimes(whiteTime, blackTime);
}, 200);


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
    if (username) {
        socket.emit('leave', { room: username })
        socket.emit('logoff', { username })
    }
    username = usernameInputElement.value;
    localStorage.setItem('handicap-chess-username', username);
    socket.emit('join', { room: username });
    socket.emit('logon', { username });
    populateFriendsList();
}

setInterval(() => {
    if (username) {
        socket.emit('logon', { username });
    }
}, 5000);

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
    if (element.getAttribute('piece') == 'Q') {
        element.click();
    }
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

gameIdInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
        loadGame();
    }
    if (e.key === 'Escape') {
        gameIdInput.blur();
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

yourHandicapSelectionElements = document.querySelectorAll('.handicap-selection[yours="t"]')

yourHandicapSelectionElements.forEach(element => {
    element.addEventListener('click', function () {
        if (element.classList.contains('selected')) {
            element.classList.remove('selected');
            yourHandicapSelection = null;
            return;
        }
        yourHandicapSelectionElements.forEach(element => {
            element.classList.remove('selected');
        });
        element.classList.add('selected');
        yourHandicapSelection = element.getAttribute('diff');
    });
});

theirHandicapSelectionElements = document.querySelectorAll('.handicap-selection[yours="f"]')

theirHandicapSelectionElements.forEach(element => {
    element.addEventListener('click', function () {
        if (element.classList.contains('selected')) {
            element.classList.remove('selected');
            theirHandicapSelection = null;
            return;
        }
        theirHandicapSelectionElements.forEach(element => {
            element.classList.remove('selected');
        });
        element.classList.add('selected');
        theirHandicapSelection = element.getAttribute('diff');
    });
});

document.querySelectorAll('.handicap-selection[yours="t"][diff="easy"]').forEach(element => {
    element.click();
});

document.querySelectorAll('.handicap-selection[yours="f"][diff="easy"]').forEach(element => {
    element.click();
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

function updateTimeControls(body) {
    if (unlimitedTimeCheckbox.checked) {
        return body
    } if (incrementMinutes || incrementSeconds) {
        body['increment'] = parseInt(incrementMinutes.value) * 60 + parseInt(incrementSeconds.value);
    } body['timeControl'] = parseInt(timeControlMinutes.value) * 60 + parseInt(timeControlSeconds.value);
    return body;
}

function newGameBody() {
    ret = {};
    if (gameIdInput.value) {
        ret['gameId'] = gameIdInput.value;
    } if (colorSelection != 'random') {
        ret['color'] = colorSelection;
    } if (yourHandicapSelection){
        ret['yourHandicap'] = yourHandicapSelection;
    } if (theirHandicapSelection){
        ret['theirHandicap'] = theirHandicapSelection;
    } if (username) {
        ret['username'] = username;
    } if (publicCheckbox.checked) {
        ret['public'] = true;
    }
    ret = updateTimeControls(ret);
    return ret
}

function getHandicap() {
    fetchWrapper(URL + 'handicap', { 'gameId': gameId, 'color': color }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            handicapInfo.textContent = data['handicap'];
        });
}

function initGame() {
    gameResultToastElement.style.display = 'none';
    showOpponentsHandicapButton.style.display = 'none';
    setWhoseTurn('White');
    gameIsOver = false;
    whiteboard_messages = [];
    updateWhiteboard();
    initBoard();
}

function newGame(toast = true) {
    fetchWrapper(URL + 'new_game', newGameBody(), 'POST')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                addToWhiteboard(data['error'])
                return;
            }
            setGameId(data['gameId']);
            setOrientation(data['color']);
            getHandicap();
            toast && showToast('Successfully created game', 5);
            updateState();
            ticking = false;
        });
        initGame();
        closeModals();
}

function invite(friend) {
    fetchWrapper(URL + 'invite', { gameId, friend , username })
        .then((response) => response.json())
        .then((data) => {
            showToast(data.success ? `Successfully invited ${friend}` : data.error);
        });
}

function loadGame(game = null, color = null) {
    game = game || gameIdInput.value;
    gameIdInput.value = '';
    if (!game) {
        showToast('Enter the game ID', 3);
        return;
    }
    closeModals();
    gameResultToastElement.style.display = 'none';
    showOpponentsHandicapButton.style.display = 'none';
    d = { 'gameId': game }
    if (username) {
        d['username'] = username;
    } if (color) {
        d['color'] = color;
    }
    fetchWrapper(URL + 'join_game', d, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                showToast(data['error'], 3);
                if (color) {
                    newGame(false);
                }
                return;
            }
            setGameId(game); 
            setOrientation(data['color']);
            gameIsOver = false;
            if (data['winner']) {
                board.position(data['board']);
                processGameOver(data['winner']);
            } else {
                board.position(data['board']);
                setWhoseTurn(data['whoseTurn']);
                getHandicap();
                gameIdInput.value = '';
                showToast('Game loaded', 3);
                mostRecentMove = data['mostRecentMove'];
                ticking = data['ticking'];
                mostRecentMove && updateMostRecentMove(mostRecentMove['from'], mostRecentMove['to']);
                updateTimes(data['whiteTime'], data['blackTime']);
            }
            updateState();
            whiteboard_messages = [];
            updateWhiteboard();
        });
}

function openNewGameModal() {
    closeModals(false);
    newGameModal.style.display = 'flex';
    newGameModalOverlay.style.display = 'block';
}

function openJoinGameModal() {
    closeModals(false);
    joinGameModal.style.display = 'flex';
    joinGameModalOverlay.style.display = 'block';
}

function openRulesModal() {
    closeModals(false);
    rulesModal.style.display = 'flex';
    rulesModalOverlay.style.display = 'block';
}

function openPublicGamesModal() {
    closeModals(false);
    publicGamesModal.style.display = 'flex';
    publicGamesModalOverlay.style.display = 'block';
}

function confirmDraw() {
    confirmDrawElement.style.display = 'inline-block';
}

function confirmResign() {
    confirmResignElement.style.display = 'inline-block';
}

function closeModals(closeToasts=true) {
    newGameModal.style.display = 'none';
    newGameModalOverlay.style.display = 'none';
    joinGameModal.style.display = 'none';
    joinGameModalOverlay.style.display = 'none';
    rulesModal.style.display = 'none';
    rulesModalOverlay.style.display = 'none';
    publicGamesModal.style.display = 'none';
    publicGamesModalOverlay.style.display = 'none';
    if (closeToasts) {
        noDrawButton.click();
        cancelDrawButton.click();
        cancelResignButton.click();
    }
}

function flipVisibility(element) {
    element.style.visibility = element.style.visibility == 'hidden' ? 'visible' : 'hidden';
}

function handleKeyDown(event) {
    k = event.key.toLowerCase();
    if (event.shiftKey) {
        shiftKeyIsDown = true;
    }
    if (event.ctrlKey) {
        return
    }
    else if (k == 'c') {
        if (admin() && event.ctrlKey) {
            showOpponentsHandicap();
        } else {
            copyGameIdButton.click();
        }
    } else if (k == 'escape') {
        closeModals(false);
    } else if (k == 'enter' && newGameModal.style.display == 'flex') {
        event.preventDefault();
        createGameButton.click();
    } else if (k == 'p') {
        displayPromotionOptionsButton.click();
    } else if (k == 'f') {
        displayFriendsListButton.click();
    } else if (k == 'a') {
        ignoreOtherPlayerCheckButton.click();
    } else if (k == 'h') {
        rulesButton.click();
    } else if (k == 'n') {
        newGameButton.click();
    } else if (k == 'j') {
        event.preventDefault();
        openJoinDialogButton.click();
    } else if (k == 'd') {
        toggleThemeButton.click();
    } else if (k == 'o') {
        offerDrawButton.click();
    } else if (k == 'r') {
        resignButton.click();
    } else if (k == 'g') {
        publicGamesButton.click();
    }
}

function handleKeyUp(event) {
    k = event.key.toLowerCase();
    if (event.key == 'Shift') {
        shiftKeyIsDown = false;
    }
}

document.addEventListener("click", function (event) {
    if (event.target === newGameModalOverlay || event.target === joinGameModalOverlay || event.target == rulesModalOverlay || event.target == publicGamesModalOverlay) {
        closeModals(false);
    }
});

newGameButton.addEventListener('click', () => {
    shiftKeyIsDown ? newGame() : openNewGameModal();
});

rulesButton.addEventListener('click', () => {
    openRulesModal();
});

publicGamesButton.addEventListener('click', () => {
    getPublicGames();
    openPublicGamesModal();
});

openJoinDialogButton.addEventListener('click', () => {
    openJoinGameModal();
    gameIdInput.focus();
})

joinGameButton.addEventListener('click', () => {
    loadGame();
});

resignButton.addEventListener('click', () => {
    if (gameIsOver) {
        showToast('Game is over, can\'t resign', 5);
        return ;
    }
    shiftKeyIsDown && confirmResignElement.style.display == 'inline-block' ? resign() : confirmResign();
});

offerDrawButton.addEventListener('click', () => {
    if (gameIsOver) {
        showToast('Game is over, can\'t offer draw', 5);
        return ;
    }
    if (drawToastElement.style.display == 'inline-block') {
        showToast('Respond to your opponent\'s draw offer first', 5);
        return ;
    }
    shiftKeyIsDown && confirmDrawElement.style.display == 'inline-block' ? offerDraw() : confirmDraw();
});

toggleThemeButton.addEventListener('click', () => {
    toggleTheme();
});

createGameButton.addEventListener('click', () => {
    closeModals();
    newGame();
});

function copyToClipboard(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
}

showOpponentsHandicapButton.addEventListener('click', () => {
    showOpponentsHandicap();
});

function showOpponentsHandicap() {
    fetchWrapper(URL + 'handicap', { 'gameId': gameId, 'color': color == 'White' ? 'Black' : 'White' }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            showToast(data['handicap'], 10);
        });
}

function copyGameId() {
    copyToClipboard(gameId);
    showToast(`Copied game id`);
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

    fetchWrapper(URL + 'legal_moves', { 'start': source, 'gameId': gameId, ignoreOtherPlayerCheck , 'promotion': promotionPiece || 'Q'}, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                // This is pretty weird, so always display the error
                addToWhiteboard(data['error']);
                data['exception'] && console.log(`Exception: ${data['exception']}`)
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
                // If there's an exception field, something went really wrong. If there's not, you might have just dragged a piece to an illegal square or something.
                if (data['exception']) {
                    console.log(`Exception: ${data['exception']}`)
                    addToWhiteboard(data['error'])
                }
                // If we get an error, we need to pull down the state to undo the move on the frontend
                updateState();
                return;
            }
            else {
                board.move(`${from}-${to}`, false); // this should be unnecessary except in a retry but it doesn't hurt anyway
                updateMostRecentMove(from, to);
                data['whoseTurn'] && setWhoseTurn(data['whoseTurn']);
                data['winner'] && processGameOver(data['winner']);
                updateTimes(data['whiteTime'], data['blackTime']);
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
            if (data['mostRecentMove']) {
                updateMostRecentMove(data['mostRecentMove']['from'], data['mostRecentMove']['to']);
            }
            ticking = data['ticking'];
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

function populateFriendsList() {
    fetchWrapper(URL + 'friends', { 'username': username }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            }
            displayFriends(data['online'], data['offline'])
        })
}

setInterval(function () {
    if (!username) {
        return;
    } else {
        populateFriendsList();
    }
}, 3000);

function toggleTheme() {
    document.body.classList.toggle('dark');
    currentThemeIsDark = document.body.classList.contains('dark');
    localStorage.setItem('hchess-dark-mode', currentThemeIsDark);
}

function makeFriendElement(name, isOnline) {
    onClick = isOnline ? `onclick="invite('${name}')"` : '';
    content = `<button class="game-button ${isOnline ? "active" : "dead"} ${currentThemeIsDark ? 'dark' : ''}" ${onClick}>Invite ${name}</button>`
    return `
        <div class="friend">
            ${content}
            <button class="remove-friend-button ${currentThemeIsDark ? 'dark' : ''}" onClick="removeFriend('${name}')">
                X
            </button>
        </div>
    `;
}

function displayFriends(online, offline) {
    activeGamesWrapper.innerHTML = '<h4> Friends </h4>';
    online.forEach(name => {
        activeGamesWrapper.innerHTML += makeFriendElement(name, true);
    });
    offline.forEach(name => {
        activeGamesWrapper.innerHTML += makeFriendElement(name, false);
    });
}

setInterval(() => {
    if (currentWidth != window.innerWidth || currentHeight != window.innerHeight) {
        currentWidth = window.innerWidth;
        currentHeight = window.innerHeight;
        !holdingPiece && board.resize();
        highlightMostRecentMove();
    }
}, 100);

function rejoin() {
    fetchWrapper('rejoin', {username}, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                newGame(false);
            } else {
                initGame() || loadGame(data['gameId'], data['color'])
            }
        });
}

function getPublicGames() {
    fetchWrapper('public_games', {}, 'GET')
        .then((response) => response.json())
        .then((data) => {
            if (!data['success']) {
                return;
            }
            displayPublicGames(data['games']);
        });
}

function makePublicGameElement(game) {
    pgusername = game['username'];
    if (pgusername.length > 20) {
        pgusername = pgusername.substring(0, 20) + '...';
    }
    pggameId = game['gameId'];
    pgcolor = game['color'];
    pgdifficulty = game['difficulty'];
    onClick = `onclick="loadGame('${pggameId}')"`;
    content = `<button class="game-button small active ${currentThemeIsDark ? 'dark' : ''}" ${onClick}>Join as ${pgcolor.toLowerCase()} (Handicap: ${pgdifficulty})</button>`
    return `
        <div class="friend">
            <span class="public-game-username"> ${pgusername} </span>
            ${content}
        </div> 
    `;
}

setInterval(() => {
    if (publicGamesModal.style.display == 'flex') {
        getPublicGames();
    }
}, 3000);

function displayPublicGames(games) {
    publicGamesWrapper.innerHTML = '<h4> Public Games </h4>';

    games = games.filter(game => game['gameId'] != gameId);

    games.forEach(game => {
        publicGamesWrapper.innerHTML += makePublicGameElement(game);
    });

    if (games.length == 0) {
        publicGamesWrapper.innerHTML += '<span> No public games </span>';
    }

}

hotkeysVisibilityButton.addEventListener('click', () => {
    hotkeysElement.style.display = hotkeysElement.style.display == 'none' ? 'grid' : 'none';
    hotkeysVisibilityButton.textContent = hotkeysElement.style.display == 'none' ? 'Show' : 'Hide';
    localStorage.setItem('hchess-hotkeys', hotkeysElement.style.display);
});

if (localStorage.getItem('hchess-dark-mode') == 'true') {
    toggleTheme();
}

admin() && (whiteKingElement.click() || toggleOtherPlayerCheck());

updateWhiteboard();

rejoin();
populateFriendsList();

if (!localStorage.getItem('hchess-cookie')) {
    openRulesModal();    
    localStorage.setItem('hchess-cookie', 'true');
}

if (localStorage.getItem('hchess-hotkeys') == 'none') {
    hotkeysVisibilityButton.click();
}