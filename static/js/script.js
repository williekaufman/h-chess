// URL = 'http://ec2-34-192-101-140.compute-1.amazonaws.com:5003/'

URL = 'http://localhost:5001/'

previousToast = null;
get_btn = document.getElementById('get-button');
set_btn = document.getElementById('set-button'); 

key = document.getElementById('key');
value = document.getElementById('value');

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

fetchWrapper(URL + 'example', {}, 'GET')
    .then((response) => response.json())
    .then((data) => {
        document.getElementById('example').textContent = data['message'];
    }
    )

set_btn.addEventListener('click', () => {
    set(key, value);
});

get_btn.addEventListener('click', () => {
    get(key.value);
});

async function set(key, value) {
    fetchWrapper(URL + 'rset', { 'value': value.value, 'key': key.value })
}

async function get(key) {
    fetchWrapper(URL + 'rget', { key }, 'GET')
        .then((response) => response.json())
        .then((data) => {
            console.log(data);
            value.value = data.value;
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

document.addEventListener('keydown', handleKeyDown);

